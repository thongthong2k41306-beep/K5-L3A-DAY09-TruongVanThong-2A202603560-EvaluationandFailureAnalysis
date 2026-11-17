"""Measure the optional workflow draft call with the official benchmark harness.

Run from src/:
    python -m tests.run_draft_ablation --out reports/ablation_workflow_draft.json

Only this experiment temporarily overrides workflow._done's existing draft flag.
The shape, host, metrics, fixtures and main benchmark artifact stay unchanged.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial, wraps
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from typing import Any, Iterator
from unittest.mock import patch

from lab8.benchmark import run_benchmark
from lab8.config_loader import repo_path
from lab8.db import load_json, load_jsonl
from lab8.shapes import workflow
from lab8.trace import Trace

SEEDS = [11, 22, 33, 44, 55]
HYPOTHESIS = {
    "pass_rate_delta": 0.0,
    "pass_5_delta": 0.0,
    "mean_model_calls_delta": -1.0,
    "cost_per_success_saving_vnd_range": [0.8, 1.2],
    "paired_status_tool_calls_and_trace_steps_unchanged": True,
}


@contextmanager
def workflow_condition(*, draft_enabled: bool, trace_directory: Path) -> Iterator[None]:
    """Switch one existing option; restore all bindings even if a run raises."""
    original_done = workflow._done

    @wraps(original_done)
    def done(*args, **kwargs):
        if not draft_enabled:
            kwargs["draft"] = False
        return original_done(*args, **kwargs)

    # Both conditions get the same tracer, with separate artifact directories.
    with (
        patch.object(workflow, "_done", done),
        patch.object(workflow, "Trace", partial(Trace, directory=trace_directory)),
    ):
        yield


def source_hashes() -> dict[str, str]:
    paths = [
        *repo_path("lab8").rglob("*.py"),
        *repo_path("config").glob("*.yaml"),
        repo_path("data", "public_claims.jsonl"),
        repo_path("data", "public_world_state.json"),
        repo_path("requirements.txt"),
        Path(__file__).resolve(),
    ]
    return {
        path.relative_to(repo_path()).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def git_head() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path().parent,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def compare_conditions(variants: dict[str, Any]) -> dict[str, Any]:
    enabled = variants["draft_on"]
    disabled = variants["draft_off"]
    if enabled["controlled_variables"] != disabled["controlled_variables"]:
        raise ValueError("conditions do not share the same controlled variables")

    def indexed(report):
        rows = {(row["claim_id"], row["seed"]): row for row in report["trials"]}
        if len(rows) != len(report["trials"]):
            raise ValueError("duplicate claim/seed pairs")
        return rows

    on_rows, off_rows = indexed(enabled), indexed(disabled)
    if on_rows.keys() != off_rows.keys():
        raise ValueError("conditions do not contain the same claim/seed pairs")

    on = enabled["by_shape"]["workflow"]
    off = disabled["by_shape"]["workflow"]
    on_cost = on["cost_per_success_vnd"]
    off_cost = off["cost_per_success_vnd"]
    saving = None if on_cost is None or off_cost is None else on_cost - off_cost
    paired_fields = ("status", "passed", "reason", "tool_calls", "steps")
    mismatches = [
        {"claim_id": claim_id, "seed": seed}
        for claim_id, seed in sorted(on_rows)
        if any(on_rows[(claim_id, seed)][field] != off_rows[(claim_id, seed)][field]
               for field in paired_fields)
    ]
    low, high = HYPOTHESIS["cost_per_success_saving_vnd_range"]
    model_delta = off["mean_model_calls"] - on["mean_model_calls"]
    checks = {
        "all_trials_pass_official_evaluator": all(
            row["passed"] is True for report in variants.values() for row in report["trials"]
        ),
        "paired_fields_unchanged": not mismatches,
        "pass_rate_delta_matches_hypothesis": off["pass_rate"] - on["pass_rate"] == 0,
        "pass_5_delta_matches_hypothesis": off["pass_5"] - on["pass_5"] == 0,
        "one_fewer_model_call_per_trial": model_delta == -1,
        "saving_within_predicted_range": saving is not None and low <= saving <= high,
    }
    return {
        "paired_trials": len(on_rows),
        "paired_fields": list(paired_fields),
        "mismatched_pairs": mismatches,
        "pass_rate_delta": off["pass_rate"] - on["pass_rate"],
        "pass_5_delta": off["pass_5"] - on["pass_5"],
        "mean_model_calls_delta": model_delta,
        "cost_per_success_saving_vnd": saving,
        "cost_reduction_percent": None if saving is None or not on_cost else 100 * saving / on_cost,
        "hypothesis_checks": checks,
        "hypothesis_supported_on_public": all(checks.values()),
    }


def run_experiment(trace_root: Path) -> dict[str, Any]:
    hashes_before = source_hashes()
    world = load_json(repo_path("data", "public_world_state.json"))
    claims = load_jsonl(repo_path("data", "public_claims.jsonl"))
    variants = {}
    for name, enabled in (("draft_on", True), ("draft_off", False)):
        with workflow_condition(draft_enabled=enabled, trace_directory=trace_root / name):
            variants[name] = run_benchmark(
                world=world, claims=claims, shapes=["workflow"], seeds=SEEDS
            )
    if hashes_before != source_hashes():
        raise RuntimeError("source/config/data changed during the experiment; rerun on a stable tree")
    return {
        "experiment_id": "workflow_draft_ablation_v1",
        "research_question": "R3",
        "source_url": "https://aclanthology.org/2026.aacl-long.44/",
        "independent_variable": "workflow optional MockLLM draft call: on/off",
        "hypothesis_before_run": HYPOTHESIS,
        "provenance": {
            "git_head": git_head(),
            "python": platform.python_version(),
            "note": "Source hashes identify the working tree, including uncommitted code.",
            "sha256": hashes_before,
        },
        "method": {
            "harness": "lab8.benchmark.run_benchmark (unmodified)",
            "evaluator": "lab8.metrics.trial_pass (unmodified)",
            "treatment": "Scoped override of workflow._done(draft=False); native default for draft_on.",
            "isolation": "Fresh SQLite per trial; separate trace directory per condition.",
            "trace_directories": {name: (trace_root / name).as_posix() for name in variants},
            "run_id_note": "Shape, claim and seed stay the same; condition plus run_id identifies a run.",
        },
        "variants": variants,
        "comparison": compare_conditions(variants),
        "limitations": [
            "Only 14 public claims and 5 seeded MockLLM trials per condition; no hidden evaluation.",
            "The evaluator does not score customer-facing reply quality; draft output is not in RunResult.",
            "Only drafting is ablated; this does not isolate topology effects across A/B/C/D.",
            "Cost is simulated VND. Latency is unavailable; this is not a production model study.",
            "Paired fields compare status/pass/reason/tool calls/trace steps; ledger and money are checked separately by the official evaluator.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/ablation_workflow_draft.json"))
    parser.add_argument("--trace-root", type=Path, default=Path("traces/ablation_workflow_draft"))
    args = parser.parse_args(argv)
    report = run_experiment(args.trace_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, benchmark in report["variants"].items():
        stats = benchmark["by_shape"]["workflow"]
        cost = stats["cost_per_success_vnd"]
        cost_text = "unavailable" if cost is None else f"{cost:.6f}"
        print(f"{name}: {stats['successes']}/{stats['trials']} pass; "
              f"pass^5={stats['pass_5']:.3f}; cost/success={cost_text} VND; "
              f"model_calls/trial={stats['mean_model_calls']:.1f}")
    print(json.dumps(report["comparison"], ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0 if report["comparison"]["hypothesis_supported_on_public"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
