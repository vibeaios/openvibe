"""Generic Temporal activity for running any operator workflow.

This is the bridge between Temporal (scheduling) and operators (LangGraph workflows).
Temporal calls this activity → activity runs the appropriate LangGraph graph.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from temporalio import activity


@dataclass
class OperatorActivityInput:
    operator_id: str
    trigger_id: str
    input_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperatorActivityOutput:
    operator_id: str
    trigger_id: str
    status: str  # "success" | "error"
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_seconds: float = 0.0


@activity.defn
async def run_operator(inp: OperatorActivityInput) -> OperatorActivityOutput:
    """Temporal activity: run an operator workflow via the OperatorRuntime.

    Chain: Temporal activity → OperatorRuntime.activate() → LangGraph graph → Claude API
    """
    start = time.time()

    try:
        from vibe_ai_ops.main import build_system

        activity.logger.info(
            f"Starting operator {inp.operator_id} trigger {inp.trigger_id}"
        )

        system = build_system()
        runtime = system["runtime"]
        result = runtime.activate(inp.operator_id, inp.trigger_id, inp.input_data)

        duration = time.time() - start
        activity.logger.info(
            f"Operator {inp.operator_id}/{inp.trigger_id} complete ({duration:.1f}s)"
        )

        return OperatorActivityOutput(
            operator_id=inp.operator_id,
            trigger_id=inp.trigger_id,
            status="success",
            result=result if isinstance(result, dict) else {},
            duration_seconds=duration,
        )

    except Exception as e:
        return OperatorActivityOutput(
            operator_id=inp.operator_id,
            trigger_id=inp.trigger_id,
            status="error",
            error=str(e),
            duration_seconds=time.time() - start,
        )
