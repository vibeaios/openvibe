"""Journey Optimization workflow — collect_metrics → analyze_funnel → recommend.

3 nodes: 1 logic (collect_metrics) + 2 LLM (analyze_funnel, recommend).
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.content_engine.state import ContentEngineState
from vibe_ai_ops.shared.config import load_prompt


def _collect_metrics(state: ContentEngineState) -> ContentEngineState:
    """Node 1 (logic): Collect and normalize funnel metrics."""
    metrics = state.get("funnel_metrics", {})

    # Ensure standard funnel stages exist
    default_stages = ["awareness", "consideration", "decision", "purchase"]
    if "stages" not in metrics:
        metrics["stages"] = {stage: {"visitors": 0, "conversions": 0} for stage in default_stages}
    if "period" not in metrics:
        metrics["period"] = "last_30_days"

    # Calculate conversion rates per stage
    stages = metrics.get("stages", {})
    for stage_name, stage_data in stages.items():
        visitors = stage_data.get("visitors", 0)
        conversions = stage_data.get("conversions", 0)
        stage_data["conversion_rate"] = (
            round(conversions / visitors * 100, 1) if visitors > 0 else 0.0
        )

    state["funnel_metrics"] = metrics
    return state


def _analyze_funnel(state: ContentEngineState) -> ContentEngineState:
    """Node 2 (LLM): Analyze funnel metrics for drop-off points and opportunities."""
    try:
        prompt = load_prompt("config/prompts/marketing/m6_journey_optimization.md")
    except FileNotFoundError:
        prompt = (
            "You are a conversion funnel analyst. Identify drop-off points, "
            "bottlenecks, and opportunities to improve the buyer journey."
        )

    metrics = state.get("funnel_metrics", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Analyze this funnel data:\n\n"
            f"{json.dumps(metrics, default=str)}\n\n"
            f"Identify:\n"
            f"1. Biggest drop-off points\n"
            f"2. Conversion rate benchmarks vs actual\n"
            f"3. Content gaps in the journey\n"
            f"4. Quick wins for improvement"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["funnel_analysis"] = response.content
    return state


def _recommend(state: ContentEngineState) -> ContentEngineState:
    """Node 3 (LLM): Generate optimization recommendations."""
    analysis = state.get("funnel_analysis", "")
    response = call_claude(
        system_prompt=(
            "You create actionable optimization recommendations. "
            "Prioritize by impact and effort. Use clear, specific language."
        ),
        user_message=(
            f"Based on this funnel analysis, generate optimization recommendations:\n\n"
            f"{analysis}\n\n"
            f"For each recommendation:\n"
            f"- What to change\n"
            f"- Expected impact\n"
            f"- Effort level (low/medium/high)\n"
            f"- Priority (1-5)"
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["optimization_recommendations"] = response.content
    return state


def create_journey_optimization_graph(checkpointer=None):
    """Create the Journey Optimization LangGraph workflow."""
    workflow = StateGraph(ContentEngineState)

    workflow.add_node("collect_metrics", _collect_metrics)
    workflow.add_node("analyze_funnel", _analyze_funnel)
    workflow.add_node("recommend", _recommend)

    workflow.set_entry_point("collect_metrics")
    workflow.add_edge("collect_metrics", "analyze_funnel")
    workflow.add_edge("analyze_funnel", "recommend")
    workflow.add_edge("recommend", END)

    return workflow.compile(checkpointer=checkpointer)
