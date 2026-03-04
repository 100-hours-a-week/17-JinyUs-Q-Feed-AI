# providers/stt/fallback.py

import time
from typing import Callable, Awaitable

from core.logging import get_logger
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage

logger = get_logger(__name__)

TranscribeFunc = Callable[[str], Awaitable[str]]

# GPU STT → HuggingFace 로 fallback 을 트리거할 에러 타입들
# - 서비스 불가 / 타임아웃 / 서버 연결 실패
# - GPU 서버 내부 오류로 인한 STT_CONVERSION_FAILED
_FALLBACK_ERRORS = {
    ErrorMessage.STT_SERVICE_UNAVAILABLE,
    ErrorMessage.STT_TIMEOUT,
    ErrorMessage.SERVER_CONNECTION_FAILED,
    ErrorMessage.STT_CONVERSION_FAILED,
}


class FallbackSTTProvider:
    """GPU STT primary → HuggingFace fallback Provider (TTL 기반 Lazy 재시도)

    - GPU STT 호출 실패(연결 불가/타임아웃/503) 시 HuggingFace로 자동 전환
    - TTL(retry_interval) 경과 후 다음 요청에서 GPU STT 재시도
    - 재시도 성공 시 GPU STT 복귀, 실패 시 TTL 갱신 후 HuggingFace 유지
    """

    DEFAULT_RETRY_INTERVAL = 300  # 5분

    def __init__(
        self,
        primary_fn: TranscribeFunc,
        primary_name: str,
        fallback_fn: TranscribeFunc,
        fallback_name: str,
        retry_interval: int = DEFAULT_RETRY_INTERVAL,
    ):
        self._primary_fn = primary_fn
        self._primary_name = primary_name
        self._fallback_fn = fallback_fn
        self._fallback_name = fallback_name
        self._retry_interval = retry_interval
        self._fallback_since: float | None = None

    @property
    def _using_fallback(self) -> bool:
        if self._fallback_since is None:
            return False
        if time.time() - self._fallback_since > self._retry_interval:
            logger.info("TTL 만료 → GPU STT 재시도 허용")
            self._fallback_since = None
            return False
        return True

    def _mark_fallback(self) -> None:
        self._fallback_since = time.time()
        logger.warning(
            f"GPU STT → HuggingFace fallback 전환 | "
            f"retry_after={self._retry_interval}s"
        )

    @property
    def provider_name(self) -> str:
        if self._using_fallback:
            return self._fallback_name
        return self._primary_name

    @staticmethod
    def _is_fallback_error(exc: AppException) -> bool:
        try:
            return ErrorMessage(exc.message) in _FALLBACK_ERRORS
        except ValueError:
            return False

    async def transcribe(self, audio_url: str) -> str:
        if not self._using_fallback:
            try:
                return await self._primary_fn(audio_url)
            except AppException as e:
                if not self._is_fallback_error(e):
                    raise
                self._mark_fallback()

        return await self._fallback_fn(audio_url)
