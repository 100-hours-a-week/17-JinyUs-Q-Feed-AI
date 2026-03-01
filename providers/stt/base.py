from typing import Protocol, Callable, Awaitable


class STTProvider(Protocol):
    @property
    def provider_name(self) -> str: ...
    async def transcribe(self, audio_url: str) -> str: ...


class SimpleSTTProvider:
    """단일 STT 함수를 STTProvider 인터페이스로 감싸는 래퍼"""

    def __init__(self, transcribe_fn: Callable[[str], Awaitable[str]], name: str):
        self._fn = transcribe_fn
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    async def transcribe(self, audio_url: str) -> str:
        return await self._fn(audio_url)