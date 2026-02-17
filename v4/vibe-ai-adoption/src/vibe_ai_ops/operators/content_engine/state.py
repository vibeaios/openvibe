"""Content Engine Operator state — used across all 6 workflows."""

from __future__ import annotations

from typing import Any, TypedDict


class ContentEngineState(TypedDict, total=False):
    # --- Segment Research ---
    segment_data: list[dict[str, Any]]
    segment_analysis: str
    segment_report: str

    # --- Message Testing ---
    message_variants: list[dict[str, Any]]
    evaluation: str
    recommendation: str

    # --- Content Generation ---
    topic: str
    research: str
    draft: str
    polished_content: str

    # --- Repurposing ---
    source_content: str
    content_formats: list[str]
    adapted_content: dict[str, str]

    # --- Distribution ---
    channels: list[str]
    schedule: list[dict[str, Any]]
    distribution_report: str

    # --- Journey Optimization ---
    funnel_metrics: dict[str, Any]
    funnel_analysis: str
    optimization_recommendations: str
