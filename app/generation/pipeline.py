import re
import time
from dataclasses import dataclass, field
from app.core.config import settings
from app.generation.context import build_context
from app.generation.llm import generate
from app.generation.prompts import NO_ANSWER_MESSAGE, SYSTEM_PROMPT, build_user_prompt
from app.retrieval.retriever import retrieve_with_timings
from app.retrieval.semantic import SearchResult

CITATION_PATTERN = re.compile(r"[\[【](\d{1,2}(?:\s*,\s*\d{1,2})*)(?:†[^\]】]*)?[\]】]")


@dataclass
class Answer:
    question: str
    text: str
    refused: bool
    cited: dict[int, SearchResult] = field(default_factory=dict)
    invalid_citations: list[int] = field(default_factory=list)
    uncited: bool = False
    refusal_reason: str = ""
    top_score: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    retrieval_seconds: float = 0.0
    llm_seconds: float = 0.0
    context: str = ""
    retrieved: list[dict] = field(default_factory=list)
    stage_seconds: dict[str, float] = field(default_factory=dict)
    estimated_cost_usd: float = 0.0



def extract_citations(text: str) -> list[int]:
    numbers: list[int] = []
    for group in CITATION_PATTERN.findall(text):
        for part in group.split(","):
            n = int(part)
            if n not in numbers:
                numbers.append(n)
    return numbers

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * settings.llm_price_input_per_m
        + output_tokens * settings.llm_price_output_per_m
    ) / 1_000_000


def normalize_citations(text: str) -> str:
    def rewrite(match: re.Match) -> str:
        return "".join(f"[{part.strip()}]" for part in match.group(1).split(","))

    return CITATION_PATTERN.sub(rewrite, text)

def answer(question: str, k: int = 5) -> Answer:
    start = time.perf_counter()
    results, stage_seconds = retrieve_with_timings(question, k=k)
    retrieval_seconds = time.perf_counter() - start
    top_score = results[0].score if results else 0.0
    common = {
        "retrieved": [
            {"chunk_id": r.chunk_id, "source": r.source, "page": r.page,
             "score": round(r.score, 2)}
            for r in results
        ],
        "stage_seconds": stage_seconds,
        "top_score": top_score,
        "retrieval_seconds": retrieval_seconds,
    }

    if not results:
        return Answer(question, NO_ANSWER_MESSAGE, True, refusal_reason="no_results", **common)
    if top_score < settings.relevance_threshold:
        return Answer(question, NO_ANSWER_MESSAGE, True,
                      refusal_reason="below_relevance_threshold", **common)

    context, used = build_context(results)
    response = generate(SYSTEM_PROMPT, build_user_prompt(question, context))
    text = normalize_citations(response.text.strip())

    refused = NO_ANSWER_MESSAGE.lower() in text.lower()
    numbers = extract_citations(text)
    cited = {n: used[n - 1] for n in numbers if 1 <= n <= len(used)}
    invalid = [n for n in numbers if n not in cited]


    return Answer(
        question=question,
        text=text,
        refused=refused,
        cited={} if refused else cited,
        invalid_citations=invalid,
        uncited=not refused and not cited,
        refusal_reason="model_refused" if refused else "",
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        llm_seconds=response.latency_seconds,
        estimated_cost_usd=estimate_cost(response.input_tokens, response.output_tokens),
        context=context,
        **common,
    )