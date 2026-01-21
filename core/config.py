# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    stt_provider: str = "huggingface"  # or "runpod"

    #v1 : HuggingFace
    huggingface_api_key: str
    huggingface_model_id: str = "openai/whisper-large-v3-turbo"

    #v3 : RunPod
    
    model_config = {"env_file": ".env"}

settings = Settings()