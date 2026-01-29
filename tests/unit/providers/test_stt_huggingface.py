# test/unit/providers/test_stt_huggingface.py
import pytest
from unittest.mock import MagicMock
import httpx

from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage
from providers.stt.huggingface import download_audio, transcribe, get_content_type


class TestDownloadAudio:
    """download_audio 함수 테스트"""

    @pytest.mark.asyncio
    async def test_download_audio_success(self, sample_audio_bytes, mock_http_success_response, mock_httpx_context):
        """정상적인 오디오 다운로드"""
        with mock_httpx_context(get_response=mock_http_success_response):
            result = await download_audio("https://example.com/audio.mp3")
            assert result == sample_audio_bytes

    @pytest.mark.asyncio
    async def test_download_audio_not_found(
        self, 
        mock_http_404_response,
        mock_httpx_context
    ):
        """404 - 오디오 파일 없음"""
        with mock_httpx_context(get_response=mock_http_404_response):
            with pytest.raises(AppException) as exc_info:
                await download_audio("https://example.com/audio.mp3")

            assert exc_info.value.message == ErrorMessage.AUDIO_NOT_FOUND
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_download_audio_forbidden(
        self, 
        mock_http_403_response,
        mock_httpx_context
    ):
        """403 - S3 접근 거부"""
        with mock_httpx_context(get_response=mock_http_403_response):
            with pytest.raises(AppException) as exc_info:
                await download_audio("https://example.com/audio.mp3")

            assert exc_info.value.message == ErrorMessage.S3_ACCESS_FORBIDDEN
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_download_audio_timeout(self, mock_httpx_context):
        """오디오 다운로드 타임아웃 에러"""
        with mock_httpx_context(
            get_side_effect=httpx.TimeoutException("Request timeout")
        ):
            with pytest.raises(AppException) as exc_info:
                await download_audio("https://example.com/audio.mp3")

            assert exc_info.value.message == ErrorMessage.AUDIO_DOWNLOAD_TIMEOUT
            assert exc_info.value.status_code == 408

    @pytest.mark.asyncio
    async def test_download_audio_connection_error(self, mock_httpx_context):
        """네트워크 연결 실패 - RequestError"""
        with mock_httpx_context(
            get_side_effect=httpx.ConnectError("Connection failed")
        ):
            with pytest.raises(AppException) as exc_info:
                await download_audio("https://example.com/audio.mp3")

            # RequestError는 AUDIO_DOWNLOAD_FAILED로 처리됨
            assert exc_info.value.message == ErrorMessage.AUDIO_DOWNLOAD_FAILED
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_download_audio_unexpected_error(self, mock_httpx_context):
        """예상치 못한 일반 예외"""
        with mock_httpx_context(
            get_side_effect=Exception("Unexpected error")
        ):
            with pytest.raises(AppException) as exc_info:
                await download_audio("https://example.com/audio.mp3")

            assert exc_info.value.message == ErrorMessage.AUDIO_DOWNLOAD_FAILED
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [500, 501, 502, 503, 504])
    async def test_download_audio_5xx_errors(self, status_code, mock_httpx_context):
        """모든 5xx 에러는 INTERNAL_SERVER_ERROR로 처리"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.content = f'{{"error": "Error {status_code}"}}'.encode()

        with mock_httpx_context(
            get_side_effect=httpx.HTTPStatusError(
                f"{status_code} Server Error",
                request=MagicMock(),
                response=mock_response
            )
        ):
            with pytest.raises(AppException) as exc_info:
                await download_audio("https://example.com/audio.mp3")

            assert exc_info.value.message == ErrorMessage.INTERNAL_SERVER_ERROR
            assert exc_info.value.status_code == 500

class TestGetContentType:
    """get_content_type 함수 테스트"""

    @pytest.mark.parametrize("url,expected", [
        ("https://example.com/audio.mp3", "audio/mpeg"),
        ("https://example.com/audio.m4a", "audio/x-m4a"),
        ("https://example.com/audio.mp4", "audio/x-m4a"),
        # 쿼리 파라미터 포함
        ("https://example.com/audio.mp3?token=abc123", "audio/mpeg"),
        ("https://example.com/audio.m4a?token=abc123&user=test", "audio/x-m4a"),
    ])
    def test_get_content_type_variations(self, url, expected):
        """다양한 URL 형식의 content-type 확인"""
        result = get_content_type(url)
        assert result == expected

    def test_get_content_type_case_insensitive(self):
        """대소문자 구분 없이 처리"""
        assert get_content_type("https://example.com/audio.MP3") == "audio/mpeg"
        assert get_content_type("https://example.com/audio.M4A") == "audio/x-m4a"

    # 확장자 에러처리도 필요한가?
    def test_get_content_type_unknown_extension(self):
        """지원하지 않는 확장자 - KeyError 발생"""
        with pytest.raises(KeyError):
            get_content_type("https://example.com/audio.xyz")

    def test_get_content_type_no_extension(self):
        """확장자가 없는 URL - KeyError 발생"""
        with pytest.raises(KeyError):
            get_content_type("https://example.com/audio")


class TestTranscribe:
    """transcribe 함수 테스트"""

    @pytest.mark.asyncio
    async def test_transcribe_success(
        self,
        sample_audio_url,
        mock_http_success_response,
        mock_stt_api_success_response,
        mock_httpx_context
    ):
        """정상적인 STT 변환"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_response=mock_stt_api_success_response
        ):
            result = await transcribe(sample_audio_url)
            assert result == "변환된 텍스트입니다"

    @pytest.mark.asyncio
    async def test_transcribe_download_fails(
        self,
        sample_audio_url,
        mock_httpx_context
    ):
        """다운로드 실패 시 transcribe도 실패"""
        with mock_httpx_context(
            get_side_effect=httpx.TimeoutException("Download timeout")
        ):
            with pytest.raises(AppException) as exc_info:
                await transcribe(sample_audio_url)

            assert exc_info.value.message == ErrorMessage.AUDIO_DOWNLOAD_TIMEOUT.value

    @pytest.mark.asyncio
    async def test_transcribe_api_timeout(
        self,
        sample_audio_url,
        mock_http_success_response,
        mock_httpx_context
    ):
        """Huggingface API 타임아웃"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.TimeoutException("API timeout")
        ):
            with pytest.raises(AppException) as exc_info:
                await transcribe(sample_audio_url)

            assert exc_info.value.message == ErrorMessage.STT_TIMEOUT.value
            assert exc_info.value.status_code == 408

    @pytest.mark.asyncio
    async def test_transcribe_api_unauthorized(
        self,
        sample_audio_url,
        mock_http_success_response,
        mock_stt_api_401_response,
        mock_httpx_context
    ):
        """401 - API 키 인증 실패"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_stt_api_401_response
            )
        ):
            with pytest.raises(AppException) as exc_info:
                await transcribe(sample_audio_url)

            assert exc_info.value.message == ErrorMessage.API_KEY_INVALID
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_transcribe_rate_limit(
        self,
        sample_audio_url,
        mock_http_success_response,
        mock_stt_api_429_response,
        mock_httpx_context
    ):
        """429 - Rate Limit 초과"""
        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=MagicMock(),
                response=mock_stt_api_429_response
            )
        ):
            with pytest.raises(AppException) as exc_info:
                await transcribe(sample_audio_url)

            assert exc_info.value.message == ErrorMessage.RATE_LIMIT_EXCEEDED
            assert exc_info.value.status_code == 429



    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [500, 501, 502, 503, 504])
    async def test_transcribe_api_5xx_errors(
        self,
        status_code,
        sample_audio_url,
        mock_http_success_response,
        mock_httpx_context
    ):
        """모든 5xx 에러는 STT_CONVERSION_FAILED로 처리"""
        error_response = MagicMock()
        error_response.status_code = status_code
        error_response.content = f'{{"error": "Error {status_code}"}}'.encode()
        error_response.json.return_value = {"error": f"Error {status_code}"}

        with mock_httpx_context(
            get_response=mock_http_success_response,
            post_side_effect=httpx.HTTPStatusError(
                f"{status_code} Server Error",
                request=MagicMock(),
                response=error_response
            )
        ):
            with pytest.raises(AppException) as exc_info:
                await transcribe(sample_audio_url)

            assert exc_info.value.message == ErrorMessage.STT_CONVERSION_FAILED
            assert exc_info.value.status_code == 500
