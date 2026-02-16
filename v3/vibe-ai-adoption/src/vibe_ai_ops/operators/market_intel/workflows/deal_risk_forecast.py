"""Deal Risk Forecast workflow — pull_deals → model_risk → forecast → report.

Nodes: 1 logic (pull_deals) + 3 LLM (model_risk, forecast, report)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.market_intel.state import MarketIntelState
from vibe_ai_ops.shared.config import load_prompt


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _pull_deals(state: MarketIntelState) -> MarketIntelState:
    """Node 1 (logic): Normalize and enrich deal data from state."""
    deals = state.get("deals", [])
    # Add computed fields for each deal
    for deal in deals:
        stage = deal.get("stage", "unknown")
        amount = deal.get("amount", 0)
        days_in_stage = deal.get("days_in_stage", 0)

        # Flag stale deals (>30 days in same stage)
        deal["is_stale"] = days_in_stage > 30
        # Weighted value by stage
        stage_weights = {
            "discovery": 0.1,
            "proposal": 0.3,
            "negotiation": 0.6,
            "closing": 0.8,
        }
        deal["weighted_value"] = round(
            amount * stage_weights.get(stage, 0.1), 2
        )

    state["deals"] = deals
    return state


def _model_risk(state: MarketIntelState) -> MarketIntelState:
    """Node 2 (LLM): Model risk factors for each deal."""
    try:
        prompt = load_prompt("config/prompts/intelligence/deal_risk.md")
    except FileNotFoundError:
        prompt = (
            "You are a sales risk analyst. You assess pipeline deals for "
            "risk factors including stagnation, competitor threats, budget "
            "concerns, and stakeholder changes."
        )

    deals = state.get("deals", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Assess risk for these deals:\n\n{deals}\n\n"
            "For each deal, identify: risk level (high/medium/low), "
            "key risk factors, and recommended actions."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["risk_model"] = response.content
    return state


def _forecast(state: MarketIntelState) -> MarketIntelState:
    """Node 3 (LLM): Generate revenue forecast based on risk model."""
    try:
        prompt = load_prompt("config/prompts/intelligence/deal_forecast.md")
    except FileNotFoundError:
        prompt = (
            "You are a revenue forecasting specialist. You project likely "
            "outcomes based on deal risk assessments and pipeline data."
        )

    risk_model = state.get("risk_model", "")
    deals = state.get("deals", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Based on this risk assessment:\n\n{risk_model}\n\n"
            f"And these deals:\n\n{deals}\n\n"
            "Provide a revenue forecast: best case, expected, and worst case. "
            "Include confidence levels and key assumptions."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["forecast"] = response.content
    return state


def _report(state: MarketIntelState) -> MarketIntelState:
    """Node 4 (LLM): Produce final forecast report for leadership."""
    try:
        prompt = load_prompt("config/prompts/intelligence/forecast_report.md")
    except FileNotFoundError:
        prompt = (
            "You write clear, concise executive reports on pipeline health "
            "and revenue forecasts. You lead with the bottom line."
        )

    forecast = state.get("forecast", "")
    risk_model = state.get("risk_model", "")
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Risk assessment:\n{risk_model}\n\n"
            f"Forecast:\n{forecast}\n\n"
            "Write a 1-page executive report. Start with the headline number, "
            "then risks, then recommended actions."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["forecast_report"] = response.content
    return state


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def create_deal_risk_forecast_graph(checkpointer=None):
    """Create the Deal Risk Forecast LangGraph workflow.

    Graph: pull_deals → model_risk → forecast → report → END
    """
    workflow = StateGraph(MarketIntelState)

    workflow.add_node("pull_deals", _pull_deals)
    workflow.add_node("model_risk", _model_risk)
    workflow.add_node("forecast", _forecast)
    workflow.add_node("report", _report)

    workflow.set_entry_point("pull_deals")
    workflow.add_edge("pull_deals", "model_risk")
    workflow.add_edge("model_risk", "forecast")
    workflow.add_edge("forecast", "report")
    workflow.add_edge("report", END)

    return workflow.compile(checkpointer=checkpointer)
