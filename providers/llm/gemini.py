# providers/llm/gemini.py

import json
from typing import Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from core.config import settings


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
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=config,
        )
        
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
        # ✅ 프롬프트는 스키마 없이 구성
        full_prompt = self._build_prompt(prompt, system_prompt)
        schema = response_model.model_json_schema()
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=schema,  # 스키마는 여기로!
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,  # 스키마가 없는 프롬프트
            config=config,
        )
        print(f"raw_text : {response.text}")
        
        parsed_data = json.loads(response.text)
        return response_model.model_validate(parsed_data)
    
    def _build_prompt(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> str:
        """프롬프트 구성"""
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt
    