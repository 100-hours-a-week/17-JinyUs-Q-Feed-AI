# utils/prompt_hub.py
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from core.config import get_settings

_client: Client | None = None
settings = get_settings()

def get_client() -> Client:
    """LangSmith 클라이언트 싱글톤"""
    global _client
    if _client is None:
        _client = Client()
    return _client

def pull_prompt(name: str, version: str | None = None) -> ChatPromptTemplate:
    """
    LangSmith Hub에서 프롬프트 가져오기
    
    Args:
        name: 프롬프트 이름 (e.g., "winenu/rubric-evaluator")
        version: 버전 태그 또는 커밋 해시 (e.g., "prod", "dev", "a1b2c3d4")
                 None이면 settings.ENVIRONMENT 사용
    
    Returns:
        ChatPromptTemplate
    """
    if version is None:
        version = settings.ENVIRONMENT
    
    return get_client().pull_prompt(
        f"{name}:{version}",
        skip_cache=False,  # 내장 캐시 활성화 (기본값)
    )

def push_prompt(
    name: str,
    prompt: ChatPromptTemplate,
    tags: list[str] | None = None,
) -> str:
    """LangSmith Hub에 프롬프트 푸시"""
    client = get_client()
    return client.push_prompt(
        prompt_identifier=name,
        object=prompt,
        commit_tags=tags,
    )