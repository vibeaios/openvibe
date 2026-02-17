"""Buyer Intelligence workflow — scan → analyze → brief.

New workflow (no existing graph to migrate).
3 nodes: 1 logic (scan) + 2 LLM (analyze, brief).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.revenue_ops.state import RevenueOpsState
from vibe_ai_ops.shared.config import load_prompt


def _scan(state: RevenueOpsState) -> RevenueOpsState:
    """Node 1 (logic): Scan for buyer signals from available data."""
    # In production, this pulls from CRM, social, news APIs
    # For now, aggregate what we know from state
    signals = state.get("signals", [])
    deals = state.get("active_deals", [])
    scores = state.get("recent_scores", [])

    # Combine into a signals summary
    state["signals"] = signals or [
        {"source": "deals", "count": len(deals), "data": deals[:5]},
        {"source": "scores", "count": len(scores), "data": scores[:5]},
    ]
    return state


def _analyze(state: RevenueOpsState) -> RevenueOpsState:
    """Node 2 (LLM): Analyze buyer signals for patterns and insights."""
    try:
        prompt = load_prompt("config/prompts/sales/s2_buyer_intelligence.md")
    except FileNotFoundError:
        prompt = "You are a buyer intelligence analyst."

    signals = state.get("signals", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze these buyer signals and identify patterns:\n\n"
            f"{json.dumps(signals, default=str)}\n\n"
            f"Focus on:\n"
            f"1. Emerging trends in buyer behavior\n"
            f"2. Signals that indicate high intent\n"
            f"3. Risks or concerns to watch\n"
            f"4. Actionable recommendations"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["analysis"] = response.content
    return state


def _brief(state: RevenueOpsState) -> RevenueOpsState:
    """Node 3 (LLM): Format analysis into a concise brief."""
    response = call_claude(
        system_prompt=(
            "You format intelligence analyses into concise executive briefs. "
            "Use bullet points. Max 200 words."
        ),
        user_message=(
            f"Format this analysis into a brief:\n\n"
            f"{state.get('analysis', '')}"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["brief"] = response.content
    return state


def create_buyer_intel_graph(checkpointer=None):
    """Create the Buyer Intelligence LangGraph workflow."""
    workflow = StateGraph(RevenueOpsState)

    workflow.add_node("scan", _scan)
    workflow.add_node("analyze", _analyze)
    workflow.add_node("brief", _brief)

    workflow.set_entry_point("scan")
    workflow.add_edge("scan", "analyze")
    workflow.add_edge("analyze", "brief")
    workflow.add_edge("brief", END)

    return workflow.compile(checkpointer=checkpointer)
