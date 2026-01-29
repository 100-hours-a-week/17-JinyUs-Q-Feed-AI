"""
Answer Analyzer Service Unit Tests

테스트 대상: services/answer_analyzer.py
- AnswerAnalyzerService.analyze(): 답변 분석 실행
- AnswerAnalyzerService.is_bad_case(): Bad Case 여부 확인 헬퍼
- AnswerAnalyzerService.needs_followup(): 꼬리질문 필요 여부 확인 헬퍼
"""

import pytest
from unittest.mock import AsyncMock

from services.answer_analyzer import AnswerAnalyzerService
from schemas.feedback import AnswerAnalyzerResult, BadCaseType

# ============================================
# AnswerAnalyzerService 초기화 테스트
# ============================================

class TestAnswerAnalyzerServiceInit:
    """AnswerAnalyzerService 초기화 테스트"""

    def test_기본_초기화(self):
        """기본 LLM provider로 초기화"""
        service = AnswerAnalyzerService()

        assert service.llm is not None

    def test_커스텀_llm_provider_주입(self):
        """커스텀 LLM provider 주입"""
        mock_llm = AsyncMock()

        service = AnswerAnalyzerService(llm_provider=mock_llm)

        assert service.llm == mock_llm


# ============================================
# analyze 메서드 테스트
# ============================================

class TestAnalyze:
    """analyze 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_정상_답변_분석(
        self,
        sample_feedback_request,
        sample_analyzer_result_normal,
    ):
        """정상 답변 분석 성공"""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(
            return_value=sample_analyzer_result_normal
        )

        service = AnswerAnalyzerService(llm_provider=mock_llm)

        result = await service.analyze(sample_feedback_request)

        # 반환값 검증
        assert isinstance(result, AnswerAnalyzerResult)
        # LLM 호출 검증
        mock_llm.generate_structured.assert_called_once()
        call_kwargs = mock_llm.generate_structured.call_args.kwargs
        assert call_kwargs["response_model"] == AnswerAnalyzerResult

    @pytest.mark.asyncio
    async def test_약점_있는_답변_분석(
        self,
        sample_feedback_request,
        sample_analyzer_result_with_weakness,
    ):
        """약점이 있는 답변 분석"""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(
            return_value=sample_analyzer_result_with_weakness
        )

        service = AnswerAnalyzerService(llm_provider=mock_llm)

        result = await service.analyze(sample_feedback_request)

        assert result.is_bad_case is False
        assert result.has_weakness is True
        assert result.needs_followup is True
        assert result.followup_reason is not None

    @pytest.mark.asyncio
    async def test_bad_case_답변_분석(
        self,
        sample_feedback_request,
        sample_analyzer_result_bad_case_refuse,
    ):
        """Bad Case 답변 분석"""
        mock_llm = AsyncMock()
        mock_llm.generate_structured = AsyncMock(
            return_value=sample_analyzer_result_bad_case_refuse
        )

        service = AnswerAnalyzerService(llm_provider=mock_llm)

        result = await service.analyze(sample_feedback_request)

        assert result.is_bad_case is True
        assert result.bad_case_type == BadCaseType.REFUSE_TO_ANSWER


# ============================================
# is_bad_case 헬퍼 메서드 테스트
# ============================================

class TestIsBadCase:
    """is_bad_case 헬퍼 메서드 테스트"""

    def test_정상_답변_false(self, sample_analyzer_result_normal):
        """정상 답변 → False"""
        service = AnswerAnalyzerService()

        result = service.is_bad_case(sample_analyzer_result_normal)

        assert result is False

    def test_bad_case_답변_true(self, sample_analyzer_result_bad_case_refuse):
        """Bad Case 답변 → True"""
        service = AnswerAnalyzerService()

        result = service.is_bad_case(sample_analyzer_result_bad_case_refuse)

        assert result is True

    def test_약점_있는_답변_false(self, sample_analyzer_result_with_weakness):
        """약점 있지만 Bad Case 아님 → False"""
        service = AnswerAnalyzerService()

        result = service.is_bad_case(sample_analyzer_result_with_weakness)

        assert result is False


# ============================================
# needs_followup 헬퍼 메서드 테스트 -  v2
# ============================================

# class TestNeedsFollowup:
#     """needs_followup 헬퍼 메서드 테스트"""

#     def test_정상_답변_followup_불필요(self, sample_analyzer_result_normal):
#         """정상 답변, 꼬리질문 불필요 → False"""
#         service = AnswerAnalyzerService()

#         result = service.needs_followup(sample_analyzer_result_normal)

#         assert result == False

#     def test_약점_있는_답변_followup_필요(self, sample_analyzer_result_with_weakness):
#         """약점 있는 답변, 꼬리질문 필요 → True"""
#         service = AnswerAnalyzerService()

#         result = service.needs_followup(sample_analyzer_result_with_weakness)

#         assert result == True

#     def test_bad_case는_followup_불필요(self, sample_analyzer_result_bad_case_with_followup):
#         """Bad Case면 needs_followup=True여도 → False 반환"""
#         service = AnswerAnalyzerService()

#         # Bad Case이면서 needs_followup=True인 엣지 케이스
#         result = service.needs_followup(sample_analyzer_result_bad_case_with_followup)

#         # Bad Case는 꼬리질문 대신 재답변 유도해야 함
#         assert result == False

#     def test_bad_case_기본_followup_false(self, sample_analyzer_result_bad_case_refuse):
#         """Bad Case, needs_followup=False → False"""
#         service = AnswerAnalyzerService()

#         result = service.needs_followup(sample_analyzer_result_bad_case_refuse)

#         assert result == False