from dataclasses import replace
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.retrieval.semantic import SearchResult


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(settings.reranker_model, max_length=512)


def rerank(query: str, results: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
    if not results:
        return []
    pairs = [(query, r.content) for r in results]
    scores = get_reranker().predict(pairs, batch_size=16)
    ranked = sorted(zip(results, scores), key=lambda pair: pair[1], reverse=True)
    return [replace(r, score=float(s)) for r, s in ranked[:top_k]]