import json

import pytest

from lab8.db import connect
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD


def count_refund(db, claim_id):
    conn = connect(db)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)).fetchone()["n"]
    finally:
        conn.close()


# T02: ticket noi tre 5 ngay nhung DB chi 2 ngay -> phai denied, ke ca seed 55
@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_t02_khong_tin_ticket(public_db, seed):
    res = run_claim("C-002", seed=seed, store_path=str(public_db))
    assert res.status == "denied"
    assert res.proposal_amount == 0
    assert count_refund(public_db, "C-002") == 0


# T14: truyen full quote 150k, host tu tru 30k da hoan
def test_t14_full_quote(public_db):
    res = run_claim("C-014", seed=11, store_path=str(public_db))
    assert res.status == "resolved"
    assert res.proposal_amount == 150000

    conn = connect(public_db)
    amount = conn.execute("SELECT amount_vnd FROM refund_ledger WHERE claim_id = 'C-014'").fetchone()["amount_vnd"]
    conn.close()
    assert amount == 120000


def test_claim_khong_ton_tai(public_db):
    res = run_claim("C-999", seed=11, store_path=str(public_db))
    assert res.status == "failed"

    with open(res.trace_path, encoding="utf-8") as f:
        trace = json.load(f)
    assert trace["run_id"] == res.run_id


def test_trace_khong_lo_secret(public_db):
    cam = []
    for c in CLAIMS:
        cam.append(c["parent_secret"])
    for o in WORLD["orders"]:
        cam += [o["phone"], o["address"], o["internal_note"], o["item_name"]]
    cam = [x for x in cam if x]

    for claim_id in BY_ID:
        res = run_claim(claim_id, seed=11, store_path=str(public_db))
        with open(res.trace_path, encoding="utf-8") as f:
            text = f.read()
        text += json.dumps(res.as_dict(), ensure_ascii=False)
        for s in cam:
            assert s not in text, f"{claim_id} lo {s}"
