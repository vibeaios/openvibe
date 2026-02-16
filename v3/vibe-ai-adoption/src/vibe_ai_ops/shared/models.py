from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Tier(str, Enum):
    DEEP_DIVE = "deep_dive"
    VALIDATION = "validation"


class ArchitectureType(str, Enum):
    TEMPORAL_LANGGRAPH_CREWAI = "temporal_langgraph_crewai"  # Deep dive: full pipeline
    TEMPORAL_CREWAI = "temporal_crewai"  # Validation: Temporal triggers CrewAI directly


class TriggerType(str, Enum):
    CRON = "cron"
    WEBHOOK = "webhook"
    ON_DEMAND = "on_demand"
    EVENT = "event"


class TriggerConfig(BaseModel):
    type: TriggerType
    schedule: str | None = None  # cron expression
    event_source: str | None = None  # e.g. "hubspot:new_lead"


class AgentConfig(BaseModel):
    id: str
    name: str
    engine: str  # marketing | sales | cs | intelligence
    tier: Tier
    architecture: ArchitectureType = ArchitectureType.TEMPORAL_CREWAI
    trigger: TriggerConfig
    output_channel: str  # e.g. "slack:#marketing-agents"
    prompt_file: str  # relative to config/prompts/
    enabled: bool = True
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    temperature: float = 0.7
    crew_config: dict[str, Any] | None = None  # CrewAI crew setup
    graph_config: dict[str, Any] | None = None  # LangGraph workflow setup


# ---------------------------------------------------------------------------
# Operator models — replaces flat agent model with grouped operators
# ---------------------------------------------------------------------------


class NodeType(str, Enum):
    LOGIC = "logic"
    LLM = "llm"


class OperatorTriggerConfig(BaseModel):
    id: str
    type: TriggerType
    schedule: str | None = None
    source: str | None = None
    workflow: str
    description: str = ""


class NodeConfig(BaseModel):
    id: str
    type: NodeType = NodeType.LOGIC
    model: str | None = None
    prompt_file: str | None = None


class WorkflowConfig(BaseModel):
    id: str
    description: str = ""
    nodes: list[NodeConfig]
    checkpointed: bool = True
    durable: bool = False
    max_duration_days: int | None = None
    timeout_minutes: int = 5


class OperatorConfig(BaseModel):
    id: str
    name: str
    owner: str = ""
    description: str = ""
    output_channels: list[str] = Field(default_factory=list)
    state_schema: str = ""
    triggers: list[OperatorTriggerConfig]
    workflows: list[WorkflowConfig]
    enabled: bool = True


class AgentOutput(BaseModel):
    agent_id: str
    content: str
    destination: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRun(BaseModel):
    agent_id: str
    status: str  # "success" | "error" | "skipped"
    input_summary: str = ""
    output_summary: str = ""
    error: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
