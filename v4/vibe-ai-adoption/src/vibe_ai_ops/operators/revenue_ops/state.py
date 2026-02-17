"""Revenue Operations shared state — used across all 5 workflows."""

from __future__ import annotations

from typing import Any, TypedDict


class RevenueOpsState(TypedDict, total=False):
    # --- Shared across workflows ---
    pipeline_total: float
    pipeline_by_stage: dict[str, float]
    active_deals: list[dict[str, Any]]
    deals_at_risk: list[dict[str, Any]]
    recent_scores: list[dict[str, Any]]

    # --- Lead Qualification ---
    contact_id: str
    source: str
    enriched_data: dict[str, Any]
    score: dict[str, Any] | None
    route: str | None
    crm_updated: bool

    # --- Engagement ---
    buyer_profile: dict[str, Any]
    segment: str
    research_notes: str
    outreach_sequence: list[dict[str, Any]]
    personalized_sequence: list[dict[str, Any]]
    final_plan: dict[str, Any]

    # --- Nurture ---
    lead_data: dict[str, Any]
    lead_score: int
    current_stage: str
    touches_completed: int
    max_touches: int
    touch_interval_days: int
    touch_content: str
    touch_channel: str
    escalation_reason: str
    touch_history: list[dict[str, Any]]

    # --- Buyer Intelligence ---
    signals: list[dict[str, Any]]
    analysis: str
    brief: str

    # --- Deal Support ---
    risk_assessment: str
    actions: str
