# routers/feedback.py

from fastapi import APIRouter

from schemas.feedback import FeedbackRequest, FeedbackResponse
from services.feedback_service import feedback_service
from core.logging import get_logger, log_execution_time

router = APIRouter()
logger = get_logger(__name__)

@router.post("/interview/feedback/request", response_model=FeedbackResponse)
@log_execution_time(logger)
async def request_feedback(request: FeedbackRequest):
    """
    면접 답변에 대한 피드백 생성
    
    - Answer Analyzer로 Bad Case 감지
    - 루브릭 기반 평가 (정확도, 논리력, 구체성, 완성도, 전달력)
    - 피드백 텍스트 생성 (잘한 점 / 개선할 점)
    """
    logger.info(
        f"user_id={request.user_id} | question_id={request.question_id} | "
        f"answer_length={len(request.answer_text)}"
    )
    result = await feedback_service.generate_feedback(request)
    logger.info(f"응답 | message={result.message}")
    return result

