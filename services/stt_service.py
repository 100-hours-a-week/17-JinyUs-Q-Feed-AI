
from typing import Callable, Awaitable
import httpx

from core.config import settings
from exceptions.error_messages import ErrorMessage
from exceptions.exceptions import AppException

from providers.stt.huggingface import transcribe, transcribe_local
# from services.providers.stt.runpod import transcribe as runpod_transcribe   

MAX_SIZE = 10 * 1024 * 1024  # 10 MB
# Provider 함수 타입
TranscribeFunc = Callable[[str], Awaitable[str]]

def get_stt_provider() -> TranscribeFunc:
     """설정에 따라 STT provider 반환 - gpu 인스턴스 장애 시 huggingface로 전환 가능"""
     if settings.stt_provider == "huggingface":
         # s3 세팅될대까지 local로 테스트
         return transcribe_local 
    # runpod 이전 시
    #  elif settings.stt_provider == "runpod":
    #      return runpod_transcribe
    
async def get_file_size(url: str) -> int:
    """S3 오디오 파일 크기 조회"""
    try:
        # s3에서 HEAD 요청으로 파일 크기 가져오기
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(url)
            if response.status_code == 404:
                return None
            return int(response.headers.get("content-length", 0))
    except httpx.RequestError:
        return None


async def process_transcribe(audio_url: str) -> str:
        # file_size = await get_file_size(audio_url)

        # if file_size is None:
        #     raise AppException(ErrorMessage.AUDIO_NOT_FOUND)
        
        # if file_size > MAX_SIZE:
        #     raise AppException(ErrorMessage.AUDIO_TOO_LARGE)
        
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


        #S3에서 파일 찾기
        if not await check_s3_exists(andio_url):
            ## 사용자정의 에러로 변경할 것
            raise FileNotFoundError("Audio file not found in S3.")
        
        #파일 크기 초과
        if file_size > MAX_SIZE:
            ## 사용자정의 에러로 변경할 것
            raise ValueError("Audio file size exceeds the maximum limit.")  
