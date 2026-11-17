"""M6 reliability estimators and their aggregate/gate integration; no file writes."""
from itertools import combinations
import math

import pytest

pytestmark = pytest.mark.student


def test_pass_estimators_match_exhaustive_sampling_without_replacement():
    from lab9.stats import pass_at_k, pass_hat_k

    for n in range(1, 8):
        for c in range(n + 1):
            outcomes = [True] * c + [False] * (n - c)
            for k in range(1, n + 1):
                samples = list(combinations(outcomes, k))
                at_least_one = sum(any(sample) for sample in samples) / len(samples)
                all_pass = sum(all(sample) for sample in samples) / len(samples)
                assert pass_at_k(n, c, k) == pytest.approx(at_least_one)
                assert pass_hat_k(n, c, k) == pytest.approx(all_pass)
                assert pass_hat_k(n, c, k) <= c / n + 1e-12
                assert c / n <= pass_at_k(n, c, k) + 1e-12


@pytest.mark.parametrize("args", [
    (0, 0, 1), (-1, 0, 1), (5, -1, 1), (5, 6, 1), (5, 2, 0),
    (5, 2, -1), (3, 1, 4), (5.0, 2, 1), (5, 2.0, 1), (5, 2, 1.0),
    (True, 1, 1), (5, False, 1), (5, 2, True), (5, math.nan, 1),
])
def test_both_pass_estimators_reject_invalid_counts(args):
    from lab9.stats import pass_at_k, pass_hat_k

    for estimator in (pass_at_k, pass_hat_k):
        with pytest.raises(ValueError):
            estimator(*args)


def test_pass_at_k_retains_rare_success_probability():
    from lab9.stats import pass_at_k

    assert math.isclose(pass_at_k(10**18, 1, 2), 2e-18, rel_tol=1e-12, abs_tol=0)


def test_four_of_five_passes_is_not_reliable_for_all_five():
    from lab9.stats import pass_at_k, pass_hat_k

    assert pass_at_k(5, 4, 5) == 1.0
    assert pass_hat_k(5, 4, 5) == 0.0
    assert pass_hat_k(5, 4, 3) == pytest.approx(0.4)


def test_eval_aggregate_reports_reliability_per_item():
    from lab9.eval import aggregate

    rows = [{"item_id": item, "seed": seed, "pass_rate": passed, "cost": 1.0}
            for item, outcomes in (("a", [True] * 5), ("b", [True] * 4 + [False]))
            for seed, passed in enumerate(outcomes)]
    metrics = aggregate(rows, ["pass_rate"], k_values=[1, 3, 5])
    assert metrics["pass_rate"] == 0.9
    assert metrics["pass_at_1"] == metrics["pass_hat_1"] == 0.9
    assert metrics["pass_at_5"] == 1.0
    assert metrics["pass_hat_3"] == 0.7
    assert metrics["pass_hat_5"] == metrics["pass_5"] == 0.5


def test_gate_blocks_unreliable_agent_despite_passing_mean():
    from lab9.gate import check

    spec = {"metrics": [
        {"id": "pass_rate", "threshold": {"min": 0.85}, "blocking": True},
        {"id": "pass_hat_5", "threshold": {"min": 0.85}, "blocking": True},
    ]}
    def reliability_report(flaky_items, mean, reliable):
        rows = [{"item_id": f"E-{item}", "seed": seed,
                 "pass_rate": not (item < flaky_items and seed == 4)}
                for item in range(28) for seed in range(5)]
        return {"manifest": {"eval_set_sha": "same", "items": 28, "seeds": list(range(5))},
                "rows": rows, "evaluator_failures": [],
                "metrics": {"pass_rate": mean, "pass_hat_5": reliable}}

    base = reliability_report(3, 0.9786, 0.8929)
    pr = reliability_report(8, 0.9429, 0.7143)
    assert check(base, base, spec)[0] == []
    assert check(pr, base, spec)[0] == ["pass_hat_5"]
