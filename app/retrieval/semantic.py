from dataclasses import dataclass

import psycopg
from pgvector.psycopg import register_vector

from app.core.config import settings
from app.retrieval.embeddings import embed_query

SEARCH_SQL = """
SELECT chunk_id, content, source, doc_type, page,
       1 - (embedding <=> %s) AS score
FROM chunks
WHERE (%s::text IS NULL OR doc_type = %s)
  AND (%s::text IS NULL OR source = %s)
ORDER BY embedding <=> %s
LIMIT %s
"""


@dataclass
class SearchResult:
    chunk_id: str
    content: str
    source: str
    doc_type: str
    page: int | None
    score: float


def semantic_search(
    query: str,
    k: int = 5,
    doc_type: str | None = None,
    source: str | None = None,
) -> list[SearchResult]:
    vector = embed_query(query)
    params = (vector, doc_type, doc_type, source, source, vector, k)
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        rows = conn.execute(SEARCH_SQL, params).fetchall()
    return [SearchResult(*row) for row in rows]