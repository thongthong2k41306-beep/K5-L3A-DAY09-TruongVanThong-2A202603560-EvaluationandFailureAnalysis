"""Cover crash windows missing from the workflow and single student tests."""

from __future__ import annotations

import time

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count
from lab8.metrics import trial_pass
from lab8.shapes import SHAPES
from tests.conftest import BY_ID


@pytest.mark.parametrize("shape", ["workflow", "single"])
@pytest.mark.parametrize(
    ("point", "expected_committed"),
    [("before_effect", 0), ("after_checkpoint", 1)],
)
def test_resume_other_crash_windows(public_db, shape, point, expected_committed):
    run_claim = SHAPES[shape]

    # The requested crash must fire, rather than being ignored or swallowed.
    with pytest.raises(InjectedCrash, match=point):
        run_claim("C-012", seed=11, store_path=str(public_db), crash_at=point)

    # Inspect durable state through a new connection after the interrupted run.
    conn = connect(public_db)
    try:
        refund_count = conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = ?",
            ("C-012",),
        ).fetchone()[0]
        assert refund_count == expected_committed
        assert committed_audit_count(conn, "C-012") == expected_committed
    finally:
        conn.close()

    # Resume against the same store, without resetting the existing ledger.
    started_at = time.time()
    result = run_claim("C-012", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        # The shared evaluator checks money, ledger rows, audit and fresh trace.
        passed, reason = trial_pass(
            result.as_dict(),
            BY_ID["C-012"]["expected"],
            conn,
            started_at=started_at,
        )
        assert passed, reason
    finally:
        conn.close()
