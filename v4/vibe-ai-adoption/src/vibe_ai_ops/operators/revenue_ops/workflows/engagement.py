"""Engagement workflow — research_buyer → generate_sequence → personalize → format.

Migrated from graphs/sales/s3_engagement.py (was stub).
3 LLM nodes replace the 3-agent CrewAI crew (Buyer Researcher → Outreach Copywriter → Engagement Strategist).
"""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.revenue_ops.state import RevenueOpsState
from vibe_ai_ops.shared.config import load_prompt


def _research_buyer(state: RevenueOpsState) -> RevenueOpsState:
    """Node 1 (LLM): Deep research on the buyer for personalization."""
    try:
        prompt = load_prompt("config/prompts/sales/s3_engagement.md")
    except FileNotFoundError:
        prompt = "You are a buyer research specialist."

    buyer_profile = state.get("buyer_profile", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Research this buyer for personalized outreach:\n\n"
            f"Profile: {json.dumps(buyer_profile)}\n"
            f"Segment: {state.get('segment', 'unknown')}\n\n"
            f"Produce detailed research notes covering:\n"
            f"1. Company context and challenges\n"
            f"2. Buyer's likely priorities\n"
            f"3. Relevant talking points\n"
            f"4. Personalization hooks"
        ),
        model="claude-sonnet-4-5-20250929",
    )
    state["research_notes"] = response.content
    return state


def _generate_sequence(state: RevenueOpsState) -> RevenueOpsState:
    """Node 2 (LLM): Generate multi-touch outreach sequence."""
    try:
        prompt = load_prompt("config/prompts/sales/s3_engagement.md")
    except FileNotFoundError:
        prompt = "You are an outreach copywriter."

    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Generate a 3-touch outreach sequence based on this research:\n\n"
            f"{state.get('research_notes', '')}\n\n"
            f"Return ONLY valid JSON array of touches:\n"
            f"[{{\"touch\": 1, \"channel\": \"email|linkedin|phone\", "
            f"\"subject\": \"...\", \"body\": \"...\", \"wait_days\": N}}]"
        ),
        model="claude-sonnet-4-5-20250929",
    )
    try:
        state["outreach_sequence"] = json.loads(response.content)
    except (json.JSONDecodeError, TypeError):
        state["outreach_sequence"] = [
            {"touch": 1, "channel": "email", "subject": "Introduction",
             "body": response.content[:500], "wait_days": 0},
        ]
    return state


def _personalize(state: RevenueOpsState) -> RevenueOpsState:
    """Node 3 (LLM): Personalize each touch with research insights."""
    sequence = state.get("outreach_sequence", [])
    research = state.get("research_notes", "")

    response = call_claude(
        system_prompt=(
            "You personalize outreach messages using buyer research. "
            "Keep the core message but add specific, relevant details."
        ),
        user_message=(
            f"Personalize this outreach sequence using the research:\n\n"
            f"Research: {research}\n\n"
            f"Sequence: {json.dumps(sequence)}\n\n"
            f"Return the same JSON array but with personalized body text."
        ),
        model="claude-haiku-4-5-20251001",
    )
    try:
        state["personalized_sequence"] = json.loads(response.content)
    except (json.JSONDecodeError, TypeError):
        state["personalized_sequence"] = sequence
    return state


def _format(state: RevenueOpsState) -> RevenueOpsState:
    """Node 4 (logic): Format final engagement plan."""
    state["final_plan"] = {
        "contact_id": state.get("contact_id", ""),
        "segment": state.get("segment", ""),
        "sequence": state.get("personalized_sequence", []),
        "status": "ready",
    }
    return state


def create_engagement_graph(checkpointer=None):
    """Create the Engagement LangGraph workflow."""
    workflow = StateGraph(RevenueOpsState)

    workflow.add_node("research_buyer", _research_buyer)
    workflow.add_node("generate_sequence", _generate_sequence)
    workflow.add_node("personalize", _personalize)
    workflow.add_node("format", _format)

    workflow.set_entry_point("research_buyer")
    workflow.add_edge("research_buyer", "generate_sequence")
    workflow.add_edge("generate_sequence", "personalize")
    workflow.add_edge("personalize", "format")
    workflow.add_edge("format", END)

    return workflow.compile(checkpointer=checkpointer)
