from evaluation.compare_runs import regressions

REF = {
    "false_refusal_rate": 0.05,
    "missed_refusal_rate": 0.10,
    "citation_valid_rate": 0.90,
    "faithful_rate": 0.90,
}


def test_change_within_tolerance_is_not_a_regression():
    assert regressions(REF, {**REF, "faithful_rate": 0.85}, 0.10) == []


def test_drop_beyond_tolerance_is_flagged():
    problems = regressions(REF, {**REF, "faithful_rate": 0.70}, 0.10)
    assert len(problems) == 1 and "faithful_rate" in problems[0]


def test_lower_is_better_metrics_flag_increases():
    problems = regressions(REF, {**REF, "missed_refusal_rate": 0.40}, 0.10)
    assert any("missed_refusal_rate" in p for p in problems)


def test_missing_metrics_are_skipped():
    assert regressions(REF, {"faithful_rate": None}, 0.10) == []