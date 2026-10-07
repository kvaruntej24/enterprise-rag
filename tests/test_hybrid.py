from app.retrieval.bm25 import tokenize
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.semantic import SearchResult


def make(chunk_id: str) -> SearchResult:
    return SearchResult(chunk_id, "text", "doc.pdf", "pdf", 1, 0.0)


def test_tokenize_keeps_compound_ids_and_parts():
    tokens = tokenize("See GV.OC-03 now")
    assert "gv.oc-03" in tokens
    assert {"gv", "oc", "03"} <= set(tokens)


def test_rrf_prefers_chunks_ranked_in_both_lists():
    a, b, c = make("a"), make("b"), make("c")
    fused = reciprocal_rank_fusion([[a, b], [c, a]])
    assert fused[0].chunk_id == "a"
    assert {r.chunk_id for r in fused} == {"a", "b", "c"}