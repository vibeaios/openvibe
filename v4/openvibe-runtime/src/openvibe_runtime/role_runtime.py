"""RoleRuntime — manages Roles and dispatches activations (Layer 2)."""

from __future__ import annotations

from typing import Any, Callable

from openvibe_sdk.llm import LLMProvider
from openvibe_sdk.role import Role


class RoleRuntime:
    """Manages Roles + connects infrastructure.

    Workflow factories receive an Operator instance (with Role-aware LLM).
    Factory signature: (operator: Operator) -> CompiledGraph
    """

    def __init__(
        self,
        roles: list[type[Role]],
        llm: LLMProvider,
        workspace: Any = None,
    ) -> None:
        self.llm = llm
        self.workspace = workspace
        self._roles: dict[str, Role] = {}
        self._workflow_factories: dict[str, dict[str, Callable]] = {}

        for role_class in roles:
            from openvibe_sdk.memory.agent_memory import AgentMemory

            agent_mem = AgentMemory(
                agent_id=role_class.role_id,
                workspace=workspace,
            )
            role = role_class(llm=llm, agent_memory=agent_mem)
            self._roles[role.role_id] = role

    def get_role(self, role_id: str) -> Role:
        """Get a Role by ID."""
        role = self._roles.get(role_id)
        if not role:
            raise ValueError(f"Unknown role: {role_id}")
        return role

    def register_workflow(
        self,
        operator_id: str,
        workflow_id: str,
        factory: Callable,
    ) -> None:
        """Register a graph factory.

        Factory signature: (operator: Operator) -> CompiledGraph
        """
        if operator_id not in self._workflow_factories:
            self._workflow_factories[operator_id] = {}
        self._workflow_factories[operator_id][workflow_id] = factory

    def activate(
        self,
        role_id: str,
        operator_id: str,
        workflow_id: str,
        input_data: dict,
    ) -> dict:
        """Activate: Role -> Operator -> workflow -> result."""
        role = self.get_role(role_id)
        operator = role.get_operator(operator_id)

        factories = self._workflow_factories.get(operator_id, {})
        factory = factories.get(workflow_id)
        if not factory:
            raise ValueError(
                f"No workflow '{workflow_id}' registered for "
                f"operator '{operator_id}'"
            )

        graph = factory(operator)
        return graph.invoke(input_data)

    def list_roles(self) -> list[Role]:
        """List all registered roles."""
        return list(self._roles.values())
