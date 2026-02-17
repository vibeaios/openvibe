from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from temporalio import activity


@dataclass
class AgentActivityInput:
    agent_id: str
    agent_config_path: str
    input_data: dict[str, Any]


@dataclass
class AgentActivityOutput:
    agent_id: str
    status: str  # "success" | "error"
    content: str = ""
    error: str = ""
    cost_usd: float = 0.0
    duration_seconds: float = 0.0


async def _execute_agent(inp: AgentActivityInput) -> AgentActivityOutput:
    """Execute agent — deprecated, use run_operator() instead."""
    raise NotImplementedError("Wire to specific agent implementation")


@activity.defn
async def run_validation_agent(inp: AgentActivityInput) -> AgentActivityOutput:
    """Temporal activity: run a validation-tier agent."""
    return await _execute_agent(inp)


@activity.defn
async def run_deep_dive_agent(inp: AgentActivityInput) -> AgentActivityOutput:
    """Temporal activity: run a deep-dive agent via LangGraph."""
    return await _execute_agent(inp)
