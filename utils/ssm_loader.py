# utils/ssm_loader.py
import boto3
from functools import lru_cache
from botocore.exceptions import ClientError
from exceptions.exceptions import AppException
from exceptions.error_messages import ErrorMessage

class SSMConfigLoader:
    """AWS Parameter Store 기반 설정 로더"""
    
    def __init__(self, region: str = 'ap-northeast-2'):
        self._client = boto3.client('ssm', region_name=region)
        self._cache: dict[str, str] = {}
    
    def get_parameter(
        self, 
        ssm_path: str, 
        env_fallback: str | None = None,
        required: bool = True
    ) -> str | None:
        """Parameter Store에서 값 로드, fallback으로 환경변수"""
        
        # 캐시 확인
        if ssm_path in self._cache:
            return self._cache[ssm_path]
        
        # SSM 시도
        try:
            response = self._client.get_parameter(
                Name=ssm_path,
                WithDecryption=True
            )
            value = response['Parameter']['Value']
            self._cache[ssm_path] = value
            return value
        except ClientError:
            raise  AppException(ErrorMessage.API_KEY_INVALID)
        
        # # Fallback: 환경변수
        # if env_fallback:
        #     value = os.getenv(env_fallback)
        #     if value:
        #         return value
        
        # if required:
        #     raise ValueError(f"설정을 찾을 수 없음: {ssm_path}")
        # return None

@lru_cache
def get_ssm_loader() -> SSMConfigLoader:
    return SSMConfigLoader()