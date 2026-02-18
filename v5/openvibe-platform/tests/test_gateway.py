from datetime import datetime, timezone
import pytest
from openvibe_platform.gateway import RoleGateway
from openvibe_sdk.role import Role
from openvibe_sdk.models import AuthorityConfig, Event, RoutingDecision


class CRORole(Role):
    role_id = "cro"
    domains = ["revenue"]
    reports_to = "charles"
    authority = AuthorityConfig(autonomous=["qualify_lead"])

    def _match_operator(self, event):
        if event.type == "qualify_lead":
            return "revenue_ops", "qualify"
        return None, None


def _event(type_: str, domain: str = "revenue") -> Event:
    return Event(id="e1", type=type_, source="test", domain=domain,
                 payload={}, timestamp=datetime.now(timezone.utc))


def test_gateway_routes_to_correct_role():
    gw = RoleGateway(workspace_id="vibe-team")
    cro = CRORole()
    gw.register_role(cro)

    decision = gw.dispatch(_event("qualify_lead"))
    assert decision.action == "delegate"
    assert decision.operator_id == "revenue_ops"


def test_gateway_ignores_unknown_domain():
    gw = RoleGateway(workspace_id="vibe-team")
    cro = CRORole()
    gw.register_role(cro)

    decision = gw.dispatch(_event("campaign.launched", domain="marketing"))
    assert decision.action == "ignore"


def test_gateway_lists_roles():
    gw = RoleGateway(workspace_id="vibe-team")
    gw.register_role(CRORole())
    roles = gw.list_roles()
    assert len(roles) == 1
    assert roles[0].id == "cro"
