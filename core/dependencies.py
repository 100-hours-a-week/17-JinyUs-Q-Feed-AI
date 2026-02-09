# core/dependencies.py
from functools import lru_cache
from core.config import get_settings
from providers.llm.vllm import VLLMProvider
from providers.llm.gemini import GeminiProvider


# from providers.stt.base import STTProvider
# from providers.stt.huggingface import HuggingFaceSTTProvider
settings = get_settings()

@lru_cache
def get_llm_provider() -> VLLMProvider:
    if settings.LLM_PROVIDER == "vllm":
        return VLLMProvider()
    return GeminiProvider()


# @lru_cache  
# def get_stt_provider() -> STTProvider:
#     if settings.STT_PROVIDER == "huggingface":

#         return HuggingFaceSTTProvider()

#     return RunpodSTTProvider()