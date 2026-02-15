from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END


class ContentGenState(TypedDict, total=False):
    segment_id: str
    content_type: str  # blog_post, whitepaper, case_study
    winning_message: str
    research_notes: str
    outline: str
    draft: str
    final_content: str
    quality_score: int
    quality_notes: str


def _research(state: ContentGenState) -> ContentGenState:
    """Node 1: Research — gather data, stats, examples for the topic."""
    # Will be wired to CrewAI researcher agent
    return state


def _outline(state: ContentGenState) -> ContentGenState:
    """Node 2: Outline — structure the content based on research."""
    # Will be wired to content structuring logic
    return state


def _draft(state: ContentGenState) -> ContentGenState:
    """Node 3: Draft — write the full content piece."""
    # Will be wired to CrewAI writer agent
    return state


def _polish(state: ContentGenState) -> ContentGenState:
    """Node 4: Polish — edit, review, and finalize."""
    # Will be wired to CrewAI editor agent
    state["quality_score"] = state.get("quality_score", 0)
    return state


def create_content_gen_graph(checkpointer=None):
    """Create the M3 Content Generation LangGraph workflow."""
    workflow = StateGraph(ContentGenState)

    workflow.add_node("research", _research)
    workflow.add_node("outline", _outline)
    workflow.add_node("draft", _draft)
    workflow.add_node("polish", _polish)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "outline")
    workflow.add_edge("outline", "draft")
    workflow.add_edge("draft", "polish")
    workflow.add_edge("polish", END)

    return workflow.compile(checkpointer=checkpointer)
