import re
from dataclasses import replace
from functools import lru_cache

import psycopg
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.retrieval.semantic import SearchResult

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[.\-_][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.findall(text.lower()):
        tokens.append(match)
        parts = re.split(r"[.\-_]", match)
        if len(parts) > 1:
            tokens.extend(parts)
    return tokens


@lru_cache(maxsize=1)
def get_index() -> tuple[BM25Okapi, list[SearchResult]]:
    with psycopg.connect(settings.database_url) as conn:
        rows = conn.execute(
            "SELECT chunk_id, content, source, doc_type, page "
            "FROM chunks ORDER BY chunk_id"
        ).fetchall()
    chunks = [SearchResult(*row, 0.0) for row in rows]
    return BM25Okapi([tokenize(c.content) for c in chunks]), chunks


def bm25_search(
    query: str,
    k: int = 5,
    doc_type: str | None = None,
    source: str | None = None,
) -> list[SearchResult]:
    bm25, chunks = get_index()
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)

    results: list[SearchResult] = []
    for i in ranked:
        chunk = chunks[i]
        if scores[i] <= 0:
            break
        if doc_type and chunk.doc_type != doc_type:
            continue
        if source and chunk.source != source:
            continue
        results.append(replace(chunk, score=float(scores[i])))
        if len(results) == k:
            break
    return results