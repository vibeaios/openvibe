"""Nurture Sequence workflow — assess → generate → record → evaluate.

Migrated from graphs/sales/s5_nurture_sequence.py.
Replaces s5_kickoff() CrewAI crew with call_claude().
Durable: Temporal workflow loops with sleep between iterations.
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.revenue_ops.state import RevenueOpsState
from vibe_ai_ops.shared.config import load_prompt


STAGE_PROGRESSION = [
    "educational",
    "solution_aware",
    "product_aware",
    "decision_ready",
]


def _assess_lead(state: RevenueOpsState) -> RevenueOpsState:
    """Node 1 (LLM): Assess lead's current position and determine nurture stage."""
    score = state.get("lead_score", 0)
    touches = state.get("touches_completed", 0)

    # Set defaults
    if "max_touches" not in state:
        state["max_touches"] = 10
    if "touch_interval_days" not in state:
        state["touch_interval_days"] = 3
    if "touch_history" not in state:
        state["touch_history"] = []

    # Determine stage from score
    if score >= 80:
        state["current_stage"] = "decision_ready"
    elif score >= 60:
        state["current_stage"] = "product_aware"
    elif score >= 40:
        state["current_stage"] = "solution_aware"
    else:
        state["current_stage"] = "educational"

    return state


def _generate_touch(state: RevenueOpsState) -> RevenueOpsState:
    """Node 2 (LLM): Generate the next nurture touch using Claude."""
    try:
        prompt = load_prompt("config/prompts/sales/s5_nurture.md")
    except FileNotFoundError:
        prompt = "You are a lead nurture specialist."

    lead_data = state.get("lead_data", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Generate the next nurture touch for this lead:\n\n"
            f"Lead data: {json.dumps(lead_data)}\n"
            f"Current stage: {state.get('current_stage', 'educational')}\n"
            f"Touches completed: {state.get('touches_completed', 0)}\n"
            f"Lead score: {state.get('lead_score', 0)}\n\n"
            f"Return ONLY valid JSON:\n"
            f"{{\"content\": \"...\", \"channel\": \"email|linkedin|phone\", "
            f"\"updated_score\": N}}"
        ),
        model="claude-sonnet-4-5-20250929",
        temperature=0.5,
    )

    try:
        result = json.loads(response.content)
        state["touch_content"] = result.get("content", "")
        state["touch_channel"] = result.get("channel", "email")
        if "updated_score" in result:
            state["lead_score"] = result["updated_score"]
    except (json.JSONDecodeError, TypeError):
        state["touch_content"] = response.content[:500]
        state["touch_channel"] = "email"

    return state


def _record_touch(state: RevenueOpsState) -> RevenueOpsState:
    """Node 3 (logic): Record touch in history and increment counter."""
    history = state.get("touch_history", [])
    history.append({
        "touch_number": state.get("touches_completed", 0) + 1,
        "stage": state.get("current_stage", ""),
        "channel": state.get("touch_channel", ""),
        "content_preview": state.get("touch_content", "")[:100],
    })
    state["touch_history"] = history
    state["touches_completed"] = state.get("touches_completed", 0) + 1
    return state


def _evaluate_next(state: RevenueOpsState) -> RevenueOpsState:
    """Node 4 (logic): Decide whether to continue, escalate, or complete nurture."""
    score = state.get("lead_score", 0)
    touches = state.get("touches_completed", 0)
    max_touches = state.get("max_touches", 10)

    if score >= 80:
        state["route"] = "escalate"
        state["escalation_reason"] = f"Lead score {score} >= 80, ready for sales"
    elif touches >= max_touches:
        state["route"] = "complete"
        state["escalation_reason"] = f"Max touches ({max_touches}) reached"
    else:
        state["route"] = "continue"
        state["escalation_reason"] = ""

    return state


def _route_decision(state: RevenueOpsState) -> str:
    """Conditional edge: route based on evaluation."""
    route = state.get("route", "continue")
    if route == "escalate":
        return "escalate"
    elif route == "complete":
        return "complete"
    else:
        return "wait_and_loop"


def _escalate(state: RevenueOpsState) -> RevenueOpsState:
    """Terminal node: lead is ready for sales handoff."""
    state["route"] = "escalate"
    return state


def _complete(state: RevenueOpsState) -> RevenueOpsState:
    """Terminal node: nurture sequence exhausted."""
    state["route"] = "complete"
    return state


def _wait_and_loop(state: RevenueOpsState) -> RevenueOpsState:
    """Pause point for Temporal sleep before next touch."""
    state["route"] = "continue"
    return state


def create_nurture_graph(checkpointer=None):
    """Create the Nurture Sequence LangGraph workflow.

    Handles a single iteration. For multi-day durable execution,
    wrap in a Temporal workflow that loops: invoke → sleep → invoke → ...
    """
    workflow = StateGraph(RevenueOpsState)

    workflow.add_node("assess", _assess_lead)
    workflow.add_node("generate_touch", _generate_touch)
    workflow.add_node("record_touch", _record_touch)
    workflow.add_node("evaluate", _evaluate_next)
    workflow.add_node("escalate", _escalate)
    workflow.add_node("complete", _complete)
    workflow.add_node("wait_and_loop", _wait_and_loop)

    workflow.set_entry_point("assess")
    workflow.add_edge("assess", "generate_touch")
    workflow.add_edge("generate_touch", "record_touch")
    workflow.add_edge("record_touch", "evaluate")
    workflow.add_conditional_edges(
        "evaluate",
        _route_decision,
        {
            "escalate": "escalate",
            "complete": "complete",
            "wait_and_loop": "wait_and_loop",
        },
    )
    workflow.add_edge("escalate", END)
    workflow.add_edge("complete", END)
    workflow.add_edge("wait_and_loop", END)

    return workflow.compile(checkpointer=checkpointer)
