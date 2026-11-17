from __future__ import annotations

import time

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.metrics import check_trace, trial_pass
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_orchestrator_resumes_each_crash_window(public_db, point):
    with pytest.raises(InjectedCrash, match=point):
        run_claim("C-012", seed=11, store_path=str(public_db), crash_at=point)

    conn = connect(public_db)
    try:
        before_resume = conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-012'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert before_resume == (0 if point == "before_effect" else 1)

    started = time.time()
    result = run_claim("C-012", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID["C-012"]["expected"], conn, started_at=started)
        assert passed, reason
        assert conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-012'"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE claim_id = 'C-012' AND step = 'issue_refund'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_orchestrator_unknown_claim_returns_fresh_trace(public_db):
    started = time.time()
    result = run_claim("C-UNKNOWN", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    ok, reason = check_trace(result.as_dict(), started_at=started)
    assert ok, reason
