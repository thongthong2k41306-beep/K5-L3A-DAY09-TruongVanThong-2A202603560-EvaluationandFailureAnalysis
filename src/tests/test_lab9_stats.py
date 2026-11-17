"""M2/M4 self-check. Run: python -m pytest -q -m student -o addopts= -k lab9"""
import csv
from pathlib import Path

import pytest

pytestmark = pytest.mark.student
TONE = Path("data/eval/judge_tone_public.csv")


@pytest.fixture(scope="module")
def stats():
    # The overlaid Lab 8 CI collects these tests with only Lab 8 dependencies.
    from lab9 import stats

    return stats


def _labels():
    rows = list(csv.DictReader(TONE.open(encoding="utf-8")))
    return [r["human"] for r in rows], [r["judge"] for r in rows]


def test_confusion_tone(stats):
    assert stats.confusion(*_labels()) == {"tp": 24, "fp": 4, "fn": 6, "tn": 66}


def test_precision_recall_kappa_tone(stats):
    p, r = stats.precision_recall(*_labels())
    assert (round(p, 3), round(r, 3)) == (0.857, 0.8)
    assert round(stats.cohen_kappa(*_labels()), 3) == 0.757


def test_kappa_undefined_for_constant_judge(stats):
    with pytest.raises(ValueError):
        stats.cohen_kappa(["PASS"] * 5, ["PASS"] * 5)


def test_rogan_gladen_clips(stats):
    assert stats.rogan_gladen(0.28, 0.8, 66 / 70) == pytest.approx(0.3, abs=0.01)
    assert stats.rogan_gladen(0.0, 0.8, 0.9) == 0.0


@pytest.mark.parametrize("human,judge", [
    (["PASS"], []),
    (["UNKNOWN"], ["PASS"]),
    (["PASS"], ["UNKNOWN"]),
])
def test_confusion_rejects_unpaired_or_invalid_labels(stats, human, judge):
    with pytest.raises(ValueError):
        stats.confusion(human, judge)


def test_precision_recall_without_positive_predictions(stats):
    assert stats.precision_recall(["PASS", "FAIL"], ["PASS", "PASS"]) == (0.0, 0.0)
    assert stats.precision_recall(["PASS"], ["FAIL"]) == (0.0, 0.0)


def test_kappa_empty_and_constant_predictions(stats):
    with pytest.raises(ValueError):
        stats.cohen_kappa([], [])
    # Constant predictions on mixed truth have defined kappa=0, not p_e=1.
    assert stats.cohen_kappa(["PASS", "FAIL"], ["PASS", "PASS"]) == 0.0


@pytest.mark.parametrize("observed,sensitivity,specificity", [
    (0.2, 0.5, 0.5),
    (0.2, 0.2, 0.3),
    (float("nan"), 0.8, 0.9),
    (1.1, 0.8, 0.9),
])
def test_rogan_gladen_rejects_unidentifiable_or_invalid_rates(stats, observed, sensitivity, specificity):
    with pytest.raises(ValueError):
        stats.rogan_gladen(observed, sensitivity, specificity)


def test_rogan_gladen_upper_clip(stats):
    assert stats.rogan_gladen(1.0, 0.8, 0.9) == 1.0


def test_judge_calibration_decisions():
    from lab9.judge import calibrate

    tone = calibrate(TONE)
    helpful = calibrate(Path("data/eval/judge_helpful_public.csv"))
    assert tone["passed"] is True
    assert helpful["passed"] is False
    assert helpful["confusion"] == {"tp": 9, "fp": 0, "fn": 21, "tn": 70}
    assert (helpful["precision"], helpful["recall"], helpful["kappa"]) == (1.0, 0.3, 0.375)


def test_judge_undefined_kappa_fails_without_crashing(monkeypatch):
    from lab9.judge import calibrate
    import math
    from unittest.mock import mock_open

    # This test checks calibration, not filesystem permissions. Supply the CSV
    # in memory so restricted Windows temp directories cannot prevent setup.
    path = Path("constant.csv")
    csv_open = mock_open(read_data="item_id,reply,human,judge\nX,OK,PASS,PASS\n")
    monkeypatch.setattr(Path, "open", csv_open)
    result = calibrate(path)
    csv_open.assert_called_once_with(encoding="utf-8")
    assert result["passed"] is False
    assert math.isnan(result["kappa"])
    assert math.isnan(result["corrected_fail_rate"])


def test_judge_does_not_round_a_failing_precision_into_a_pass(monkeypatch):
    from lab9 import judge

    monkeypatch.setattr(judge.stats, "precision_recall", lambda human, predictions: (0.7996, 0.8))
    result = judge.calibrate(TONE)
    assert result["precision"] == 0.8  # Display rounding must not loosen floors.
    assert result["passed"] is False


def test_paired_bootstrap_reference(stats):
    d, lo, hi = stats.paired_bootstrap([1, 1, 0.8, 1, 0.6], [1, 0.8, 0.8, 0.6, 0.6])
    assert d == pytest.approx(0.12, abs=1e-9)
    assert lo == pytest.approx(0.0, abs=0.01) and hi == pytest.approx(0.28, abs=0.01)


def test_paired_bootstrap_identical_is_zero(stats):
    assert stats.paired_bootstrap([1, 0, 1], [1, 0, 1]) == (0.0, 0.0, 0.0)


def test_paired_bootstrap_preserves_pairing(stats):
    # Every item's improvement is 0.1. Resampling the two arrays independently
    # would invent uncertainty that is absent from these paired differences.
    d, lo, hi = stats.paired_bootstrap([0.2, 0.5, 0.9], [0.1, 0.4, 0.8])
    assert (d, lo, hi) == pytest.approx((0.1, 0.1, 0.1))


def test_paired_bootstrap_lab9_regression_reference(stats):
    base = [1.0] * 14
    base[1] = 0.8
    regression = [1.0] * 14
    for index in (1, 6, 12, 13):
        regression[index] = 0.0
    d, lo, hi = stats.paired_bootstrap(regression, base)
    assert d == pytest.approx(-0.2714285714)
    assert lo == pytest.approx(-0.500, abs=0.01)
    assert hi == pytest.approx(-0.057, abs=0.01)


@pytest.mark.parametrize("a,b,options", [
    ([], [], {}),
    ([1, 0], [1], {}),
    ([[1], [0]], [[1], [0]], {}),
    ([float("nan"), 1], [0, 1], {}),
    ([1, 1], [0, float("inf")], {}),
    ([1, 1], [0, 1], {"n_resamples": 0}),
    ([1, 1], [0, 1], {"confidence": 1.0}),
    ([1], [0], {}),
])
def test_paired_bootstrap_rejects_invalid_samples(stats, a, b, options):
    with pytest.raises(ValueError):
        stats.paired_bootstrap(a, b, **options)
