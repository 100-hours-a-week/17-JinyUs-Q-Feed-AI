# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    stt_provider: str = "huggingface"  # or "runpod"

    #v1 : HuggingFace
    huggingface_api_key: str
    huggingface_model_id: str = "openai/whisper-large-v3-turbo"

    # gemini
    gemini_api_key: str
    gemini_model_id: str = "gemini-2.5-pro"

    # AWS S3 설정
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "ap-northeast-2"
    # 버킷 설정 - 환경별
    AWS_S3_AUDIO_BUCKET: str


    # Callback 설정 (V2)
    feedback_callback_url: str = "http://backend-server/ai/interview/feedback/generate"
    callback_timeout_seconds: int = 30

    #v3 : RunPod
    
    model_config = {"env_file": ".env"}

settings = Settings()