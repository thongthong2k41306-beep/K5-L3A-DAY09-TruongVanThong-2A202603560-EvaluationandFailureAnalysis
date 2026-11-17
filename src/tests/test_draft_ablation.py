"""Check that removing drafting preserves business outcomes and patch isolation."""

from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

from lab8.db import connect, init_store
from lab8.metrics import check_trace, trial_pass
from lab8.shapes import workflow
from tests.conftest import BY_ID, CLAIMS, WORLD
from tests.run_draft_ablation import workflow_condition


@pytest.mark.parametrize("claim_id", ["C-001", "C-004", "C-014", "C-NOT-FOUND"])
def test_draft_ablation_preserves_money_and_outcome(tmp_path, claim_id):
    results = []
    traces = []
    for name, enabled in (("draft_on", True), ("draft_off", False)):
        store = tmp_path / f"{name}.sqlite"
        init_store(store, WORLD, CLAIMS).close()
        started_at = time.time()
        with workflow_condition(draft_enabled=enabled, trace_directory=tmp_path / name):
            result = workflow.run_claim(claim_id, seed=11, store_path=str(store))
        payload = result.as_dict()
        conn = connect(store)
        try:
            if claim_id in BY_ID:
                passed, reason = trial_pass(
                    payload, BY_ID[claim_id]["expected"], conn, started_at=started_at
                )
                assert passed, reason
            else:
                assert result.status == "failed"
                assert result.refund_effects == []
                assert result.error_reason == "unknown_claim"
                valid, reason = check_trace(payload, started_at=started_at)
                assert valid, reason
        finally:
            conn.close()
        traces.append(json.loads(Path(result.trace_path).read_text(encoding="utf-8")))
        results.append(payload)

    on, off = results
    for field in ("status", "proposal_amount", "refund_effects", "committed_audit_count", "error_reason", "tool_calls"):
        assert on[field] == off[field], field
    assert traces[0] == traces[1]
    assert off["model_calls"] == 0
    assert off["input_tokens"] == off["output_tokens"] == 0
    if claim_id in BY_ID:
        assert on["model_calls"] == 1
        assert off["cost_estimate"] < on["cost_estimate"]
    else:
        # Unknown claims already skip drafting in the native workflow.
        assert on["model_calls"] == 0
        assert off["cost_estimate"] == on["cost_estimate"]


def test_draft_ablation_restores_shape_after_exception(tmp_path):
    original_done, original_trace = workflow._done, workflow.Trace
    with pytest.raises(RuntimeError, match="interrupted experiment"):
        with workflow_condition(draft_enabled=False, trace_directory=tmp_path):
            raise RuntimeError("interrupted experiment")
    assert workflow._done is original_done
    assert workflow.Trace is original_trace
