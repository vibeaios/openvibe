"""Market Intelligence Operator state — shared across all 4 workflows."""

from __future__ import annotations

from typing import Any, TypedDict


class MarketIntelState(TypedDict, total=False):
    # --- Funnel Monitor ---
    funnel_metrics: dict[str, Any]
    anomalies: str
    funnel_brief: str

    # --- Deal Risk Forecast ---
    deals: list[dict[str, Any]]
    risk_model: str
    forecast: str
    forecast_report: str

    # --- Conversation Analysis ---
    transcripts: list[dict[str, Any]]
    patterns: str
    conversation_summary: str

    # --- NL Query ---
    question: str
    parsed_intent: str
    query_results: dict[str, Any]
    reasoning: str
    answer: str
