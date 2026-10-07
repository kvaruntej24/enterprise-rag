import psycopg
import pytest

from app.core.config import settings
from app.retrieval.semantic import semantic_search


def _db_has_chunks() -> bool:
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            return conn.execute("SELECT count(*) FROM chunks").fetchone()[0] > 0
    except Exception:
        return False


requires_db = pytest.mark.skipif(
    not _db_has_chunks(), reason="database not available or empty"
)


@requires_db
def test_search_returns_k_results_sorted_by_score():
    results = semantic_search("How should passwords be stored?", k=5)
    assert len(results) == 5
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@requires_db
def test_doc_type_filter_is_applied():
    results = semantic_search("What is zero trust?", k=5, doc_type="pdf")
    assert results and all(r.doc_type == "pdf" for r in results)