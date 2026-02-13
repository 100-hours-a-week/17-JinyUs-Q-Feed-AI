
from typing import Callable, Awaitable

from core.config import get_settings
from core.logging import get_logger, log_execution_time
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage
from providers.stt.huggingface import transcribe
from providers.stt.gpu_stt import transcribe as runpod_transcribe   

logger = get_logger(__name__)

# Provider 함수 타입
TranscribeFunc = Callable[[str], Awaitable[str]]
settings = get_settings()

def get_stt_provider() -> TranscribeFunc:
    """설정에 따라 STT provider 반환"""
    if settings.STT_PROVIDER == "huggingface":
        return transcribe
    elif settings.STT_PROVIDER == "runpod":
        return runpod_transcribe
    return transcribe
    
@log_execution_time(logger)
async def process_transcribe(audio_url: str) -> str:
    """음성 파일을 텍스트로 변환 처리"""
    file_name = audio_url.split('?')[0].split('/')[-1] if audio_url else "unknown"
    logger.debug(f"STT 변환 시작 | file={file_name}")

    # 2. STT 변환 처리
    provider = get_stt_provider()

    text = await provider(audio_url)  # AppException은 그냥 통과
    
    if not text or not text.strip():
        logger.warning(f"STT 결과 비어있음 | file={file_name}")
        raise AppException(ErrorMessage.AUDIO_UNPROCESSABLE)
    
    logger.info(f"STT 변환 완료 | file={file_name}")
    return text
