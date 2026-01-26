
from typing import Callable, Awaitable
import httpx

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
    
async def get_file_size(url: str) -> int:
    """S3 오디오 파일 유무 및 크기 조회"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            print(response)
            ## 
            if response.status_code == 200:
                return int(response.headers.get("content-length", 0))
            # 상태 코드별로 구체적인 에러 발생
            
            elif response.status_code == 403:
                raise AppException(ErrorMessage.S3_ACCESS_FORBIDDEN)
            elif response.status_code == 404:
                raise AppException(ErrorMessage.AUDIO_NOT_FOUND)
            else:
                raise AppException(ErrorMessage.AUDIO_ACCESS_FAILED)
        
    except httpx.RequestError:
        return None


async def process_transcribe(audio_url: str) -> str:
        
        # 1. 사전 검증 (provider 호출 전)
        file_size = await get_file_size(audio_url)
        
        if file_size is None:
            raise AppException(ErrorMessage.AUDIO_NOT_FOUND)
        
        if file_size > MAX_SIZE:
            raise AppException(ErrorMessage.AUDIO_TOO_LARGE)
        
        if file_size == 0:             # 빈 파일
            raise AppException(ErrorMessage.AUDIO_EMPTY)

        # 2. STT 변환 처리
        provider = get_stt_provider()
        print(f"Provider: {provider}")  # 디버깅용
        print(f"Audio URL: {audio_url}")  # 디버깅용

        try:
            text = await provider(audio_url)
        except httpx.TimeoutException:
            raise AppException(ErrorMessage.STT_TIMEOUT)
        except httpx.ConnectError:
            raise AppException(ErrorMessage.STT_SERVICE_UNAVAILABLE)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                raise AppException(ErrorMessage.AUDIO_UNPROCESSABLE)
            elif e.response.status_code == 429:
                raise AppException(ErrorMessage.RATE_LIMIT_EXCEEDED)
            else:
                raise AppException(ErrorMessage.STT_CONVERSION_FAILED)
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")  # 실제 에러 확인
            raise AppException(ErrorMessage.STT_CONVERSION_FAILED)
        
        if not text or not text.strip():
            raise AppException(ErrorMessage.AUDIO_UNPROCESSABLE)
        
        return text
