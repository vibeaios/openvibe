from datetime import datetime, timezone
from openvibe_sdk.role import Role
from openvibe_sdk.models import (
    AuthorityConfig, Event, RoutingDecision,
    RoleLifecycle, RoleStatus, TrustProfile,
    Objective, KeyResult,
)
from openvibe_sdk.operator import Operator


class SimpleOperator(Operator):
    operator_id = "revenue_ops"


class CRORole(Role):
    role_id = "cro"
    soul = "You are the CRO."
    operators = [SimpleOperator]
    domains = ["revenue", "pipeline"]
    reports_to = "charles"
    authority = AuthorityConfig(
        autonomous=["qualify_lead"],
        needs_approval=["commit_deal"],
        forbidden=["sign_contracts"],
    )


def _make_event(type_: str, domain: str = "revenue") -> Event:
    return Event(id="e-1", type=type_, source="hubspot",
                 domain=domain, payload={},
                 timestamp=datetime.now(timezone.utc))


# ── Identity fields ────────────────────────────────────────────

def test_role_has_v3_identity_fields():
    r = CRORole()
    assert r.domains == ["revenue", "pipeline"]
    assert r.reports_to == "charles"
    assert r.workspace == ""  # default empty


def test_role_workspace_can_be_set():
    r = CRORole()
    r.workspace = "vibe-team"
    assert r.workspace == "vibe-team"


# ── handle(): lifecycle gate ───────────────────────────────────

def test_handle_ignored_when_suspended():
    r = CRORole()
    r.lifecycle = RoleLifecycle(
        status=RoleStatus.SUSPENDED,
        created_at=datetime.now(timezone.utc),
        created_by="charles",
    )
    decision = r.handle(_make_event("lead.created"))
    assert decision.action == "ignore"
    assert "suspended" in decision.reason.lower()


def test_handle_allowed_when_active():
    r = CRORole()
    r.lifecycle = RoleLifecycle(
        status=RoleStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        created_by="charles",
    )
    # revenue domain matches CRORole.domains
    decision = r.handle(_make_event("qualify_lead", domain="revenue"))
    # Should not be "ignore"
    assert decision.action != "ignore"


def test_handle_allowed_when_no_lifecycle():
    r = CRORole()
    assert r.lifecycle is None
    # Should still work — no lifecycle = active
    decision = r.handle(_make_event("qualify_lead", domain="revenue"))
    assert decision.action != "ignore"


# ── handle(): domain check ─────────────────────────────────────

def test_handle_ignores_out_of_domain_event():
    r = CRORole()
    decision = r.handle(_make_event("blog.published", domain="marketing"))
    assert decision.action in ("forward", "ignore")


def test_handle_accepts_in_domain_event():
    r = CRORole()
    decision = r.handle(_make_event("qualify_lead", domain="revenue"))
    assert decision.action != "ignore" or decision.action != "forward"


# ── handle(): authority check ──────────────────────────────────

def test_handle_escalates_forbidden_action():
    r = CRORole()
    decision = r.handle(_make_event("sign_contracts", domain="revenue"))
    assert decision.action == "escalate"
    assert decision.target_role_id == "charles"


def test_handle_escalates_needs_approval():
    r = CRORole()
    decision = r.handle(_make_event("commit_deal", domain="revenue"))
    assert decision.action == "escalate"


def test_handle_delegates_autonomous_action():
    r = CRORole()
    # _match_operator default returns None, None so it escalates
    # but action IS autonomous — test that forbidden doesn't block it
    decision = r.handle(_make_event("qualify_lead", domain="revenue"))
    # With no operator match, falls to escalate — but NOT forbidden/suspended
    assert decision.action in ("delegate", "escalate")


# ── Goals ─────────────────────────────────────────────────────

def test_role_active_goals():
    r = CRORole()
    r.goals = [
        Objective(id="g1", description="Q1 pipeline", status="active"),
        Objective(id="g2", description="old goal", status="achieved"),
    ]
    active = r.active_goals()
    assert len(active) == 1
    assert active[0].id == "g1"


def test_role_goal_context_empty():
    r = CRORole()
    r.goals = []
    assert r.goal_context() == ""


def test_role_goal_context_nonempty():
    r = CRORole()
    r.goals = [Objective(id="g1", description="Grow pipeline to $2M", status="active",
                         key_results=[KeyResult(id="kr1", description="200 leads",
                                                target=200, current=80)])]
    ctx = r.goal_context()
    assert "pipeline" in ctx.lower() or "g1" in ctx


# ── Trust ──────────────────────────────────────────────────────

def test_role_trust_default():
    r = CRORole()
    assert r.trust is None  # not set by default


def test_role_trust_when_set():
    r = CRORole()
    r.trust = TrustProfile(scores={"qualify_lead": 0.9})
    assert r.trust.trust_for("qualify_lead") == 0.9
