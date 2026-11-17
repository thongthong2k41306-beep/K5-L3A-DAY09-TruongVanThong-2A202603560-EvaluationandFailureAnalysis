"""Eval-set identity must survive Git's Windows/Linux newline conversion."""
import hashlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.student


def test_evalset_hash_is_identical_for_lf_and_crlf(monkeypatch):
    from lab9.evalset import sha12

    content = b'{"item_id":"E-001","failure_modes":["FM-03"]}\n'
    payloads = {"linux.jsonl": content, "windows.jsonl": content.replace(b"\n", b"\r\n")}
    monkeypatch.setattr(Path, "read_bytes", lambda path: payloads[path.name])
    expected = hashlib.sha256(content).hexdigest()[:12]
    assert sha12(Path("linux.jsonl")) == expected
    assert sha12(Path("windows.jsonl")) == expected


def test_evalset_hash_still_detects_content_and_final_newline_changes(monkeypatch):
    from lab9.evalset import sha12

    content = b'{"claim_id":"C-001"}\n'
    payloads = {"original.jsonl": content,
                "changed.jsonl": content.replace(b"C-001", b"C-002"),
                "no_newline.jsonl": content.rstrip(b"\n")}
    monkeypatch.setattr(Path, "read_bytes", lambda path: payloads[path.name])
    assert sha12(Path("original.jsonl")) != sha12(Path("changed.jsonl"))
    assert sha12(Path("original.jsonl")) != sha12(Path("no_newline.jsonl"))
