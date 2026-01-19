from fastapi import APIRouter   

router = APIRouter()

@router.get("/feedback")
async def health_check():
    return {"status": "feedback ok"}