import json
import sys
from pathlib import Path

label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
judge = json.loads(
    Path(f"evaluation/results/judge_{label}.json").read_text(encoding="utf-8")
)["judgments"]
human = json.loads(Path("evaluation/human_labels.json").read_text(encoding="utf-8"))

for metric in ("faithfulness", "correctness"):
    ids = [i for i in human if metric in human[i] and i in judge]
    agree = [i for i in ids if human[i][metric] == judge[i][metric]]
    print(f"{metric}: judge agrees with me on {len(agree)}/{len(ids)}")
    for i in ids:
        if i not in agree:
            print(f"  disagree {i}: human={human[i][metric]}, judge={judge[i][metric]}")