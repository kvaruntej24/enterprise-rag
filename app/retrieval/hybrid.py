from dataclasses import replace

from app.retrieval.bm25 import bm25_search
from app.retrieval.semantic import SearchResult, semantic_search


def reciprocal_rank_fusion(
    rankings: list[list[SearchResult]], k: int = 60
) -> list[SearchResult]:
    scores: dict[str, float] = {}
    by_id: dict[str, SearchResult] = {}
    for ranking in rankings:
        for rank, result in enumerate(ranking, start=1):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (k + rank)
            by_id.setdefault(result.chunk_id, result)
    fused = sorted(by_id.values(), key=lambda r: scores[r.chunk_id], reverse=True)
    return [replace(r, score=scores[r.chunk_id]) for r in fused]


def hybrid_search(
    query: str,
    k: int = 5,
    candidates: int = 20,
    doc_type: str | None = None,
    source: str | None = None,
) -> list[SearchResult]:
    semantic = semantic_search(query, k=candidates, doc_type=doc_type, source=source)
    keyword = bm25_search(query, k=candidates, doc_type=doc_type, source=source)
    return reciprocal_rank_fusion([semantic, keyword])[:k]