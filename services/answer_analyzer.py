# services/answer_analyzer.py

from schemas.feedback import FeedbackRequest, AnswerAnalyzerResult
from providers.llm.gemini import GeminiProvider
from prompts.analyzer import ANALYZER_SYSTEM_PROMPT, build_analyzer_prompt


class AnswerAnalyzerService:
    """답변 분석 서비스 - 피드백/꼬리질문 생성의 공용 모듈"""

    def __init__(self, llm_provider: GeminiProvider | None = None):
        self.llm = llm_provider or GeminiProvider()
    
    async def analyze(self, request: FeedbackRequest) -> AnswerAnalyzerResult:
        """답변 분석 실행"""
        prompt = build_analyzer_prompt(
            category=request.category.value,
            question=request.question,
            answer=request.answer_text,
        )
        
        return await self.llm.generate_structured(
            prompt=prompt,
            response_model=AnswerAnalyzerResult,
            system_prompt=ANALYZER_SYSTEM_PROMPT,
            temperature=0.0,
        )

    def is_bad_case(self, result: AnswerAnalyzerResult) -> bool:
        """Bad Case 여부 확인 헬퍼"""
        return result.is_bad_case
    
    def needs_followup(self, result: AnswerAnalyzerResult) -> bool:
        """꼬리질문 필요 여부 확인 헬퍼"""
        return result.needs_followup and not result.is_bad_case


# 싱글톤 인스턴스
answer_analyzer = AnswerAnalyzerService()
