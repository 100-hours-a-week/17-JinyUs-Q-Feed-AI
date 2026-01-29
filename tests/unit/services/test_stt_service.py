import pytest
from unittest.mock import AsyncMock, patch

from services.stt_service import process_transcribe
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage


class TestProcessTranscribe:
    """process_transcribe 함수 테스트"""

    @pytest.mark.asyncio
    async def test_정상_변환_성공(self, sample_audio_url, sample_transcribed_text):
        """정상적인 오디오 URL로 STT 변환 성공"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value=sample_transcribed_text)
            mock_get_provider.return_value = mock_provider
            
            result = await process_transcribe(sample_audio_url)
            
            assert result == sample_transcribed_text
            mock_provider.assert_called_once_with(sample_audio_url)

    @pytest.mark.asyncio
    async def test_쿼리_파라미터_포함_URL_처리(
        self, sample_audio_url_with_query, sample_transcribed_text
    ):
        """쿼리 파라미터가 포함된 URL도 정상 처리"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value=sample_transcribed_text)
            mock_get_provider.return_value = mock_provider
            
            result = await process_transcribe(sample_audio_url_with_query)
            
            assert result == sample_transcribed_text
            mock_provider.assert_called_once_with(sample_audio_url_with_query)

    @pytest.mark.asyncio
    async def test_빈_결과_예외_발생(self, sample_audio_url):
        """STT 결과가 빈 문자열이면 AppException 발생"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value="")
            mock_get_provider.return_value = mock_provider
            
            with pytest.raises(AppException) as exc_info:
                await process_transcribe(sample_audio_url)
            assert exc_info.value.message == ErrorMessage.AUDIO_UNPROCESSABLE.value

    @pytest.mark.asyncio
    async def test_공백만_있는_결과_예외_발생(self, sample_audio_url):
        """STT 결과가 공백만 있으면 AppException 발생"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value="   \n\t  ")
            mock_get_provider.return_value = mock_provider
            
            with pytest.raises(AppException) as exc_info:
                await process_transcribe(sample_audio_url)
            
            assert exc_info.value.message == ErrorMessage.AUDIO_UNPROCESSABLE.value

    @pytest.mark.asyncio
    async def test_None_결과_예외_발생(self, sample_audio_url):
        """STT 결과가 None이면 AppException 발생"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value=None)
            mock_get_provider.return_value = mock_provider
            
            with pytest.raises(AppException) as exc_info:
                await process_transcribe(sample_audio_url)
            
            assert exc_info.value.message == ErrorMessage.AUDIO_UNPROCESSABLE.value

    @pytest.mark.asyncio
    async def test_provider_AppException_전파(self, sample_audio_url):
        """Provider에서 발생한 AppException이 그대로 전파됨"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            expected_error = ErrorMessage.AUDIO_DOWNLOAD_FAILED
            mock_provider = AsyncMock(side_effect=AppException(expected_error))
            mock_get_provider.return_value = mock_provider
            
            with pytest.raises(AppException) as exc_info:
                await process_transcribe(sample_audio_url)
            
            assert exc_info.value.message == expected_error

    @pytest.mark.asyncio
    async def test_다양한_오디오_형식_처리(self, sample_transcribed_text):
        """다양한 오디오 형식(mp3, m4a, mp4) URL 처리"""
        test_urls = [
            "https://example.com/audio/test.mp3",
            "https://example.com/audio/test.m4a",
            "https://example.com/audio/test.mp4",
        ]
        
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value=sample_transcribed_text)
            mock_get_provider.return_value = mock_provider
            
            for url in test_urls:
                result = await process_transcribe(url)
                assert result == sample_transcribed_text

    @pytest.mark.asyncio
    async def test_빈_URL_처리(self, sample_transcribed_text):
        """빈 URL도 provider에 전달됨 (provider에서 처리)"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value=sample_transcribed_text)
            mock_get_provider.return_value = mock_provider
            
            # 빈 URL은 서비스 레이어에서 체크하지 않고 provider에 위임
            await process_transcribe("")
            
            mock_provider.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_파일명_추출_로깅(self, sample_audio_url, sample_transcribed_text):
        """로깅을 위한 파일명 추출이 정상 동작"""
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            with patch("services.stt_service.logger") as mock_logger:
                mock_provider = AsyncMock(return_value=sample_transcribed_text)
                mock_get_provider.return_value = mock_provider
                
                await process_transcribe(sample_audio_url)
                
                # debug 로그가 호출되었는지 확인
                mock_logger.debug.assert_called()
                # info 로그가 호출되었는지 확인
                mock_logger.info.assert_called()


class TestProcessTranscribeEdgeCases:
    """process_transcribe 엣지 케이스 테스트"""

    @pytest.mark.asyncio
    async def test_presigned_url_처리(self):
        """AWS S3 Presigned URL 처리"""
        presigned_url = (
            "https://bucket.s3.amazonaws.com/audio/test.mp3"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE"
            "&X-Amz-Date=20240101T000000Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-Signature=abc123"
        )
        expected_text = "변환된 텍스트"
        
        with patch("services.stt_service.get_stt_provider") as mock_get_provider:
            mock_provider = AsyncMock(return_value=expected_text)
            mock_get_provider.return_value = mock_provider
            
            result = await process_transcribe(presigned_url)
            
            assert result == expected_text
            mock_provider.assert_called_once_with(presigned_url)