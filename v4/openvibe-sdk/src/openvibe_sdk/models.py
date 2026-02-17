"""Config models for operators, workflows, nodes, and triggers."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    CRON = "cron"
    WEBHOOK = "webhook"
    ON_DEMAND = "on_demand"
    EVENT = "event"


class NodeType(str, Enum):
    LOGIC = "logic"
    LLM = "llm"


class TriggerConfig(BaseModel):
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
    triggers: list[TriggerConfig]
    workflows: list[WorkflowConfig]
    enabled: bool = True
