from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from vibe_ai_ops.shared.models import AgentConfig
from vibe_ai_ops.shared.config import load_prompt
from vibe_ai_ops.crews.marketing.validation_agents import create_m1_crew, create_m4_crew
from vibe_ai_ops.crews.marketing.m3_content_generation import create_content_gen_crew


class ContentPipelineState(TypedDict, total=False):
    # Inputs
    segment_id: str
    content_type: str  # blog_post, whitepaper, case_study
    # M1 outputs
    segment_profile: dict[str, Any]
    messaging_hypotheses: list[str]
    winning_message: str
    # M3 outputs
    research_notes: str
    outline: str
    draft: str
    final_content: str
    quality_score: int
    quality_notes: str
    # M4 outputs
    repurposed_variants: list[dict[str, Any]]
    # Pipeline metadata
    pipeline_status: str


def _default_config(agent_id: str, prompt_file: str) -> AgentConfig:
    """Build a default AgentConfig for pipeline agents."""
    return AgentConfig(
        id=agent_id,
        name=agent_id,
        engine="marketing",
        tier="validation",
        trigger={"type": "on_demand"},
        output_channel="slack:#marketing-agents",
        prompt_file=prompt_file,
        temperature=0.7,
    )


# --- Crew kickoff helpers (mockable in tests) ---

def m1_kickoff(config: AgentConfig, prompt: str, segment_id: str) -> str:
    crew = create_m1_crew(config, system_prompt=prompt)
    result = crew.kickoff(inputs={"segment": segment_id})
    return str(result)


def m3_kickoff(config: AgentConfig, prompt: str, inputs: dict) -> str:
    crew = create_content_gen_crew(config, system_prompt=prompt)
    result = crew.kickoff(inputs=inputs)
    return str(result)


def m4_kickoff(config: AgentConfig, prompt: str, content: str) -> str:
    crew = create_m4_crew(config, system_prompt=prompt)
    result = crew.kickoff(inputs={"content": content})
    return str(result)


# --- Graph nodes ---

def _segment_research(state: ContentPipelineState) -> ContentPipelineState:
    """Node 1 (M1): Research the target segment and extract messaging hypotheses."""
    config = _default_config("m1", "marketing/m1_segment_research.md")
    try:
        prompt = load_prompt(config.prompt_file)
    except FileNotFoundError:
        prompt = "You are a market research specialist."

    segment_id = state.get("segment_id", "")
    raw = m1_kickoff(config, prompt, segment_id)

    try:
        profile = json.loads(raw)
        state["segment_profile"] = profile
        hypotheses = profile.get("messaging_hypotheses", [])
        state["messaging_hypotheses"] = hypotheses
        state["winning_message"] = hypotheses[0] if hypotheses else ""
    except (json.JSONDecodeError, TypeError):
        state["segment_profile"] = {"raw": raw[:500]}
        state["messaging_hypotheses"] = []
        state["winning_message"] = ""

    return state


def _content_generation(state: ContentPipelineState) -> ContentPipelineState:
    """Node 2 (M3): Generate full content piece using research and winning message."""
    config = _default_config("m3", "marketing/m3_content_generation.md")
    try:
        prompt = load_prompt(config.prompt_file)
    except FileNotFoundError:
        prompt = "You are a content creation specialist."

    inputs = {
        "content_type": state.get("content_type", "blog_post"),
        "segment": state.get("segment_id", ""),
        "winning_message": state.get("winning_message", ""),
    }
    raw = m3_kickoff(config, prompt, inputs)

    try:
        content = json.loads(raw)
        state["final_content"] = content.get("content", raw)
        state["quality_score"] = content.get("quality_score", 0)
        state["quality_notes"] = content.get("quality_notes", "")
    except (json.JSONDecodeError, TypeError):
        state["final_content"] = raw
        state["quality_score"] = 0
        state["quality_notes"] = "Failed to parse crew output"

    return state


def _content_repurposing(state: ContentPipelineState) -> ContentPipelineState:
    """Node 3 (M4): Repurpose the content into 10 format variants."""
    config = _default_config("m4", "marketing/m4_content_repurposing.md")
    try:
        prompt = load_prompt(config.prompt_file)
    except FileNotFoundError:
        prompt = "You are a content repurposing specialist."

    content = state.get("final_content", "")
    raw = m4_kickoff(config, prompt, content)

    try:
        variants = json.loads(raw)
        if isinstance(variants, list):
            state["repurposed_variants"] = variants
        else:
            state["repurposed_variants"] = [variants]
    except (json.JSONDecodeError, TypeError):
        state["repurposed_variants"] = [{"format": "raw", "content": raw[:500]}]

    state["pipeline_status"] = "complete"
    return state


def create_content_pipeline_graph(checkpointer=None):
    """Create the unified Content Pipeline LangGraph: M1 → M3 → M4."""
    workflow = StateGraph(ContentPipelineState)

    workflow.add_node("segment_research", _segment_research)
    workflow.add_node("content_generation", _content_generation)
    workflow.add_node("content_repurposing", _content_repurposing)

    workflow.set_entry_point("segment_research")
    workflow.add_edge("segment_research", "content_generation")
    workflow.add_edge("content_generation", "content_repurposing")
    workflow.add_edge("content_repurposing", END)

    return workflow.compile(checkpointer=checkpointer)
