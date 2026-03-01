# providers/llm/fallback.py

import time
from typing import Type, TypeVar

from pydantic import BaseModel

from providers.llm.vllm import VLLMProvider
from providers.llm.gemini import GeminiProvider
from core.logging import get_logger
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage

T = TypeVar("T", bound=BaseModel)
logger = get_logger(__name__)

_FALLBACK_ERRORS = {
    ErrorMessage.LLM_SERVICE_UNAVAILABLE,
    ErrorMessage.LLM_TIMEOUT,
}


class FallbackLLMProvider:
    """vLLM primary → Gemini fallback Provider (TTL 기반 Lazy 재시도)

    - vLLM 호출 실패(연결 불가/타임아웃) 시 Gemini로 자동 전환
    - TTL(RETRY_INTERVAL) 경과 후 다음 요청에서 vLLM 재시도
    - 재시도 성공 시 vLLM 복귀, 실패 시 TTL 갱신 후 Gemini 유지

    NOTE: TTL 만료 직후 vLLM 재시도-실패 시, 해당 1회 요청은
    vLLM용 system_prompt로 Gemini가 호출될 수 있음 (provider_name 참조 시점 차이).
    다음 요청부터는 provider_name이 "gemini"를 반환하므로 정상 동작.
    """

    DEFAULT_RETRY_INTERVAL = 300  # 5분

    def __init__(
        self,
        primary: VLLMProvider,
        fallback: GeminiProvider,
        retry_interval: int = DEFAULT_RETRY_INTERVAL,
    ):
        self._primary = primary
        self._fallback = fallback
        self._retry_interval = retry_interval
        self._fallback_since: float | None = None

    @property
    def _using_fallback(self) -> bool:
        if self._fallback_since is None:
            return False
        if time.time() - self._fallback_since > self._retry_interval: # TTL 만료 시 vLLM 재시도 허용
            logger.info("TTL 만료 → vLLM 재시도 허용")
            self._fallback_since = None
            return False
        return True

    def _mark_fallback(self) -> None:
        self._fallback_since = time.time()
        logger.warning(
            f"vLLM → Gemini fallback 전환 | "
            f"retry_after={self._retry_interval}s"
        )

    @property
    def provider_name(self) -> str:
        if self._using_fallback:
            return self._fallback.provider_name
        return self._primary.provider_name

    def _is_fallback_error(self, exc: AppException) -> bool:
        try:
            return ErrorMessage(exc.message) in _FALLBACK_ERRORS
        except ValueError:
            return False

    async def generate(
        self,
        prompt: str,
        response_model: Type[T],
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        if not self._using_fallback:
            try:
                return await self._primary.generate(
                    prompt=prompt,
                    response_model=response_model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except AppException as e:
                if not self._is_fallback_error(e):
                    raise
                self._mark_fallback()

        return await self._fallback.generate(
            prompt=prompt,
            response_model=response_model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> T:
        if not self._using_fallback:
            try:
                return await self._primary.generate_structured(
                    prompt=prompt,
                    response_model=response_model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except AppException as e:
                if not self._is_fallback_error(e):
                    raise
                self._mark_fallback()

        return await self._fallback.generate_structured(
            prompt=prompt,
            response_model=response_model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
