# routers/feedback.py
from fastapi import APIRouter

from schemas.feedback import FeedbackRequest, FeedbackResponse
from services.feedback_service import FeedbackService
from core.logging import get_logger, log_execution_time

router = APIRouter()
logger = get_logger(__name__)

# def get_feedback_service(llm: LLMProvider = Depends(get_llm_provider)) -> FeedbackService:
#     """FeedbackService 의존성 생성"""
#     analyzer = AnswerAnalyzerService(llm_provider=llm)
#     return FeedbackService(analyzer=analyzer, llm_provider=llm)

@router.post("/interview/feedback/request", response_model=FeedbackResponse)
@log_execution_time(logger)
async def request_feedback(request: FeedbackRequest,):
    """
    면접 답변에 대한 피드백 생성
    """

    # bad case 체크
    service = FeedbackService()
    return await service.generate_feedback(request)

