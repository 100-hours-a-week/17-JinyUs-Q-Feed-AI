# services/bad_case_checker.py
import re
from functools import lru_cache

from kiwipiepy import Kiwi
from korcen import korcen
from sentence_transformers.util import cos_sim

from schemas.feedback import BadCaseResult, BadCaseType
from providers.embedding.sentence_transformer import get_embedding_provider

FILLER_POS = {
    "JKS", "JKC", "JKG", "JKO", "JKB", "JKV", "JX", "JC",
    "IC", "EP", "EF", "EC", "ETN", "ETM",
    "SF", "SP", "SS", "SE", "SO", "SW",
}


@lru_cache(maxsize=1)
def _get_kiwi() -> Kiwi:
    return Kiwi()

class BadCaseChecker:
    def __init__(self, min_meaningful_tokens: int = 3, similarity_threshold: float = 0.3):
        self.min_meaningful_tokens = min_meaningful_tokens
        self.similarity_threshold = similarity_threshold
        self._kiwi = _get_kiwi()
        self._model = get_embedding_provider()

    def check_inappropriate(self, answer: str) -> bool:
        return korcen.check(answer)
    
    def check_insufficient(self, answer: str) -> bool:
        if self._has_repetitive_pattern(answer):
            return True
        if self._count_meaningful_tokens(answer) < self.min_meaningful_tokens:
            return True
        return False

    def check_off_topic(self, question: str, answer: str) -> bool:
        q_emb, a_emb = self._model.encode([question, answer])
        similarity = cos_sim(q_emb, a_emb).item()
        return similarity < self.similarity_threshold

    def _count_meaningful_tokens(self, text: str) -> int:
        tokens = self._kiwi.tokenize(text)
        return sum(1 for t in tokens if t.tag not in FILLER_POS)

    def _has_repetitive_pattern(self, answer: str) -> bool:
        if re.search(r'(.)\1{4,}', answer):
            return True
        if re.search(r'(\S+)(\s+\1){2,}', answer):
            return True
        words = answer.split()
        if len(words) >= 4 and len(set(words)) / len(words) < 0.3:
            return True
        return False
    
    def check(self, question: str, answer: str) -> BadCaseResult:
            """단일 Q&A 쌍 체크 - 메인 인터페이스"""

            if self.check_inappropriate(answer):
                return BadCaseResult.bad(BadCaseType.INAPPROPRIATE)
            
            if self.check_insufficient(answer):
                return BadCaseResult.bad(BadCaseType.INSUFFICIENT)
            
            if self.check_off_topic(question, answer):
                return BadCaseResult.bad(BadCaseType.OFF_TOPIC)
            
            return BadCaseResult.normal()
    
@lru_cache(maxsize=1)
def get_bad_case_checker() -> BadCaseChecker:
    return BadCaseChecker()
