from __future__ import annotations

import os
from typing import Any

from langsmith import traceable


def init_tracing() -> dict[str, Any]:
    """Initialize LangSmith tracing from environment variables."""
    enabled = os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"
    project = os.environ.get("LANGCHAIN_PROJECT", "vibe-ai-ops")
    api_key = os.environ.get("LANGCHAIN_API_KEY", "")

    return {
        "enabled": enabled and bool(api_key),
        "project": project,
    }


def get_tracer(agent_name: str):
    """Return a LangSmith traceable decorator for an agent."""
    return traceable(name=agent_name, run_type="chain")
