import re

from app.retrieval.semantic import SearchResult


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def is_relevant(chunk: SearchResult, row: dict, strict: bool) -> bool:
    if chunk.source == row["gold_source"]:
        if row.get("gold_page") and chunk.page != row["gold_page"]:
            return False
        return not strict or normalize(row["evidence"]) in normalize(chunk.content)
    return chunk.source in row.get("alt_sources", [])


def first_rank(results: list[SearchResult], row: dict, strict: bool) -> int | None:
    for rank, chunk in enumerate(results, start=1):
        if is_relevant(chunk, row, strict):
            return rank
    return None


def summarize(ranks: list[int | None]) -> dict:
    n = len(ranks)
    if n == 0:
        return {"n": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0}
    return {
        "n": n,
        "hit@1": sum(1 for r in ranks if r and r <= 1) / n,
        "hit@3": sum(1 for r in ranks if r and r <= 3) / n,
        "hit@5": sum(1 for r in ranks if r and r <= 5) / n,
        "mrr@5": sum(1 / r for r in ranks if r) / n,
    }