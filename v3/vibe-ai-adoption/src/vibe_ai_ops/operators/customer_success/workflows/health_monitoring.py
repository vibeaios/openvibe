"""Health Monitoring workflow — pull_signals → score_health → flag_risks.

Nodes: 1 logic (pull_signals) + 1 LLM (score_health) + 1 logic (flag_risks).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.customer_success.state import CustomerSuccessState
from vibe_ai_ops.shared.config import load_prompt


def _pull_signals(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 1 (logic): Pull health signals from available data sources."""
    signals = state.get("health_signals", [])
    if not signals:
        # Default signals when none provided
        state["health_signals"] = [
            {"type": "usage", "value": "unknown", "source": "product"},
            {"type": "support_tickets", "value": 0, "source": "helpdesk"},
            {"type": "nps", "value": "unknown", "source": "survey"},
        ]
    return state


def _score_health(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 2 (LLM): Score customer health based on signals."""
    try:
        prompt = load_prompt("config/prompts/cs/c3_health_monitoring.md")
    except FileNotFoundError:
        prompt = "You are a customer health scoring specialist."

    signals = state.get("health_signals", [])
    customer_name = state.get("customer_name", "Unknown")

    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Score the health of customer '{customer_name}' based on these signals:\n\n"
            f"{json.dumps(signals, default=str)}\n\n"
            f"Provide:\n"
            f"1. Overall health score (healthy / at-risk / critical)\n"
            f"2. Key factors driving the score\n"
            f"3. Trend direction (improving / stable / declining)"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["health_score"] = response.content
    return state


def _flag_risks(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 3 (logic): Extract and flag risks from health score."""
    health_score = state.get("health_score", "")
    lower = health_score.lower()

    risks = []
    if "critical" in lower:
        risks.append({
            "level": "critical",
            "customer": state.get("customer_name", "Unknown"),
            "detail": "Customer health is critical — immediate attention required",
        })
    elif "at-risk" in lower or "at risk" in lower:
        risks.append({
            "level": "warning",
            "customer": state.get("customer_name", "Unknown"),
            "detail": "Customer health is at risk — proactive outreach recommended",
        })

    state["risks"] = risks
    return state


def create_health_monitoring_graph(checkpointer=None):
    """Create the Health Monitoring LangGraph workflow."""
    workflow = StateGraph(CustomerSuccessState)

    workflow.add_node("pull_signals", _pull_signals)
    workflow.add_node("score_health", _score_health)
    workflow.add_node("flag_risks", _flag_risks)

    workflow.set_entry_point("pull_signals")
    workflow.add_edge("pull_signals", "score_health")
    workflow.add_edge("score_health", "flag_risks")
    workflow.add_edge("flag_risks", END)

    return workflow.compile(checkpointer=checkpointer)
