"""Urgent Review workflow — assess_situation → recommend_action → alert_team.

Nodes: 2 LLM (assess_situation, recommend_action) + 1 logic (alert_team).
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.customer_success.state import CustomerSuccessState
from vibe_ai_ops.shared.config import load_prompt


def _assess_situation(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 1 (LLM): Assess the urgency and context of the situation."""
    try:
        prompt = load_prompt("config/prompts/cs/c1_onboarding.md")
    except FileNotFoundError:
        prompt = "You are a customer success crisis specialist."

    customer_name = state.get("customer_name", "Unknown")
    reason = state.get("reason", "Unspecified")
    deal_id = state.get("deal_id", "")

    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Assess this urgent customer situation:\n\n"
            f"Customer: {customer_name}\n"
            f"Deal: {deal_id}\n"
            f"Reason: {reason}\n\n"
            f"Provide:\n"
            f"1. Severity assessment (critical / high / medium)\n"
            f"2. Root cause hypothesis\n"
            f"3. Immediate impact if unaddressed\n"
            f"4. Key stakeholders to involve"
        ),
        model="claude-sonnet-4-5-20250929",
        temperature=0.3,
    )
    state["situation"] = response.content
    return state


def _recommend_action(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 2 (LLM): Recommend specific actions to resolve the situation."""
    response = call_claude(
        system_prompt=(
            "You recommend specific, time-bound actions for urgent customer situations. "
            "Prioritize retention. Be direct and actionable."
        ),
        user_message=(
            f"Recommend actions for this situation:\n\n"
            f"{state.get('situation', '')}\n\n"
            f"Provide:\n"
            f"1. Immediate action (next 2 hours)\n"
            f"2. Short-term plan (next 48 hours)\n"
            f"3. Follow-up cadence\n"
            f"4. Escalation criteria if situation worsens"
        ),
        model="claude-sonnet-4-5-20250929",
        temperature=0.3,
    )
    state["recommendation"] = response.content
    return state


def _alert_team(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 3 (logic): Mark alert as sent (in production, triggers Slack/PagerDuty)."""
    state["alert_sent"] = True
    return state


def create_urgent_review_graph(checkpointer=None):
    """Create the Urgent Review LangGraph workflow."""
    workflow = StateGraph(CustomerSuccessState)

    workflow.add_node("assess_situation", _assess_situation)
    workflow.add_node("recommend_action", _recommend_action)
    workflow.add_node("alert_team", _alert_team)

    workflow.set_entry_point("assess_situation")
    workflow.add_edge("assess_situation", "recommend_action")
    workflow.add_edge("recommend_action", "alert_team")
    workflow.add_edge("alert_team", END)

    return workflow.compile(checkpointer=checkpointer)
