from fastapi import APIRouter

router = APIRouter()

@router.get("/stt")
async def health_check():
    return {"status": "stt ok"}