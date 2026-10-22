import json
import sys
import time
from collections import Counter
from pathlib import Path

from app.core.config import settings
from app.generation.pipeline import answer

sys.stdout.reconfigure(encoding="utf-8")

QUESTIONS_PATH = Path("evaluation/questions.jsonl")
RESULTS_DIR = Path("evaluation/results")


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({n / d:.0%})" if d else "n/a"


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    by_id = {r["id"]: r for r in rows}

    records = []
    for row in rows:
        try:
            result = answer(row["question"])
        except Exception as exc:
            print(f"ERROR {row['id']}: {type(exc).__name__}: {exc}")
            records.append({"id": row["id"], "type": row["type"], "error": str(exc)})
            continue
        records.append({
            "id": row["id"],
            "type": row["type"],
            "tags": row.get("tags") or ["llm_drafted"],
            "question": row["question"],
            "answer": result.text,
            "refused": result.refused,
            "refusal_reason": result.refusal_reason,
            "top_score": result.top_score,
            "cited_sources": sorted({c.source for c in result.cited.values()}),
            "invalid_citations": result.invalid_citations,
            "uncited": result.uncited,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "retrieval_seconds": result.retrieval_seconds,
            "llm_seconds": result.llm_seconds,
        })
        status = "REFUSED " if result.refused else "ANSWERED"
        print(f"{row['id']}: {status} {result.refusal_reason or ''}")
        time.sleep(2)

    ok = [r for r in records if "error" not in r]
    answerable = [r for r in ok if r["type"] == "answerable"]
    unanswerable = [r for r in ok if r["type"] == "unanswerable"]
    answered = [r for r in answerable if not r["refused"]]

    def source_ok(record: dict) -> bool:
        gold = by_id[record["id"]]
        allowed = {gold["gold_source"], *gold.get("alt_sources", [])}
        return bool(allowed & set(record["cited_sources"]))

    valid = [r for r in answered if not r["uncited"] and not r["invalid_citations"]]
    source_correct = [r for r in answered if source_ok(r)]
    false_refusals = [r for r in answerable if r["refused"]]
    correct_refusals = [r for r in unanswerable if r["refused"]]
    missed_refusals = [r for r in unanswerable if not r["refused"]]
    llm_calls = [r for r in ok if r["input_tokens"] > 0]

    summary = {
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        "errors": len(records) - len(ok),
        "false_refusals": len(false_refusals),
        "correct_refusals": len(correct_refusals),
        "missed_refusals": len(missed_refusals),
        "answered_with_valid_citations": len(valid),
        "answered_with_correct_source": len(source_correct),
        "answered": len(answered),
        "llm_calls": len(llm_calls),
        "avg_input_tokens_per_llm_call": (
            sum(r["input_tokens"] for r in llm_calls) / len(llm_calls) if llm_calls else 0
        ),
        "avg_llm_seconds": (
            sum(r["llm_seconds"] for r in llm_calls) / len(llm_calls) if llm_calls else 0
        ),
    }

    print(f"\n{len(ok)} questions evaluated, {summary['errors']} errors")
    print(f"Answerable, refused (false refusal):     {pct(len(false_refusals), len(answerable))}")
    print(f"Unanswerable, refused (correct):         {pct(len(correct_refusals), len(unanswerable))}")
    print(f"Unanswerable, answered (missed refusal): {pct(len(missed_refusals), len(unanswerable))}")
    print(f"Answered with valid citations:           {pct(len(valid), len(answered))}")
    print(f"Answered citing the gold/alt source:     {pct(len(source_correct), len(answered))}")
    reasons = Counter(r["refusal_reason"] for r in correct_refusals)
    print(f"Why unanswerable questions were refused: {dict(reasons)}")
    print(f"LLM calls made: {len(llm_calls)} of {len(ok)} questions; "
          f"avg input tokens {summary['avg_input_tokens_per_llm_call']:.0f}")

    for title, group in (
        ("False refusals", false_refusals),
        ("Missed refusals", missed_refusals),
        ("Answered without valid citations", [r for r in answered if r not in valid]),
        ("Answered but wrong cited source", [r for r in answered if r not in source_correct]),
    ):
        if group:
            print(f"\n{title}:")
            for r in group:
                print(f"  {r['id']} (top score {r['top_score']:.2f}): {r['question'][:80]}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"generation_{label}.json"
    out.write_text(json.dumps({
        "label": label,
        "config": {
            "relevance_threshold": settings.relevance_threshold,
            "llm_model": settings.llm_model,
            "chunk_size": settings.chunk_size,
            "k": 5,
        },
        "summary": summary,
        "records": records,
    }, indent=2), encoding="utf-8")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()