"""YAML config loader and prompt reader."""

from __future__ import annotations

from pathlib import Path

import yaml

from openvibe_sdk.models import OperatorConfig


def load_operator_configs(
    config_path: str,
    enabled_only: bool = False,
) -> list[OperatorConfig]:
    """Load operator configs from a YAML file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "operators" not in data:
        raise ValueError(f"Invalid config: expected 'operators' key in {config_path}")
    configs = [OperatorConfig(**op) for op in data["operators"]]
    if enabled_only:
        configs = [c for c in configs if c.enabled]
    return configs


def load_prompt(prompt_path: str) -> str:
    """Read a prompt file and return its content."""
    return Path(prompt_path).read_text()
