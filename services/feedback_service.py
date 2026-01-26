# services/feedback_service.py

from schemas.feedback import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackData,
    FeedbackContent,
    AnswerAnalyzerResult,
    RubricEvaluationResult,
    BadCaseFeedback
)
from providers.llm.gemini import GeminiProvider
from services.answer_analyzer import AnswerAnalyzerService
from prompts.feedback import build_feedback_prompt, FEEDBACK_SYSTEM_PROMPT
from prompts.rubric import build_rubric_prompt, RUBRIC_SYSTEM_PROMPT


class FeedbackService:
    """피드백 생성 서비스"""

    def __init__(
        self,
        llm_provider: GeminiProvider | None = None,
        analyzer: AnswerAnalyzerService | None = None,
    ):
        self.llm = llm_provider or GeminiProvider()
        self.analyzer = analyzer or AnswerAnalyzerService(llm_provider=self.llm)

    async def generate_feedback(
        self,
        request: FeedbackRequest,
        analysis: AnswerAnalyzerResult | None = None,
    ) -> FeedbackResponse:
        """피드백 생성 파이프라인"""
        # Step 1: 답변 분석 (전달받지 않은 경우에만 수행)
        if analysis is None:
            analysis = await self.analyzer.analyze(request)

        # Bad Case인 경우 조기 반환
        if analysis.is_bad_case:
            return self._build_bad_case_response(request, analysis)

        # Step 2: 루브릭 평가
        rubric_result = await self._evaluate_rubrics(request)

        # Step 3: 피드백 텍스트 생성
        feedback_content = await self._generate_feedback_content(
            request=request,
            rubric_result=rubric_result,
        )

        return FeedbackResponse(
            message="success",
            data=FeedbackData(
                user_id=request.user_id,
                question_id=request.question_id,
                metrics=rubric_result.to_metrics_list(),
                bad_case=None,
                weakness=analysis.has_weakness,
                feedback=feedback_content,
            )
        )

    def _build_bad_case_response(
        self, 
        request: FeedbackRequest, 
        analysis: AnswerAnalyzerResult
    ) -> FeedbackResponse:
        """Bad Case 응답 생성"""
        return FeedbackResponse(
            message="bad_case_detected",
            data=FeedbackData(
                user_id=request.user_id,
                question_id=request.question_id,
                bad_case_feedback=BadCaseFeedback.from_type(analysis.bad_case_type),
                metrics=None,
                weakness=None,
                feedback=None
            )
        )

    async def _evaluate_rubrics(self, request: FeedbackRequest) -> RubricEvaluationResult:
        """루브릭 기반 평가"""
        return await self.llm.generate_structured(
            prompt=build_rubric_prompt(
                question_type=request.question_type.value,
                category=request.category.value,
                question=request.question,
                answer=request.answer_text,
            ),
            response_model=RubricEvaluationResult,
            system_prompt=RUBRIC_SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=4000
        )

    async def _generate_feedback_content(
        self,
        request: FeedbackRequest,
        rubric_result: RubricEvaluationResult,
    ) -> FeedbackContent:
        """피드백 텍스트 생성"""
        return await self.llm.generate_structured(
            prompt=build_feedback_prompt(
                question_type=request.question_type.value,
                category=request.category.value,
                question=request.question,
                answer=request.answer_text,
                rubric_result=rubric_result,
            ),
            response_model=FeedbackContent,
            system_prompt=FEEDBACK_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=4000,
        )


# 싱글톤 인스턴스
feedback_service = FeedbackService()