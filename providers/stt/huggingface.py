import httpx
import time
from pathlib import Path

from core.config import get_settings
from core.logging import get_logger, get_metrics_logger, log_execution_time
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage

logger = get_logger(__name__)
metrics_logger = get_metrics_logger()   
settings = get_settings()

# MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
headers = {
    "Authorization": f"Bearer {settings.huggingface_api_key}",
}

CONTENT_TYPE_MAP = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/x-m4a",
    ".m4a": "audio/x-m4a",
}


@log_execution_time(logger)
async def download_audio(url: str) -> bytes:
    """오디오 다운로드"""
    logger.debug("오디오 다운로드 시작")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code == 404:
                logger.warning("오디오 파일 없음 | status=404")
                raise AppException(ErrorMessage.AUDIO_NOT_FOUND)
            elif response.status_code == 403:
                logger.warning("S3 접근 거부 | status=403")
                raise AppException(ErrorMessage.S3_ACCESS_FORBIDDEN)
            
            response.raise_for_status()
            audio_data = response.content
            
            logger.info(f"size={len(audio_data) / 1024:.1f}KB")
            return audio_data
            
    except AppException:
        raise  # 우리가 던진 건 그대로 전파
    except httpx.TimeoutException:
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_TIMEOUT)
    except httpx.RequestError as re:
        logger.error(f"오디오 다운로드 실패 |{type(re).__name__}: {re}")
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)
    except Exception as e:
        # 예상치 못한 에러
        logger.error(f"오디오 다운로드 예외 |{type(e).__name__}: {e}")
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)


def get_content_type(audio_url: str) -> str:
    ext = Path(audio_url).suffix.lower()  # URL에서 확장자 추출
    # 쿼리 파라미터 제거 필요!
    if '?' in audio_url:
        audio_url = audio_url.split('?')[0]
    ext = Path(audio_url).suffix.lower()
    return CONTENT_TYPE_MAP[ext]

@log_execution_time(logger)
async def transcribe(audio_url: str) -> str:
    """Presigned URL에서 오디오 다운로드하여 STT 수행"""
    content_type = get_content_type(audio_url)
    audio_data = await download_audio(audio_url)
    audio_size_kb = len(audio_data) / 1024

    logger.debug("Huggingface API 호출 시작 | model=whisper-large-v3-turbo | content_type={content_type} | audio_size={audio_size_kb:.1f}KB")
    api_start = time.perf_counter()

    # Huggingface API 호출
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                API_URL,
                headers={"Content-Type": content_type, **headers},
                content=audio_data,
            )
            response.raise_for_status()
            text = response.json()["text"]
            
            api_elapsed_ms = (time.perf_counter() - api_start) * 1000
            logger.info(f"Huggingface API 완료(순수 STT 시간) | {api_elapsed_ms:.2f}ms")
            
            # 메트릭 로깅 (성공 시에만)
            metrics_logger.info(
                f"STT_METRIC | provider=huggingface | model=whisper-large-v3-turbo | "
                f"audio_size_kb={audio_size_kb:.1f} | api_latency_ms={api_elapsed_ms:.2f} | "
                f"text_length={len(text)}"
            )
            
            return text
    except httpx.TimeoutException:
        logger.error("Huggingface API 타임아웃 ")
        raise AppException(ErrorMessage.STT_TIMEOUT)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.warning("Huggingface API 인증 실패")
            raise AppException(ErrorMessage.API_KEY_INVALID)
        if e.response.status_code == 429:
            logger.warning("Huggingface Rate Limit 초과")
            raise AppException(ErrorMessage.RATE_LIMIT_EXCEEDED)
        raise AppException(ErrorMessage.STT_CONVERSION_FAILED)
        
