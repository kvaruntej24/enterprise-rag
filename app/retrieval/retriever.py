import time

from app.retrieval.bm25 import bm25_search
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.rerank import rerank
from app.retrieval.semantic import SearchResult, semantic_search


def retrieve_with_timings(
    query: str,
    k: int = 5,
    candidates: int = 20,
    doc_type: str | None = None,
    source: str | None = None,
) -> tuple[list[SearchResult], dict[str, float]]:
    t0 = time.perf_counter()
    semantic = semantic_search(query, k=candidates, doc_type=doc_type, source=source)
    t1 = time.perf_counter()
    keyword = bm25_search(query, k=candidates, doc_type=doc_type, source=source)
    t2 = time.perf_counter()
    fused = reciprocal_rank_fusion([semantic, keyword])[:candidates]
    t3 = time.perf_counter()
    top = rerank(query, fused, top_k=k)
    t4 = time.perf_counter()
    timings = {
        "semantic_s": t1 - t0,
        "bm25_s": t2 - t1,
        "fusion_s": t3 - t2,
        "rerank_s": t4 - t3,
    }
    return top, timings


def retrieve(query: str, k: int = 5, candidates: int = 20,
             doc_type: str | None = None, source: str | None = None) -> list[SearchResult]:
    return retrieve_with_timings(query, k, candidates, doc_type, source)[0]