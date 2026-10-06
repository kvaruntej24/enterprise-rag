import argparse

from app.retrieval.semantic import semantic_search

parser = argparse.ArgumentParser()
parser.add_argument("query")
parser.add_argument("-k", type=int, default=5)
parser.add_argument("--doc-type")
parser.add_argument("--source")
args = parser.parse_args()

results = semantic_search(args.query, args.k, args.doc_type, args.source)
for rank, r in enumerate(results, start=1):
    page = f" p.{r.page}" if r.page else ""
    print(f"{rank}. [{r.score:.3f}] {r.source}{page}")
    print("   " + r.content[:300].replace("\n", " "))
    print()