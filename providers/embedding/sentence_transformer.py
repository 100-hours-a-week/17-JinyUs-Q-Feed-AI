from functools import lru_cache
from sentence_transformers import SentenceTransformer

class SentenceTransformerProvider:
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        self._model = SentenceTransformer(model_name)
    
    def encode(self, texts: list[str]):
        return self._model.encode(texts)

@lru_cache(maxsize=1)
def get_embedding_provider() -> SentenceTransformerProvider:
    return SentenceTransformerProvider()