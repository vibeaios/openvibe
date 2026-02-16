from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence import (
        create_nurture_graph,
    )
    from vibe_ai_ops.operators.revenue_ops.state import RevenueOpsState


@dataclass
class NurtureWorkflowInput:
    contact_id: str
    lead_data: dict[str, Any]
    lead_score: int
    max_touches: int = 10
    touch_interval_days: int = 3


@dataclass
class NurtureWorkflowOutput:
    contact_id: str
    final_route: str  # escalate | complete
    touches_completed: int
    final_score: int
    escalation_reason: str


@workflow.defn
class NurtureSequenceWorkflow:
    """Temporal workflow: durable multi-day nurture sequence.

    Loops: run LangGraph (one touch) → sleep interval → repeat
    until lead escalates or max touches reached.
    """

    @workflow.run
    async def run(self, inp: NurtureWorkflowInput) -> NurtureWorkflowOutput:
        state: RevenueOpsState = {
            "contact_id": inp.contact_id,
            "lead_data": inp.lead_data,
            "lead_score": inp.lead_score,
            "max_touches": inp.max_touches,
            "touch_interval_days": inp.touch_interval_days,
            "touches_completed": 0,
            "touch_history": [],
        }

        while True:
            # Run one nurture iteration via LangGraph
            graph = create_nurture_graph()
            state = graph.invoke(state)

            route = state.get("route", "continue")

            if route in ("escalate", "complete"):
                return NurtureWorkflowOutput(
                    contact_id=inp.contact_id,
                    final_route=route,
                    touches_completed=state.get("touches_completed", 0),
                    final_score=state.get("lead_score", 0),
                    escalation_reason=state.get("escalation_reason", ""),
                )

            # Durable sleep — Temporal persists state across days
            interval = timedelta(days=state.get("touch_interval_days", 3))
            await workflow.sleep(interval)
