import httpx
from pathlib import Path
from core.config import settings

API_URL = "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo"
headers = {
    "Authorization": f"Bearer {settings.huggingface_api_key}",
}

CONTENT_TYPE_MAP = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
}

def get_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in CONTENT_TYPE_MAP:
        raise ValueError(f"Unsupported audio format: {ext}. Supported: mp3, mp4")
    return CONTENT_TYPE_MAP[ext]

async def transcribe(audio_url: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # S3에서 오디오 다운로드
        audio_res = await client.get(audio_url)
        audio_res.raise_for_status()

        # huggingface API 호출
        content_type = get_content_type(audio_url)
        response = await client.post(
            API_URL,
            headers={"Content-Type": content_type, **headers},
            content=audio_res.content,
        )
        response.raise_for_status()
        return response.json()["text"]
    

async def transcribe_local(audio_path: str) -> str:
    """로컬 오디오 파일로 테스트하는 함수"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # 로컬 파일 읽기
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        with open(audio_file, "rb") as f:
            audio_content = f.read()

        # huggingface API 호출
        content_type = get_content_type(audio_path)
        response = await client.post(
            API_URL,
            headers={"Content-Type": content_type, **headers},
            content=audio_content,
        )
        response.raise_for_status()
        return response.json()["text"]