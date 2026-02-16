"""Company Intelligence Operator — demo of the full 3-layer stack.

Operator pattern:
  Temporal (trigger) → LangGraph (workflow) → CrewAI (agents) → Claude

This operator takes a company name and produces a research brief
by running a 4-node LangGraph graph where 2 nodes use CrewAI agents.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

from crewai import Agent, Crew, Task, Process
from langgraph.graph import StateGraph, END
from langfuse import observe


# ---------------------------------------------------------------------------
# 1. State — what the Operator remembers across nodes
# ---------------------------------------------------------------------------

class CompanyIntelState(TypedDict, total=False):
    company_name: str
    research: str       # raw research output from CrewAI
    analysis: str       # strategic analysis from CrewAI
    prospect_quality: str  # high / medium / low
    report: str         # formatted final output
    completed: bool


# ---------------------------------------------------------------------------
# 2. CrewAI helpers — assemble temporary agents on demand
# ---------------------------------------------------------------------------

def _create_researcher_crew(company_name: str) -> Crew:
    """Assemble a researcher agent, give it a task, return a Crew."""
    agent = Agent(
        role="Company Research Analyst",
        goal="Produce a comprehensive but concise company brief",
        backstory=(
            "You are a senior research analyst specializing in B2B company "
            "analysis. You focus on what the company does, their market "
            "position, size, technology, and recent developments."
        ),
        llm="anthropic/claude-haiku-4-5-20251001",
        verbose=False,
    )

    task = Task(
        description=(
            "Research the company: {company_name}\n\n"
            "Cover:\n"
            "1. What they do (core product/service)\n"
            "2. Industry and market position\n"
            "3. Approximate size (employees, revenue if public)\n"
            "4. Technology stack or technical focus\n"
            "5. Recent news or developments\n\n"
            "Be factual and concise. 200 words max."
        ),
        expected_output="A concise company research brief",
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )


def _create_analyst_crew(company_name: str) -> Crew:
    """Assemble a strategic analyst agent."""
    agent = Agent(
        role="Strategic Sales Analyst",
        goal="Determine if this company is a good sales prospect",
        backstory=(
            "You evaluate companies for sales targeting. You assess "
            "prospect quality based on company size, growth signals, "
            "technology adoption, and likelihood of needing AI/automation "
            "solutions."
        ),
        llm="anthropic/claude-haiku-4-5-20251001",
        verbose=False,
    )

    task = Task(
        description=(
            "Based on this research about {company_name}:\n\n"
            "{research}\n\n"
            "Analyze and return ONLY valid JSON (no markdown, no explanation):\n"
            '{{"prospect_quality": "high|medium|low", '
            '"reasoning": "2-3 sentence explanation", '
            '"pain_points": ["point1", "point2"], '
            '"approach_angle": "suggested sales approach"}}'
        ),
        expected_output="JSON with prospect_quality, reasoning, pain_points, approach_angle",
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )


# ---------------------------------------------------------------------------
# 3. LangGraph nodes — each node is one step in the workflow
# ---------------------------------------------------------------------------

@observe(name="research-node")
def _research(state: CompanyIntelState) -> CompanyIntelState:
    """Node 1: Research the company using CrewAI researcher agent."""
    company_name = state.get("company_name", "Unknown")
    crew = _create_researcher_crew(company_name)
    result = crew.kickoff(inputs={"company_name": company_name})
    state["research"] = str(result)
    return state


@observe(name="analyze-node")
def _analyze(state: CompanyIntelState) -> CompanyIntelState:
    """Node 2: Analyze prospect quality using CrewAI analyst agent."""
    company_name = state.get("company_name", "Unknown")
    research = state.get("research", "")
    crew = _create_analyst_crew(company_name)
    result = crew.kickoff(inputs={
        "company_name": company_name,
        "research": research,
    })
    state["analysis"] = str(result)
    return state


@observe(name="decide-node")
def _decide(state: CompanyIntelState) -> CompanyIntelState:
    """Node 3: Extract prospect quality from analysis (pure logic, no AI)."""
    analysis = state.get("analysis", "")

    # Try to parse JSON from the analysis
    try:
        parsed = json.loads(analysis)
        state["prospect_quality"] = parsed.get("prospect_quality", "medium")
    except (json.JSONDecodeError, TypeError):
        # Fallback: look for keywords
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
    """Node 4: Format final report (pure logic, no AI)."""
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
# 4. Graph factory — build the LangGraph workflow
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
