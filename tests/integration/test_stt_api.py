"""
STT API Integration Tests

테스트 대상: POST /ai/stt
- Router → Service → Provider 전체 흐름 통합 테스트
- 외부 API (Huggingface, S3)만 mock
- HTTP 요청/응답 형식 검증
- 에러 전파 검증
"""
from unittest.mock import MagicMock
import httpx


class TestSTTAPISuccess:
    """STT API 성공 케이스 통합 테스트"""

    def test_정상_stt_변환(
        self,
        client,
        sample_stt_request_dict,
        mock_http_success_response,
        mock_stt_api_success_response,
        mock_httpx_context,
    ):
        """정상적인 STT 변환 요청 - 전체 파이프라인"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_response=mock_stt_api_success_response,
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        # HTTP 응답 검증
        assert response.status_code == 200

        # 응답 구조 검증
        data = response.json()
        assert data["message"] == "speech_to_text_success"
        assert data["data"]["user_id"] == sample_stt_request_dict["user_id"]
        assert data["data"]["session_id"] == sample_stt_request_dict["session_id"]
        assert data["data"]["text"] == "변환된 텍스트입니다"

    def test_쿼리_파라미터_포함_url_처리(
        self,
        client,
        mock_http_success_response,
        mock_stt_api_success_response,
        mock_httpx_context,
    ):
        """쿼리 파라미터가 포함된 S3 Presigned URL 처리"""
        request_data = {
            "user_id": 1,
            "session_id": 100,
            "audio_url": "https://bucket.s3.amazonaws.com/audio.mp3?X-Amz-Signature=abc123",
        }

        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_response=mock_stt_api_success_response,
        ):
            response = client.post("/ai/stt", json=request_data)

        assert response.status_code == 200
        assert response.json()["message"] == "speech_to_text_success"


class TestSTTAPIAudioDownloadErrors:
    """STT API 오디오 다운로드 에러 테스트"""

    def test_오디오_파일_없음_404(
        self,
        client,
        sample_stt_request_dict,
        mock_http_404_response,
        mock_httpx_context,
    ):
        """오디오 파일 없음 - 404 에러"""
        with mock_httpx_context(get_response=mock_http_404_response):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 404
        assert response.json()["message"] == "audio_not_found"

    def test_s3_접근_거부_403(
        self,
        client,
        sample_stt_request_dict,
        mock_http_403_response,
        mock_httpx_context,
    ):
        """S3 접근 거부 - 403 에러 (Presigned URL 만료 등)"""
        with mock_httpx_context(get_response=mock_http_403_response):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 403
        assert response.json()["message"] == "s3_access_forbidden"


    def test_오디오_다운로드_타임아웃(
        self,
        client,
        sample_stt_request_dict,
        mock_httpx_context,
    ):
        """오디오 다운로드 타임아웃"""
        with mock_httpx_context(
            get_side_effect=httpx.TimeoutException("Download timeout")
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 408
        assert response.json()["message"] == "audio_download_timeout"

    def test_오디오_다운로드_연결_실패(
        self,
        client,
        sample_stt_request_dict,
        mock_httpx_context,
    ):
        """오디오 다운로드 네트워크 연결 실패"""
        with mock_httpx_context(
            get_side_effect=httpx.ConnectError("Connection failed")
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 403
        assert response.json()["message"] == "audio_download_failed"


class TestSTTAPIProviderErrors:
    """STT API Provider(Huggingface) 에러 테스트"""

    def test_stt_api_인증_실패_401(
        self,
        client,
        sample_stt_request_dict,
        mock_http_success_response,
        mock_stt_api_401_response,
        mock_httpx_context,
    ):
        """Huggingface API 인증 실패 - 401"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_stt_api_401_response,
            ),
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 401
        assert response.json()["message"] == "api_key_invalid"

    def test_stt_api_rate_limit_429(
        self,
        client,
        sample_stt_request_dict,
        mock_http_success_response,
        mock_stt_api_429_response,
        mock_httpx_context,
    ):
        """Huggingface API Rate Limit 초과 - 429"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=MagicMock(),
                response=mock_stt_api_429_response,
            ),
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 429
        assert response.json()["message"] == "rate_limit_exceeded"

    def test_stt_api_서버_에러_500(
        self,
        client,
        sample_stt_request_dict,
        mock_http_success_response,
        mock_httpx_context,
    ):
        """Huggingface API 서버 에러 - 500"""
        mock_500_response = MagicMock()
        mock_500_response.status_code = 500
        mock_500_response.content = b'{"error": "Internal Server Error"}'

        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=mock_500_response,
            ),
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 500
        assert response.json()["message"] == "stt_conversion_failed"

    def test_stt_api_타임아웃(
        self,
        client,
        sample_stt_request_dict,
        mock_http_success_response,
        mock_httpx_context,
    ):
        """Huggingface API 타임아웃"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.TimeoutException("API timeout"),
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        assert response.status_code == 408
        assert response.json()["message"] == "stt_timeout"


class TestSTTAPIValidation:
    """STT API 요청 검증 테스트"""

    def test_필수_필드_누락_user_id(self, client):
        """user_id 누락"""
        request_data = {
            "session_id": 100,
            "audio_url": "https://example.com/audio.mp3",
        }

        response = client.post("/ai/stt", json=request_data)

        assert response.status_code == 422  # Validation Error

    def test_필수_필드_누락_audio_url(self, client):
        """audio_url 누락"""
        request_data = {
            "user_id": 1,
            "session_id": 100,
        }

        response = client.post("/ai/stt", json=request_data)

        assert response.status_code == 422

    def test_잘못된_타입_user_id(self, client):
        """user_id 타입 에러"""
        request_data = {
            "user_id": "not_a_number",
            "session_id": 100,
            "audio_url": "https://example.com/audio.mp3",
        }

        response = client.post("/ai/stt", json=request_data)

        assert response.status_code == 422


class TestSTTAPIEmptyResult:
    """STT 결과가 비어있는 케이스 테스트"""

    def test_stt_결과_빈_문자열(
        self,
        client,
        sample_stt_request_dict,
        mock_http_success_response,
        mock_httpx_context,
    ):
        """STT 결과가 빈 문자열인 경우"""
        mock_empty_response = MagicMock()
        mock_empty_response.status_code = 200
        mock_empty_response.json.return_value = {"text": ""}

        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_response=mock_empty_response,
        ):
            response = client.post("/ai/stt", json=sample_stt_request_dict)

        # 빈 결과는 에러로 처리됨
        assert response.status_code == 422
        assert response.json()["message"] == "audio_unprocessable"