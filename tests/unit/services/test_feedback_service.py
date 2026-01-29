import pytest
from unittest.mock import AsyncMock

from services.feedback_service import FeedbackService
from schemas.feedback import (
    FeedbackResponse,
    FeedbackData,
    FeedbackContent,
    RubricEvaluationResult,
    BadCaseType
)


# ============================================
# FeedbackService 초기화 테스트
# ============================================

class TestFeedbackServiceInit:
    """FeedbackService 초기화 테스트"""

    def test_기본_초기화(self):
        """기본 provider와 analyzer로 초기화"""
        service = FeedbackService()

        assert service.llm is not None
        assert service.analyzer is not None

    def test_커스텀_llm_provider_주입(self):
        """커스텀 LLM provider 주입"""
        mock_llm = AsyncMock()

        service = FeedbackService(llm_provider=mock_llm)

        assert service.llm == mock_llm

    def test_커스텀_analyzer_주입(self):
        """커스텀 analyzer 주입"""
        mock_analyzer = AsyncMock()

        service = FeedbackService(analyzer=mock_analyzer)

        assert service.analyzer == mock_analyzer

    def test_llm과_analyzer_모두_주입(self):
        """LLM provider와 analyzer 모두 주입"""
        mock_llm = AsyncMock()
        mock_analyzer = AsyncMock()

        service = FeedbackService(llm_provider=mock_llm, analyzer=mock_analyzer)

        assert service.llm == mock_llm
        assert service.analyzer == mock_analyzer


# ============================================
# generate_feedback 정상 케이스 테스트
# ============================================

class TestGenerateFeedbackNormalCase:
    """generate_feedback 정상 케이스 테스트"""

    @pytest.mark.asyncio
    async def test_정상_피드백_생성(
        self,
        sample_feedback_request,
        mock_llm_provider,
        mock_analyzer_normal,
    ):
        """정상적인 답변에 대한 피드백 생성 성공"""
        service = FeedbackService(
            llm_provider=mock_llm_provider,
            analyzer=mock_analyzer_normal,
        )

        response = await service.generate_feedback(sample_feedback_request)

        # 1. 응답 타입 검증 (스키마 구조)
        assert isinstance(response, FeedbackResponse)
        assert isinstance(response.data, FeedbackData)

        # analyzer 호출 검증
        mock_analyzer_normal.analyze.assert_called_once_with(sample_feedback_request)

        # LLM 2번 호출 검증 (루브릭 + 피드백)
        assert mock_llm_provider.generate_structured.call_count == 2

    @pytest.mark.asyncio
    async def test_약점_있는_답변_피드백_생성(
        self,
        sample_feedback_request,
        mock_llm_provider,
        mock_analyzer_with_weakness,
    ):
        """약점이 있는 답변에 대한 피드백 생성"""
        service = FeedbackService(
            llm_provider=mock_llm_provider,
            analyzer=mock_analyzer_with_weakness,
        )

        response = await service.generate_feedback(sample_feedback_request)

        assert response.message == "generate_feedback_success"
        assert response.data.weakness # weakenss True인지 검증
        assert response.data.metrics is not None
        assert response.data.feedback is not None



# ============================================
# generate_feedback Bad Case 테스트
# ============================================

class TestGenerateFeedbackBadCase:
    """generate_feedback Bad Case 테스트"""

    @pytest.mark.asyncio
    async def test_답변_거부_bad_case(
        self,
        sample_feedback_request,
        mock_llm_provider,
        mock_analyzer_bad_case_refuse,
    ):
        """답변 거부 Bad Case 처리"""
        service = FeedbackService(
            llm_provider=mock_llm_provider,
            analyzer=mock_analyzer_bad_case_refuse,
        )

        response = await service.generate_feedback(sample_feedback_request)

        # Bad Case 응답 검증
        assert response.message == "bad_case_detected"
        assert response.data.bad_case_feedback is not None
        assert response.data.bad_case_feedback.type == BadCaseType.REFUSE_TO_ANSWER
        assert response.data.metrics is None
        assert response.data.feedback is None
        assert response.data.weakness is None

        # LLM 호출되지 않음 (조기 반환)
        mock_llm_provider.generate_structured.assert_not_called()

    @pytest.mark.asyncio
    async def test_너무_짧은_답변_bad_case(
        self,
        sample_feedback_request,
        mock_llm_provider,
        mock_analyzer_bad_case_too_short,
    ):
        """너무 짧은 답변 Bad Case 처리"""
        service = FeedbackService(
            llm_provider=mock_llm_provider,
            analyzer=mock_analyzer_bad_case_too_short,
        )

        response = await service.generate_feedback(sample_feedback_request)

        assert response.message == "bad_case_detected"
        assert response.data.bad_case_feedback.type == BadCaseType.TOO_SHORT

    @pytest.mark.asyncio
    async def test_부적절한_답변_bad_case(
        self,
        sample_feedback_request,
        mock_llm_provider,
        sample_analyzer_result_bad_case_inappropriate,
    ):
        """부적절한 답변 Bad Case 처리"""
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze = AsyncMock(
            return_value=sample_analyzer_result_bad_case_inappropriate
        )

        service = FeedbackService(
            llm_provider=mock_llm_provider,
            analyzer=mock_analyzer,
        )

        response = await service.generate_feedback(sample_feedback_request)

        assert response.message == "bad_case_detected"
        assert response.data.bad_case_feedback.type == BadCaseType.INAPPROPRIATE


# ============================================
# _evaluate_rubrics 테스트
# ============================================

class TestEvaluateRubrics:
    """_evaluate_rubrics 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_루브릭_평가_호출(
        self,
        sample_feedback_request,
        sample_rubric_result,
    ):
        """루브릭 평가 LLM 호출 검증"""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=sample_rubric_result)

        service = FeedbackService(llm_provider=mock_llm)

        result = await service._evaluate_rubrics(sample_feedback_request)

        # 반환값 검증
        assert result == sample_rubric_result
        assert result.accuracy == 4
        assert result.logic == 3

        # LLM 호출 검증
        mock_llm.generate_structured.assert_called_once()
        call_kwargs = mock_llm.generate_structured.call_args.kwargs
        assert call_kwargs["response_model"] == RubricEvaluationResult

    @pytest.mark.asyncio
    async def test_루브릭_평가_결과_metrics_변환(
        self,
        sample_feedback_request,
        sample_rubric_result,
    ):
        """루브릭 평가 결과가 metrics 리스트로 변환되는지 확인"""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=sample_rubric_result)

        service = FeedbackService(llm_provider=mock_llm)

        result = await service._evaluate_rubrics(sample_feedback_request)
        metrics = result.to_metrics_list()

        assert len(metrics) == 5


# ============================================
# _generate_feedback_content 테스트
# ============================================

class TestGenerateFeedbackContent:
    """_generate_feedback_content 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_피드백_텍스트_생성(
        self,
        sample_feedback_request,
        sample_rubric_result,
        sample_feedback_content,
    ):
        """피드백 텍스트 생성 LLM 호출 검증"""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(return_value=sample_feedback_content)

        service = FeedbackService(llm_provider=mock_llm)

        result = await service._generate_feedback_content(
            request=sample_feedback_request,
            rubric_result=sample_rubric_result,
        )

        # 반환값 검증
        assert result == sample_feedback_content
        assert result.strengths is not None
        assert result.improvements is not None

        # LLM 호출 검증
        mock_llm.generate_structured.assert_called_once()
        call_kwargs = mock_llm.generate_structured.call_args.kwargs
        assert call_kwargs["response_model"] == FeedbackContent


# ============================================
# _build_bad_case_response 테스트
# ============================================

class TestBuildBadCaseResponse:
    """_build_bad_case_response 메서드 테스트"""

    def test_답변_거부_응답_생성(
        self,
        sample_feedback_request,
        sample_analyzer_result_bad_case_refuse,
    ):
        """답변 거부 Bad Case 응답 생성"""
        service = FeedbackService()

        response = service._build_bad_case_response(
            sample_feedback_request,
            sample_analyzer_result_bad_case_refuse,
        )

        assert response.message == "bad_case_detected"
        assert isinstance(response.data, FeedbackData)
            
        assert response.data.feedback is None

    def test_너무_짧은_답변_응답_생성(
        self,
        sample_feedback_request,
        sample_analyzer_result_bad_case_too_short,
    ):
        """너무 짧은 답변 Bad Case 응답 생성"""
        service = FeedbackService()

        response = service._build_bad_case_response(
            sample_feedback_request,
            sample_analyzer_result_bad_case_too_short,
        )

        assert response.data.bad_case_feedback.type == BadCaseType.TOO_SHORT

    def test_부적절한_답변_응답_생성(
        self,
        sample_feedback_request,
        sample_analyzer_result_bad_case_inappropriate,
    ):
        """부적절한 답변 Bad Case 응답 생성"""
        service = FeedbackService()

        response = service._build_bad_case_response(
            sample_feedback_request,
            sample_analyzer_result_bad_case_inappropriate,
        )

        assert response.data.bad_case_feedback.type == BadCaseType.INAPPROPRIATE