"""Repurposing workflow — analyze_content → adapt_formats → finalize.

3 nodes: 2 logic (analyze_content, finalize) + 1 LLM (adapt_formats).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.content_engine.state import ContentEngineState
from vibe_ai_ops.shared.config import load_prompt


def _analyze_content(state: ContentEngineState) -> ContentEngineState:
    """Node 1 (logic): Analyze source content and determine target formats."""
    source = state.get("source_content", "")
    formats = state.get("content_formats", [])

    # Default formats if none specified
    if not formats:
        word_count = len(source.split())
        formats = ["social_post", "email_snippet"]
        if word_count > 200:
            formats.append("blog_summary")
        if word_count > 500:
            formats.append("newsletter_section")
        state["content_formats"] = formats

    return state


def _adapt_formats(state: ContentEngineState) -> ContentEngineState:
    """Node 2 (LLM): Adapt content into each target format."""
    try:
        prompt = load_prompt("config/prompts/marketing/m4_repurposing.md")
    except FileNotFoundError:
        prompt = (
            "You repurpose content across formats. Maintain the core message "
            "while adapting tone, length, and structure for each format."
        )

    source = state.get("source_content", "")
    formats = state.get("content_formats", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Repurpose this content into the following formats:\n\n"
            f"Source content:\n{source}\n\n"
            f"Target formats: {', '.join(formats)}\n\n"
            f"Return ONLY valid JSON with format names as keys:\n"
            f'{{"social_post": "...", "email_snippet": "...", ...}}'
        ),
        model="claude-haiku-4-5-20251001",
    )

    try:
        adapted = json.loads(response.content)
        state["adapted_content"] = adapted if isinstance(adapted, dict) else {}
    except (json.JSONDecodeError, TypeError):
        # Fallback: use raw response for all formats
        state["adapted_content"] = {fmt: response.content for fmt in formats}
    return state


def _finalize(state: ContentEngineState) -> ContentEngineState:
    """Node 3 (logic): Validate and finalize adapted content."""
    adapted = state.get("adapted_content", {})
    formats = state.get("content_formats", [])

    # Ensure all requested formats have content
    for fmt in formats:
        if fmt not in adapted or not adapted[fmt]:
            adapted[fmt] = f"[Content adaptation pending for {fmt}]"

    state["adapted_content"] = adapted
    return state


def create_repurposing_graph(checkpointer=None):
    """Create the Repurposing LangGraph workflow."""
    workflow = StateGraph(ContentEngineState)

    workflow.add_node("analyze_content", _analyze_content)
    workflow.add_node("adapt_formats", _adapt_formats)
    workflow.add_node("finalize", _finalize)

    workflow.set_entry_point("analyze_content")
    workflow.add_edge("analyze_content", "adapt_formats")
    workflow.add_edge("adapt_formats", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile(checkpointer=checkpointer)
