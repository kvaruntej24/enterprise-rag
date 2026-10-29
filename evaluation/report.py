import json
import sys
from collections import Counter
from pathlib import Path

from evaluation.compare_runs import load_metrics

sys.stdout.reconfigure(encoding="utf-8")
RESULTS = Path("evaluation/results")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def retrieval(label: str) -> None:
    data = read(RESULTS / f"retrieval_{label}.json")
    section(f"Retrieval, evidence-level ({label})")
    if not data:
        print("missing")
        return
    print(f"answerable questions: {data['n_answerable']}")
    print(f"{'retriever':15} {'Hit@1':>6} {'Hit@3':>6} {'Hit@5':>6} {'MRR@5':>6} {'sec/q':>7}")
    for name, m in data["summary"].items():
        e = m["evidence"]
        print(f"{name:15} {e['hit@1']:6.2f} {e['hit@3']:6.2f} {e['hit@5']:6.2f} "
              f"{e['mrr@5']:6.2f} {m['sec_per_query']:7.2f}")


def gate() -> None:
    data = read(RESULTS / "gate_calibration.json")
    section("Gate calibration")
    if not data:
        print("missing")
        return
    cur = data["current_threshold"]
    print(f"threshold in config when run: {cur}; "
          f"{data['n_answerable']} answerable, {data['n_unanswerable']} unanswerable")
    for row in data["table"]:
        if abs(row["threshold"] - cur) <= 1.0:
            print(f"  {row['threshold']:5.1f}  false_refusal {row['false_refusal']:.2f}  "
                  f"false_accept {row['false_accept']:.2f}")


def generation(label: str) -> None:
    data = read(RESULTS / f"generation_{label}.json")
    section(f"Generation ({label})")
    if not data:
        print("missing")
        return
    print("config:", data["config"])
    for key, value in data["summary"].items():
        print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")


def judge(label: str) -> None:
    data = read(RESULTS / f"judge_{label}.json")
    section(f"Judge ({label})")
    if not data:
        print("missing")
        return
    judgments = data["judgments"]
    print(f"judged {data['n_judged']} | answer model: {data['answer_model']} | "
          f"judge model: {data['judge_model']} | same model: {data['same_model']}")
    print("faithfulness:", dict(Counter(j["faithfulness"] for j in judgments.values())))
    print("correctness: ", dict(Counter(j["correctness"] for j in judgments.values())))


def agreement(label: str) -> None:
    judged = read(RESULTS / f"judge_{label}.json")
    human = read(Path("evaluation/human_labels.json"))
    section("Judge vs my hand labels")
    if not judged or not human:
        print("missing")
        return
    for metric in ("faithfulness", "correctness"):
        ids = [i for i in human if metric in human[i] and i in judged["judgments"]]
        agree = [i for i in ids if human[i][metric] == judged["judgments"][i][metric]]
        print(f"{metric}: agree on {len(agree)}/{len(ids)}")


def rates(labels: list[str]) -> None:
    section("Run comparison (rates)")
    for label in labels:
        try:
            metrics = load_metrics(label)
        except FileNotFoundError:
            print(f"{label}: missing")
            continue
        print(label, {k: (round(v, 2) if v is not None else None) for k, v in metrics.items()})


def main() -> None:
    labels = sys.argv[1:] or ["baseline"]
    retrieval("baseline")
    retrieval("v1_1")
    gate()
    for label in labels:
        generation(label)
        judge(label)
    agreement(labels[0])
    rates(labels)


if __name__ == "__main__":
    main()