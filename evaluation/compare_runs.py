import argparse
import json
import sys
from pathlib import Path

RESULTS = Path("evaluation/results")

# (metric name, higher is better)
METRICS = [
    ("false_refusal_rate", False),
    ("missed_refusal_rate", False),
    ("citation_valid_rate", True),
    ("source_correct_rate", True),
    ("faithful_rate", True),
    ("correct_rate", True),
    ("judge_error_rate", False),
]


def rate(n: int, d: int) -> float | None:
    return n / d if d else None

def judge_rates(judgments: dict) -> dict:
    faith = [v for v in judgments.values() if v["faithfulness"] != "judge_error"]
    corr = [v for v in judgments.values() if v["correctness"] != "judge_error"]
    errored = [v for v in judgments.values()
               if "judge_error" in (v["faithfulness"], v["correctness"])]
    return {
        "faithful_rate": rate(sum(1 for v in faith if v["faithfulness"] == "faithful"), len(faith)),
        "correct_rate": rate(sum(1 for v in corr if v["correctness"] == "correct"), len(corr)),
        "judge_error_rate": rate(len(errored), len(judgments)),
    }


def load_metrics(label: str) -> dict:
    gen = json.loads((RESULTS / f"generation_{label}.json").read_text(encoding="utf-8"))
    s = gen["summary"]
    metrics = {
        "false_refusal_rate": rate(s["false_refusals"], s["answerable"]),
        "missed_refusal_rate": rate(s["missed_refusals"], s["unanswerable"]),
        "citation_valid_rate": rate(s["answered_with_valid_citations"], s["answered"]),
        "source_correct_rate": rate(s["answered_with_correct_source"], s["answered"]),
        "faithful_rate": None,
        "correct_rate": None,
        "avg_input_tokens": s["avg_input_tokens_per_llm_call"],
        "avg_llm_seconds": s["avg_llm_seconds"],
        "judge_error_rate": None,
    }
    judge_path = RESULTS / f"judge_{label}.json"
    if judge_path.exists():
        judgments = json.loads(judge_path.read_text(encoding="utf-8"))["judgments"]
        metrics.update(judge_rates(judgments))
    return metrics


def regressions(reference: dict, candidate: dict, tolerance: float) -> list[str]:
    problems = []
    for name, higher_is_better in METRICS:
        ref, cand = reference.get(name), candidate.get(name)
        if ref is None or cand is None:
            continue
        worse_by = (ref - cand) if higher_is_better else (cand - ref)
        if worse_by > tolerance:
            problems.append(
                f"{name}: {ref:.2f} -> {cand:.2f} (worse by {worse_by:.2f}, "
                f"tolerance {tolerance:.2f})"
            )
    return problems


def show(value, fmt: str) -> str:
    return "n/a" if value is None else format(value, fmt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--check", action="store_true", help="exit 1 on regression")
    parser.add_argument("--tolerance", type=float, default=0.10)
    args = parser.parse_args()

    ref = load_metrics(args.reference)
    cand = load_metrics(args.candidate)

    print(f"{'metric':22} {args.reference:>12} {args.candidate:>12}")
    for name, _ in METRICS:
        print(f"{name:22} {show(ref[name], '.2f'):>12} {show(cand[name], '.2f'):>12}")
    print(f"{'avg_input_tokens':22} {ref['avg_input_tokens']:12.0f} {cand['avg_input_tokens']:12.0f}")
    print(f"{'avg_llm_seconds':22} {ref['avg_llm_seconds']:12.2f} {cand['avg_llm_seconds']:12.2f}")

    problems = regressions(ref, cand, args.tolerance)
    for problem in problems:
        print("REGRESSION:", problem)
    if args.check:
        print("FAIL" if problems else "PASS")
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())