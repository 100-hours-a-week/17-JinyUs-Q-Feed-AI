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
from core.config import get_settings
from providers.llm.base import LLMProvider
from services.answer_analyzer import AnswerAnalyzerService
from prompts.feedback import build_feedback_prompt, get_feedback_system_prompt
from prompts.rubric import build_rubric_prompt, get_rubric_system_prompt
from core.logging import get_logger, log_execution_time

logger = get_logger(__name__)
settings = get_settings()

class FeedbackService:
    """피드백 생성 서비스"""

    def __init__(
        self,
        llm_provider : LLMProvider,  # 타입 힌트 유연하게
        analyzer: AnswerAnalyzerService | None = None
    ):
        self.llm = llm_provider
        self.analyzer = analyzer

    @log_execution_time(logger)
    async def generate_feedback(
        self,
        request: FeedbackRequest,
    ) -> FeedbackResponse:
        """피드백 생성 파이프라인"""

        logger.info(
            f"피드백 생성 시작 | user_id={request.user_id} | "
            f"question_id={request.question_id} | interview_type={request.interview_type.value} | "
            f"question_type={request.question_type.value} | category={request.category.value} "
        )

        # Step 1: 답변 분석 (전달받지 않은 경우에만 수행)
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

        logger.debug("피드백 생성 완료 ")

        return FeedbackResponse(
            message="generate_feedback_success",
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
    
    @log_execution_time(logger)
    async def _evaluate_rubrics(self, request: FeedbackRequest) -> RubricEvaluationResult:
        """루브릭 기반 평가"""
        logger.info(f"루브릭 평가 시작 | user_id={request.user_id} | "
            f"question_id={request.question_id} | interview_type={request.interview_type.value} | "
            f"question_type={request.question_type.value} | category={request.category.value} "
        )   
        system_prompt = get_rubric_system_prompt(self.llm.provider_name)

        result = await self.llm.generate_structured(
            prompt=build_rubric_prompt(
                question_type=request.question_type.value,
                category=request.category.value,
                question=request.question,
                answer=request.answer_text,
            ),
            response_model=RubricEvaluationResult,
            system_prompt=system_prompt,
            temperature=0.0,
            max_tokens=4000
        )
        
        logger.debug(f"루브릭 평가 완료 | scores={result.to_metrics_list()}")
        return result

    @log_execution_time(logger)
    async def _generate_feedback_content(
        self,
        request: FeedbackRequest,
        rubric_result: RubricEvaluationResult,
    ) -> FeedbackContent:
        """피드백 텍스트 생성"""
        logger.info("피드백 텍스트 생성 시작 | user_id={request.user_id} | question_id={request.question_id}")
        
        system_prompt = get_feedback_system_prompt(self.llm.provider_name)
        
        result = await self.llm.generate_structured(
            prompt=build_feedback_prompt(
                question_type=request.question_type.value,
                category=request.category.value,
                question=request.question,
                answer=request.answer_text,
                rubric_result=rubric_result,
            ),
            response_model=FeedbackContent,
            system_prompt=system_prompt,  # ✅ 문자열 전달
            temperature=0.3,
            max_tokens=4000,
        )
        
        strengths_count = len(result.strengths) if result.strengths else 0
        improvements_count = len(result.improvements) if result.improvements else 0
        logger.debug(f"피드백 텍스트 생성 완료 | strengths={strengths_count} | improvements={improvements_count}")
        return result