from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from graphs.feedback.state import FeedbackGraphState
from schemas.feedback import KeywordCheckResult

@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("jhgan/ko-sroberta-multitask")

def keyword_checker(state: FeedbackGraphState, similarity_threshold: float = 0.3) -> dict:
    """키워드 커버리지 체크 노드"""

    #실전모드의 경우 필수키워드 체크 안함
    if not state["keywords"]:
        return {
            "keyword_result": KeywordCheckResult(
                covered_keywords=[],
                missing_keywords=[],
                coverage_ratio=1.0,
            ),
            "current_step": "keyword_checker",
        }
    
    #연습모드의 경우만 필수키워드 체크
    model = _get_embedding_model()

    #연습모드 답변 텍스트
    answer = state["interview_history"][0].answer_text

    # 임베딩 생성
    texts = [answer] + state["keywords"]
    embeddings = model.encode(texts)

    answer_emb = embeddings[0]
    keyword_embs = embeddings[1:]

    # 각 키워드와 답변 간 유사도 계산
    covered = []
    missing = []

    for keyword, kw_emb in zip(state["keywords"], keyword_embs):
        similarity = cos_sim(answer_emb, kw_emb).item()
        if similarity >= similarity_threshold:
            covered.append(keyword)
        else:
            missing.append(keyword)
    
    coverage = len(covered) / len(state["keywords"])
    return {
        "keyword_result": KeywordCheckResult(
            covered_keywords=covered,
            missing_keywords=missing,
            coverage_ratio=coverage,
        ),
        "current_step": "keyword_checker",
    }