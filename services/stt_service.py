
from typing import Callable, Awaitable

from core.config import get_settings
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage
from providers.stt.huggingface import transcribe
# from services.providers.stt.runpod import transcribe as runpod_transcribe   

MAX_SIZE = 10 * 1024 * 1024  # 10 MB
# Provider 함수 타입
TranscribeFunc = Callable[[str], Awaitable[str]]
settings = get_settings()

def get_stt_provider() -> TranscribeFunc:
     """설정에 따라 STT provider 반환 - gpu 인스턴스 장애 시 huggingface로 전환 가능"""
     if settings.stt_provider == "huggingface":
         return transcribe 
    # runpod 이전 시
    #  elif settings.stt_provider == "runpod":
    #      return runpod_transcribe
    

async def process_transcribe(audio_url: str) -> str:
    """음성 파일을 텍스트로 변환 처리"""
    # 2. STT 변환 처리
    provider = get_stt_provider()

    text = await provider(audio_url)  # AppException은 그냥 통과
    
    if not text or not text.strip():
        raise AppException(ErrorMessage.AUDIO_UNPROCESSABLE)
    
    return text
