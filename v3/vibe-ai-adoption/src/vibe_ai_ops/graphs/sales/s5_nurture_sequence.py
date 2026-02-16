from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from vibe_ai_ops.shared.models import AgentConfig
from vibe_ai_ops.shared.config import load_prompt
from vibe_ai_ops.crews.sales.validation_agents import create_s5_crew


class NurtureState(TypedDict, total=False):
    # Lead identity
    contact_id: str
    lead_data: dict[str, Any]
    lead_score: int
    # Nurture plan
    current_stage: str  # educational, solution_aware, product_aware, decision_ready
    touches_completed: int
    max_touches: int
    touch_interval_days: int
    # Current touch
    touch_content: str
    touch_channel: str  # email, linkedin, phone
    # Routing
    route: str  # continue, escalate, pause, complete
    escalation_reason: str
    # History
    touch_history: list[dict[str, Any]]


STAGE_PROGRESSION = [
    "educational",
    "solution_aware",
    "product_aware",
    "decision_ready",
]


def _default_config() -> AgentConfig:
    return AgentConfig(
        id="s5",
        name="Lead Nurture",
        engine="sales",
        tier="validation",
        trigger={"type": "event", "event_source": "lead_qualification:nurture"},
        output_channel="slack:#sales-agents",
        prompt_file="sales/s5_nurture.md",
        temperature=0.5,
    )


# --- Crew kickoff (mockable in tests) ---

def s5_kickoff(config: AgentConfig, prompt: str, lead_data: dict) -> str:
    crew = create_s5_crew(config, system_prompt=prompt)
    result = crew.kickoff(inputs={"lead_data": json.dumps(lead_data)})
    return str(result)


# --- Graph nodes ---

def _assess_lead(state: NurtureState) -> NurtureState:
    """Node 1: Assess lead's current position and determine nurture stage."""
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


def _generate_touch(state: NurtureState) -> NurtureState:
    """Node 2: Generate the next nurture touch using S5 crew."""
    config = _default_config()
    try:
        prompt = load_prompt(config.prompt_file)
    except FileNotFoundError:
        prompt = "You are a lead nurture specialist."

    lead_data = state.get("lead_data", {})
    lead_data["current_stage"] = state.get("current_stage", "educational")
    lead_data["touches_completed"] = state.get("touches_completed", 0)
    lead_data["lead_score"] = state.get("lead_score", 0)

    raw = s5_kickoff(config, prompt, lead_data)

    try:
        result = json.loads(raw)
        state["touch_content"] = result.get("content", "")
        state["touch_channel"] = result.get("channel", "email")
        # Update score if crew suggests it
        if "updated_score" in result:
            state["lead_score"] = result["updated_score"]
    except (json.JSONDecodeError, TypeError):
        state["touch_content"] = raw[:500]
        state["touch_channel"] = "email"

    return state


def _record_touch(state: NurtureState) -> NurtureState:
    """Node 3: Record touch in history and increment counter."""
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


def _evaluate_next(state: NurtureState) -> NurtureState:
    """Node 4: Decide whether to continue, escalate, or complete nurture."""
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


def _route_decision(state: NurtureState) -> str:
    """Conditional edge: route based on evaluation."""
    route = state.get("route", "continue")
    if route == "escalate":
        return "escalate"
    elif route == "complete":
        return "complete"
    else:
        return "wait_and_loop"


def _escalate(state: NurtureState) -> NurtureState:
    """Terminal node: lead is ready for sales handoff."""
    state["route"] = "escalate"
    return state


def _complete(state: NurtureState) -> NurtureState:
    """Terminal node: nurture sequence exhausted."""
    state["route"] = "complete"
    return state


def _wait_and_loop(state: NurtureState) -> NurtureState:
    """Node: marks that a wait is needed before next touch.

    In a real Temporal workflow, this is where the durable sleep happens.
    The LangGraph graph pauses here and the Temporal workflow sleeps
    for `touch_interval_days` before re-invoking.
    """
    state["route"] = "continue"
    return state


def create_nurture_graph(checkpointer=None):
    """Create the S5 Nurture Sequence LangGraph workflow.

    This graph handles a single nurture iteration (one touch).
    For multi-day durable execution, wrap this in a Temporal workflow
    that loops: invoke graph → sleep → invoke graph → ...
    """
    workflow = StateGraph(NurtureState)

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
