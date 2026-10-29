import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

from app.core.config import settings
from app.generation.llm import generate

sys.stdout.reconfigure(encoding="utf-8")

RESULTS_DIR = Path("evaluation/results")
QUESTIONS_PATH = Path("evaluation/questions.jsonl")

FAITHFULNESS_SYSTEM = (
    "You are a strict fact-checker. You receive SOURCES and an ANSWER. Identify every "
    "factual claim in the ANSWER that is NOT supported by the SOURCES; ignore citation "
    "markers such as [1]. Reply with JSON only: "
    '{"unsupported_claims": ["..."], "verdict": "faithful" | "partially_faithful" | "unfaithful"}. '
    '"faithful" means every claim is supported; "partially_faithful" means some claims are '
    'unsupported; "unfaithful" means most claims are unsupported or contradicted.'
)

CORRECTNESS_SYSTEM = (
    "You compare an ANSWER with a REFERENCE answer for the same QUESTION. Reply with JSON "
    'only: {"reason": "...", "verdict": "correct" | "partially_correct" | "incorrect"}. '
    '"correct" means the answer contains the key facts of the reference and does not '
    'contradict it; "partially_correct" means some key facts are missing; "incorrect" means '
    "it contradicts the reference or misses its main point."
)


def ask_judge(system: str, user: str, attempts: int = 4) -> dict:
    last_error = ""
    for attempt in range(attempts):
        try:
            reply = generate(system, user, model=settings.judge_model or None, max_tokens=1500)
            match = re.search(r"\{.*\}", reply.text, re.S)
            if not match:
                raise ValueError(f"no JSON in reply: {reply.text[:80]!r}")
            data = json.loads(match.group(0))
            if "verdict" not in data:
                raise ValueError("reply has no verdict field")
            return data
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(5 * (attempt + 1))
    return {"verdict": "judge_error", "reason": last_error}


def main() -> None:
    retry_only = "--retry-errors" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    label = args[0] if args else "baseline"
    previous = {}
    previous_path = RESULTS_DIR / f"judge_{label}.json"
    if retry_only and previous_path.exists():
        previous = json.loads(previous_path.read_text(encoding="utf-8"))["judgments"]
    generated = json.loads(
        (RESULTS_DIR / f"generation_{label}.json").read_text(encoding="utf-8")
    )
    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    questions = {r["id"]: r for r in (json.loads(line) for line in lines if line.strip())}

    targets = [
        r for r in generated["records"]
        if r.get("type") == "answerable" and not r.get("refused") and "error" not in r
    ]
    if any(not r.get("context") for r in targets):
        sys.exit("Results file has no context: rerun evaluation.generation_eval first.")
    print(f"judging {len(targets)} answered questions")

    judgments = {}
    for rec in targets:
        old = previous.get(rec["id"])
        if old and "judge_error" not in (old["faithfulness"], old["correctness"]):
            judgments[rec["id"]] = old
            continue
        q = questions[rec["id"]]
        faith = ask_judge(
            FAITHFULNESS_SYSTEM, f"SOURCES:\n{rec['context']}\n\nANSWER:\n{rec['answer']}"
        )
        time.sleep(4)
        corr = ask_judge(
            CORRECTNESS_SYSTEM,
            f"QUESTION: {q['question']}\nREFERENCE ANSWER: {q['reference_answer']}\n"
            f"ANSWER: {rec['answer']}",
        )
        time.sleep(4)
        judgments[rec["id"]] = {
            "faithfulness": faith.get("verdict", "judge_error"),
            "unsupported_claims": faith.get("unsupported_claims", []),
            "faithfulness_error": faith.get("reason", "") if faith.get("verdict") == "judge_error" else "",
            "correctness": corr.get("verdict", "judge_error"),
            "correctness_reason": corr.get("reason", ""),
        }
        j = judgments[rec["id"]]
        print(f"  {rec['id']}: faithfulness={j['faithfulness']}, correctness={j['correctness']}")

    n = len(judgments)
    faith_counts = Counter(j["faithfulness"] for j in judgments.values())
    corr_counts = Counter(j["correctness"] for j in judgments.values())
    print(f"\nJudged {n} answered questions")
    faith_errors = faith_counts["judge_error"]
    corr_errors = corr_counts["judge_error"]
    print(f"Faithfulness: {dict(faith_counts)} -> faithful: "
          f"{faith_counts['faithful']}/{n - faith_errors} (judge errors excluded: {faith_errors})")
    print(f"Correctness:  {dict(corr_counts)} -> correct: "
          f"{corr_counts['correct']}/{n - corr_errors} (judge errors excluded: {corr_errors})")
    failed = [(q, j["faithfulness_error"] or j["correctness_reason"])
              for q, j in judgments.items()
              if "judge_error" in (j["faithfulness"], j["correctness"])]
    if failed:
        print("\nJudge errors (why):")
        for q, why in failed:
            print(f"  {q}: {why[:160]}")

    print("\nNot fully faithful:")
    for qid, j in judgments.items():
        if j["faithfulness"] != "faithful":
            print(f"  {qid} [{j['faithfulness']}]: {j['unsupported_claims']}")
    print("\nNot fully correct:")
    for qid, j in judgments.items():
        if j["correctness"] != "correct":
            print(f"  {qid} [{j['correctness']}]: {j['correctness_reason'][:140]}")

    answerer = settings.llm_model
    judge_model = settings.judge_model or settings.llm_model
    (RESULTS_DIR / f"judge_{label}.json").write_text(json.dumps({
        "label": label,
        "answer_model": answerer,
        "judge_model": judge_model,
        "same_model": judge_model == answerer,
        "n_judged": n,
        "judgments": judgments,
    }, indent=2), encoding="utf-8")

    sample = sorted(random.Random(42).sample(sorted(judgments), min(10, n)))
    review = []
    for qid in sample:
        rec = next(r for r in targets if r["id"] == qid)
        q = questions[qid]
        review.append(
            f"=== {qid} ===\nQUESTION: {q['question']}\nREFERENCE: {q['reference_answer']}\n"
            f"ANSWER: {rec['answer']}\n\nSOURCES SHOWN TO THE MODEL:\n{rec['context']}\n"
        )
    review_path = RESULTS_DIR / f"judge_review_{label}.txt"
    review_path.write_text("\n\n".join(review), encoding="utf-8")
    print(f"\nHand-label these {len(sample)}: {sample}")
    print(f"Review file (no judge verdicts, to avoid anchoring): {review_path}")


if __name__ == "__main__":
    main()