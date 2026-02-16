"""Expansion Scan workflow — analyze_usage → identify_opportunities → draft_proposals.

Nodes: 1 logic (analyze_usage) + 2 LLM (identify_opportunities, draft_proposals).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.customer_success.state import CustomerSuccessState
from vibe_ai_ops.shared.config import load_prompt


def _analyze_usage(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 1 (logic): Analyze product usage data for expansion signals."""
    usage = state.get("usage_data", {})
    if not usage:
        state["usage_data"] = {
            "customer_id": state.get("customer_id", "unknown"),
            "customer_name": state.get("customer_name", "Unknown"),
            "current_plan": "standard",
            "seat_utilization": "unknown",
            "feature_adoption": "unknown",
        }
    return state


def _identify_opportunities(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 2 (LLM): Identify expansion opportunities from usage patterns."""
    try:
        prompt = load_prompt("config/prompts/cs/c4_expansion.md")
    except FileNotFoundError:
        prompt = "You are a customer expansion specialist."

    usage = state.get("usage_data", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze this usage data and identify expansion opportunities:\n\n"
            f"{json.dumps(usage, default=str)}\n\n"
            f"Look for:\n"
            f"1. Upsell potential (higher tier, more seats)\n"
            f"2. Cross-sell opportunities (new products/features)\n"
            f"3. Timing signals (when to approach)\n"
            f"4. Risk of approaching too early"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["opportunities"] = response.content
    return state


def _draft_proposals(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 3 (LLM): Draft expansion proposals from identified opportunities."""
    response = call_claude(
        system_prompt=(
            "You draft concise expansion proposals for existing customers. "
            "Focus on value delivered and ROI. Keep proposals under 200 words."
        ),
        user_message=(
            f"Draft expansion proposals based on these opportunities:\n\n"
            f"{state.get('opportunities', '')}\n\n"
            f"Customer: {state.get('customer_name', 'Unknown')}\n"
            f"Format each proposal with: recommendation, justification, next step."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["proposals"] = response.content
    return state


def create_expansion_scan_graph(checkpointer=None):
    """Create the Expansion Scan LangGraph workflow."""
    workflow = StateGraph(CustomerSuccessState)

    workflow.add_node("analyze_usage", _analyze_usage)
    workflow.add_node("identify_opportunities", _identify_opportunities)
    workflow.add_node("draft_proposals", _draft_proposals)

    workflow.set_entry_point("analyze_usage")
    workflow.add_edge("analyze_usage", "identify_opportunities")
    workflow.add_edge("identify_opportunities", "draft_proposals")
    workflow.add_edge("draft_proposals", END)

    return workflow.compile(checkpointer=checkpointer)
