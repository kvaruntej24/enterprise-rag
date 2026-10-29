import threading
from collections import Counter, deque


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        self.requests = 0
        self.errors: Counter = Counter()
        self.refusals: Counter = Counter()
        self.latencies: deque = deque(maxlen=1000)
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0

    def record(self, *, total_seconds: float, refusal_reason: str,
               input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        with self._lock:
            self.requests += 1
            self.latencies.append(total_seconds)
            if refusal_reason:
                self.refusals[refusal_reason] += 1
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.cost_usd += cost_usd

    def record_error(self, status_code: int) -> None:
        with self._lock:
            self.errors[status_code] += 1

    def snapshot(self) -> dict:
        with self._lock:
            ordered = sorted(self.latencies)

            def pct(p: float):
                if not ordered:
                    return None
                return round(ordered[min(len(ordered) - 1, int(p * len(ordered)))], 3)

            return {
                "requests": self.requests,
                "errors": {str(k): v for k, v in self.errors.items()},
                "refusals": dict(self.refusals),
                "latency_p50_seconds": pct(0.50),
                "latency_p95_seconds": pct(0.95),
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "estimated_cost_usd": round(self.cost_usd, 6),
            }


metrics = Metrics()