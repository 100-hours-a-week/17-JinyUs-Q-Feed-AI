# routers/feedback.py
from fastapi import APIRouter, Depends

from schemas.feedback import FeedbackRequest, FeedbackResponse
from services.feedback_service import FeedbackService
from services.answer_analyzer import AnswerAnalyzerService
from providers.llm.base import LLMProvider
from core.dependencies import get_llm_provider
from core.logging import get_logger, log_execution_time

router = APIRouter()
logger = get_logger(__name__)

def get_feedback_service(llm: LLMProvider = Depends(get_llm_provider)) -> FeedbackService:
    """FeedbackService 의존성 생성"""
    analyzer = AnswerAnalyzerService(llm_provider=llm)
    return FeedbackService(analyzer=analyzer, llm_provider=llm)

@router.post("/interview/feedback/request", response_model=FeedbackResponse)
@log_execution_time(logger)
async def request_feedback(
    request: FeedbackRequest,
    service: FeedbackService = Depends(get_feedback_service)
):
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
    result = await service.generate_feedback(request)
    logger.info(f"응답 | message={result.message}")
    return result

