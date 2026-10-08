from app.retrieval import rerank as rerank_module
from app.retrieval.semantic import SearchResult


class FakeReranker:
    def predict(self, pairs, batch_size=16):
        return [len(text) for _, text in pairs]


def make(chunk_id: str, text: str) -> SearchResult:
    return SearchResult(chunk_id, text, "d.pdf", "pdf", 1, 0.0)


def test_rerank_sorts_by_model_score_and_limits(monkeypatch):
    monkeypatch.setattr(rerank_module, "get_reranker", lambda: FakeReranker())
    results = [make("a", "xx"), make("b", "xxxx"), make("c", "x")]
    top = rerank_module.rerank("q", results, top_k=2)
    assert [r.chunk_id for r in top] == ["b", "a"]
    assert top[0].score == 4.0


def test_rerank_empty_input_returns_empty():
    assert rerank_module.rerank("q", []) == []