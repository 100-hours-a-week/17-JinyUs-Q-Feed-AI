from langfuse import observe

from core.logging import get_logger
from core.tracing import update_span
from core.dependencies import get_stt_provider
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage

logger = get_logger(__name__)


@observe(name="stt_service")
async def process_transcribe(audio_url: str) -> str:
    """음성 파일을 텍스트로 변환 처리"""

    file_name = audio_url.split('?')[0].split('/')[-1] if audio_url else "unknown"
    logger.debug(f"STT transcribe start | file={file_name}")

    provider = get_stt_provider()
    update_span(metadata={"provider": provider.provider_name, "file_name": file_name})

    try:
        text = await provider.transcribe(audio_url)

        if not text or not text.strip():
            logger.warning(f"STT result is empty | file={file_name}")   
            raise AppException(ErrorMessage.AUDIO_UNPROCESSABLE)

        logger.info(f"STT transcribe completed | file={file_name}")
        update_span(output={"text_length": len(text)})

        return text
    except AppException:
        raise
    except Exception as e:
        logger.error(f"STT transcribe error | file={file_name} | {type(e).__name__}: {e}")
        raise AppException(ErrorMessage.STT_CONVERSION_FAILED) from e
