"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def _finite_number(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    """Preserve every existing bound and blocking decision for one eval-set version."""
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []
    problems = []

    def compare(old, new, prefix):
        if old.get("blocking") and not new.get("blocking"):
            problems.append(f"RATCHET {prefix}: blocking removed")
        if old.get("no_significant_drop") and not new.get("no_significant_drop"):
            problems.append(f"RATCHET {prefix}: no_significant_drop removed")
        for bound in ("min", "max", "max_increase"):
            if bound not in old:
                continue
            value = new.get(bound)
            if not _finite_number(value) or not _finite_number(old[bound]):
                problems.append(f"RATCHET {prefix}: {bound} missing or invalid")
            elif (bound == "min" and value < old[bound]) or (bound != "min" and value > old[bound]):
                problems.append(f"RATCHET {prefix}: {bound} loosened")

    metrics = {metric["id"]: metric for metric in spec.get("metrics", [])}
    for old in base_spec.get("metrics", []):
        mid = old["id"]
        if mid not in metrics:
            problems.append(f"RATCHET metric {mid}: removed")
            continue
        new = metrics[mid]
        compare(old, new, f"metric {mid}")
        compare(old.get("threshold", {}), new.get("threshold", {}), f"metric {mid} threshold")
        for field in ("kind", "level", "grader"):
            if field in old and new.get(field) != old[field]:
                problems.append(f"RATCHET metric {mid}: {field} changed")
    slices = {(rule["name"], rule["metric"]): rule for rule in spec.get("slices", [])}
    for old in base_spec.get("slices", []):
        key = (old["name"], old["metric"])
        if key not in slices:
            problems.append(f"RATCHET slice {key[0]}/{key[1]}: removed")
        else:
            compare(old, slices[key], f"slice {key[0]}/{key[1]}")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    metric_rules = spec.get("metrics", [])
    ids = [metric["id"] for metric in metric_rules]
    if len(ids) != len(set(ids)):
        problems.append("duplicate metric ids in spec")
    slice_ids = [(rule["name"], rule["metric"]) for rule in spec.get("slices", [])]
    if len(slice_ids) != len(set(slice_ids)):
        problems.append("duplicate slice rules in spec")
    for rule in metric_rules:
        for bound, value in rule.get("threshold", {}).items():
            if bound in {"min", "max", "max_increase"} and not _finite_number(value):
                problems.append(f"invalid threshold {rule['id']}/{bound}")
    for rule in spec.get("slices", []):
        if "min" in rule and not _finite_number(rule["min"]):
            problems.append(f"invalid slice floor {rule['name']}")
    if base_spec is not None:
        problems.extend(_ratchet(spec, base_spec))

    def inspect(report, label):
        start = len(problems)
        manifest, rows, metrics = report.get("manifest", {}), report.get("rows"), report.get("metrics")
        if not isinstance(rows, list) or not isinstance(metrics, dict):
            problems.append(f"{label}: rows/metrics missing or malformed")
            return set(), {}
        if not isinstance(report.get("evaluator_failures"), list):
            problems.append(f"{label}: evaluator_failures missing or malformed")
        elif report["evaluator_failures"]:
            problems.append(f"{label}: evaluator_failures is nonempty")
        for mid, value in metrics.items():
            if value is not None and not _finite_number(value):
                problems.append(f"{label}: metric {mid} is nonfinite or nonnumeric")
        for rule in metric_rules:
            if rule.get("blocking") and not _finite_number(metrics.get(rule["id"])):
                problems.append(f"{label}: blocking metric {rule['id']} missing or invalid")

        items, seeds = manifest.get("items"), manifest.get("seeds")
        valid_items = isinstance(items, int) and not isinstance(items, bool) and items > 0
        valid_seeds = (isinstance(seeds, list) and bool(seeds)
                       and all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds))
        if not valid_items or not valid_seeds:
            problems.append(f"{label}: manifest items/seeds invalid")
            return set(), {}
        if len(seeds) != len(set(seeds)):
            problems.append(f"{label}: duplicate manifest seeds")
        if len(rows) != items * len(seeds):
            problems.append(f"{label}: row count differs from manifest items x seeds")
        if spec.get("seeds") is not None and set(seeds) != set(spec["seeds"]):
            problems.append(f"{label}: manifest seeds differ from spec")

        graded = ({mid for mid in ids if mid in GRADERS}
                  | {mid for mid in metrics if mid in GRADERS})
        k_values = set(spec.get("pass_k", []))
        for mid in set(ids) | set(metrics):
            for prefix in ("pass_at_", "pass_hat_"):
                if mid.startswith(prefix) and mid[len(prefix):].isdigit():
                    k_values.add(int(mid[len(prefix):]))
        if k_values or "pass_5" in metrics:
            graded.add("pass_rate")
        needs_cost = "cost_per_success" in metrics or "cost_per_success" in ids
        pairs, tags, item_seeds = set(), {}, {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                problems.append(f"{label}: row {index} is not an object")
                continue
            item, seed = row.get("item_id"), row.get("seed")
            if (not isinstance(item, str) or not item or not isinstance(seed, int)
                    or isinstance(seed, bool) or seed not in seeds):
                problems.append(f"{label}: row {index} has invalid item_id/seed")
                continue
            pair = (item, seed)
            if pair in pairs:
                problems.append(f"{label}: duplicate item/seed pair {pair}")
            pairs.add(pair)
            item_seeds.setdefault(item, set()).add(seed)
            row_tags = row.get("slices", [])
            if not isinstance(row_tags, list) or any(not isinstance(tag, str) for tag in row_tags):
                problems.append(f"{label}: {pair} has invalid slice tags")
            else:
                tag_set = frozenset(row_tags)
                if item in tags and tags[item] != tag_set:
                    problems.append(f"{label}: inconsistent slice tags for {item}")
                tags[item] = tag_set
            for mid in graded:
                value = row.get(mid)
                if not _finite_number(value) or not 0 <= value <= 1:
                    problems.append(f"{label}: {pair} missing/invalid grader {mid}")
            if needs_cost and (not _finite_number(row.get("cost")) or row["cost"] < 0):
                problems.append(f"{label}: {pair} missing/invalid cost")
        if len(item_seeds) != items or any(found != set(seeds) for found in item_seeds.values()):
            problems.append(f"{label}: incomplete item x seed coverage")

        # Validate summaries against their evidence, including pass^k. A valid
        # row count alone cannot catch someone editing only the displayed means.
        if len(problems) == start:
            scored_rows = [{**row, "cost": row.get("cost", 0.0)} for row in rows]
            recomputed = aggregate(scored_rows, sorted(graded), k_values=sorted(k_values))
            for mid in (set(metrics) | set(ids)) & set(recomputed):
                actual, expected = metrics.get(mid), recomputed[mid]
                if expected is None:
                    if actual is not None:
                        problems.append(f"{label}: summary {mid} must be undefined")
                elif not _finite_number(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-8):
                    problems.append(f"{label}: summary {mid} disagrees with rows")
        return pairs, tags

    pr_pairs, pr_tags = inspect(pr, "PR")
    base_pairs, base_tags = inspect(base, "baseline")
    if pr_pairs != base_pairs:
        problems.append("PR and baseline have different (item_id, seed) sets")
    if pr_tags != base_tags:
        problems.append("PR slice tags differ from baseline")
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        sid = f"slice:{name}/{metric}"
        verdict, note, value = "ok", "", None
        pr_rows = [row for row in pr["rows"] if name in (row.get("slices") or [])]
        base_rows = [row for row in base["rows"] if name in (row.get("slices") or [])]

        def invalid(rows):
            return any(not isinstance(row.get(metric), (int, float))
                       or not math.isfinite(row[metric]) for row in rows)

        if not pr_rows:
            verdict, note = "missing", "no items in PR slice"
        elif invalid(pr_rows):
            verdict, note = "fail", "missing or nonfinite PR slice score"
        else:
            a = per_item(pr, metric, slice_name=name)
            value = sum(a.values()) / len(a)
            if "min" in rule and value < rule["min"]:
                verdict = "fail"
            if rule.get("no_significant_drop"):
                b = {} if not base_rows or invalid(base_rows) else per_item(base, metric, slice_name=name)
                if not b or a.keys() != b.keys():
                    verdict, note = "fail", "cannot pair the same valid slice items with baseline"
                else:
                    keys = sorted(a)
                    try:
                        if bs.get("method", "percentile") != "percentile":
                            raise ValueError("slice bootstrap method must be percentile")
                        delta, lo, hi = stats.paired_bootstrap(
                            [a[key] for key in keys], [b[key] for key in keys],
                            n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                            confidence=bs.get("confidence", 0.95),
                        )
                        note = f"Δ {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                        if hi < 0:
                            verdict = "fail"
                    except ValueError as error:
                        verdict, note = "fail", f"cannot bootstrap slice: {error}"

        if verdict != "ok" and rule.get("blocking"):
            blocked.append(sid)
        label = ("ok" if verdict == "ok" else
                 "MISSING" if verdict == "missing" else
                 "BLOCK" if rule.get("blocking") else "warn")
        shown = "None" if value is None else f"{value:.4f}"
        lines.append(f"  {sid:<40} {shown:<8} min={rule.get('min', '-')} {note} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    for label, report in (("PR", pr), ("baseline", base)):
        if not isinstance(report, dict) or not isinstance(report.get("manifest"), dict):
            return ["integrity"], [f"  INTEGRITY {label}: report manifest missing or malformed"]
        if not isinstance(report["manifest"].get("eval_set_sha"), str) or not report["manifest"]["eval_set_sha"]:
            return ["integrity"], [f"  INTEGRITY {label}: eval_set_sha missing"]
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif not isinstance(val, (int, float)) or not math.isfinite(val):
            verdict, note = "fail", "invalid metric value"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th:
            base_val = base["metrics"].get(mid)
            if base_val is None or not isinstance(base_val, (int, float)) or not math.isfinite(base_val):
                verdict, note = "missing", "missing or invalid baseline metric"
            elif val > base_val * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and isinstance(val, (int, float)) and math.isfinite(val):
            a, b = per_item(pr, mid), per_item(base, mid)
            if not a or a.keys() != b.keys():
                verdict, note = "fail", "cannot pair the same items with the baseline"
            else:
                keys = sorted(a)
                try:
                    if bs.get("method", "percentile") != "percentile":
                        raise ValueError("M4 bootstrap method must be percentile")
                    d, lo, hi = stats.paired_bootstrap(
                        [a[k] for k in keys], [b[k] for k in keys],
                        n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                        confidence=bs.get("confidence", 0.95),
                    )
                    note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                    if hi < 0:
                        verdict = "fail"
                except ValueError as error:
                    verdict, note = "fail", f"cannot bootstrap: {error}"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
