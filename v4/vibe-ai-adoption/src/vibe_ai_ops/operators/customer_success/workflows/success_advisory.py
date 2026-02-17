"""Success Advisory workflow — review_accounts → identify_actions → generate_playbooks.

Nodes: 1 logic (review_accounts) + 2 LLM (identify_actions, generate_playbooks).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.customer_success.state import CustomerSuccessState
from vibe_ai_ops.shared.config import load_prompt


def _review_accounts(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 1 (logic): Aggregate account data for review."""
    accounts = state.get("accounts", [])
    if not accounts:
        # Default placeholder when no accounts provided
        state["accounts"] = [
            {
                "id": state.get("customer_id", "unknown"),
                "name": state.get("customer_name", "Unknown"),
                "health": "unknown",
            }
        ]
    return state


def _identify_actions(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 2 (LLM): Identify recommended actions for each account."""
    try:
        prompt = load_prompt("config/prompts/cs/c2_success_advisory.md")
    except FileNotFoundError:
        prompt = "You are a customer success strategist."

    accounts = state.get("accounts", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Review these accounts and identify priority actions:\n\n"
            f"{json.dumps(accounts, default=str)}\n\n"
            f"For each account, recommend:\n"
            f"1. Immediate action\n"
            f"2. This-week follow-up\n"
            f"3. Risk mitigation if needed"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["actions"] = response.content
    return state


def _generate_playbooks(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 3 (LLM): Generate tailored playbooks from identified actions."""
    response = call_claude(
        system_prompt=(
            "You create concise, actionable CS playbooks. "
            "Structure each playbook with clear steps and expected outcomes."
        ),
        user_message=(
            f"Generate CS playbooks based on these recommended actions:\n\n"
            f"{state.get('actions', '')}\n\n"
            f"Format as structured playbooks with steps and success criteria."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["playbooks"] = response.content
    return state


def create_success_advisory_graph(checkpointer=None):
    """Create the Success Advisory LangGraph workflow."""
    workflow = StateGraph(CustomerSuccessState)

    workflow.add_node("review_accounts", _review_accounts)
    workflow.add_node("identify_actions", _identify_actions)
    workflow.add_node("generate_playbooks", _generate_playbooks)

    workflow.set_entry_point("review_accounts")
    workflow.add_edge("review_accounts", "identify_actions")
    workflow.add_edge("identify_actions", "generate_playbooks")
    workflow.add_edge("generate_playbooks", END)

    return workflow.compile(checkpointer=checkpointer)
