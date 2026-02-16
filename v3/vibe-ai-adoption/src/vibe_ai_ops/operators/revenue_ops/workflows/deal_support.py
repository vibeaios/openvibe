"""Deal Support workflow — pull_deals → assess_risk → generate_actions.

New workflow (no existing graph to migrate).
3 nodes: 1 logic (pull_deals) + 2 LLM (assess_risk, generate_actions).
"""

from __future__ import annotations

import json
import os

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.revenue_ops.state import RevenueOpsState
from vibe_ai_ops.shared.config import load_prompt
from vibe_ai_ops.shared.hubspot_client import HubSpotClient

# Module-level client — lazy init, mockable in tests
hubspot_client: HubSpotClient | None = None


def _get_hubspot() -> HubSpotClient:
    global hubspot_client
    if hubspot_client is None:
        hubspot_client = HubSpotClient(api_key=os.environ.get("HUBSPOT_API_KEY"))
    return hubspot_client


def _pull_deals(state: RevenueOpsState) -> RevenueOpsState:
    """Node 1 (logic): Pull active deals from HubSpot."""
    hs = _get_hubspot()
    state["active_deals"] = hs.get_active_deals(limit=50)
    return state


def _assess_risk(state: RevenueOpsState) -> RevenueOpsState:
    """Node 2 (LLM): Assess risk across active deals."""
    try:
        prompt = load_prompt("config/prompts/sales/s4_deal_support.md")
    except FileNotFoundError:
        prompt = "You are a deal risk analyst."

    deals = state.get("active_deals", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Assess risk for these active deals:\n\n"
            f"{json.dumps(deals[:20], default=str)}\n\n"
            f"For each deal, identify:\n"
            f"1. Risk level (high/medium/low)\n"
            f"2. Key risk factors\n"
            f"3. Stalled or slipping indicators\n\n"
            f"Return a concise risk assessment."
        ),
        model="claude-sonnet-4-5-20250929",
    )
    state["risk_assessment"] = response.content
    return state


def _generate_actions(state: RevenueOpsState) -> RevenueOpsState:
    """Node 3 (LLM): Generate recommended actions for at-risk deals."""
    response = call_claude(
        system_prompt=(
            "You generate actionable recommendations for sales teams. "
            "Be specific and prioritized. Max 300 words."
        ),
        user_message=(
            f"Based on this risk assessment, generate recommended actions:\n\n"
            f"{state.get('risk_assessment', '')}\n\n"
            f"For each high-risk deal, provide:\n"
            f"1. Immediate action (today)\n"
            f"2. Follow-up action (this week)\n"
            f"3. Escalation criteria"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["actions"] = response.content
    return state


def create_deal_support_graph(checkpointer=None):
    """Create the Deal Support LangGraph workflow."""
    workflow = StateGraph(RevenueOpsState)

    workflow.add_node("pull_deals", _pull_deals)
    workflow.add_node("assess_risk", _assess_risk)
    workflow.add_node("generate_actions", _generate_actions)

    workflow.set_entry_point("pull_deals")
    workflow.add_edge("pull_deals", "assess_risk")
    workflow.add_edge("assess_risk", "generate_actions")
    workflow.add_edge("generate_actions", END)

    return workflow.compile(checkpointer=checkpointer)
