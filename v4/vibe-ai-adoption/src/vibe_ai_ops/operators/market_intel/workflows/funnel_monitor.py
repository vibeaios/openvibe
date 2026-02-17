"""Funnel Monitor workflow — pull_metrics → detect_anomalies → brief.

Nodes: 1 logic (pull_metrics) + 2 LLM (detect_anomalies, brief)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.market_intel.state import MarketIntelState
from vibe_ai_ops.shared.config import load_prompt


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _pull_metrics(state: MarketIntelState) -> MarketIntelState:
    """Node 1 (logic): Extract and normalize funnel metrics from state."""
    metrics = state.get("funnel_metrics", {})
    # Ensure metrics has basic structure — enrich with computed ratios
    if metrics:
        leads = metrics.get("leads", 0)
        mqls = metrics.get("mqls", 0)
        sqls = metrics.get("sqls", 0)
        deals = metrics.get("deals", 0)

        if leads > 0:
            metrics["lead_to_mql_rate"] = round(mqls / leads * 100, 1)
        if mqls > 0:
            metrics["mql_to_sql_rate"] = round(sqls / mqls * 100, 1)
        if sqls > 0:
            metrics["sql_to_deal_rate"] = round(deals / sqls * 100, 1)

        state["funnel_metrics"] = metrics
    return state


def _detect_anomalies(state: MarketIntelState) -> MarketIntelState:
    """Node 2 (LLM): Detect anomalies in funnel metrics using Claude."""
    try:
        prompt = load_prompt("config/prompts/intelligence/funnel_monitor.md")
    except FileNotFoundError:
        prompt = (
            "You are a marketing analytics expert. You detect anomalies "
            "and unusual patterns in sales funnel metrics."
        )

    metrics = state.get("funnel_metrics", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze these funnel metrics for anomalies:\n\n{metrics}\n\n"
            "Identify any concerning drops, unusual ratios, or trends that "
            "need attention. Be specific about what looks off and why."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["anomalies"] = response.content
    return state


def _brief(state: MarketIntelState) -> MarketIntelState:
    """Node 3 (LLM): Generate executive brief from anomaly analysis."""
    try:
        prompt = load_prompt("config/prompts/intelligence/funnel_brief.md")
    except FileNotFoundError:
        prompt = (
            "You are a concise executive briefing writer. You summarize "
            "funnel health and anomalies into actionable briefs."
        )

    anomalies = state.get("anomalies", "")
    metrics = state.get("funnel_metrics", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Metrics: {metrics}\n\nAnomalies found: {anomalies}\n\n"
            "Write a 3-5 sentence executive brief on funnel health. "
            "Lead with the most important finding."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["funnel_brief"] = response.content
    return state


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def create_funnel_monitor_graph(checkpointer=None):
    """Create the Funnel Monitor LangGraph workflow.

    Graph: pull_metrics → detect_anomalies → brief → END
    """
    workflow = StateGraph(MarketIntelState)

    workflow.add_node("pull_metrics", _pull_metrics)
    workflow.add_node("detect_anomalies", _detect_anomalies)
    workflow.add_node("brief", _brief)

    workflow.set_entry_point("pull_metrics")
    workflow.add_edge("pull_metrics", "detect_anomalies")
    workflow.add_edge("detect_anomalies", "brief")
    workflow.add_edge("brief", END)

    return workflow.compile(checkpointer=checkpointer)
