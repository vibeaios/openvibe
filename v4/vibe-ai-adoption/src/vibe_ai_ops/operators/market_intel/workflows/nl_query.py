"""NL Query workflow — parse_question → query_data → reason → respond.

Nodes: 1 logic (query_data) + 3 LLM (parse_question, reason, respond)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.market_intel.state import MarketIntelState
from vibe_ai_ops.shared.config import load_prompt


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _parse_question(state: MarketIntelState) -> MarketIntelState:
    """Node 1 (LLM): Parse natural language question into structured intent."""
    try:
        prompt = load_prompt("config/prompts/intelligence/nl_parser.md")
    except FileNotFoundError:
        prompt = (
            "You parse natural language business questions into structured "
            "intents. Identify what metric, entity, or comparison the user "
            "is asking about. Be precise and structured."
        )

    question = state.get("question", "")
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Parse this question into a structured intent:\n\n"
            f"\"{question}\"\n\n"
            "Return: what metric/data is needed, any filters (time range, "
            "segment, etc.), and the type of answer expected (number, "
            "comparison, trend, explanation)."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["parsed_intent"] = response.content
    return state


def _query_data(state: MarketIntelState) -> MarketIntelState:
    """Node 2 (logic): Simulate querying data based on parsed intent."""
    intent = state.get("parsed_intent", "")
    # In production, this would query a database or API.
    # For now, return whatever query_results are already in state,
    # or provide a stub result based on the intent.
    if "query_results" not in state or not state.get("query_results"):
        state["query_results"] = {
            "source": "simulated",
            "intent_received": intent[:200] if intent else "",
            "data": {},
            "note": "No live data source connected. Using stub results.",
        }
    return state


def _reason(state: MarketIntelState) -> MarketIntelState:
    """Node 3 (LLM): Reason over query results to form an answer."""
    try:
        prompt = load_prompt("config/prompts/intelligence/nl_reasoning.md")
    except FileNotFoundError:
        prompt = (
            "You are a data analyst who reasons over query results to "
            "answer business questions. You explain your reasoning step "
            "by step and note any caveats or limitations."
        )

    parsed_intent = state.get("parsed_intent", "")
    query_results = state.get("query_results", {})
    question = state.get("question", "")
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Original question: {question}\n\n"
            f"Parsed intent: {parsed_intent}\n\n"
            f"Query results: {query_results}\n\n"
            "Reason through the data to form an answer. Note any gaps "
            "or caveats in the data."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["reasoning"] = response.content
    return state


def _respond(state: MarketIntelState) -> MarketIntelState:
    """Node 4 (LLM): Generate user-friendly answer from reasoning."""
    try:
        prompt = load_prompt("config/prompts/intelligence/nl_respond.md")
    except FileNotFoundError:
        prompt = (
            "You write clear, direct answers to business questions. "
            "Lead with the answer, then provide supporting context. "
            "Keep it conversational but precise."
        )

    reasoning = state.get("reasoning", "")
    question = state.get("question", "")
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Question: {question}\n\n"
            f"Reasoning: {reasoning}\n\n"
            "Write a clear, direct answer. Lead with the bottom line. "
            "Keep it under 150 words."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["answer"] = response.content
    return state


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def create_nl_query_graph(checkpointer=None):
    """Create the NL Query LangGraph workflow.

    Graph: parse_question → query_data → reason → respond → END
    """
    workflow = StateGraph(MarketIntelState)

    workflow.add_node("parse_question", _parse_question)
    workflow.add_node("query_data", _query_data)
    workflow.add_node("reason", _reason)
    workflow.add_node("respond", _respond)

    workflow.set_entry_point("parse_question")
    workflow.add_edge("parse_question", "query_data")
    workflow.add_edge("query_data", "reason")
    workflow.add_edge("reason", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile(checkpointer=checkpointer)
