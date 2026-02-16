"""Customer Success Operator state — used across all 6 workflows."""

from __future__ import annotations

from typing import Any, TypedDict


class CustomerSuccessState(TypedDict, total=False):
    # --- Shared ---
    customer_id: str
    customer_name: str

    # --- Onboarding ---
    onboarding_plan: str
    milestones: list[dict[str, Any]]
    welcome_sent: bool

    # --- Success Advisory ---
    accounts: list[dict[str, Any]]
    actions: str
    playbooks: str

    # --- Health Monitoring ---
    health_signals: list[dict[str, Any]]
    health_score: str
    risks: list[dict[str, Any]]

    # --- Expansion ---
    usage_data: dict[str, Any]
    opportunities: str
    proposals: str

    # --- Customer Voice ---
    feedback: list[dict[str, Any]]
    themes: str
    voice_report: str

    # --- Urgent Review ---
    situation: str
    deal_id: str
    reason: str
    recommendation: str
    alert_sent: bool
