# exceptions/error_messages.py
from enum import Enum


class ErrorMessage(str, Enum):
    """API 에러 메시지 (응답 body의 message 필드로 전송)"""
    # STT 관련
    AUDIO_NOT_FOUND = "audio_not_found"
    STT_TIMEOUT = "stt_timeout"
    AUDIO_UNPROCESSABLE = "audio_unprocessable" 
    STT_CONVERSION_FAILED = "stt_conversion_failed"
    STT_SERVICE_UNAVAILABLE = "stt_service_unavailable"

    #S3 관련
    S3_ACCESS_FORBIDDEN = "s3_access_forbidden"
    AUDIO_DOWNLOAD_FAILED = "audio_download_failed"
    AUDIO_DOWNLOAD_TIMEOUT = "audio_download_timeout"

    # Feedback 관련
    EMPTY_QUESTION = "empty_question"
    EMPTY_ANSWER = "empty_answer"
    ANSWER_TOO_SHORT = "answer_too_short"
    ANSWER_TOO_LONG = "answer_too_long"
    INVALID_ANSWER_FORMAT = "invalid_answer_format"
    FEEDBACK_ALREADY_IN_PROGRESS = "feedback_already_in_progress"
    RUBRIC_EVALUATION_FAILED = "rubric_evaluation_failed"
    FEEDBACK_GENERATION_FAILED = "feedback_generation_failed"

    # LLM 관련
    LLM_SERVICE_UNAVAILABLE = "llm_service_unavailable"
    LLM_RESPONSE_PARSE_FAILED = "llm_response_parse_failed"
    LLM_TIMEOUT = "llm_timeout"

    # 공통
    API_KEY_INVALID = "api_key_invalid"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_TEMPORARILY_UNAVAILABLE = "service_temporarily_unavailable"


# HTTP status code 매핑
ERROR_STATUS_CODE: dict[ErrorMessage, int] = {
    # 400 Bad Request
    ErrorMessage.EMPTY_QUESTION: 400,
    ErrorMessage.EMPTY_ANSWER: 400,
    ErrorMessage.ANSWER_TOO_SHORT: 400,
    ErrorMessage.ANSWER_TOO_LONG: 400,
    ErrorMessage.INVALID_ANSWER_FORMAT: 400,

    # 403 Forbidden
    ErrorMessage.S3_ACCESS_FORBIDDEN: 403,
    ErrorMessage.AUDIO_DOWNLOAD_FAILED: 403,


    # 404 Not Found
    ErrorMessage.AUDIO_NOT_FOUND: 404,

    # 408 Request Timeout
    ErrorMessage.AUDIO_DOWNLOAD_TIMEOUT: 408,
    ErrorMessage.STT_TIMEOUT: 408,
    ErrorMessage.LLM_TIMEOUT: 408,

    # 409 Conflict
    ErrorMessage.FEEDBACK_ALREADY_IN_PROGRESS: 409,

    # 422 Unprocessable Entity
    ErrorMessage.AUDIO_UNPROCESSABLE: 422,

    # 429 Too Many Requests
    ErrorMessage.RATE_LIMIT_EXCEEDED: 429,

    # 500 Internal Server Error
    ErrorMessage.STT_CONVERSION_FAILED: 500,
    ErrorMessage.FEEDBACK_GENERATION_FAILED: 500,
    ErrorMessage.RUBRIC_EVALUATION_FAILED: 500,
    ErrorMessage.INTERNAL_SERVER_ERROR: 500,
    ErrorMessage.API_KEY_INVALID: 500,

    # 502 Bad Gateway
    ErrorMessage.STT_SERVICE_UNAVAILABLE: 502,
    ErrorMessage.LLM_SERVICE_UNAVAILABLE: 502,
    ErrorMessage.LLM_RESPONSE_PARSE_FAILED: 502,

    # 503 Service Unavailable
    ErrorMessage.SERVICE_TEMPORARILY_UNAVAILABLE: 503,
}
