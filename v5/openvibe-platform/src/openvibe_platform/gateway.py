"""RoleGateway — routes events to the correct Role within a workspace."""

from __future__ import annotations

from openvibe_sdk.models import Event, RoutingDecision
from openvibe_sdk.registry import InMemoryRegistry, Participant
from openvibe_sdk.role import Role


class RoleGateway:
    """Routes events to the correct Role within a workspace."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        self._registry = InMemoryRegistry()
        self._roles: dict[str, Role] = {}

    def register_role(self, role: Role) -> None:
        self._roles[role.role_id] = role
        role._registry = self._registry
        self._registry.register_participant(
            Participant(id=role.role_id, type="role", domains=role.domains),
            workspace=self.workspace_id,
        )

    def dispatch(self, event: Event) -> RoutingDecision:
        owners = self._registry.find_by_domain(self.workspace_id, event.domain)
        if not owners:
            return RoutingDecision(action="ignore",
                                   reason=f"No role owns domain '{event.domain}'")
        role = self._roles.get(owners[0].id)
        if not role:
            return RoutingDecision(action="ignore", reason="Role not loaded")
        return role.handle(event)

    def list_roles(self) -> list[Participant]:
        return self._registry.list_roles(self.workspace_id)
