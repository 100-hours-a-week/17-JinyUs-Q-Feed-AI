"""
QFeed 테스트 공통 설정

이 파일에는 모든 테스트에서 공통으로 사용하는 fixture를 포함합니다.
- 앱/클라이언트 fixtures
- pytest 마커 자동 적용
- 환경 설정 mock (E2E 제외)
- 공통 HTTP mock fixtures
- 공통 샘플 데이터 fixtures

테스트별 전용 fixtures:
- Unit: tests/unit/conftest.py (Provider/Service mock)
- Integration: tests/integration/conftest.py (API 요청 dict)
- E2E: tests/e2e/conftest.py (실제 서버 연결)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import contextmanager
from fastapi.testclient import TestClient

from main import app
from schemas.feedback import (
    FeedbackRequest,
    InterviewType,
    QuestionType,
    QuestionCategory,
    RubricEvaluationResult,
    FeedbackContent,
    AnswerAnalyzerResult,
    BadCaseType
)


# ============================================
# 앱 관련 fixtures
# ============================================

@pytest.fixture
def test_app():
    """FastAPI 앱 인스턴스"""
    return app


@pytest.fixture
def client(test_app):
    """테스트용 클라이언트"""
    return TestClient(test_app)


# ============================================
# 환경 설정 fixtures
# ============================================

@pytest.fixture(autouse=True, scope="function")
def mock_gemini_settings(request):
    """
    Gemini Provider 테스트용 settings mock
    - E2E 테스트에서는 적용하지 않음 (실제 API 사용)
    """
    # E2E 테스트는 mock 적용 안함
    if "/e2e/" in str(request.fspath):
        yield None
        return
    
    with patch("providers.llm.gemini.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.gemini_api_key = "test_gemini_key"
        mock_settings.gemini_model_id = "gemini-2.0-flash-exp"
        mock_get_settings.return_value = mock_settings
        yield mock_settings


# ============================================
# HTTP Mock fixtures (공통)
# ============================================

@pytest.fixture
def mock_httpx_client_factory():
    """재사용 가능한 httpx AsyncClient mock 생성 팩토리"""
    def create_mock(get_response=None, post_response=None, 
                    get_side_effect=None, post_side_effect=None):
        """
        Args:
            get_response: GET 요청 응답 mock
            post_response: POST 요청 응답 mock
            get_side_effect: GET 요청 side_effect (예외 발생용)
            post_side_effect: POST 요청 side_effect (예외 발생용)
        """
        mock_instance = AsyncMock()
        
        if get_side_effect:
            mock_instance.get = AsyncMock(side_effect=get_side_effect)
        else:
            mock_instance.get = AsyncMock(return_value=get_response)
        
        if post_side_effect:
            mock_instance.post = AsyncMock(side_effect=post_side_effect)
        else:
            mock_instance.post = AsyncMock(return_value=post_response)
        
        return mock_instance
    
    return create_mock


@pytest.fixture
def mock_httpx_context(mock_httpx_client_factory):
    """httpx.AsyncClient context manager mock을 쉽게 설정하는 헬퍼"""
    
    @contextmanager
    def setup_mock(get_response=None, post_response=None,
                   get_side_effect=None, post_side_effect=None):
        """
        사용 예:
        with mock_httpx_context(get_response=mock_response):
            result = await download_audio(url)
        """
        mock_client = mock_httpx_client_factory(
            get_response=get_response,
            post_response=post_response,
            get_side_effect=get_side_effect,
            post_side_effect=post_side_effect
        )
        
        with patch("providers.stt.huggingface.httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = mock_client
            yield mock_client
    
    return setup_mock


# ============================================
# HTTP Response Mock fixtures
# ============================================

@pytest.fixture
def sample_audio_bytes():
    """테스트용 더미 오디오 데이터"""
    return b"fake_audio_data_for_testing"


@pytest.fixture
def mock_http_success_response(sample_audio_bytes):
    """200 OK 응답 mock"""
    response = MagicMock()
    response.status_code = 200
    response.content = sample_audio_bytes
    return response


@pytest.fixture
def mock_http_404_response():
    """404 Not Found 응답 mock"""
    response = MagicMock()
    response.status_code = 404
    return response


@pytest.fixture
def mock_http_403_response():
    """403 Forbidden 응답 mock"""
    response = MagicMock()
    response.status_code = 403
    return response


@pytest.fixture
def mock_http_500_response():
    """500 Internal Server Error 응답 mock"""
    response = MagicMock()
    response.status_code = 500
    return response


# ============================================
# STT API Mock fixtures
# ============================================

@pytest.fixture
def mock_stt_api_success_response():
    """STT API 성공 응답 mock"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"text": "변환된 텍스트입니다"}
    return response


@pytest.fixture
def mock_stt_api_401_response():
    """STT API 401 Unauthorized 응답 mock"""
    response = MagicMock()
    response.status_code = 401
    response.content = b'{"error": "Invalid API key"}'
    response.json.return_value = {"error": "Invalid API key"}
    return response


@pytest.fixture
def mock_stt_api_429_response():
    """STT API 429 Rate Limit 응답 mock"""
    response = MagicMock()
    response.status_code = 429
    response.content = b'{"error": "Rate limit exceeded"}'
    response.json.return_value = {"error": "Rate limit exceeded"}
    return response


# ============================================
# STT 샘플 데이터 fixtures
# ============================================

@pytest.fixture
def sample_audio_url():
    """테스트용 오디오 URL"""
    return "https://example.com/audio/test.mp3"


@pytest.fixture
def sample_audio_url_with_query():
    """쿼리 파라미터가 포함된 오디오 URL"""
    return "https://example.com/audio/test.mp3?token=abc123&user=test"


@pytest.fixture
def sample_transcribed_text():
    """STT 결과 텍스트 샘플"""
    return "HTTPS는 HTTP에 SSL/TLS 암호화가 추가된 프로토콜입니다"


# ============================================
# Feedback 요청/결과 샘플 데이터
# ============================================

@pytest.fixture
def sample_feedback_request():
    """피드백 요청 샘플 - Pydantic 모델"""
    return FeedbackRequest(
        user_id=1,
        question_id=42,
        interview_type=InterviewType.PRACTICE_INTERVIEW,
        question_type=QuestionType.CS,
        category=QuestionCategory.NETWORK,
        question="HTTP와 HTTPS의 차이점을 설명해주세요",
        answer_text="HTTPS는 HTTP에 SSL/TLS 암호화가 추가된 프로토콜입니다"
    )


@pytest.fixture
def sample_rubric_result():
    """루브릭 평가 결과 샘플"""
    return RubricEvaluationResult(
        accuracy=4,
        logic=3,
        specificity=4,
        completeness=3,
        delivery=4,
        accuracy_rationale="SSL/TLS 암호화 개념을 정확히 설명함",
        logic_rationale="HTTP에서 HTTPS로의 발전 과정을 논리적으로 설명",
        specificity_rationale="암호화 프로토콜을 구체적으로 언급",
        completeness_rationale="포트 번호, 인증서 등 추가 설명 부족",
        delivery_rationale="간결하고 명확하게 전달",
    )


@pytest.fixture
def sample_feedback_content():
    """피드백 내용 샘플"""
    return FeedbackContent(
        strengths="SSL/TLS 암호화의 핵심 개념을 정확히 이해하고 있습니다.",
        improvements="HTTPS의 포트 번호(443), 인증서 검증 과정도 언급하면 더 완성도 높은 답변이 됩니다."
    )


# ============================================
# Analyzer 결과 샘플 fixtures
# ============================================

@pytest.fixture
def sample_analyzer_result_normal():
    """정상 답변 분석 결과"""
    return AnswerAnalyzerResult(
        is_bad_case=False,
        bad_case_type=None,
        short_advice="좋은 답변입니다.",
        has_weakness=False,
        needs_followup=False,
        followup_reason=None,
    )


@pytest.fixture
def sample_analyzer_result_with_weakness():
    """약점이 있는 답변 분석 결과"""
    return AnswerAnalyzerResult(
        is_bad_case=False,
        bad_case_type=None,
        short_advice="일부 보완이 필요합니다.",
        has_weakness=True,
        needs_followup=True,
        followup_reason="개념 설명이 부족합니다.",
    )


@pytest.fixture
def sample_analyzer_result_bad_case_refuse():
    """답변 거부 Bad Case"""
    return AnswerAnalyzerResult(
        is_bad_case=True,
        bad_case_type=BadCaseType.REFUSE_TO_ANSWER,
        short_advice="답변을 입력해주세요.",
        has_weakness=False,
    )


@pytest.fixture
def sample_analyzer_result_bad_case_too_short():
    """너무 짧은 답변 Bad Case"""
    return AnswerAnalyzerResult(
        is_bad_case=True,
        bad_case_type=BadCaseType.TOO_SHORT,
        short_advice="더 자세히 설명해주세요.",
        has_weakness=False,
    )


# ============================================
# 마커 자동 적용
# ============================================

def pytest_collection_modifyitems(config, items):
    """경로 기반으로 마커 자동 적용"""
    for item in items:
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
