from app.generation.llm import LLMResponse
from app.generation.pipeline import answer, extract_citations, normalize_citations
from app.generation.prompts import NO_ANSWER_MESSAGE
from app.retrieval.semantic import SearchResult


def fake_results(n: int = 3) -> list[SearchResult]:
    return [
        SearchResult(f"id{i}", f"content {i}", f"doc{i}.pdf", "pdf", i, 0.9)
        for i in range(1, n + 1)
    ]


def patch_pipeline(monkeypatch, results, llm_text):
    monkeypatch.setattr("app.generation.pipeline.retrieve", lambda q, k=5: results)
    monkeypatch.setattr(
        "app.generation.pipeline.generate",
        lambda system, user: LLMResponse(llm_text, 10, 5, 0.1),
    )


def test_extract_citations_unique_and_ordered():
    assert extract_citations("A [2] and B [1][2]") == [2, 1]


def test_extract_citations_accepts_comma_form():
    assert extract_citations("See [1, 5].") == [1, 5]


def test_extract_citations_accepts_fullwidth_brackets():
    assert extract_citations("Use hashing【1】【2†L7-L9】.") == [1, 2]


def test_normalize_citations_rewrites_to_plain_format():
    assert normalize_citations("A【1】 B [2, 3]") == "A[1] B [2][3]"


def test_valid_citations_are_mapped_to_sources(monkeypatch):
    patch_pipeline(monkeypatch, fake_results(3), "Hash passwords [1][2].")
    result = answer("q")
    assert set(result.cited) == {1, 2}
    assert not result.refused and not result.uncited and not result.invalid_citations


def test_citation_outside_provided_sources_is_flagged(monkeypatch):
    patch_pipeline(monkeypatch, fake_results(3), "Some claim [4].")
    result = answer("q")
    assert result.invalid_citations == [4]
    assert result.uncited


def test_refusal_is_detected(monkeypatch):
    patch_pipeline(monkeypatch, fake_results(3), NO_ANSWER_MESSAGE)
    result = answer("q")
    assert result.refused and result.cited == {}


def test_no_results_refuses_without_calling_llm(monkeypatch):
    monkeypatch.setattr("app.generation.pipeline.retrieve", lambda q, k=5: [])

    def fail(*args, **kwargs):
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr("app.generation.pipeline.generate", fail)
    assert answer("q").refused