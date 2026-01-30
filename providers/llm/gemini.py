# providers/llm/gemini.py

import json
import time
from typing import Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from core.config import get_settings
from core.logging import get_logger, get_metrics_logger
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage


T = TypeVar("T", bound=BaseModel)
settings = get_settings()
logger = get_logger(__name__)
metrics_logger = get_metrics_logger()


class GeminiProvider:
    """Google Gemini Provider"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        self.model = model or settings.GEMINI_MODEL_ID

    async def generate(
        self,
        prompt: str,
        response_model: Type[T],
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """일반 텍스트 생성"""
        full_prompt = self._build_prompt(prompt, system_prompt)
        task_name = response_model.__name__

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await self._call_api(full_prompt, task_name, config)
        return response.text

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> T:
        """Structured Output 생성 - JSON 파싱하여 Pydantic 모델로 반환"""
        full_prompt = self._build_prompt(prompt, system_prompt)
        schema = response_model.model_json_schema()
        task_name = response_model.__name__

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=schema,
        )

        response = await self._call_api(full_prompt, task_name, config)

        try:
            parsed_data = json.loads(response.text)
            result = response_model.model_validate(parsed_data)
            logger.debug(f"JSON 파싱 성공 | model={task_name}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패 | model={task_name} | error={e}")
            raise AppException(ErrorMessage.LLM_RESPONSE_PARSE_FAILED) from e
        except ValidationError as e:  # pydantic에서 import
            logger.error(f"Pydantic 검증 실패 | model={task_name} | error={e}")
            raise AppException(ErrorMessage.LLM_RESPONSE_PARSE_FAILED) from e
        except Exception as e:
            logger.error(f"응답 처리 실패 | model={task_name} | {type(e).__name__}: {e}")
            raise AppException(ErrorMessage.LLM_RESPONSE_PARSE_FAILED) from e
        

    async def _call_api(
        self,
        prompt: str,
        task: str,
        config: types.GenerateContentConfig,
    ):
        """Gemini API 호출 - 공통 에러 처리"""
        start_time = time.perf_counter()
        prompt_length = len(prompt)
        
        logger.debug(f"Gemini API 호출 시작 | task={task} | model={self.model}")
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            response_length = len(response.text) if response.text else 0
            
            logger.debug(f"Gemini API 완료 | task={task} | {elapsed_ms:.2f}ms")
            
            # 메트릭 로깅
            metrics_logger.info(
                f"LLM_METRIC | provider=gemini | model={self.model} | task={task} | prompt_chars={prompt_length} | "
                f"response_chars={response_length} | latency_ms={elapsed_ms:.2f}"
            )
            
            return response
        
        except TimeoutError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Gemini API 타임아웃 | task={task} | {elapsed_ms:.2f}ms")
            raise AppException(ErrorMessage.LLM_TIMEOUT) from e
        except ConnectionError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Gemini API 연결 실패 | task={task} | {elapsed_ms:.2f}ms")
            raise AppException(ErrorMessage.LLM_SERVICE_UNAVAILABLE) from e
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_message = str(e).lower()
            
            if "timeout" in error_message:
                logger.error(f"Gemini API 타임아웃 | task={task} | {elapsed_ms:.2f}ms")
                raise AppException(ErrorMessage.LLM_TIMEOUT) from e
            if "connection" in error_message or "unavailable" in error_message:
                logger.error(f"Gemini API 연결 실패 | task={task} | {elapsed_ms:.2f}ms")
                raise AppException(ErrorMessage.LLM_SERVICE_UNAVAILABLE) from e
            
            logger.error(f"Gemini API 에러 | task={task} | {elapsed_ms:.2f}ms | {type(e).__name__}: {e}")
            raise AppException(ErrorMessage.LLM_SERVICE_UNAVAILABLE) from e

    def _build_prompt(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> str:
        """프롬프트 구성"""
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt