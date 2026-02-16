"""Onboarding workflow — create_plan → setup_milestones → send_welcome.

Nodes: 1 LLM (create_plan) + 2 logic (setup_milestones, send_welcome).
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.customer_success.state import CustomerSuccessState
from vibe_ai_ops.shared.config import load_prompt


def _create_plan(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 1 (LLM): Generate a tailored onboarding plan for the customer."""
    try:
        prompt = load_prompt("config/prompts/cs/c1_onboarding.md")
    except FileNotFoundError:
        prompt = "You are a customer success onboarding specialist."

    customer_name = state.get("customer_name", "Unknown")
    customer_id = state.get("customer_id", "")

    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Create a 30-day onboarding plan for customer: {customer_name} "
            f"(ID: {customer_id}).\n\n"
            f"Include:\n"
            f"1. Week 1: Setup and initial configuration\n"
            f"2. Week 2: Core feature adoption\n"
            f"3. Week 3: Advanced workflows\n"
            f"4. Week 4: Review and optimization\n\n"
            f"Be concise and actionable."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["onboarding_plan"] = response.content
    return state


def _setup_milestones(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 2 (logic): Create milestone checkpoints from the plan."""
    plan = state.get("onboarding_plan", "")
    milestones = [
        {"week": 1, "milestone": "Setup complete", "status": "pending"},
        {"week": 2, "milestone": "Core features adopted", "status": "pending"},
        {"week": 3, "milestone": "Advanced workflows configured", "status": "pending"},
        {"week": 4, "milestone": "Review and optimization done", "status": "pending"},
    ]
    state["milestones"] = milestones
    return state


def _send_welcome(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 3 (logic): Mark welcome as sent (in production, triggers Slack/email)."""
    state["welcome_sent"] = True
    return state


def create_onboarding_graph(checkpointer=None):
    """Create the Onboarding LangGraph workflow."""
    workflow = StateGraph(CustomerSuccessState)

    workflow.add_node("create_plan", _create_plan)
    workflow.add_node("setup_milestones", _setup_milestones)
    workflow.add_node("send_welcome", _send_welcome)

    workflow.set_entry_point("create_plan")
    workflow.add_edge("create_plan", "setup_milestones")
    workflow.add_edge("setup_milestones", "send_welcome")
    workflow.add_edge("send_welcome", END)

    return workflow.compile(checkpointer=checkpointer)
