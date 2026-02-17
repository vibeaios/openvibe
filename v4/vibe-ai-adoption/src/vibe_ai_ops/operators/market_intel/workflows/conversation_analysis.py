"""Conversation Analysis workflow — pull_transcripts → extract_patterns → summarize.

Nodes: 1 logic (pull_transcripts) + 2 LLM (extract_patterns, summarize)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.market_intel.state import MarketIntelState
from vibe_ai_ops.shared.config import load_prompt


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _pull_transcripts(state: MarketIntelState) -> MarketIntelState:
    """Node 1 (logic): Normalize and prepare transcripts for analysis."""
    transcripts = state.get("transcripts", [])
    # Enrich each transcript with metadata
    for i, t in enumerate(transcripts):
        if "id" not in t:
            t["id"] = f"transcript-{i + 1}"
        if "word_count" not in t and "text" in t:
            t["word_count"] = len(t["text"].split())
    state["transcripts"] = transcripts
    return state


def _extract_patterns(state: MarketIntelState) -> MarketIntelState:
    """Node 2 (LLM): Extract patterns and themes from transcripts."""
    try:
        prompt = load_prompt("config/prompts/intelligence/conversation_patterns.md")
    except FileNotFoundError:
        prompt = (
            "You are a conversation intelligence analyst. You extract "
            "recurring themes, objections, buying signals, and competitive "
            "mentions from sales call transcripts."
        )

    transcripts = state.get("transcripts", [])
    # Build a condensed view for the LLM
    transcript_text = "\n\n---\n\n".join(
        f"[{t.get('id', 'unknown')}] {t.get('text', '')}" for t in transcripts
    )
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze these call transcripts:\n\n{transcript_text}\n\n"
            "Extract: top themes, common objections, buying signals, "
            "competitive mentions, and sentiment trends."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["patterns"] = response.content
    return state


def _summarize(state: MarketIntelState) -> MarketIntelState:
    """Node 3 (LLM): Summarize patterns into actionable intelligence."""
    try:
        prompt = load_prompt("config/prompts/intelligence/conversation_summary.md")
    except FileNotFoundError:
        prompt = (
            "You write concise intelligence summaries for sales leaders. "
            "Focus on what's actionable and what's changing."
        )

    patterns = state.get("patterns", "")
    transcript_count = len(state.get("transcripts", []))
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Based on analysis of {transcript_count} transcripts:\n\n"
            f"{patterns}\n\n"
            "Write a summary with: key findings, recommended actions, "
            "and trends to watch. Keep it under 300 words."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["conversation_summary"] = response.content
    return state


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def create_conversation_analysis_graph(checkpointer=None):
    """Create the Conversation Analysis LangGraph workflow.

    Graph: pull_transcripts → extract_patterns → summarize → END
    """
    workflow = StateGraph(MarketIntelState)

    workflow.add_node("pull_transcripts", _pull_transcripts)
    workflow.add_node("extract_patterns", _extract_patterns)
    workflow.add_node("summarize", _summarize)

    workflow.set_entry_point("pull_transcripts")
    workflow.add_edge("pull_transcripts", "extract_patterns")
    workflow.add_edge("extract_patterns", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile(checkpointer=checkpointer)
