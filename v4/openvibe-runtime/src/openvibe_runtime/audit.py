"""Audit log — records every LLM/agent node execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# Pricing constants (claude-sonnet-4-6, update as needed)
COST_PER_INPUT_TOKEN = 3.0 / 1_000_000   # $3 per 1M input tokens
COST_PER_OUTPUT_TOKEN = 15.0 / 1_000_000  # $15 per 1M output tokens


@dataclass
class AuditEntry:
    role_id: str
    operator_id: str
    node_name: str
    action: str          # "llm_call" | "agent_loop"
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditLog:
    """In-memory audit log. Replace with DB-backed version in Platform."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def filter(self, role_id: str | None = None,
               operator_id: str | None = None) -> list[AuditEntry]:
        result = self.entries
        if role_id:
            result = [e for e in result if e.role_id == role_id]
        if operator_id:
            result = [e for e in result if e.operator_id == operator_id]
        return result

    def total_cost(self) -> float:
        return sum(e.cost_usd for e in self.entries)

    def cost_by_role(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for e in self.entries:
            result[e.role_id] = result.get(e.role_id, 0.0) + e.cost_usd
        return result

    def cost_by_operator(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for e in self.entries:
            result[e.operator_id] = result.get(e.operator_id, 0.0) + e.cost_usd
        return result


def compute_cost(tokens_in: int, tokens_out: int) -> float:
    return (tokens_in * COST_PER_INPUT_TOKEN) + (tokens_out * COST_PER_OUTPUT_TOKEN)
