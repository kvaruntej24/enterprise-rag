import sys

from app.generation.context import build_context
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from app.retrieval.semantic import semantic_search

question = sys.argv[1]
results = semantic_search(question, k=5)
context, used = build_context(results)

print(SYSTEM_PROMPT)
print("=" * 60)
print(build_user_prompt(question, context))
print("=" * 60)
print(f"chunks used: {len(used)} of {len(results)}, "
      f"context chars: {len(context)}")