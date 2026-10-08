import openai
import psycopg
from fastapi.testclient import TestClient

from app.api import main
from app.generation.pipeline import Answer
from app.retrieval.semantic import SearchResult

client = TestClient(main.app)


def fake_answer(question, k=5):
    chunk = SearchResult("id1", "Passwords should be hashed.", "doc.pdf", "pdf", 3, 5.0)
    return Answer(question, "Hash passwords [1].", False, cited={1: chunk}, top_score=5.0)


def raising(exc):
    def _raise(question, k=5):
        raise exc
    return _raise


def test_ask_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(main, "answer", fake_answer)
    response = client.post("/ask", json={"question": "How should passwords be stored?"})
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is False
    assert body["sources"][0]["source"] == "doc.pdf"
    assert body["sources"][0]["page"] == 3
    assert response.headers["x-request-id"] == body["request_id"]


def test_short_question_is_rejected_with_422():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422


def test_database_error_becomes_503_without_leaking_details(monkeypatch):
    monkeypatch.setattr(main, "answer", raising(psycopg.OperationalError("secret-db-host")))
    response = client.post("/ask", json={"question": "How should passwords be stored?"})
    assert response.status_code == 503
    assert "secret-db-host" not in response.text
    assert "Reference" in response.json()["detail"]


def test_llm_error_becomes_502(monkeypatch):
    monkeypatch.setattr(main, "answer", raising(openai.OpenAIError("secret-llm-detail")))
    response = client.post("/ask", json={"question": "How should passwords be stored?"})
    assert response.status_code == 502
    assert "secret-llm-detail" not in response.text


def test_unexpected_error_becomes_500(monkeypatch):
    monkeypatch.setattr(main, "answer", raising(RuntimeError("secret-bug")))
    response = client.post("/ask", json={"question": "How should passwords be stored?"})
    assert response.status_code == 500
    assert "secret-bug" not in response.text


def test_health_reports_503_when_database_is_down(monkeypatch):
    def boom(*args, **kwargs):
        raise psycopg.OperationalError("down")

    monkeypatch.setattr(main.psycopg, "connect", boom)
    assert client.get("/health").status_code == 503