import json

import pytest

from lab8.db import init_store
from lab8.shapes import SHAPES
from tests.conftest import CLAIMS, WORLD


@pytest.mark.parametrize(
    "shape",
    ["workflow", "single", "orchestrator"],
)
def test_unknown_claim_has_no_refund_and_valid_trace(tmp_path, shape):
    store = tmp_path / f"{shape}-unknown.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    result = SHAPES[shape](
        "C-NOT-FOUND",
        seed=11,
        store_path=str(store),
    )

    assert result.claim_id == "C-NOT-FOUND"
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    assert result.error_reason == "unknown_claim"

    with open(result.trace_path, encoding="utf-8") as stream:
        trace = json.load(stream)

    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    assert trace["events"]