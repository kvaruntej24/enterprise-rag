import sys

from app.retrieval.retriever import retrieve

sys.stdout.reconfigure(encoding="utf-8")

question = sys.argv[1]
k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
for i, r in enumerate(retrieve(question, k=k), start=1):
    print(f"[{i}] score {r.score:.2f} | {r.source} p.{r.page}")
    print(r.content)
    print("-" * 60)