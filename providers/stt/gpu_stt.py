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
        logger.error("오디오 다운로드 타임 아웃")
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_TIMEOUT)
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            logger.error(f"서버 내부 오류 | status={e.response.status_code}")
            raise AppException(ErrorMessage.INTERNAL_SERVER_ERROR)
        logger.error(f"오디오 다운로드 에러 | status={e.response.status_code}")
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)
    except httpx.RequestError as re:
        logger.error(f"네트워크 연결 실패 | {type(re).__name__}: {re}")
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)
    except Exception as e:
        # 예상치 못한 에러
        logger.error(f"오디오 다운로드 예외 |{type(e).__name__}: {e}")
        raise AppException(ErrorMessage.AUDIO_DOWNLOAD_FAILED)
    
def get_filename(audio_url: str) -> str:
    """URL에서 파일명 추출"""
    if "?" in audio_url:
        audio_url = audio_url.split("?")[0]
    return Path(audio_url).name or "audio.mp4"

@log_execution_time(logger)
async def transcribe(audio_url: str, language: str = "ko") -> str:
    """Presigned URL에서 오디오 다운로드하여 RunPod GPU 인스턴스로 STT 수행"""
    filename = get_filename(audio_url)
    audio_data = await download_audio(audio_url)
    audio_size_kb = len(audio_data) / 1024

    logger.debug(
        f"RunPod API 호출 시작 | model=whisper-large-v3-turbo | "
        f"filename={filename} | audio_size={audio_size_kb:.1f}KB"
    )
    api_start = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.GPU_BASE_URL}/whisper/stt",
                files={"audio": (filename, audio_data)},
                data={"language": language},
            )

            if response.status_code == 503:
                logger.error("RunPod 모델 미로드 | status=503")
                raise AppException(ErrorMessage.STT_SERVICE_UNAVAILABLE)

            if response.status_code == 400:
                logger.error(f"오디오 디코딩 실패 | detail={response.text}")
                raise AppException(ErrorMessage.AUDIO_UNPROCESSABLE)

            response.raise_for_status()
            result = response.json()
            text = result.get("text", "").strip()

            api_elapsed_ms = (time.perf_counter() - api_start) * 1000

            logger.info(
                f"RunPod API 완료 | duration={result.get('duration', 0):.1f}s | "
                f"processing_time={result.get('processing_time_ms', 0):.0f}ms | "
                f"api_latency={api_elapsed_ms:.0f}ms"
            )

            # 메트릭 로깅
            metrics_logger.info(
                f"STT_METRIC | provider=runpod | model=whisper-large-v3-turbo | "
                f"audio_size_kb={audio_size_kb:.1f} | api_latency_ms={api_elapsed_ms:.2f} | "
                f"audio_duration_s={result.get('duration', 0):.1f} | "
                f"text_length={len(text)}"
            )

            return text

    except AppException:
        raise
    except httpx.TimeoutException:
        logger.error("RunPod API 타임아웃")
        raise AppException(ErrorMessage.STT_TIMEOUT)
    except httpx.HTTPStatusError as e:
        logger.error(
            "RunPod API 에러",
            extra={
                "status_code": e.response.status_code,
                "response_text": e.response.text,
            },
        )
        if e.response.status_code == 429:
            logger.warning("RunPod Rate Limit 초과")
            raise AppException(ErrorMessage.RATE_LIMIT_EXCEEDED)
        raise AppException(ErrorMessage.STT_CONVERSION_FAILED)
    except httpx.RequestError as re:
        logger.error(f"RunPod 연결 실패 | {type(re).__name__}: {re}")
        raise AppException(ErrorMessage.STT_CONNECTION_FAILED)
    except Exception as e:
        logger.error(f"RunPod STT 예외 | {type(e).__name__}: {e}")
        raise AppException(ErrorMessage.STT_CONVERSION_FAILED)