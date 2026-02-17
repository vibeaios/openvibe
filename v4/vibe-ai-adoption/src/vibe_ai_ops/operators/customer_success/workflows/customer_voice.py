"""Customer Voice workflow — collect_feedback → analyze_themes → report.

Nodes: 1 logic (collect_feedback) + 2 LLM (analyze_themes, report).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.customer_success.state import CustomerSuccessState
from vibe_ai_ops.shared.config import load_prompt


def _collect_feedback(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 1 (logic): Collect and aggregate customer feedback."""
    feedback = state.get("feedback", [])
    if not feedback:
        state["feedback"] = [
            {
                "source": "nps",
                "customer": state.get("customer_name", "Unknown"),
                "data": "No feedback collected yet",
            }
        ]
    return state


def _analyze_themes(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 2 (LLM): Analyze feedback for recurring themes and sentiment."""
    try:
        prompt = load_prompt("config/prompts/cs/c5_customer_voice.md")
    except FileNotFoundError:
        prompt = "You are a customer feedback analyst."

    feedback = state.get("feedback", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze this customer feedback for themes and patterns:\n\n"
            f"{json.dumps(feedback, default=str)}\n\n"
            f"Identify:\n"
            f"1. Top 3 recurring themes\n"
            f"2. Overall sentiment (positive / neutral / negative)\n"
            f"3. Actionable insights\n"
            f"4. Urgent issues requiring immediate attention"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["themes"] = response.content
    return state


def _report(state: CustomerSuccessState) -> CustomerSuccessState:
    """Node 3 (LLM): Generate a Voice of Customer report."""
    response = call_claude(
        system_prompt=(
            "You create concise Voice of Customer reports for leadership. "
            "Use bullet points. Include recommendations. Max 250 words."
        ),
        user_message=(
            f"Create a Voice of Customer report from this analysis:\n\n"
            f"Themes: {state.get('themes', '')}\n\n"
            f"Format as an executive summary with key findings and recommendations."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["voice_report"] = response.content
    return state


def create_customer_voice_graph(checkpointer=None):
    """Create the Customer Voice LangGraph workflow."""
    workflow = StateGraph(CustomerSuccessState)

    workflow.add_node("collect_feedback", _collect_feedback)
    workflow.add_node("analyze_themes", _analyze_themes)
    workflow.add_node("report", _report)

    workflow.set_entry_point("collect_feedback")
    workflow.add_edge("collect_feedback", "analyze_themes")
    workflow.add_edge("analyze_themes", "report")
    workflow.add_edge("report", END)

    return workflow.compile(checkpointer=checkpointer)
