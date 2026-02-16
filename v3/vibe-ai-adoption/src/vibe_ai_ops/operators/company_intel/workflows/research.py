"""Company Intelligence research workflow — replaces CrewAI with call_claude().

Graph: research → analyze → decide → report → END
Nodes: 2 LLM (research, analyze) + 2 logic (decide, report)
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph
try:
    from langfuse import observe
except ImportError:
    def observe(name: str = ""):  # noqa: ARG001
        """No-op decorator when langfuse is not installed."""
        def decorator(func):
            return func
        return decorator

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.company_intel.state import CompanyIntelState


# Re-export for backward compatibility
__all__ = ["CompanyIntelState", "create_company_intel_graph"]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


@observe(name="research-node")
def _research(state: CompanyIntelState) -> CompanyIntelState:
    """Node 1 (LLM): Research the company using Claude."""
    company_name = state.get("company_name", "Unknown")
    response = call_claude(
        system_prompt=(
            "You are a senior research analyst specializing in B2B company "
            "analysis. You focus on what the company does, their market "
            "position, size, technology, and recent developments."
        ),
        user_message=(
            f"Research the company: {company_name}\n\n"
            "Cover:\n"
            "1. What they do (core product/service)\n"
            "2. Industry and market position\n"
            "3. Approximate size (employees, revenue if public)\n"
            "4. Technology stack or technical focus\n"
            "5. Recent news or developments\n\n"
            "Be factual and concise. 200 words max."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["research"] = response.content
    return state


@observe(name="analyze-node")
def _analyze(state: CompanyIntelState) -> CompanyIntelState:
    """Node 2 (LLM): Analyze prospect quality using Claude."""
    company_name = state.get("company_name", "Unknown")
    research = state.get("research", "")
    response = call_claude(
        system_prompt=(
            "You evaluate companies for sales targeting. You assess "
            "prospect quality based on company size, growth signals, "
            "technology adoption, and likelihood of needing AI/automation "
            "solutions."
        ),
        user_message=(
            f"Based on this research about {company_name}:\n\n"
            f"{research}\n\n"
            "Analyze and return ONLY valid JSON (no markdown, no explanation):\n"
            '{"prospect_quality": "high|medium|low", '
            '"reasoning": "2-3 sentence explanation", '
            '"pain_points": ["point1", "point2"], '
            '"approach_angle": "suggested sales approach"}'
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["analysis"] = response.content
    return state


@observe(name="decide-node")
def _decide(state: CompanyIntelState) -> CompanyIntelState:
    """Node 3 (logic): Extract prospect quality from analysis."""
    analysis = state.get("analysis", "")
    try:
        parsed = json.loads(analysis)
        state["prospect_quality"] = parsed.get("prospect_quality", "medium")
    except (json.JSONDecodeError, TypeError):
        lower = analysis.lower()
        if "high" in lower:
            state["prospect_quality"] = "high"
        elif "low" in lower:
            state["prospect_quality"] = "low"
        else:
            state["prospect_quality"] = "medium"
    return state


@observe(name="report-node")
def _report(state: CompanyIntelState) -> CompanyIntelState:
    """Node 4 (logic): Format final report."""
    company = state.get("company_name", "Unknown")
    quality = state.get("prospect_quality", "unknown")
    research = state.get("research", "")
    analysis = state.get("analysis", "")

    state["report"] = (
        f"=== Company Intelligence Report ===\n"
        f"Company: {company}\n"
        f"Prospect Quality: {quality.upper()}\n"
        f"\n--- Research ---\n{research}\n"
        f"\n--- Analysis ---\n{analysis}\n"
    )
    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def create_company_intel_graph(checkpointer=None):
    """Create the Company Intelligence LangGraph workflow.

    Graph: research → analyze → decide → report → END
    """
    workflow = StateGraph(CompanyIntelState)

    workflow.add_node("research", _research)
    workflow.add_node("analyze", _analyze)
    workflow.add_node("decide", _decide)
    workflow.add_node("report", _report)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "analyze")
    workflow.add_edge("analyze", "decide")
    workflow.add_edge("decide", "report")
    workflow.add_edge("report", END)

    return workflow.compile(checkpointer=checkpointer)
