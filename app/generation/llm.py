import time
from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI

from app.core.config import settings


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=2,
    )


def generate(system: str, user: str) -> LLMResponse:
    start = time.perf_counter()
    completion = get_client().chat.completions.create(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    latency = time.perf_counter() - start
    usage = completion.usage
    return LLMResponse(
        text=completion.choices[0].message.content or "",
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
        latency_seconds=latency,
    )