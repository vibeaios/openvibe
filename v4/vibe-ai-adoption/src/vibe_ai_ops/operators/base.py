"""Operator runtime — call_claude() helper and OperatorRuntime.

call_claude() is the single function that replaces all CrewAI crew.kickoff() calls.
Every LLM node in every operator uses this function.

OperatorRuntime loads operators.yaml and provides activation/lookup.
"""

from __future__ import annotations

from typing import Any, Callable

from vibe_ai_ops.shared.claude_client import ClaudeClient, ClaudeResponse
from vibe_ai_ops.shared.config import load_operator_configs
from vibe_ai_ops.shared.models import OperatorConfig


# ---------------------------------------------------------------------------
# call_claude — 1:1 replacement for crew.kickoff()
# ---------------------------------------------------------------------------

_client: ClaudeClient | None = None


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> ClaudeResponse:
    """Send a single prompt to Claude and return the response.

    This replaces every CrewAI crew.kickoff() call in the system.
    Uses the existing ClaudeClient wrapper which tracks tokens and cost.
    """
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client.send(system_prompt, user_message, model, max_tokens, temperature)


# ---------------------------------------------------------------------------
# OperatorRuntime — loads config, registers operators, dispatches activations
# ---------------------------------------------------------------------------


class OperatorRuntime:
    """Central runtime for all operators.

    Loads operators.yaml, indexes by ID, and provides lookup/activation.
    """

    def __init__(self, config_path: str = "config/operators.yaml"):
        self._config_path = config_path
        self.operators: dict[str, OperatorConfig] = {}
        self._workflow_factories: dict[str, dict[str, Callable]] = {}

    def load(self, enabled_only: bool = True) -> None:
        """Load all operator configs from YAML."""
        configs = load_operator_configs(self._config_path, enabled_only=enabled_only)
        for config in configs:
            self.operators[config.id] = config

    def register_workflow(
        self, operator_id: str, workflow_id: str, factory: Callable
    ) -> None:
        """Register a LangGraph graph factory for an operator workflow."""
        if operator_id not in self._workflow_factories:
            self._workflow_factories[operator_id] = {}
        self._workflow_factories[operator_id][workflow_id] = factory

    def get_workflow_factory(
        self, operator_id: str, workflow_id: str
    ) -> Callable | None:
        """Get the graph factory for a specific workflow."""
        return self._workflow_factories.get(operator_id, {}).get(workflow_id)

    def activate(
        self, operator_id: str, trigger_id: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Activate an operator: resolve trigger → workflow → run graph."""
        config = self.operators.get(operator_id)
        if not config:
            raise ValueError(f"Unknown operator: {operator_id}")

        trigger = next(
            (t for t in config.triggers if t.id == trigger_id), None
        )
        if not trigger:
            raise ValueError(
                f"Unknown trigger '{trigger_id}' for operator '{operator_id}'"
            )

        factory = self.get_workflow_factory(operator_id, trigger.workflow)
        if not factory:
            raise ValueError(
                f"No graph factory registered for {operator_id}/{trigger.workflow}"
            )

        graph = factory()
        return graph.invoke(input_data)

    def list_operators(self) -> list[OperatorConfig]:
        """List all registered operators."""
        return list(self.operators.values())

    def get_operator(self, operator_id: str) -> OperatorConfig | None:
        """Get a single operator config by ID."""
        return self.operators.get(operator_id)

    def summary(self) -> dict[str, Any]:
        """System summary: operator counts, node counts, trigger counts."""
        total_workflows = 0
        total_nodes = 0
        total_triggers = 0
        logic_nodes = 0
        llm_nodes = 0

        for op in self.operators.values():
            total_triggers += len(op.triggers)
            for wf in op.workflows:
                total_workflows += 1
                for node in wf.nodes:
                    total_nodes += 1
                    if node.type.value == "logic":
                        logic_nodes += 1
                    elif node.type.value == "llm":
                        llm_nodes += 1

        return {
            "operators": len(self.operators),
            "workflows": total_workflows,
            "triggers": total_triggers,
            "nodes": total_nodes,
            "logic_nodes": logic_nodes,
            "llm_nodes": llm_nodes,
        }
