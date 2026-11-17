"""Shape B: bounded single-agent ReAct loop."""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))
    conn = connect(store_path)

    try:
        def done(status, proposal=0, reason=None):
            trace.add(
                "decision",
                {
                    "status": status,
                    "proposal_amount": proposal,
                    "reason": reason,
                },
            )
            return finish(
                conn,
                shape="single",
                claim_id=claim_id,
                seed=seed,
                status=status,
                proposal_amount=proposal,
                budget=budget,
                trace=trace,
                error_reason=reason,
            )

        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)

        if not claim["found"]:
            return done("failed", reason="unknown_claim")

        if not claim.get("order_id"):
            return done("needs_info", reason="missing_order_id")

        def decide(observation):
            last_tool = observation.get("last_tool")
            last_result = observation.get("last_result") or {}

            # MockLLM records a simulated reasoning call.
            # Structured tool results determine actions and money.
            complete(
                budget,
                seed=seed,
                purpose="decide",
                prompt=f"claim={claim_id}; last_tool={last_tool}",
            )

            if last_tool is None:
                action = {
                    "tool": "lookup_order",
                    "args": {
                        "order_id": claim["order_id"],
                        "principal_id": claim["principal_id"],
                    },
                }
                trace.add("action", {"tool": "lookup_order"})
                return action

            if last_tool == "lookup_order":
                trace.add("observation", {
                    "tool": last_tool,
                    "visible": last_result["visible"],
                    "reason": last_result["reason"],
                })

                if not last_result["visible"]:
                    return {
                        "final": {
                            "status": "escalated",
                            "proposal_amount": 0,
                            "reason": last_result["reason"],
                        }
                    }

                trace.add("action", {"tool": "compute_compensation"})
                return {
                    "tool": "compute_compensation",
                    "args": {"order": last_result["order"]},
                }

            if last_tool == "compute_compensation":
                proposal = int(last_result["amount_vnd"])
                trace.add("quote", last_result)
                return {
                    "final": {
                        "status": "quoted",
                        "proposal_amount": proposal,
                        "reason": last_result["reason"],
                    }
                }

            return {
                "final": {
                    "status": "failed",
                    "proposal_amount": 0,
                    "reason": "unexpected_observation",
                }
            }

        result = run_react(
            conn,
            budget,
            observation={"claim": claim},
            decide=decide,
            max_steps=8,
        )

        final = result["final"]
        proposal = int(final.get("proposal_amount", 0))
        reason = final.get("reason") or final.get("error_reason")

        if result["stopped"] != "final":
            return done("failed", reason=reason or "step_cap")

        if final["status"] in {"escalated", "failed"}:
            return done(final["status"], proposal, reason)

        if proposal <= 0:
            return done("denied", reason=reason)

        # Only the host writes refunds, after the ReAct loop.
        outcome = issue_refund(
            conn,
            claim_id,
            proposal,
            crash_at=crash_at,
        )

        if not outcome["ok"]:
            status = "failed" if outcome["conflict"] else "denied"
            return done(status, proposal, outcome["reason"])

        return done("resolved", proposal)

    finally:
        conn.close()