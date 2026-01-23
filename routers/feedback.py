from fastapi import APIRouter   

router = APIRouter()

@router.post("/interview/feedback/request")
async def health_check():
    return {"status": "feedback ok"}