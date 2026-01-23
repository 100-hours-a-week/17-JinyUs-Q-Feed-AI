# routers/feedback.py

from fastapi import APIRouter, Response

from schemas.feedback import FeedbackRequest, FeedbackResponse
from services.feedback_service import feedback_service

router = APIRouter()


@router.post("/interview/feedback/request", response_model=FeedbackResponse)
async def request_feedback(request: FeedbackRequest, response: Response):
    """
    면접 답변에 대한 피드백 생성
    
    - Answer Analyzer로 Bad Case 감지
    - 루브릭 기반 평가 (정확도, 논리력, 구체성, 완성도, 전달력)
    - 피드백 텍스트 생성 (잘한 점 / 개선할 점)
    """
    try:
        result = await feedback_service.generate_feedback(request)
        return result
    except Exception as e:
        response.status_code = 500
        return FeedbackResponse(
            message="feedback_generation_failed",
            data=None,
        )
