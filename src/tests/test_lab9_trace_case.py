"""Replay the archived C-002@11 trace pair without running shapes or writing files."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.student


def test_c002_ticket_override_fails_and_fixed_keeps_db_fact():
    from lab9.graders import DbFactKept

    folder = Path(__file__).parent / "fixtures" / "lab9"
    broken = json.loads((folder / "R-seeded_regression-C-002-s11.json").read_text(encoding="utf-8"))
    fixed = json.loads((folder / "R-fixed-C-002-s11.json").read_text(encoding="utf-8"))
    assert broken["run_id"] == "R-seeded_regression-C-002-s11"
    assert fixed["run_id"] == "R-fixed-C-002-s11"

    for trace in (broken, fixed):
        assert trace["events"][1]["kind"] == "investigator"
        assert trace["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2

    assert broken["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}
    assert fixed["events"][2]["kind"] == "quote"
    assert fixed["events"][2]["payload"]["amount_vnd"] == 0
    assert broken["events"][3]["payload"]["amount_vnd"] == 20000
    grader = DbFactKept()
    assert grader.evaluate(SimpleNamespace(output={"events": broken["events"]})).value is False
    assert grader.evaluate(SimpleNamespace(output={"events": fixed["events"]})).value is True
