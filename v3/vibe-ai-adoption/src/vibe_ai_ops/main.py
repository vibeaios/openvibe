from __future__ import annotations

from typing import Any, Callable

from crewai import Crew

from vibe_ai_ops.shared.config import load_agent_configs, load_prompt
from vibe_ai_ops.shared.models import AgentConfig
from vibe_ai_ops.shared.tracing import init_tracing
from vibe_ai_ops.temporal.schedules import build_schedule_specs

# --- Deep-dive crew factories ---
from vibe_ai_ops.crews.sales.s1_lead_qualification import create_lead_qual_crew
from vibe_ai_ops.crews.sales.s3_engagement import create_engagement_crew
from vibe_ai_ops.crews.marketing.m3_content_generation import create_content_gen_crew

# --- Validation crew registries ---
from vibe_ai_ops.crews.marketing.validation_agents import MARKETING_CREW_REGISTRY
from vibe_ai_ops.crews.sales.validation_agents import SALES_CREW_REGISTRY
from vibe_ai_ops.crews.cs.validation_agents import CS_CREW_REGISTRY
from vibe_ai_ops.crews.intelligence.validation_agents import INTELLIGENCE_CREW_REGISTRY

# Unified registry: agent_id → crew factory function
# All 20 agents: 3 deep-dive + 17 validation
CREW_REGISTRY: dict[str, Callable[[AgentConfig, str], Crew]] = {
    # Deep-dive agents
    "s1": create_lead_qual_crew,
    "s3": create_engagement_crew,
    "m3": create_content_gen_crew,
    # Validation agents (from engine registries)
    **MARKETING_CREW_REGISTRY,
    **SALES_CREW_REGISTRY,
    **CS_CREW_REGISTRY,
    **INTELLIGENCE_CREW_REGISTRY,
}


def build_system(
    config_path: str = "config/agents.yaml",
    prompts_dir: str = "config/prompts",
) -> dict[str, Any]:
    """Build the complete agent system.

    Loads all configs, creates crews, and builds Temporal schedule specs.
    Returns a dict with system state for inspection or further wiring.
    """
    configs = load_agent_configs(config_path, enabled_only=True)
    tracing = init_tracing()
    schedules = build_schedule_specs(configs)

    # Build crews for all registered agents
    crews: dict[str, Crew] = {}
    for config in configs:
        factory = CREW_REGISTRY.get(config.id)
        if factory:
            prompt_path = f"{prompts_dir}/{config.prompt_file}"
            try:
                prompt = load_prompt(prompt_path)
            except FileNotFoundError:
                prompt = f"You are {config.name}."
            crews[config.id] = factory(config, prompt)

    return {
        "agent_count": len(configs),
        "configs": configs,
        "schedules": schedules,
        "crews": crews,
        "tracing": tracing,
    }
