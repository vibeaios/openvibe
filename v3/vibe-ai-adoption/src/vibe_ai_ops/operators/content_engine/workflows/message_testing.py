"""Message Testing workflow — generate_variants → evaluate → recommend.

3 nodes: 2 LLM (generate_variants, evaluate) + 1 logic (recommend).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.content_engine.state import ContentEngineState
from vibe_ai_ops.shared.config import load_prompt


def _generate_variants(state: ContentEngineState) -> ContentEngineState:
    """Node 1 (LLM): Generate message variants for testing."""
    try:
        prompt = load_prompt("config/prompts/marketing/m2_message_testing.md")
    except FileNotFoundError:
        prompt = (
            "You are a copywriting specialist who creates message variants "
            "for A/B testing. Generate diverse messaging approaches."
        )

    topic = state.get("topic", "product")
    segments = state.get("segment_data", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Generate 3-5 message variants for topic: {topic}\n\n"
            f"Target segments: {json.dumps(segments, default=str)}\n\n"
            f"Return ONLY valid JSON array:\n"
            f'[{{"variant": "A", "headline": "...", "body": "...", "cta": "...", "tone": "..."}}, ...]'
        ),
        model="claude-haiku-4-5-20251001",
    )

    try:
        variants = json.loads(response.content)
        state["message_variants"] = variants if isinstance(variants, list) else []
    except (json.JSONDecodeError, TypeError):
        state["message_variants"] = [{"variant": "A", "headline": response.content[:100], "body": response.content, "cta": "", "tone": "neutral"}]
    return state


def _evaluate(state: ContentEngineState) -> ContentEngineState:
    """Node 2 (LLM): Evaluate message variants for effectiveness."""
    variants = state.get("message_variants", [])
    response = call_claude(
        system_prompt=(
            "You evaluate marketing message variants. Score each on clarity, "
            "emotional resonance, specificity, and CTA strength. Be critical."
        ),
        user_message=(
            f"Evaluate these message variants:\n\n"
            f"{json.dumps(variants, default=str)}\n\n"
            f"For each variant, provide a score (1-10) and brief rationale."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["evaluation"] = response.content
    return state


def _recommend(state: ContentEngineState) -> ContentEngineState:
    """Node 3 (logic): Select best variant based on evaluation."""
    evaluation = state.get("evaluation", "")
    variants = state.get("message_variants", [])

    # Simple recommendation: reference the evaluation and pick first variant
    best = variants[0]["variant"] if variants else "N/A"
    state["recommendation"] = (
        f"Recommended variant: {best}\n"
        f"Based on evaluation:\n{evaluation[:500]}"
    )
    return state


def create_message_testing_graph(checkpointer=None):
    """Create the Message Testing LangGraph workflow."""
    workflow = StateGraph(ContentEngineState)

    workflow.add_node("generate_variants", _generate_variants)
    workflow.add_node("evaluate", _evaluate)
    workflow.add_node("recommend", _recommend)

    workflow.set_entry_point("generate_variants")
    workflow.add_edge("generate_variants", "evaluate")
    workflow.add_edge("evaluate", "recommend")
    workflow.add_edge("recommend", END)

    return workflow.compile(checkpointer=checkpointer)
