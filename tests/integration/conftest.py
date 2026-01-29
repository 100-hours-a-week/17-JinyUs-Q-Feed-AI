"""
Integration 테스트 전용 Fixtures

API 통합 테스트에 필요한 추가 샘플 데이터
(공통 HTTP mock과 샘플 데이터는 tests/conftest.py에 있음)
"""

import pytest

from schemas.stt import STTRequest


# ============================================
# STT 요청 샘플 데이터 (Integration 전용)
# ============================================

@pytest.fixture
def sample_m4a_url():
    """M4A 파일 URL"""
    return "https://example.com/audio/test.m4a"


@pytest.fixture
def sample_mp4_url():
    """MP4 파일 URL"""
    return "https://example.com/audio/test.mp4"


@pytest.fixture
def sample_stt_request():
    """STT 요청 샘플 - Pydantic 모델"""
    return STTRequest(
        user_id=1,
        session_id=100,
        audio_url="https://example.com/audio/test.mp3"
    )


@pytest.fixture
def sample_stt_request_dict():
    """STT 요청 dict (API 호출용)"""
    return {
        "user_id": 1,
        "session_id": 100,
        "audio_url": "https://example.com/audio/test.mp3"
    }


# ============================================
# Feedback 요청 샘플 데이터 (Integration 전용)
# ============================================

@pytest.fixture
def sample_feedback_request_dict():
    """피드백 요청 dict (API 호출용)"""
    return {
        "user_id": 1,
        "question_id": 42,
        "interview_type": "PRACTICE_INTERVIEW",
        "question_type": "CS",
        "category": "NETWORK",
        "question": "HTTP와 HTTPS의 차이점을 설명해주세요",
        "answer_text": "HTTPS는 HTTP에 SSL/TLS 암호화가 추가된 프로토콜입니다"
    }
