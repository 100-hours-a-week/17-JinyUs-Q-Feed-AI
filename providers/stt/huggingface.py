import httpx
from core.config import get_settings
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage
from pathlib import Path

settings = get_settings()

# MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
headers = {
    "Authorization": f"Bearer {settings.huggingface_api_key}",
}

# S3 테스트 후 삭제해도됨
CONTENT_TYPE_MAP = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
}

async def download_audio(url: str) -> bytes:
    """오디오 다운로드"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code == 404:
                raise AppException(ErrorMessage.AUDIO_NOT_FOUND)
            elif response.status_code == 403:
                raise AppException(ErrorMessage.S3_ACCESS_FORBIDDEN)
            response.raise_for_status()
            return response.content
            
    except AppException:
        raise  # 우리가 던진 건 그대로 전파
    except httpx.TimeoutException:
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_TIMEOUT)
    except httpx.RequestError:
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)
    except Exception:
        # 예상치 못한 에러
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)


def get_content_type(audio_url: str) -> str:
    ext = Path(audio_url).suffix.lower()  # URL에서 확장자 추출
    # 쿼리 파라미터 제거 필요!
    if '?' in audio_url:
        audio_url = audio_url.split('?')[0]
    ext = Path(audio_url).suffix.lower()
    return CONTENT_TYPE_MAP[ext]


async def transcribe(audio_url: str) -> str:
    """Presigned URL에서 오디오 다운로드하여 STT 수행"""
    content_type = get_content_type(audio_url)
    audio_data = await download_audio(audio_url)

    # Huggingface API 호출
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                API_URL,
                headers={"Content-Type": content_type, **headers},
                content=audio_data,
            )
            response.raise_for_status()
            return response.json()["text"]
    except httpx.TimeoutException:
        raise AppException(ErrorMessage.STT_TIMEOUT)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise AppException(ErrorMessage.RATE_LIMIT_EXCEEDED)
        raise AppException(ErrorMessage.STT_CONVERSION_FAILED)
        
