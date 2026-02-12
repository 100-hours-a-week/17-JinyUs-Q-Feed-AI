# services/feedback_service.py
from schemas.feedback import (
    FeedbackRequest, 
    FeedbackResponse, 
    BadCaseResult,
    InterviewType,
)

from services.bad_case_checker import get_bad_case_checker
from graphs.feedback.state import create_initial_state
from graphs.feedback.feedback_graph import run_feedback_pipeline

from core.logging import get_logger, log_execution_time

logger = get_logger(__name__)

class FeedbackService:
    """피드백 생성 서비스"""

    @log_execution_time(logger)
    async def generate_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        """피드백 생성 메인 로직"""

        # Step 1: bad case 체크(연습모드에서만) - bad case로 필터링 되면 bad case 응답 
        bad_case_result = self._check_bad_case(request)
        if bad_case_result:
            return FeedbackResponse.from_bad_case(
                user_id=request.user_id,
                question_id=request.question_id,
                session_id=request.session_id,
                bad_case_result=bad_case_result,
            )

        # Step 2: 그래프 실행
        result = await self._run_pipeline(request)
        print(f"Graph result keys: {result.keys()}")
        print(f"Graph result: {result}")

        # Step 3: 응답 변환 - 정상 피드백 응답
        return FeedbackResponse.from_evaluation(
            user_id=result["user_id"],
            question_id=result["question_id"],
            session_id=result["session_id"],
            rubric_result=result["rubric_result"],
            keyword_result=result["keyword_result"],
            topics_feedback=result["topics_feedback"],
            overall_feedback=result["overall_feedback"]
        )

    def _check_bad_case(self, request: FeedbackRequest) -> BadCaseResult | None:
        """Bad case 체크, 해당 시 응답 반환"""
        # 연습모드가 아니면 스킵
        if request.interview_type != InterviewType.PRACTICE_INTERVIEW:
            return None

        checker = get_bad_case_checker()
        last_turn = request.interview_history[0]
        result = checker.check(last_turn.question, last_turn.answer_text)
        # bad case일 때만 반환, 정상이면 None
        if result.is_bad_case:
            return result
        return None
    
    @log_execution_time(logger)
    async def _run_pipeline(self, request: FeedbackRequest) -> dict:
        """그래프 파이프라인 실행"""
        initial_state = create_initial_state(
            user_id=request.user_id,
            question_id=request.question_id,
            interview_history=request.interview_history,
            interview_type=request.interview_type,
            question_type=request.question_type,
            session_id=request.session_id,
            category=request.category,
            keywords=request.keywords,
        )
        return await run_feedback_pipeline(initial_state)
