import json
import random
import re
import sys
import time
from pathlib import Path

import psycopg

from app.core.config import settings
from app.generation.llm import generate

sys.stdout.reconfigure(encoding="utf-8")

QUOTAS = {"pdf": 18, "markdown": 14, "html": 8}
OUT_PATH = Path("evaluation/draft_questions.jsonl")

SYSTEM = (
    "You write evaluation questions for a document search system. Given a passage, "
    "write ONE question that a user could ask and that this passage answers. Rules: "
    "the question must make sense on its own (never say 'this passage' or 'the text'); "
    "paraphrase instead of copying phrases from the passage; give a short answer; and "
    "copy ONE supporting sentence EXACTLY as it appears in the passage. "
    'Reply with JSON only: {"question": "...", "answer": "...", "evidence": "..."}'
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def main() -> None:
    random.seed(42)
    with psycopg.connect(settings.database_url) as conn:
        rows = conn.execute(
            "SELECT content, source, doc_type, page FROM chunks WHERE length(content) >= 500"
        ).fetchall()

    by_type: dict[str, list] = {}
    for row in rows:
        by_type.setdefault(row[2], []).append(row)

    drafts = []
    for doc_type, quota in QUOTAS.items():
        pool = by_type.get(doc_type, [])
        for content, source, _, page in random.sample(pool, min(quota, len(pool))):
            try:
                reply = generate(SYSTEM, f"Passage:\n{content}")
                data = json.loads(re.search(r"\{.*\}", reply.text, re.S).group(0))
            except Exception as exc:
                print(f"skip ({type(exc).__name__}): {source}")
                continue
            if normalize(data.get("evidence", "")) not in normalize(content):
                print(f"skip (evidence not found in passage): {source}")
                continue
            drafts.append({
                "id": f"q{len(drafts) + 1:03d}",
                "type": "answerable",
                "question": data["question"],
                "reference_answer": data["answer"],
                "gold_source": source,
                "gold_page": page,
                "evidence": data["evidence"],
            })
            time.sleep(2)

    OUT_PATH.parent.mkdir(exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for item in drafts:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"wrote {len(drafts)} draft questions to {OUT_PATH}")


if __name__ == "__main__":
    main()