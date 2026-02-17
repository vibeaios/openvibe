"""Content Generation workflow — research → draft → polish.

3 nodes: all LLM (research, draft, polish).
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.content_engine.state import ContentEngineState
from vibe_ai_ops.shared.config import load_prompt


def _research(state: ContentEngineState) -> ContentEngineState:
    """Node 1 (LLM): Research the topic for content creation."""
    try:
        prompt = load_prompt("config/prompts/marketing/m3_content_generation.md")
    except FileNotFoundError:
        prompt = (
            "You are a content researcher. Gather key facts, statistics, "
            "and angles for creating compelling content."
        )

    topic = state.get("topic", "")
    segment_analysis = state.get("segment_analysis", "")
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Research this topic for content creation: {topic}\n\n"
            f"Audience context:\n{segment_analysis}\n\n"
            f"Provide:\n"
            f"1. Key facts and data points\n"
            f"2. Expert perspectives\n"
            f"3. Common objections to address\n"
            f"4. Unique angles to explore"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["research"] = response.content
    return state


def _draft(state: ContentEngineState) -> ContentEngineState:
    """Node 2 (LLM): Draft content based on research."""
    topic = state.get("topic", "")
    research = state.get("research", "")
    response = call_claude(
        system_prompt=(
            "You are an expert content writer. Create engaging, well-structured "
            "content based on provided research. Write in a clear, authoritative tone."
        ),
        user_message=(
            f"Write a draft article on: {topic}\n\n"
            f"Based on this research:\n{research}\n\n"
            f"Requirements:\n"
            f"- Compelling headline\n"
            f"- Clear structure with subheadings\n"
            f"- Actionable takeaways\n"
            f"- 500-800 words"
        ),
        model="claude-sonnet-4-5-20250929",
    )
    state["draft"] = response.content
    return state


def _polish(state: ContentEngineState) -> ContentEngineState:
    """Node 3 (LLM): Polish and finalize the draft."""
    draft = state.get("draft", "")
    response = call_claude(
        system_prompt=(
            "You are an editor who polishes content for publication. "
            "Fix grammar, improve flow, sharpen the hook, and ensure "
            "the CTA is clear. Preserve the author's voice."
        ),
        user_message=(
            f"Polish this draft for publication:\n\n{draft}\n\n"
            f"Focus on:\n"
            f"1. Hook strength\n"
            f"2. Paragraph flow\n"
            f"3. Jargon reduction\n"
            f"4. CTA clarity"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["polished_content"] = response.content
    return state


def create_content_generation_graph(checkpointer=None):
    """Create the Content Generation LangGraph workflow."""
    workflow = StateGraph(ContentEngineState)

    workflow.add_node("research", _research)
    workflow.add_node("draft", _draft)
    workflow.add_node("polish", _polish)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "draft")
    workflow.add_edge("draft", "polish")
    workflow.add_edge("polish", END)

    return workflow.compile(checkpointer=checkpointer)
