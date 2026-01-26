# providers/llm/gemini.py

import json
from typing import Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from core.config import settings
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage


T = TypeVar("T", bound=BaseModel)


class GeminiProvider:
    """Google Gemini Provider"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.client = genai.Client(api_key=api_key or settings.gemini_api_key)
        self.model = model or settings.gemini_model_id

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """일반 텍스트 생성"""
        full_prompt = self._build_prompt(prompt, system_prompt)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await self._call_api(full_prompt, config)
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

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=schema,
        )

        response = await self._call_api(full_prompt, config)

        try:
            parsed_data = json.loads(response.text)
            return response_model.model_validate(parsed_data)
        except json.JSONDecodeError as e:
            raise AppException(ErrorMessage.LLM_RESPONSE_PARSE_FAILED) from e
        except Exception as e:
            raise AppException(ErrorMessage.LLM_RESPONSE_PARSE_FAILED) from e

    async def _call_api(
        self,
        prompt: str,
        config: types.GenerateContentConfig,
    ):
        """Gemini API 호출 - 공통 에러 처리"""
        try:
            return await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        except TimeoutError as e:
            raise AppException(ErrorMessage.LLM_TIMEOUT) from e
        except ConnectionError as e:
            raise AppException(ErrorMessage.LLM_SERVICE_UNAVAILABLE) from e
        except Exception as e:
            error_message = str(e).lower()
            if "timeout" in error_message:
                raise AppException(ErrorMessage.LLM_TIMEOUT) from e
            if "connection" in error_message or "unavailable" in error_message:
                raise AppException(ErrorMessage.LLM_SERVICE_UNAVAILABLE) from e
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