from typing import Protocol

class STTProvider(Protocol):
    async def transcribe(self, audio_url: str) -> str:
        """ 음성 파일을 텍스트로 변환"""
        ...