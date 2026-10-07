import sys

from app.retrieval.bm25 import bm25_search
from app.retrieval.hybrid import hybrid_search
from app.retrieval.semantic import semantic_search

sys.stdout.reconfigure(encoding="utf-8")

QUERIES = [
    "GV.OC-03",
    "PW.4",
    "FIPS 199 high impact",
    "LLM01 prompt injection",
    "How should passwords be stored?",
    "What does zero trust mean?",
    "Table 1 vulnerability mitigation time summary matrix",
]


def show(label: str, results, query: str) -> None:
    print(f"  {label}")
    for r in results[:3]:
        page = f" p.{r.page}" if r.page else ""
        mark = "*" if query.lower() in r.content.lower() else " "
        print(f"    {mark} {r.source}{page}")


for q in QUERIES:
    print(f"\nQ: {q}")
    show("semantic", semantic_search(q, k=3), q)
    show("bm25    ", bm25_search(q, k=3), q)
    show("hybrid  ", hybrid_search(q, k=3), q)
print("\n(* = chunk contains the query string literally)")