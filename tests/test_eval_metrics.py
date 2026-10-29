from app.retrieval.semantic import SearchResult
from evaluation.metrics import first_rank, is_relevant, summarize

ROW = {
    "gold_source": "a.pdf",
    "gold_page": 3,
    "evidence": "Hash passwords with Argon2.",
    "alt_sources": ["b.md"],
}


def chunk(source: str, page: int | None, text: str) -> SearchResult:
    return SearchResult("id", text, source, "pdf", page, 0.0)


def test_strict_needs_evidence_and_page():
    good = chunk("a.pdf", 3, "x Hash passwords\nwith Argon2. y")
    wrong_page = chunk("a.pdf", 4, "Hash passwords with Argon2.")
    no_evidence = chunk("a.pdf", 3, "unrelated text")
    assert is_relevant(good, ROW, strict=True)
    assert not is_relevant(wrong_page, ROW, strict=True)
    assert not is_relevant(no_evidence, ROW, strict=True)
    assert is_relevant(no_evidence, ROW, strict=False)


def test_alternate_source_counts_as_relevant():
    assert is_relevant(chunk("b.md", None, "anything"), ROW, strict=True)


def test_first_rank_and_miss():
    results = [chunk("z.pdf", 1, "no"), chunk("a.pdf", 3, "Hash passwords with Argon2.")]
    assert first_rank(results, ROW, strict=True) == 2
    assert first_rank(results[:1], ROW, strict=True) is None


def test_summarize_hit_and_mrr():
    m = summarize([1, 2, None, 5])
    assert m["hit@1"] == 0.25
    assert m["hit@3"] == 0.5
    assert m["hit@5"] == 0.75
    assert abs(m["mrr@5"] - (1 + 0.5 + 0 + 0.2) / 4) < 1e-9