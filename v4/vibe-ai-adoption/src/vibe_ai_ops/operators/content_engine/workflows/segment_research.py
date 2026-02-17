"""Segment Research workflow — gather_data → analyze_segments → report.

3 nodes: 1 logic (gather_data) + 2 LLM (analyze_segments, report).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.content_engine.state import ContentEngineState
from vibe_ai_ops.shared.config import load_prompt


def _gather_data(state: ContentEngineState) -> ContentEngineState:
    """Node 1 (logic): Gather and normalize segment data."""
    segments = state.get("segment_data", [])
    # Ensure each segment has required fields
    normalized = []
    for seg in segments:
        normalized.append({
            "name": seg.get("name", "unknown"),
            "size": seg.get("size", 0),
            "characteristics": seg.get("characteristics", []),
            **{k: v for k, v in seg.items() if k not in ("name", "size", "characteristics")},
        })
    state["segment_data"] = normalized
    return state


def _analyze_segments(state: ContentEngineState) -> ContentEngineState:
    """Node 2 (LLM): Analyze segment data for content opportunities."""
    try:
        prompt = load_prompt("config/prompts/marketing/m1_segment_research.md")
    except FileNotFoundError:
        prompt = (
            "You are a market segmentation analyst. Identify content opportunities "
            "and messaging strategies for each audience segment."
        )

    segments = state.get("segment_data", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze these audience segments and identify content opportunities:\n\n"
            f"{json.dumps(segments, default=str)}\n\n"
            f"For each segment, provide:\n"
            f"1. Key pain points\n"
            f"2. Content themes that resonate\n"
            f"3. Preferred content formats\n"
            f"4. Messaging tone and approach"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["segment_analysis"] = response.content
    return state


def _report(state: ContentEngineState) -> ContentEngineState:
    """Node 3 (LLM): Generate a structured segment research report."""
    response = call_claude(
        system_prompt=(
            "You create concise, actionable segment research reports. "
            "Use clear headings and bullet points. Max 300 words."
        ),
        user_message=(
            f"Create a segment research report from this analysis:\n\n"
            f"{state.get('segment_analysis', '')}\n\n"
            f"Include: executive summary, per-segment recommendations, "
            f"and priority actions."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["segment_report"] = response.content
    return state


def create_segment_research_graph(checkpointer=None):
    """Create the Segment Research LangGraph workflow."""
    workflow = StateGraph(ContentEngineState)

    workflow.add_node("gather_data", _gather_data)
    workflow.add_node("analyze_segments", _analyze_segments)
    workflow.add_node("report", _report)

    workflow.set_entry_point("gather_data")
    workflow.add_edge("gather_data", "analyze_segments")
    workflow.add_edge("analyze_segments", "report")
    workflow.add_edge("report", END)

    return workflow.compile(checkpointer=checkpointer)
