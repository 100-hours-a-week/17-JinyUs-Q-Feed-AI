# exceptions/error_messages.py
from enum import Enum


class ErrorMessage(str, Enum):
    """API 에러 메시지 (응답 body의 message 필드로 전송)"""
    # STT 관련
    AUDIO_TOO_LONG = "audio_too_long"
    AUDIO_TOO_LARGE = "audio_too_large"
    INVALID_AUDIO_FORMAT = "invalid_audio_format"
    AUDIO_NOT_FOUND = "audio_not_found"
    SESSION_NOT_FOUND = "session_not_found"
    STT_TIMEOUT = "stt_timeout"
    AUDIO_UNPROCESSABLE = "audio_unprocessable"
    STT_CONVERSION_FAILED = "stt_conversion_failed"
    STT_SERVICE_UNAVAILABLE = "stt_service_unavailable"

    # Feedback 관련
    FEEDBACK_GENERATION_FAILED = "feedback_generation_failed"
    INVALID_ANSWER_FORMAT = "invalid_answer_format"

    # 공통
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SERVICE_TEMPORARILY_UNAVAILABLE = "service_temporarily_unavailable"


# HTTP status code 매핑
ERROR_STATUS_CODE: dict[ErrorMessage, int] = {
    # 400 Bad Request
    ErrorMessage.AUDIO_TOO_LONG: 400,
    ErrorMessage.AUDIO_TOO_LARGE: 400,
    ErrorMessage.INVALID_AUDIO_FORMAT: 400,
    ErrorMessage.INVALID_ANSWER_FORMAT: 400,

    # 404 Not Found
    ErrorMessage.AUDIO_NOT_FOUND: 404,
    ErrorMessage.SESSION_NOT_FOUND: 404,

    # 408 Request Timeout
    ErrorMessage.STT_TIMEOUT: 408,

    # 422 Unprocessable Entity
    ErrorMessage.AUDIO_UNPROCESSABLE: 422,

    # 429 Too Many Requests
    ErrorMessage.RATE_LIMIT_EXCEEDED: 429,

    # 500 Internal Server Error
    ErrorMessage.STT_CONVERSION_FAILED: 500,
    ErrorMessage.FEEDBACK_GENERATION_FAILED: 500,

    # 502 Bad Gateway
    ErrorMessage.STT_SERVICE_UNAVAILABLE: 502,

    # 503 Service Unavailable
    ErrorMessage.SERVICE_TEMPORARILY_UNAVAILABLE: 503,
}
