"""M5 mapping, v2 build and slice gate; no shapes or temporary-file writes."""
import copy
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.student


def report(values, tags=("money_movement",)):
    rows = [{"item_id": item, "seed": seed, "slices": list(tags), "pass_rate": value}
            for item, scores in values.items() for seed, value in enumerate(scores)]
    return {"rows": rows, "evaluator_failures": [],
            "manifest": {"eval_set_sha": "same", "items": len(values),
                         "seeds": sorted({row["seed"] for row in rows})}}


def spec(floor=0.9, paired=True, blocking=True):
    return {"bootstrap": {"n_resamples": 1000, "rng": 2027, "confidence": 0.95},
            "slices": [{"name": "money_movement", "metric": "pass_rate", "min": floor,
                        "no_significant_drop": paired, "blocking": blocking}]}


def test_v2_build_preserves_v1_labels_and_covers_all_mechanisms(monkeypatch):
    from lab9 import evalset
    import yaml

    base = evalset.load_jsonl(evalset.ITEMS)
    base_labels = json.loads(evalset.LABELS.read_text(encoding="utf-8"))
    pack = json.loads(evalset.PACK.read_text(encoding="utf-8"))
    mapping = yaml.safe_load(evalset.FM_MAP.read_text(encoding="utf-8"))
    mechanisms = {m for claim in pack["claims"] for m in claim["mechanisms"]}
    assert set(mapping) == mechanisms
    assert all(evalset.FM_CODE.fullmatch(mapping[m]) for m in mechanisms)

    # Exercise the real builder/checker with output held in memory. All source
    # inputs are the repository fixtures; no write permission is required.
    writes = {}

    def capture_write(path, text, **kwargs):
        writes[str(path)] = text
        return len(text)

    monkeypatch.setattr(Path, "write_text", capture_write)
    counts = evalset.build_v2()
    original_read = Path.read_text

    def read_output(path, *args, **kwargs):
        if str(path) in writes:
            return writes[str(path)]
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_output)
    assert counts == (28, 28)
    assert evalset.check(evalset.ITEMS_V2, evalset.LABELS_V2) == []
    items = evalset.load_jsonl(evalset.ITEMS_V2)
    labels = json.loads(evalset.LABELS_V2.read_text(encoding="utf-8"))
    by_claim = {item["claim_id"]: item for item in items}
    for item in base:
        rebuilt = by_claim[item["claim_id"]]
        assert rebuilt["failure_modes"] == item["failure_modes"]
        assert rebuilt["provenance"] == item["provenance"]
        assert labels[item["claim_id"]] == base_labels[item["claim_id"]]
    for claim in pack["claims"]:
        item = by_claim[claim["claim_id"]]
        assert item["split"] == "adversarial"
        assert "adversarial" in item["slices"]
        assert ("money_movement" in item["slices"]) == (claim["expected"]["refund_vnd"] > 0)
        assert item["failure_modes"] == [mapping[m] for m in claim["mechanisms"]]
    assert all("expected" not in item and "label" not in item for item in items)


def test_slice_accepts_identical_baseline_and_boundary_floor():
    from lab9.gate import slice_check

    base = report({"a": [1, 1], "b": [1, 0]})
    assert slice_check(base, base, spec(floor=0.75))[0] == []


def test_slice_blocks_significant_drop_even_above_floor():
    from lab9.gate import slice_check

    base = report({"a": [1, 1], "b": [1, 1]})
    pr = report({"a": [0.95, 0.95], "b": [0.95, 0.95]})
    assert slice_check(pr, base, spec())[0] == ["slice:money_movement/pass_rate"]


def test_slice_floor_applies_when_ci_includes_zero():
    from lab9.gate import slice_check

    base = report({"a": [1], "b": [1]})
    pr = report({"a": [0.5], "b": [1]})
    blocked, lines = slice_check(pr, base, spec())
    assert blocked == ["slice:money_movement/pass_rate"]
    assert "+0.000" in lines[0]


def test_slice_averages_items_before_averaging_the_slice():
    from lab9.gate import slice_check

    base = report({"a": [1, 1, 1, 1], "b": [0]})
    blocked, lines = slice_check(base, base, spec(floor=0.6, paired=False))
    assert blocked == ["slice:money_movement/pass_rate"]
    assert "0.5000" in lines[0]  # Row averaging would incorrectly produce 0.8.


@pytest.mark.parametrize("bad", [None, float("nan"), float("inf")])
def test_slice_does_not_drop_invalid_scores_from_the_mean(bad):
    from lab9.gate import slice_check

    base = report({"a": [1, 1], "b": [1, 1]})
    pr = report({"a": [1, bad], "b": [1, 1]})
    assert slice_check(pr, base, spec())[0] == ["slice:money_movement/pass_rate"]


def test_slice_missing_items_or_missing_baseline_do_not_silently_pass():
    from lab9.gate import slice_check

    base = report({"a": [1, 1], "b": [1, 1]})
    for pr, baseline in [(report({}), base), (base, report({})),
                         (report({"a": [1, 1]}), base)]:
        assert slice_check(pr, baseline, spec())[0] == ["slice:money_movement/pass_rate"]


def test_nonblocking_slice_warns_and_matching_is_by_item_id():
    from lab9.gate import slice_check

    base = report({"a": [1, 1], "b": [0, 0]})
    pr = report({"b": [0, 0], "a": [1, 1]})
    blocked, lines = slice_check(pr, base, spec(blocking=False))
    assert blocked == []
    assert "warn" in lines[0] and "Δ +0.000" in lines[0]


def test_slice_bootstrap_uses_spec_settings(monkeypatch):
    from lab9 import gate

    seen = {}

    def bootstrap(a, b, **kwargs):
        seen.update(kwargs)
        return 0, 0, 0

    monkeypatch.setattr(gate.stats, "paired_bootstrap", bootstrap)
    rules = spec()
    rules["bootstrap"] = {"n_resamples": 123, "rng": 42, "confidence": 0.9}
    base = report({"a": [1], "b": [1]})
    assert gate.slice_check(base, base, rules)[0] == []
    assert seen == {"n_resamples": 123, "rng": 42, "confidence": 0.9}


def test_only_slice_blocks_a_local_drop_hidden_by_overall_average():
    from lab9.gate import check

    base = report({f"E-{i}": [1.0, 1.0] for i in range(10)}, tags=())
    base["metrics"] = {"pass_rate": 1.0}
    for row in base["rows"]:
        if row["item_id"] in {"E-0", "E-1"}:
            row["slices"] = ["money_movement"]
    pr = copy.deepcopy(base)
    for row in pr["rows"]:
        if row["slices"]:
            row["pass_rate"] = 0.8
    pr["metrics"]["pass_rate"] = 0.96
    rules = spec()
    rules["metrics"] = [{"id": "pass_rate", "blocking": True,
                         "threshold": {"min": 0.85, "no_significant_drop": True}}]
    assert check(pr, base, rules)[0] == ["slice:money_movement/pass_rate"]
