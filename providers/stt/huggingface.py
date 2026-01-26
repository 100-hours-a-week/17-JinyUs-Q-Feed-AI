import httpx
from pathlib import Path
from core.config import get_settings

settings = get_settings()

API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
headers = {
    "Authorization": f"Bearer {settings.huggingface_api_key}",
}

# S3 테스트 후 삭제해도됨
CONTENT_TYPE_MAP = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
}

def get_content_type(audio_url: str) -> str:
    ext = Path(audio_url).suffix.lower()  # URL에서 확장자 추출
    # 쿼리 파라미터 제거 필요!
    if '?' in audio_url:
        audio_url = audio_url.split('?')[0]
    ext = Path(audio_url).suffix.lower()
    return CONTENT_TYPE_MAP[ext]

async def transcribe(audio_url: str) -> str:
    """Presigned URL에서 오디오 다운로드하여 STT 수행"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # S3 Presigned URL에서 오디오 다운로드
        audio_res = await client.get(audio_url)
        audio_res.raise_for_status()

        # HuggingFace API 호출
        content_type = get_content_type(audio_url)
        response = await client.post(
            API_URL,
            headers={"Content-Type": content_type, **headers},
            content=audio_res.content,
        )
        response.raise_for_status()
        return response.json()["text"]
    
