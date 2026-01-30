# core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from utils.ssm_loader import get_ssm_loader

class Settings(BaseSettings):
    ENVIRONMENT: str = "local"  # local | production

    # 로그 설정 추가
    LOG_DIR: str = "./logs"

    @property
    def log_directory(self) -> str:
        if self.LOG_DIR:
            return self.LOG_DIR
        # 환경별 기본값 설정 -> ec2 서버 log 경로 확정되면 수정할 것
        return "./logs" if self.ENVIRONMENT == "local" else "/var/log/qfeed/ai"

    STT_PROVIDER: str = "huggingface"  # or "runpod"

    #v1 : HuggingFace
    HUGGINGFACE_API_KEY: str
    HUGGINGFACE_MODEL_ID: str = "openai/whisper-large-v3-turbo"

    # gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL_ID: str = "gemini-2.5-pro"

    # AWS S3 설정
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "ap-northeast-2"
    # 버킷 설정 - 환경별
    AWS_S3_AUDIO_BUCKET: str | None = None


    # Callback 설정 (V2)
    feedback_callback_url: str = "http://backend-server/ai/interview/feedback/generate"
    callback_timeout_seconds: int = 30

    #v3 : RunPod
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",  # 정의되지 않은 환경변수 무시 (E2E 테스트용 등)
    }

@lru_cache
def get_settings() -> Settings:
    """환경에 따라 설정 로드"""
    
    # production 환경이면 SSM에서 먼저 로드해서 환경 변수로 설정
    # (Settings() 초기화 전에 필수 필드가 있어야 하므로)
    environment = os.getenv("ENVIRONMENT", "local")
    if environment == "production":
        loader = get_ssm_loader()
        
        # SSM에서 시크릿 로드 후 환경 변수로 설정
        # pydantic_settings는 환경 변수 이름을 필드 이름과 매칭합니다
        # huggingface_api_key -> HUGGINGFACE_API_KEY 또는 huggingface_api_key
        ssm_mappings = {
            "HUGGINGFACE_API_KEY": "/qfeed/prod/ai/huggingface-api-key",
            "GEMINI_API_KEY": "/qfeed/prod/ai/gemini-api-key",
            "AWS_S3_AUDIO_BUCKET": "/qfeed/prod/ai/aws-s3-audio-bucket",
        }
        
        for env_var, ssm_path in ssm_mappings.items():
            if env_var not in os.environ:
                value = loader.get_parameter(ssm_path, required=False)
                if value:
                    os.environ[env_var] = value
    
    settings = Settings()
    print(f"=== ENVIRONMENT: {settings.ENVIRONMENT} ===") 
    return settings
