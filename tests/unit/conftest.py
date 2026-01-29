"""
Unit 테스트 전용 Fixtures

개별 Provider, Service 테스트에 필요한 mock 객체들
(공통 샘플 데이터는 tests/conftest.py에 있음)
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from schemas.feedback import (
    RubricEvaluationResult,
    AnswerAnalyzerResult,
    BadCaseType
)


# ============================================
# Provider Mock fixtures
# ============================================

@pytest.fixture
def mock_stt_provider():
    """STT Provider mock"""
    provider = AsyncMock()
    provider.transcribe.return_value = "HTTPS는 HTTP에 SSL 암호화가 추가된 보안 프로토콜입니다"
    return provider


@pytest.fixture
def mock_genai_client():
    """Google genai.Client mock"""
    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.models = MagicMock()
    return mock_client


@pytest.fixture
def mock_gemini_response():
    """Gemini API 성공 응답 mock"""
    response = MagicMock()
    response.text = "이것은 테스트 응답입니다"
    return response


@pytest.fixture
def mock_gemini_structured_response():
    """Gemini API structured output 응답 mock (JSON)"""
    response = MagicMock()
    response.text = json.dumps({
        "user_id": 101,
        "question_id": 505,
        "metrics": [
            {"name": "정확도", "score": 4, "comment": "정확도 이유"},
            {"name": "논리력", "score": 3, "comment": "논리력 이유"},
            {"name": "구체성", "score": 3, "comment": "구체성 이유"},
            {"name": "완성도", "score": 3, "comment": "완성도 이유"},
            {"name": "전달력", "score": 5, "comment": "전달력 이유"}
        ],
        "bad_case_feedback": None,
        "weakness": True,
        "feedback": {
            "strengths": "강점",
            "improvements": "약점"
        }
    })
    return response


# ============================================
# LLM Provider Mock fixtures
# ============================================

@pytest.fixture
def mock_llm_provider(sample_rubric_result, sample_feedback_content):
    """LLM Provider mock - generate_structured 호출 시 순차 반환"""
    provider = AsyncMock()
    provider.generate_structured = AsyncMock(
        side_effect=[sample_rubric_result, sample_feedback_content]
    )
    return provider


# ============================================
# Analyzer Mock fixtures
# ============================================

@pytest.fixture
def mock_analyzer_normal(sample_analyzer_result_normal):
    """정상 답변 analyzer mock"""
    analyzer = AsyncMock()
    analyzer.analyze = AsyncMock(return_value=sample_analyzer_result_normal)
    return analyzer


@pytest.fixture
def mock_analyzer_with_weakness(sample_analyzer_result_with_weakness):
    """약점 있는 답변 analyzer mock"""
    analyzer = AsyncMock()
    analyzer.analyze = AsyncMock(return_value=sample_analyzer_result_with_weakness)
    return analyzer


@pytest.fixture
def mock_analyzer_bad_case_refuse(sample_analyzer_result_bad_case_refuse):
    """답변 거부 analyzer mock"""
    analyzer = AsyncMock()
    analyzer.analyze = AsyncMock(return_value=sample_analyzer_result_bad_case_refuse)
    return analyzer


@pytest.fixture
def mock_analyzer_bad_case_too_short(sample_analyzer_result_bad_case_too_short):
    """너무 짧은 답변 Bad Case analyzer mock"""
    analyzer = AsyncMock()
    analyzer.analyze = AsyncMock(return_value=sample_analyzer_result_bad_case_too_short)
    return analyzer


# ============================================
# Unit 테스트 전용 샘플 데이터
# ============================================

@pytest.fixture
def sample_prompt():
    """테스트용 프롬프트"""
    return "HTTPS와 HTTP의 차이점을 설명해주세요"


@pytest.fixture
def sample_system_prompt():
    """테스트용 시스템 프롬프트"""
    return "당신은 기술 면접 평가자입니다."


@pytest.fixture
def sample_rubric_evaluation():
    """루브릭 평가 결과 샘플 (다른 용도)"""
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
def sample_analyzer_result_bad_case_inappropriate():
    """부적절한 답변 Bad Case"""
    return AnswerAnalyzerResult(
        is_bad_case=True,
        bad_case_type=BadCaseType.INAPPROPRIATE,
        short_advice="질문과 관련된 내용으로 답변해주세요.",
        has_weakness=False,
    )
