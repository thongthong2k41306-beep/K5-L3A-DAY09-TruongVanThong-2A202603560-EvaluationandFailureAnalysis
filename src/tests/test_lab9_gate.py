"""M4 gate decisions from paired, in-memory reports; no filesystem writes."""
import copy

import pytest

pytestmark = pytest.mark.student


def report(values, sha="same"):
    rows = [{"item_id": f"E-{index:03d}", "seed": seed, "pass_rate": value}
            for index, value in enumerate(values) for seed in (11, 22)]
    return {"manifest": {"eval_set_sha": sha}, "rows": rows,
            "metrics": {"pass_rate": sum(values) / len(values)}}


def spec(floor=0.85):
    return {"bootstrap": {"n_resamples": 1000, "rng": 2027,
                          "method": "percentile", "confidence": 0.95},
            "metrics": [{"id": "pass_rate", "blocking": True,
                         "threshold": {"min": floor, "no_significant_drop": True}}]}


def test_gate_accepts_unchanged_and_improved_reports():
    from lab9.gate import check

    base = report([1, 1, 0.8, 1])
    assert check(base, base, spec())[0] == []
    assert check(report([1, 1, 1, 1]), base, spec())[0] == []


def test_gate_blocks_significant_drop_even_above_floor():
    from lab9.gate import check

    blocked, lines = check(report([0.9] * 4), report([1.0] * 4), spec())
    assert blocked == ["pass_rate"]
    assert "CI [-0.100, -0.100]" in lines[0]


def test_gate_blocks_below_floor_even_without_significant_drop():
    from lab9.gate import check

    base = report([0.8] * 4)
    assert check(base, base, spec())[0] == ["pass_rate"]


def test_gate_rejects_a_different_eval_set():
    from lab9.gate import check

    assert check(report([1, 1], sha="new"), report([1, 1]), spec())[0] == ["eval_set_sha"]


def test_gate_does_not_silently_drop_unpaired_items():
    from lab9.gate import check

    assert check(report([1, 1]), report([1, 1, 1]), spec())[0] == ["pass_rate"]


@pytest.mark.parametrize("value", [None, float("nan"), float("inf")])
def test_gate_blocks_missing_or_nonfinite_blocking_metric(value):
    from lab9.gate import check

    base = report([1, 1])
    pr = copy.deepcopy(base)
    pr["metrics"]["pass_rate"] = value
    assert check(pr, base, spec())[0] == ["pass_rate"]


def test_gate_warns_for_nonblocking_metric_and_counts_safety_violations():
    from lab9.gate import check

    base = report([1, 1])
    pr = report([1, 1])
    pr["metrics"]["secret_leak"] = 1
    rules = spec()
    rules["metrics"] += [{"id": "secret_leak", "blocking": True, "threshold": {"max": 0}},
                         {"id": "optional", "blocking": False, "threshold": {"min": 1}}]
    assert check(pr, base, rules)[0] == ["secret_leak"]


def test_gate_uses_configured_confidence(monkeypatch):
    from lab9 import gate

    seen = {}

    def bootstrap(a, b, **kwargs):
        seen.update(kwargs)
        return 0.0, 0.0, 0.0

    monkeypatch.setattr(gate.stats, "paired_bootstrap", bootstrap)
    rules = spec()
    rules["bootstrap"]["confidence"] = 0.9
    assert gate.check(report([1, 1]), report([1, 1]), rules)[0] == []
    assert seen["confidence"] == 0.9


def test_gate_checks_cost_increase_when_baseline_is_zero():
    from lab9.gate import check

    base, pr = report([1, 1]), report([1, 1])
    base["metrics"]["cost"] = 0.0
    pr["metrics"]["cost"] = 1.0
    rules = {"metrics": [{"id": "cost", "blocking": True, "threshold": {"max_increase": 0.1}}]}
    assert check(pr, base, rules)[0] == ["cost"]
