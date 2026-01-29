# tests/unit/providers/test_llm_gemini.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from providers.llm.gemini import GeminiProvider
from schemas.feedback import RubricEvaluationResult, FeedbackResponse, FeedbackData
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage


class TestGeminiProviderInit:
    """GeminiProvider 초기화 테스트"""

    def test_init_with_custom_params(self):
        """커스텀 파라미터로 초기화"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            provider = GeminiProvider(
                api_key="custom_key",
                model="custom_model"
            )
            
            mock_client_class.assert_called_once_with(api_key="custom_key")
            assert provider.model == "custom_model"

    def test_init_with_default_params(self):
        """기본 설정으로 초기화"""
        # gemini.py 모듈의 settings를 patch
        with patch("providers.llm.gemini.settings") as mock_settings, \
             patch("providers.llm.gemini.genai.Client") as mock_client_class:
            
            # settings 속성 설정
            mock_settings.gemini_api_key = "test_default_key"
            mock_settings.gemini_model_id = "gemini-2.0-flash-exp"
            
            # Provider 생성
            provider = GeminiProvider()
            
            # 검증
            mock_client_class.assert_called_once_with(api_key="test_default_key")
            assert provider.model == "gemini-2.0-flash-exp"

class TestGenerateStructured:
    """generate_structured 메서드 테스트 - 구조화된 출력"""

    @pytest.mark.asyncio
    async def test_generate_structured_with_system_prompt(
        self,
        sample_prompt,
        sample_system_prompt,
        mock_gemini_structured_response
    ):
        """시스템 프롬프트 포함 구조화된 출력"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_gemini_structured_response
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            result = await provider.generate_structured(
                sample_prompt,
                response_model=FeedbackData,
                system_prompt=sample_system_prompt
            )
            
            assert isinstance(result, FeedbackData)

    @pytest.mark.asyncio
    async def test_generate_structured_json_decode_error(self, sample_prompt):
        """JSON 파싱 실패"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            
            # 잘못된 JSON 응답
            invalid_response = MagicMock()
            invalid_response.text = "This is not valid JSON"
            
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=invalid_response
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured(
                    sample_prompt,
                    response_model=RubricEvaluationResult
                )
            
            assert exc_info.value.message == ErrorMessage.LLM_RESPONSE_PARSE_FAILED
            assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_generate_structured_validation_error(self, sample_prompt):
        """Pydantic 검증 실패"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            
            # 유효하지 않은 데이터 (필수 필드 누락)
            invalid_data_response = MagicMock()
            invalid_data_response.text = '{"accuracy": 4}'  # 다른 필드들 누락
            
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=invalid_data_response
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured(
                    sample_prompt,
                    response_model=RubricEvaluationResult
                )
            
            assert exc_info.value.message == ErrorMessage.LLM_RESPONSE_PARSE_FAILED

    @pytest.mark.asyncio
    async def test_generate_structured_response_schema_set(
        self,
        sample_prompt,
        mock_gemini_structured_response
    ):
        """구조화된 출력에 response_schema가 설정되는지 확인"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_gemini_structured_response
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            await provider.generate_structured(
                sample_prompt,
                response_model=FeedbackData
            )
            
            # config 검증
            call_args = mock_client.aio.models.generate_content.call_args
            config = call_args.kwargs['config']
            assert config.response_mime_type == "application/json"
            assert config.response_schema is not None

    @pytest.mark.asyncio
    async def test_generate_structured_timeout(self, sample_prompt):
        """구조화된 출력에서 타임아웃"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=TimeoutError("Request timeout")
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured(
                    sample_prompt,
                    response_model=RubricEvaluationResult
                )
            
            assert exc_info.value.message == ErrorMessage.LLM_TIMEOUT


class TestBuildPrompt:
    """_build_prompt 메서드 테스트"""

    def test_build_prompt_without_system_prompt(self):
        """시스템 프롬프트 없이 빌드"""
        with patch("providers.llm.gemini.genai.Client"):
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            result = provider._build_prompt("사용자 프롬프트", None)
            
            assert result == "사용자 프롬프트"

    def test_build_prompt_with_system_prompt(self):
        """시스템 프롬프트 포함 빌드"""
        with patch("providers.llm.gemini.genai.Client"):
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            result = provider._build_prompt(
                "사용자 프롬프트",
                "시스템 프롬프트"
            )
            
            assert "시스템 프롬프트" in result
            assert "사용자 프롬프트" in result
            assert result.startswith("시스템 프롬프트")


class TestCallApiErrorHandling:
    """_call_api 에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_call_api_timeout_error(self):
        """TimeoutError 처리"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=TimeoutError("Timeout")
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured("test prompt", FeedbackResponse)
            
            assert exc_info.value.message == ErrorMessage.LLM_TIMEOUT

    @pytest.mark.asyncio
    async def test_call_api_connection_error(self):
        """ConnectionError 처리"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=ConnectionError("Connection failed")
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured("test prompt", FeedbackResponse)
            
            assert exc_info.value.message == ErrorMessage.LLM_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error_message", [
        "timeout occurred",
        "request timeout",
        "TIMEOUT error",
    ])
    async def test_call_api_generic_error_with_timeout_keyword(self, error_message):
        """에러 메시지에 'timeout' 키워드 포함"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=Exception(error_message)
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured("test prompt", FeedbackResponse)
            
            assert exc_info.value.message == ErrorMessage.LLM_TIMEOUT

    @pytest.mark.asyncio
    @pytest.mark.parametrize("error_message", [
        "connection refused",
        "service unavailable",
        "CONNECTION error",
    ])
    async def test_call_api_generic_error_with_connection_keyword(self, error_message):
        """에러 메시지에 'connection' 또는 'unavailable' 키워드 포함"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=Exception(error_message)
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured("test prompt", FeedbackResponse)
            
            assert exc_info.value.message == ErrorMessage.LLM_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_call_api_generic_error_without_keyword(self):
        """키워드 없는 일반 예외"""
        with patch("providers.llm.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=Exception("Unknown error")
            )
            mock_client_class.return_value = mock_client
            
            provider = GeminiProvider(api_key="test_key", model="test_model")
            
            with pytest.raises(AppException) as exc_info:
                await provider.generate_structured("test prompt", FeedbackResponse)
            
            # 키워드가 없으면 기본적으로 LLM_SERVICE_UNAVAILABLE
            assert exc_info.value.message == ErrorMessage.LLM_SERVICE_UNAVAILABLE

# integration test로 옮길것
# class TestIntegrationScenarios:
#     """통합 시나리오 테스트"""

#     @pytest.mark.asyncio
#     async def test_full_rubric_evaluation_flow(
#         self,
#         sample_prompt,
#         mock_gemini_structured_response
#     ):
#         """전체 루브릭 평가 플로우"""
#         with patch("providers.llm.gemini.genai.Client") as mock_client_class:
#             mock_client = MagicMock()
#             mock_client.aio.models.generate_content = AsyncMock(
#                 return_value=mock_gemini_structured_response
#             )
#             mock_client_class.return_value = mock_client
            
#             provider = GeminiProvider(api_key="test_key", model="test_model")
            
#             # 루브릭 평가 실행
#             result = await provider.generate_structured(
#                 prompt="사용자의 답변을 평가해주세요",
#                 response_model=FeedbackData,
#                 system_prompt="당신은 면접 평가자입니다",
#                 temperature=0.0
#             )
            
#             # 결과 검증
#             assert isinstance(result, RubricEvaluationResult)
#             assert 1 <= result.accuracy <= 5
#             assert 1 <= result.logic <= 5
#             assert len(result.accuracy_rationale) > 0
            
#             # metrics 변환 테스트
#             metrics = result.to_metrics_list()
#             assert len(metrics) == 5
#             assert all(m.score >= 1 and m.score <= 5 for m in metrics)

#     @pytest.mark.asyncio
#     async def test_retry_on_transient_error(
#         self,
#         sample_prompt,
#         mock_gemini_structured_response
#     ):
#         """일시적 에러 후 재시도 시나리오"""
#         with patch("providers.llm.gemini.genai.Client") as mock_client_class:
#             mock_client = MagicMock()
            
#             # 첫 시도는 실패, 두 번째는 성공
#             mock_client.aio.models.generate_content = AsyncMock(
#                 side_effect=[
#                     Exception("Service temporarily unavailable"),
#                     mock_gemini_structured_response
#                 ]
#             )
#             mock_client_class.return_value = mock_client
            
#             provider = GeminiProvider(api_key="test_key", model="test_model")
            
#             # 첫 시도 - 실패
#             with pytest.raises(AppException):
#                 await provider.generate_structured(sample_prompt, FeedbackData)
            
#             # 두 번째 시도 - 성공
#             result = await provider.generate_structured(sample_prompt, FeedbackData)
#             assert isinstance(result, FeedbackData)
