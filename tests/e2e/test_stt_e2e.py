"""
STT API E2E Tests (수동 E2E 방식)

실제 서버에 HTTP 요청을 보내 STT 파이프라인을 검증합니다.

실행 방법:
    1. 서버 실행: uv run uvicorn main:app --port 8000
    2. 테스트 실행: uv run pytest tests/e2e/test_stt_e2e.py -v

주의:
- 실제 HuggingFace API를 호출합니다 (API 비용 발생 가능)
- 테스트용 오디오 파일 URL이 필요합니다
- 환경변수 E2E_TEST_AUDIO_URL로 테스트 오디오 URL 설정 가능
"""

import pytest
import os


# ============================================
# STT 테스트용 fixtures
# ============================================

@pytest.fixture
def sample_audio_url():
    """
    테스트용 오디오 파일 URL
    - 환경변수로 오버라이드 가능: E2E_TEST_AUDIO_URL
    - 실제 접근 가능한 .mp3 또는 .m4a 파일이어야 함
    """
    # 환경변수에서 테스트 오디오 URL 가져오기
    custom_url = os.getenv("E2E_TEST_AUDIO_URL")
    if custom_url:
        return custom_url
    
    # 기본값: 테스트 전에 실제 URL로 교체 필요
    # 아래는 예시 형식 - 실제 접근 가능한 URL로 변경하세요
    pytest.skip(
        "E2E_TEST_AUDIO_URL 환경변수가 설정되지 않았습니다. "
        "테스트할 오디오 파일 URL을 설정하세요. "
        "예: E2E_TEST_AUDIO_URL=https://your-bucket.s3.amazonaws.com/test.mp3"
    )


@pytest.fixture
def sample_stt_request(sample_audio_url):
    """STT 요청 데이터"""
    return {
        "user_id": 9999,
        "session_id": 1001,
        "audio_url": sample_audio_url
    }


# ============================================
# STT E2E 테스트
# ============================================

@pytest.mark.e2e
class TestSTTE2ESuccess:
    """STT API 성공 케이스 E2E 테스트"""

    def test_정상_stt_변환(
        self,
        e2e_client,
        sample_stt_request,
    ):
        """
        정상적인 오디오 파일 → 텍스트 변환 성공
        - 실제 HuggingFace Whisper API 호출
        - 변환된 텍스트가 비어있지 않아야 함
        """
        response = e2e_client.post(
            "/ai/stt",
            json=sample_stt_request
        )

        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "speech_to_text_success"
        assert data["data"]["user_id"] == sample_stt_request["user_id"]
        assert data["data"]["session_id"] == sample_stt_request["session_id"]
        
        # 변환된 텍스트 검증
        text = data["data"]["text"]
        assert text is not None
        assert len(text.strip()) > 0, "변환된 텍스트가 비어있음"
        
        print("\n[STT 변환 결과]")
        print(f"텍스트 길이: {len(text)}자")
        print(f"변환 결과: {text[:200]}{'...' if len(text) > 200 else ''}")

    def test_session_id_없이_stt_변환(
        self,
        e2e_client,
        sample_audio_url,
    ):
        """session_id 없이도 STT 변환 가능"""
        request_data = {
            "user_id": 9999,
            # session_id 없음
            "audio_url": sample_audio_url
        }
        
        response = e2e_client.post("/ai/stt", json=request_data)

        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "speech_to_text_success"
        assert data["data"]["session_id"] is None
        
        print("\n[session_id 없이 STT 변환 성공]")
        print(f"텍스트: {data['data']['text'][:100]}...")


@pytest.mark.e2e
class TestSTTE2EValidation:
    """STT API 요청 검증 E2E 테스트"""

    def test_필수_필드_누락_user_id(self, e2e_client):
        """user_id 누락 → 422"""
        request_data = {
            # user_id 누락
            "session_id": 100,
            "audio_url": "https://example.com/audio/test.mp3"
        }

        response = e2e_client.post("/ai/stt", json=request_data)
        assert response.status_code == 422

    def test_필수_필드_누락_audio_url(self, e2e_client):
        """audio_url 누락 → 422"""
        request_data = {
            "user_id": 1,
            "session_id": 100,
            # audio_url 누락
        }

        response = e2e_client.post("/ai/stt", json=request_data)
        assert response.status_code == 422

    def test_잘못된_오디오_확장자(self, e2e_client):
        """지원하지 않는 오디오 확장자 → 422"""
        request_data = {
            "user_id": 1,
            "session_id": 100,
            "audio_url": "https://example.com/audio/test.wav"  # .wav는 지원 안함
        }

        response = e2e_client.post("/ai/stt", json=request_data)
        assert response.status_code == 422

    def test_잘못된_타입_user_id(self, e2e_client):
        """user_id 타입 에러 → 422"""
        request_data = {
            "user_id": "not_a_number",
            "session_id": 100,
            "audio_url": "https://example.com/audio/test.mp3"
        }

        response = e2e_client.post("/ai/stt", json=request_data)
        assert response.status_code == 422


@pytest.mark.e2e
class TestSTTE2EErrorCases:
    """STT API 에러 케이스 E2E 테스트"""

    def test_존재하지_않는_오디오_파일(self, e2e_client):
        """
        존재하지 않는 오디오 파일 URL → 에러
        - 404 또는 관련 에러 응답
        """
        request_data = {
            "user_id": 9999,
            "session_id": 1001,
            "audio_url": "https://example.com/nonexistent/audio.mp3"
        }

        response = e2e_client.post("/ai/stt", json=request_data)
        
        # 404 또는 다른 에러 상태 코드
        assert response.status_code in [404, 403, 500, 502]
        
        data = response.json()
        print("\n[존재하지 않는 파일 에러]")
        print(f"status: {response.status_code}")
        print(f"message: {data.get('message', 'N/A')}")
