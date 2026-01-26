from fastapi import APIRouter
from schemas.stt import STTRequest, STTResponse, STTData
from services.stt_service import process_transcribe

router = APIRouter()

@router.post("/stt")
async def speech_to_text(request: STTRequest) -> STTResponse:
    text = await process_transcribe(str(request.audio_url))
    return STTResponse(
        message="speech_to_text_success",
        data=STTData(user_id=request.user_id, session_id=request.session_id, text=text)
    )
