import json
import sys
from pathlib import Path

from app.core.config import settings
from app.retrieval.retriever import retrieve

sys.stdout.reconfigure(encoding="utf-8")

lines = Path("evaluation/questions.jsonl").read_text(encoding="utf-8").splitlines()
rows = [json.loads(line) for line in lines if line.strip()]

scored = []
for row in rows:
    results = retrieve(row["question"], k=5)
    scored.append((row, results[0].score if results else float("-inf")))

answerable = [(r, s) for r, s in scored if r["type"] == "answerable"]
unanswerable = [(r, s) for r, s in scored if r["type"] == "unanswerable"]
print(f"{len(answerable)} answerable, {len(unanswerable)} unanswerable")
if not unanswerable:
    sys.exit("No unanswerable questions in the dataset: nothing to calibrate against.")

print("\nLowest 5 answerable top scores:")
for r, s in sorted(answerable, key=lambda x: x[1])[:5]:
    print(f"  {s:7.2f}  {r['id']}  {r['question'][:70]}")

print("\nHighest 5 unanswerable top scores:")
for r, s in sorted(unanswerable, key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {s:7.2f}  {r['id']}  {r['question'][:70]}")

print(f"\n{'threshold':>9} {'false refusal':>14} {'false accept':>13}")
table = []
for t in [x / 2 for x in range(-8, 13)]:
    false_refusal = sum(1 for _, s in answerable if s < t) / len(answerable)
    false_accept = sum(1 for _, s in unanswerable if s >= t) / len(unanswerable)
    table.append({"threshold": t, "false_refusal": false_refusal, "false_accept": false_accept})
    print(f"{t:9.1f} {false_refusal:14.2f} {false_accept:13.2f}")

Path("evaluation/results").mkdir(parents=True, exist_ok=True)
Path("evaluation/results/gate_calibration.json").write_text(json.dumps({
    "current_threshold": settings.relevance_threshold,
    "n_answerable": len(answerable),
    "n_unanswerable": len(unanswerable),
    "table": table,
}, indent=2), encoding="utf-8")