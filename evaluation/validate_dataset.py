import json
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg

from app.core.config import settings

sys.stdout.reconfigure(encoding="utf-8")

PATH = Path("evaluation/questions.jsonl")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def main() -> int:
    problems: list[str] = []
    rows = []
    for number, line in enumerate(PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            problems.append(f"line {number}: invalid JSON ({exc})")

    with psycopg.connect(settings.database_url) as conn:
        chunks = conn.execute("SELECT source, page, content FROM chunks").fetchall()
    known_sources = {c[0] for c in chunks}
    corpus_text = normalize(" ".join(c[2] for c in chunks))

    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    kinds: Counter = Counter()
    tags: Counter = Counter()

    for row in rows:
        qid = row.get("id", "?")
        question = normalize(row.get("question", ""))
        if qid in seen_ids:
            problems.append(f"{qid}: duplicate id")
        seen_ids.add(qid)
        if not question:
            problems.append(f"{qid}: empty question")
        if question in seen_questions:
            problems.append(f"{qid}: duplicate question")
        seen_questions.add(question)

        kind = row.get("type")
        kinds[kind] += 1
        for tag in row.get("tags") or ["llm_drafted"]:
            tags[tag] += 1

        if kind == "answerable":
            for field in ("reference_answer", "gold_source", "evidence"):
                if not row.get(field):
                    problems.append(f"{qid}: missing {field}")
            for source in [row.get("gold_source")] + row.get("alt_sources", []):
                if source and source not in known_sources:
                    problems.append(f"{qid}: unknown source '{source}'")
            page = row.get("gold_page")
            scope = normalize(" ".join(
                c[2] for c in chunks
                if c[0] == row.get("gold_source") and (page is None or c[1] == page)
            ))
            if not scope:
                problems.append(f"{qid}: no chunks for {row.get('gold_source')} page {page}")
            elif normalize(row.get("evidence", "")) not in scope:
                problems.append(f"{qid}: evidence not found in gold source/page")
        elif kind == "unanswerable":
            if row.get("gold_source"):
                problems.append(f"{qid}: unanswerable question must not have gold_source")
            for keyword in row.get("keywords_absent", []):
                if normalize(keyword) in corpus_text:
                    problems.append(f"{qid}: keyword '{keyword}' DOES appear in the corpus")
        else:
            problems.append(f"{qid}: type must be 'answerable' or 'unanswerable'")

    print(f"{len(rows)} questions | by type: {dict(kinds)}")
    print(f"tags: {dict(tags)}")
    for problem in problems:
        print("PROBLEM:", problem)
    print("OK" if not problems else f"{len(problems)} problem(s) found")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())