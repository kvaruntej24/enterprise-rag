import sys

from app.generation.pipeline import answer

result = answer(sys.argv[1])

print(result.text)
print()
if result.refused:
    print("(refused: not enough information in the documents)")
else:
    print("Sources:")
    for n, source in sorted(result.cited.items()):
        page = f", p.{source.page}" if source.page else ""
        print(f"  [{n}] {source.source}{page}")
if result.invalid_citations:
    print(f"WARNING: invalid citations {result.invalid_citations}")
if result.uncited:
    print("WARNING: answer has no valid citations")
print(
    f"\nretrieval {result.retrieval_seconds:.2f}s | llm {result.llm_seconds:.2f}s | "
    f"tokens in/out {result.input_tokens}/{result.output_tokens}"
)