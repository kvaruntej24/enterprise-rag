import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RESULTS = Path("evaluation/results")


def load(label: str):
    gen = json.loads((RESULTS / f"generation_{label}.json").read_text(encoding="utf-8"))
    judge = json.loads((RESULTS / f"judge_{label}.json").read_text(encoding="utf-8"))
    records = {r["id"]: r for r in gen["records"] if "error" not in r}
    return records, judge["judgments"]


ref_label, cand_label = sys.argv[1], sys.argv[2]
ref_rec, ref_j = load(ref_label)
cand_rec, cand_j = load(cand_label)

changed = 0
for qid in sorted(set(ref_j) & set(cand_j)):
    before, after = ref_j[qid]["faithfulness"], cand_j[qid]["faithfulness"]
    if before == after:
        continue
    changed += 1
    same_text = ref_rec[qid]["answer"] == cand_rec[qid]["answer"]
    print(f"\n{qid}: {before} -> {after} | answer text identical: {same_text}")
    print(f"  {ref_label} unsupported: {ref_j[qid]['unsupported_claims']}")
    print(f"  {cand_label} unsupported: {cand_j[qid]['unsupported_claims']}")
    if not same_text:
        print(f"  {cand_label} answer: {cand_rec[qid]['answer'][:400]}")
print(f"\n{changed} questions changed faithfulness verdict")