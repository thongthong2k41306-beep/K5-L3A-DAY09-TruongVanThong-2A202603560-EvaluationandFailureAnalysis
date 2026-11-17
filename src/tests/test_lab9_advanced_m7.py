"""M7 report integrity and spec ratchet, including traps on apparently green reports."""
import copy

import pytest

pytestmark = pytest.mark.student


def rules():
    return {"eval_set_version": "v2", "seeds": [11, 22],
            "metrics": [
                {"id": "pass_rate", "kind": "capability", "grader": "code", "blocking": True,
                 "threshold": {"min": 0.8, "no_significant_drop": True}},
                {"id": "secret_leak", "kind": "safety", "blocking": True, "threshold": {"max": 0}},
                {"id": "cost_per_success", "blocking": False, "threshold": {"max_increase": 0.1}}],
            "slices": [{"name": "money_movement", "metric": "pass_rate", "min": 0.9,
                        "no_significant_drop": True, "blocking": True}]}


def clean_report():
    rows = [{"item_id": f"E-{item}", "seed": seed, "pass_rate": True,
             "secret_leak": False, "cost": 2.0,
             "slices": ["money_movement"] if item < 2 else []}
            for item in range(4) for seed in (11, 22)]
    return {"manifest": {"eval_set_sha": "same", "items": 4, "seeds": [11, 22]},
            "rows": rows, "evaluator_failures": [],
            "metrics": {"pass_rate": 1.0, "secret_leak": 0, "cost_per_success": 2.0}}


def test_integrity_accepts_clean_baseline_and_row_reordering():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["rows"].reverse()
    assert integrity_check(pr, base, rules(), rules()) == []


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "1.0", None])
def test_integrity_rejects_invalid_blocking_summary(value):
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["metrics"]["pass_rate"] = value
    assert integrity_check(pr, base, rules())


def test_integrity_rejects_duplicate_row_even_when_row_count_is_unchanged():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["rows"][1] = copy.deepcopy(pr["rows"][0])
    problems = integrity_check(pr, base, rules())
    assert any("duplicate" in problem for problem in problems)


def test_integrity_rejects_removed_items_even_with_rewritten_manifest():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["rows"] = [row for row in pr["rows"] if row["item_id"] != "E-3"]
    pr["manifest"]["items"] = 3
    assert integrity_check(pr, base, rules())


def test_integrity_rejects_selected_seeds_even_with_rewritten_manifest():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["rows"] = [row for row in pr["rows"] if row["seed"] == 11]
    pr["manifest"]["seeds"] = [11]
    assert integrity_check(pr, base, rules())


def test_integrity_rejects_grader_error_even_when_all_scores_are_green():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["evaluator_failures"] = ["E-0:grader:crashed"]
    assert integrity_check(pr, base, rules())


@pytest.mark.parametrize("value", [None, float("nan"), "PASS"])
def test_integrity_rejects_missing_or_invalid_row_score(value):
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["rows"][0]["pass_rate"] = value
    assert integrity_check(pr, base, rules())


def test_integrity_rejects_slice_relabelling_and_cross_seed_inconsistency():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    for row in pr["rows"]:
        if row["item_id"] == "E-0":
            row["slices"] = []
    assert integrity_check(pr, base, rules())
    pr = copy.deepcopy(base)
    pr["rows"][0]["slices"] = []
    assert integrity_check(pr, base, rules())


def test_integrity_recomputes_summary_and_reliability_from_rows():
    from lab9.gate import integrity_check

    base = clean_report()
    pr = copy.deepcopy(base)
    pr["rows"][0]["pass_rate"] = False
    assert any("summary pass_rate" in p for p in integrity_check(pr, base, rules()))
    # Fix the mean and cost but lie about the all-seeds success rate.
    pr["metrics"].update(pass_rate=0.875, cost_per_success=2.2857, pass_hat_2=1.0)
    problems = integrity_check(pr, base, rules())
    assert any("summary pass_hat_2" in problem for problem in problems)


def test_integrity_rejects_corrupt_baseline_too():
    from lab9.gate import integrity_check

    base = clean_report()
    base["evaluator_failures"] = ["baseline grader failed"]
    assert integrity_check(clean_report(), base, rules())


@pytest.mark.parametrize("change", [
    "min", "max", "max_increase", "remove_bound", "blocking", "no_significant_drop",
    "drop_metric", "grader", "drop_slice", "slice_metric", "slice_min",
    "slice_blocking", "slice_no_significant_drop",
])
def test_ratchet_rejects_every_supported_way_to_loosen_spec(change):
    from lab9.gate import integrity_check

    base_spec = rules()
    loose = copy.deepcopy(base_spec)
    if change == "min":
        loose["metrics"][0]["threshold"]["min"] = 0.5
    elif change == "max":
        loose["metrics"][1]["threshold"]["max"] = 1
    elif change == "max_increase":
        loose["metrics"][2]["threshold"]["max_increase"] = 0.5
    elif change == "remove_bound":
        loose["metrics"][0]["threshold"].pop("min")
    elif change == "blocking":
        loose["metrics"][0]["blocking"] = False
    elif change == "no_significant_drop":
        loose["metrics"][0]["threshold"].pop("no_significant_drop")
    elif change == "drop_metric":
        loose["metrics"].pop(0)
    elif change == "grader":
        loose["metrics"][0]["grader"] = "always_pass"
    elif change == "drop_slice":
        loose["slices"] = []
    elif change == "slice_metric":
        loose["slices"][0]["metric"] = "different_metric"
    elif change == "slice_min":
        loose["slices"][0]["min"] = 0.2
    elif change == "slice_blocking":
        loose["slices"][0]["blocking"] = False
    elif change == "slice_no_significant_drop":
        loose["slices"][0]["no_significant_drop"] = False
    problems = integrity_check(clean_report(), clean_report(), loose, base_spec)
    assert any("RATCHET" in problem for problem in problems)


def test_ratchet_accepts_equal_or_stricter_bounds():
    from lab9.gate import integrity_check

    base_spec = rules()
    strict = copy.deepcopy(base_spec)
    strict["metrics"][0]["threshold"]["min"] = 0.9
    strict["metrics"][2]["threshold"]["max_increase"] = 0.05
    strict["slices"][0]["min"] = 0.95
    assert integrity_check(clean_report(), clean_report(), strict, base_spec) == []


def test_integrity_rejects_duplicate_rules_and_nan_thresholds():
    from lab9.gate import integrity_check

    for kind in ("metrics", "slices"):
        spec = rules()
        spec[kind].append(copy.deepcopy(spec[kind][0]))
        assert integrity_check(clean_report(), clean_report(), spec)
    spec = rules()
    spec["metrics"][0]["threshold"]["min"] = float("nan")
    assert integrity_check(clean_report(), clean_report(), spec)
