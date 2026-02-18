"""OperatorRuntime — YAML-configured operator dispatch (Layer 2)."""

from __future__ import annotations

from typing import Any, Callable

from openvibe_sdk.config import load_operator_configs
from openvibe_sdk.models import OperatorConfig


class OperatorRuntime:
    """Central runtime for operators.

    Loads operators.yaml, indexes by ID, dispatches activations.
    """

    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path
        self.operators: dict[str, OperatorConfig] = {}
        self._workflow_factories: dict[str, dict[str, Callable]] = {}

    @classmethod
    def from_yaml(
        cls, config_path: str, enabled_only: bool = True
    ) -> OperatorRuntime:
        """Create runtime from a YAML config file."""
        runtime = cls(config_path=config_path)
        configs = load_operator_configs(config_path, enabled_only=enabled_only)
        for config in configs:
            runtime.operators[config.id] = config
        return runtime

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
        """Activate: resolve trigger -> workflow -> run graph."""
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
                f"No graph factory registered for "
                f"{operator_id}/{trigger.workflow}"
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
