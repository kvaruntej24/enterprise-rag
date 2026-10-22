import json
import sys
import time
from pathlib import Path

from app.core.config import settings
from app.retrieval.bm25 import bm25_search
from app.retrieval.hybrid import hybrid_search
from app.retrieval.retriever import retrieve
from app.retrieval.semantic import semantic_search
from evaluation.metrics import first_rank, summarize

sys.stdout.reconfigure(encoding="utf-8")

QUESTIONS_PATH = Path("evaluation/questions.jsonl")
RESULTS_DIR = Path("evaluation/results")
K = 5

RETRIEVERS = {
    "semantic": lambda q: semantic_search(q, k=K),
    "bm25": lambda q: bm25_search(q, k=K),
    "hybrid": lambda q: hybrid_search(q, k=K),
    "hybrid+rerank": lambda q: retrieve(q, k=K),
}


def tags_of(row: dict) -> list[str]:
    return row.get("tags") or ["llm_drafted"]


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    lines = QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    answerable = [r for r in rows if r["type"] == "answerable"]
    print(f"{len(answerable)} answerable questions, k={K}")

    ranks: dict[str, dict] = {name: {} for name in RETRIEVERS}
    seconds: dict[str, float] = {}
    for name, fn in RETRIEVERS.items():
        fn("warm up the models")
        start = time.perf_counter()
        for row in answerable:
            results = fn(row["question"])
            ranks[name][row["id"]] = {
                "page": first_rank(results, row, strict=False),
                "evidence": first_rank(results, row, strict=True),
            }
        seconds[name] = (time.perf_counter() - start) / len(answerable)
        print(f"  finished {name}")

    summary: dict[str, dict] = {}
    for name in RETRIEVERS:
        summary[name] = {
            level: summarize([ranks[name][r["id"]][level] for r in answerable])
            for level in ("evidence", "page")
        }
        summary[name]["sec_per_query"] = seconds[name]

    for level, title in (("evidence", "EVIDENCE-LEVEL (strict, headline)"),
                         ("page", "PAGE-LEVEL (loose)")):
        print(f"\n{title}")
        print(f"{'retriever':15} {'Hit@1':>6} {'Hit@3':>6} {'Hit@5':>6} {'MRR@5':>6} {'sec/query':>10}")
        for name in RETRIEVERS:
            m = summary[name][level]
            print(f"{name:15} {m['hit@1']:6.2f} {m['hit@3']:6.2f} {m['hit@5']:6.2f} "
                  f"{m['mrr@5']:6.2f} {seconds[name]:10.2f}")

    print("\nHit@5 (evidence-level) by question tag")
    print(f"{'tag':14} {'n':>3} " + " ".join(f"{n:>14}" for n in RETRIEVERS))
    for tag in sorted({t for r in answerable for t in tags_of(r)}):
        subset = [r for r in answerable if tag in tags_of(r)]
        cells = [
            f"{summarize([ranks[name][r['id']]['evidence'] for r in subset])['hit@5']:14.2f}"
            for name in RETRIEVERS
        ]
        print(f"{tag:14} {len(subset):3d} " + " ".join(cells))

    print("\nMissed at k=5 by hybrid+rerank (evidence-level):")
    for r in answerable:
        if ranks["hybrid+rerank"][r["id"]]["evidence"] is None:
            print(f"  {r['id']}: {r['question'][:90]}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"retrieval_{label}.json"
    out_path.write_text(json.dumps({
        "label": label,
        "config": {
            "k": K,
            "candidates": 20,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "embedding_model": settings.embedding_model,
            "reranker_model": settings.reranker_model,
        },
        "n_answerable": len(answerable),
        "summary": summary,
        "ranks": ranks,
    }, indent=2), encoding="utf-8")
    print(f"\nsaved {out_path}")


if __name__ == "__main__":
    main()