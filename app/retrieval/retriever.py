from app.retrieval.hybrid import hybrid_search
from app.retrieval.rerank import rerank
from app.retrieval.semantic import SearchResult


def retrieve(
    query: str,
    k: int = 5,
    candidates: int = 20,
    doc_type: str | None = None,
    source: str | None = None,
) -> list[SearchResult]:
    pool = hybrid_search(
        query, k=candidates, candidates=candidates, doc_type=doc_type, source=source
    )
    return rerank(query, pool, top_k=k)