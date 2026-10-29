from app.core.metrics import Metrics


def test_snapshot_counts_percentiles_and_cost():
    m = Metrics()
    for i in range(1, 101):
        m.record(total_seconds=float(i), refusal_reason="",
                 input_tokens=10, output_tokens=5, cost_usd=0.001)
    m.record(total_seconds=1.0, refusal_reason="below_relevance_threshold",
             input_tokens=0, output_tokens=0, cost_usd=0.0)
    m.record_error(503)
    s = m.snapshot()
    assert s["requests"] == 101
    assert s["errors"] == {"503": 1}
    assert s["refusals"] == {"below_relevance_threshold": 1}
    assert s["input_tokens"] == 1000
    assert abs(s["estimated_cost_usd"] - 0.1) < 1e-9
    assert 94 <= s["latency_p95_seconds"] <= 96