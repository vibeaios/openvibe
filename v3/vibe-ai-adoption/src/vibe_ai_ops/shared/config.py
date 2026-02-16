from __future__ import annotations

from pathlib import Path

import yaml

from vibe_ai_ops.shared.models import AgentConfig, OperatorConfig


def load_agent_configs(
    config_path: str = "config/agents.yaml",
    enabled_only: bool = False,
) -> list[AgentConfig]:
    with open(config_path) as f:
        data = yaml.safe_load(f)

    configs = [AgentConfig(**agent) for agent in data["agents"]]
    if enabled_only:
        configs = [c for c in configs if c.enabled]
    return configs


def load_operator_configs(
    config_path: str = "config/operators.yaml",
    enabled_only: bool = False,
) -> list[OperatorConfig]:
    with open(config_path) as f:
        data = yaml.safe_load(f)

    configs = [OperatorConfig(**op) for op in data["operators"]]
    if enabled_only:
        configs = [c for c in configs if c.enabled]
    return configs


def load_prompt(prompt_path: str) -> str:
    return Path(prompt_path).read_text()
