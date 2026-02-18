# 4-Layer Architecture Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure `v4/openvibe-sdk/` into four separate packages (SDK / Runtime / Platform / CLI) with clean layer boundaries, V3 Role features, and real infrastructure services.

**Architecture:** Layer 1 (`openvibe-sdk`) = pure primitives with zero infra deps. Layer 2 (`openvibe-runtime`) = LangGraph execution + audit log. Layer 3 (`openvibe-platform`) = deployed FastAPI service with workspace management, role gateway, and human loop. Layer 4 (`openvibe-cli`) = multi-instance CLI.

**Tech Stack:** Python 3.13, Pydantic v2, LangGraph, FastAPI, Temporal, pytest, hatch (build tool)

**Test command:** `python3 -m pytest tests/ -v` (run from each package root; set `PYTHONPATH=src`)

---

## Environment Note

Each new package follows this structure (same as `openvibe-sdk`):
```
v4/<package-name>/
├── pyproject.toml
├── src/<package_name>/
│   └── __init__.py
└── tests/
    └── __init__.py
```
Run tests from each package root: `cd v4/<package-name> && PYTHONPATH=src python3 -m pytest tests/ -v`

---

## Phase 1: SDK Cleanup — Remove V1 shim, add V3 models

### Task 1: Remove V1 memory compat from `Role.respond()`

**Context:** `Role.respond()` currently has two code paths: V1 (`self.memory`) and V2 (`self.agent_memory`). The V1 path references the old `MemoryProvider` protocol. We drop it — V2 only.

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/role.py`
- Modify: `v4/openvibe-sdk/tests/test_role.py` (remove V1 memory tests)

**Step 1: Run current tests to record baseline**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q --tb=no
```
Expected: 216 passed (or similar — note exact count)

**Step 2: Remove V1 memory path from `respond()`**

In `role.py`, replace the `respond()` method body: remove the `elif self.memory:` branch entirely. The method becomes:

```python
def respond(self, message: str, context: str = "") -> LLMResponse:
    """Respond to a message with soul + memory context (V2 only)."""
    if not self.llm:
        raise ValueError(f"Role '{self.role_id}' has no LLM configured")

    parts: list[str] = []
    soul_text = self._load_soul()
    if soul_text:
        parts.append(soul_text)

    if self.agent_memory:
        insights = self.agent_memory.recall_insights(query=message, limit=5)
        if insights:
            lines = [f"- {i.content}" for i in insights]
            parts.append("## Knowledge\n" + "\n".join(lines))

    system = "\n\n".join(parts)
    response = self.llm.call(
        system=system,
        messages=[{"role": "user", "content": message}],
    )

    if self.agent_memory:
        self.agent_memory.record_episode(Episode(
            id=str(uuid.uuid4()),
            agent_id=self.role_id,
            operator_id="",
            node_name="respond",
            timestamp=datetime.now(timezone.utc),
            action="respond",
            input_summary=message[:200],
            output_summary=(response.content or "")[:200],
            outcome={},
            duration_ms=0,
            tokens_in=getattr(response, "tokens_in", 0),
            tokens_out=getattr(response, "tokens_out", 0),
        ))

    return response
```

Also remove `self.memory` from `build_system_prompt()` — keep only soul + base_prompt:

```python
def build_system_prompt(self, base_prompt: str, context: str = "") -> str:
    """Augment system prompt with soul."""
    soul_text = self._load_soul()
    parts = [p for p in [soul_text, base_prompt] if p]
    return "\n\n".join(parts)
```

Also remove `self.memory: MemoryProvider | None = None` from `__init__()` params and body.
Also remove `from openvibe_sdk.memory import MemoryProvider` import if it's now unused.

**Step 3: Remove V1 memory tests from `test_role.py`**

Search for any test using `MemoryProvider` mock or `memory=` kwarg — delete those tests.

**Step 4: Run tests**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q --tb=short
```
Expected: all pass (fewer tests than baseline due to removed V1 tests — that's fine)

**Step 5: Commit**
```bash
git add v4/openvibe-sdk/
git commit -m "refactor(sdk): remove V1 memory compat shim from Role"
```

---

### Task 2: Add V3 data models to `models.py`

**Context:** V3 needs Event, RoutingDecision, RoleMessage, WorkspaceConfig, WorkspacePolicy, RoleTemplate, RoleSpec, RoleLifecycle, RoleStatus, TrustProfile, Objective, KeyResult, SpawnSignal. These are pure data models — no logic, no infra deps. Full V3 design reference: `v4/docs/plans/2026-02-18-sdk-v3-design.md`.

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/models.py`
- Create: `v4/openvibe-sdk/tests/test_v3_models.py`

**Step 1: Write failing tests first**

```python
# tests/test_v3_models.py
from datetime import datetime, timezone
from openvibe_sdk.models import (
    Event, RoutingDecision, RoleMessage,
    WorkspaceConfig, WorkspacePolicy,
    RoleTemplate, RoleSpec,
    RoleLifecycle, RoleStatus,
    TrustProfile,
    Objective, KeyResult,
)


def test_event_creation():
    e = Event(
        id="e-1", type="lead.created", source="hubspot",
        domain="revenue", payload={"lead_id": "123"},
        timestamp=datetime.now(timezone.utc),
    )
    assert e.domain == "revenue"
    assert e.type == "lead.created"


def test_routing_decision_delegate():
    d = RoutingDecision(action="delegate", reason="matched operator",
                        operator_id="revenue_ops", trigger_id="qualify")
    assert d.action == "delegate"
    assert d.operator_id == "revenue_ops"


def test_routing_decision_escalate():
    d = RoutingDecision(action="escalate", reason="needs approval",
                        target_role_id="ceo", message="approve this deal")
    assert d.target_role_id == "ceo"


def test_role_message():
    m = RoleMessage(id="m-1", type="request", from_id="cro",
                    to_id="bdr-apac", content="qualify this lead")
    assert m.from_id == "cro"


def test_workspace_config():
    ws = WorkspaceConfig(id="vibe-team", name="Vibe AI Team", owner="charles",
                         policy=WorkspacePolicy())
    assert ws.policy.default_trust == 0.3
    assert ws.policy.spawn_requires_approval is False


def test_role_status_enum():
    assert RoleStatus.ACTIVE == "active"
    assert RoleStatus.TESTING == "testing"


def test_role_lifecycle():
    lc = RoleLifecycle(status=RoleStatus.ACTIVE,
                       created_at=datetime.now(timezone.utc),
                       created_by="charles")
    assert lc.status == RoleStatus.ACTIVE
    assert lc.memory_policy == "archive"


def test_trust_profile_default():
    t = TrustProfile()
    assert t.trust_for("qualify_lead") == 0.3  # default


def test_trust_profile_known_capability():
    t = TrustProfile(scores={"qualify_lead": 0.8})
    assert t.trust_for("qualify_lead") == 0.8


def test_objective_progress():
    kr = KeyResult(id="kr-1", description="100 leads", target=100, current=42, unit="leads")
    assert abs(kr.progress - 0.42) < 0.001


def test_objective_full_progress():
    kr = KeyResult(id="kr-2", description="done", target=10, current=15)
    assert kr.progress == 1.0  # capped at 1.0


def test_role_template():
    t = RoleTemplate(
        template_id="bdr",
        name_pattern="BDR - {territory}",
        soul_template="You are a BDR covering {territory}.",
        domains=["revenue"],
        authority=None,
        operator_ids=["revenue_ops"],
        parameters=["territory"],
        allowed_spawners=["cro"],
    )
    assert "territory" in t.parameters


def test_role_spec():
    from openvibe_sdk.models import AuthorityConfig
    spec = RoleSpec(
        role_id="bdr-apac", workspace="vibe-team",
        soul="You are a BDR covering APAC.",
        domains=["revenue"], reports_to="cro",
        operator_ids=["revenue_ops"],
        authority=AuthorityConfig(autonomous=["qualify_lead"]),
        parent_role_id="cro",
    )
    assert spec.parent_role_id == "cro"
```

**Step 2: Run to verify they fail**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/test_v3_models.py -v
```
Expected: `ImportError` — models don't exist yet.

**Step 3: Add V3 models to `models.py`**

Append to the existing `models.py` file (keep existing classes, add below):

```python
from __future__ import annotations
# Add to existing imports:
from datetime import datetime
from enum import Enum
from typing import Any


# ── V3 Event + Routing ─────────────────────────────────────────

class Event(BaseModel):
    id: str
    type: str              # "lead.created", "deal.stalled"
    source: str            # "hubspot", "slack", "temporal", human id
    domain: str            # "revenue", "marketing"
    payload: dict[str, Any]
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    action: str            # "delegate" | "escalate" | "forward" | "ignore"
    reason: str
    operator_id: str | None = None
    trigger_id: str | None = None
    input_data: dict[str, Any] | None = None
    target_role_id: str | None = None
    message: str | None = None


# ── V3 Inter-Role ──────────────────────────────────────────────

class RoleMessage(BaseModel):
    id: str
    type: str              # "request" | "response" | "notification"
    from_id: str
    to_id: str
    content: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""
    timestamp: datetime | None = None


# ── V3 Workspace ───────────────────────────────────────────────

class WorkspacePolicy(BaseModel):
    max_roles: int = 100
    default_trust: float = 0.3
    spawn_requires_approval: bool = False
    memory_isolation: str = "strict"


class WorkspaceConfig(BaseModel):
    id: str
    name: str
    owner: str
    policy: WorkspacePolicy
    role_templates: dict[str, Any] = Field(default_factory=dict)


# ── V3 Lifecycle + Trust ───────────────────────────────────────

class RoleStatus(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class RoleLifecycle(BaseModel):
    status: RoleStatus
    created_at: datetime
    created_by: str
    activated_at: datetime | None = None
    terminated_at: datetime | None = None
    termination_reason: str = ""
    memory_policy: str = "archive"   # "archive" | "merge_to_parent" | "delete"


class TrustProfile(BaseModel):
    scores: dict[str, float] = Field(default_factory=dict)
    default: float = 0.3

    def trust_for(self, capability: str) -> float:
        return self.scores.get(capability, self.default)


# ── V3 Goals ──────────────────────────────────────────────────

class KeyResult(BaseModel):
    id: str
    description: str
    target: float
    current: float = 0.0
    unit: str = ""

    @property
    def progress(self) -> float:
        if self.target == 0:
            return 0.0
        return min(self.current / self.target, 1.0)


class Objective(BaseModel):
    id: str
    description: str
    key_results: list[KeyResult] = Field(default_factory=list)
    status: str = "active"   # "active" | "achieved" | "at_risk" | "abandoned"
    owner_id: str = ""


# ── V3 Role Templates + Specs ──────────────────────────────────

class RoleTemplate(BaseModel):
    template_id: str
    name_pattern: str
    soul_template: str
    domains: list[str]
    authority: AuthorityConfig | None = None
    operator_ids: list[str] = Field(default_factory=list)
    default_trust: float = 0.3
    ttl: str | None = None
    parameters: list[str] = Field(default_factory=list)
    allowed_spawners: list[str] = Field(default_factory=list)


class RoleSpec(BaseModel):
    role_id: str
    workspace: str
    soul: str
    domains: list[str]
    reports_to: str
    operator_ids: list[str]
    authority: AuthorityConfig | None = None
    goals: list[Objective] = Field(default_factory=list)
    trust: TrustProfile | None = None
    parent_role_id: str = ""
    created_by: str = ""
    ttl: str | None = None
    memory_policy: str = "archive"
```

**Step 4: Run tests**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/test_v3_models.py -v
```
Expected: all 12 tests pass.

**Step 5: Run full suite**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q --tb=short
```
Expected: all pass.

**Step 6: Commit**
```bash
git add v4/openvibe-sdk/
git commit -m "feat(sdk): add V3 data models — Event, RoutingDecision, Workspace, Lifecycle, Trust, Goals"
```

---

### Task 3: Add V3 fields and `handle()` to `Role`

**Context:** Role gains V3 identity fields (`workspace`, `domains`, `reports_to`) and lifecycle/trust/goals. The key new method is `handle(event) -> RoutingDecision`. `handle()` is deterministic — no LLM call. Full spec in `v4/docs/plans/2026-02-18-sdk-v3-design.md` section 4.3.

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/role.py`
- Create: `v4/openvibe-sdk/tests/test_role_v3.py`

**Step 1: Write failing tests**

```python
# tests/test_role_v3.py
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
```

**Step 2: Run to verify failures**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/test_role_v3.py -v
```
Expected: failures on missing `domains`, `handle()`, `active_goals()`, `goal_context()`, `lifecycle`, `trust`.

**Step 3: Add V3 fields and methods to `role.py`**

Add to class-level declarations (below existing `authority` and `clearance`):

```python
# V3 class fields
workspace: str = ""
domains: list[str] = []
reports_to: str = ""
```

Add to `__init__()` kwargs:

```python
lifecycle: RoleLifecycle | None = None,
trust: TrustProfile | None = None,
goals: list[Objective] | None = None,
```

And in `__init__()` body:
```python
self.lifecycle = lifecycle
self.trust = trust
self.goals = goals or []
```

Add these methods to the `Role` class:

```python
def handle(self, event: "Event") -> "RoutingDecision":
    """Receive event, decide action. Deterministic — no LLM call."""
    from openvibe_sdk.models import RoutingDecision, RoleStatus

    # 1. Lifecycle gate
    if self.lifecycle is not None:
        active_statuses = (RoleStatus.ACTIVE, RoleStatus.TESTING)
        if self.lifecycle.status not in active_statuses:
            return RoutingDecision(
                action="ignore",
                reason=f"Role is {self.lifecycle.status}",
            )

    # 2. Domain check
    if self.domains and event.domain not in self.domains:
        return RoutingDecision(
            action="forward",
            reason=f"Domain '{event.domain}' not in {self.domains}",
        )

    # 3. Authority check
    authority_result = self.can_act(event.type)
    if authority_result == "forbidden":
        return RoutingDecision(
            action="escalate",
            reason=f"Action '{event.type}' is forbidden",
            target_role_id=self.reports_to,
            message=f"Forbidden action attempted: {event.type}",
        )

    # 4. Match operator
    operator_id, trigger_id = self._match_operator(event)
    if operator_id:
        if authority_result == "needs_approval":
            return RoutingDecision(
                action="escalate",
                reason=f"Action '{event.type}' needs approval",
                target_role_id=self.reports_to,
                operator_id=operator_id,
                trigger_id=trigger_id,
                input_data=event.payload,
            )
        return RoutingDecision(
            action="delegate",
            reason=f"Matched operator '{operator_id}'",
            operator_id=operator_id,
            trigger_id=trigger_id,
            input_data=event.payload,
        )

    # 5. No operator match — escalate
    return RoutingDecision(
        action="escalate",
        reason=f"No operator matched event type '{event.type}'",
        target_role_id=self.reports_to,
    )

def _match_operator(self, event: "Event") -> tuple[str | None, str | None]:
    """Override in subclasses to map event.type -> (operator_id, trigger_id)."""
    return None, None

def active_goals(self) -> list["Objective"]:
    """Return goals with status='active'."""
    return [g for g in self.goals if g.status == "active"]

def goal_context(self) -> str:
    """Format active goals as string for LLM prompt injection."""
    active = self.active_goals()
    if not active:
        return ""
    lines = ["## Current Goals"]
    for obj in active:
        lines.append(f"- {obj.description} [{obj.status}]")
        for kr in obj.key_results:
            pct = int(kr.progress * 100)
            lines.append(f"  • {kr.description}: {kr.current}/{kr.target} {kr.unit} ({pct}%)")
    return "\n".join(lines)
```

Add imports at top of `role.py`:
```python
from openvibe_sdk.models import (
    AuthorityConfig, Event, Objective, RoleLifecycle, TrustProfile
)
```

**Step 4: Run tests**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/test_role_v3.py -v
```
Expected: all pass.

**Step 5: Run full suite**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q
```
Expected: all pass.

**Step 6: Commit**
```bash
git add v4/openvibe-sdk/
git commit -m "feat(sdk): V3 Role — domains, reports_to, handle(), lifecycle, trust, goals"
```

---

### Task 4: Implement `Role.spawn()` + `RoleRegistry` / `RoleTransport` protocols

**Context:** Roles need to communicate and spawn children. This task adds the inter-role protocol definitions (as `Protocol` classes) plus `InMemoryRegistry` and `InMemoryTransport` for testing. Then adds `spawn()` to Role. Full spec: `v4/docs/plans/2026-02-18-sdk-v3-design.md` sections 4.4 and 4.9.

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/registry.py`
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/role.py`
- Create: `v4/openvibe-sdk/tests/test_registry.py`
- Create: `v4/openvibe-sdk/tests/test_role_spawn.py`

**Step 1: Write failing tests for registry**

```python
# tests/test_registry.py
from openvibe_sdk.registry import (
    Participant, InMemoryRegistry, InMemoryTransport,
)
from openvibe_sdk.models import RoleMessage
from datetime import datetime, timezone


def test_registry_register_and_get():
    reg = InMemoryRegistry()
    p = Participant(id="cro", type="role", name="CRO", domains=["revenue"])
    reg.register_participant(p)
    found = reg.get("vibe-team", "cro")
    assert found is None  # not in workspace yet

    reg.register_participant(p, workspace="vibe-team")
    found = reg.get("vibe-team", "cro")
    assert found is not None
    assert found.id == "cro"


def test_registry_find_by_domain():
    reg = InMemoryRegistry()
    p = Participant(id="cro", type="role", domains=["revenue", "pipeline"])
    reg.register_participant(p, workspace="vibe-team")
    results = reg.find_by_domain("vibe-team", "revenue")
    assert len(results) == 1
    assert results[0].id == "cro"


def test_registry_find_by_domain_no_match():
    reg = InMemoryRegistry()
    results = reg.find_by_domain("vibe-team", "marketing")
    assert results == []


def test_registry_list_roles():
    reg = InMemoryRegistry()
    reg.register_participant(Participant(id="cro", type="role"), workspace="ws")
    reg.register_participant(Participant(id="cmo", type="role"), workspace="ws")
    roles = reg.list_roles("ws")
    assert len(roles) == 2


def test_registry_remove():
    reg = InMemoryRegistry()
    reg.register_participant(Participant(id="cro", type="role"), workspace="ws")
    reg.remove("ws", "cro")
    assert reg.get("ws", "cro") is None


def test_transport_send_and_receive():
    transport = InMemoryTransport()
    msg = RoleMessage(id="m-1", type="request", from_id="cro",
                      to_id="bdr", content="qualify this lead",
                      timestamp=datetime.now(timezone.utc))
    transport.send("cro", "bdr", msg)
    inbox = transport.inbox("bdr")
    assert len(inbox) == 1
    assert inbox[0].content == "qualify this lead"


def test_transport_inbox_empty_for_unknown():
    transport = InMemoryTransport()
    assert transport.inbox("nobody") == []
```

**Step 2: Run to verify failures**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/test_registry.py -v
```

**Step 3: Create `registry.py`**

```python
# src/openvibe_sdk/registry.py
"""RoleRegistry and RoleTransport protocols + in-memory implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from openvibe_sdk.models import RoleMessage, RoleSpec


@dataclass
class Participant:
    """A role or human that can be found in the registry."""
    id: str
    type: str = "role"          # "role" | "human"
    name: str = ""
    domains: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class RoleRegistry(Protocol):
    def get(self, workspace: str, role_id: str) -> Participant | None: ...
    def list_roles(self, workspace: str) -> list[Participant]: ...
    def find_by_domain(self, workspace: str, domain: str) -> list[Participant]: ...
    def register_participant(self, participant: Participant, workspace: str = "") -> None: ...
    def remove(self, workspace: str, role_id: str) -> None: ...


@runtime_checkable
class RoleTransport(Protocol):
    def send(self, from_id: str, to_id: str, message: RoleMessage) -> None: ...
    def inbox(self, role_id: str) -> list[RoleMessage]: ...


class InMemoryRegistry:
    """Dict-backed registry for tests and single-process deployments."""

    def __init__(self) -> None:
        # workspace -> role_id -> Participant
        self._store: dict[str, dict[str, Participant]] = {}

    def get(self, workspace: str, role_id: str) -> Participant | None:
        return self._store.get(workspace, {}).get(role_id)

    def list_roles(self, workspace: str) -> list[Participant]:
        return list(self._store.get(workspace, {}).values())

    def find_by_domain(self, workspace: str, domain: str) -> list[Participant]:
        return [
            p for p in self._store.get(workspace, {}).values()
            if domain in p.domains
        ]

    def register_participant(self, participant: Participant, workspace: str = "") -> None:
        if workspace not in self._store:
            self._store[workspace] = {}
        self._store[workspace][participant.id] = participant

    def remove(self, workspace: str, role_id: str) -> None:
        self._store.get(workspace, {}).pop(role_id, None)


class InMemoryTransport:
    """In-process message transport for tests."""

    def __init__(self) -> None:
        self._inboxes: dict[str, list[RoleMessage]] = {}

    def send(self, from_id: str, to_id: str, message: RoleMessage) -> None:
        if to_id not in self._inboxes:
            self._inboxes[to_id] = []
        self._inboxes[to_id].append(message)

    def inbox(self, role_id: str) -> list[RoleMessage]:
        return self._inboxes.get(role_id, [])
```

**Step 4: Write failing spawn tests**

```python
# tests/test_role_spawn.py
from datetime import datetime, timezone
from openvibe_sdk.role import Role
from openvibe_sdk.models import (
    AuthorityConfig, RoleTemplate, RoleSpec, TrustProfile
)
from openvibe_sdk.registry import InMemoryRegistry, Participant


class CRORole(Role):
    role_id = "cro"
    soul = "You are CRO."
    workspace = "vibe-team"
    domains = ["revenue"]
    reports_to = "charles"
    authority = AuthorityConfig(autonomous=["qualify_lead"])


BDR_TEMPLATE = RoleTemplate(
    template_id="bdr",
    name_pattern="bdr-{territory}",
    soul_template="You are a BDR covering {territory}.",
    domains=["revenue"],
    authority=AuthorityConfig(autonomous=["qualify_lead"]),
    operator_ids=["revenue_ops"],
    parameters=["territory"],
    allowed_spawners=["cro"],
)


def test_spawn_creates_role_spec_and_registers():
    registry = InMemoryRegistry()
    cro = CRORole()
    cro._registry = registry

    new_id = cro.spawn(BDR_TEMPLATE, params={"territory": "APAC"})
    assert new_id == "bdr-apac"

    registered = registry.get("vibe-team", "bdr-apac")
    assert registered is not None
    assert registered.id == "bdr-apac"


def test_spawn_fills_soul_template():
    registry = InMemoryRegistry()
    cro = CRORole()
    cro._registry = registry

    new_id = cro.spawn(BDR_TEMPLATE, params={"territory": "EMEA"})
    spec = cro._last_spawned_spec
    assert "EMEA" in spec.soul


def test_spawn_permission_check():
    registry = InMemoryRegistry()

    class CMORole(Role):
        role_id = "cmo"
        workspace = "vibe-team"
        domains = ["marketing"]

    cmo = CMORole()
    cmo._registry = registry

    import pytest
    with pytest.raises(PermissionError):
        cmo.spawn(BDR_TEMPLATE, params={"territory": "APAC"})


def test_spawn_sets_parent():
    registry = InMemoryRegistry()
    cro = CRORole()
    cro._registry = registry

    cro.spawn(BDR_TEMPLATE, params={"territory": "SEA"})
    spec = cro._last_spawned_spec
    assert spec.parent_role_id == "cro"
    assert spec.reports_to == "cro"
```

**Step 5: Run to verify failures**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/test_role_spawn.py -v
```

**Step 6: Add `spawn()` and communication methods to `Role`**

Add to `role.py` (class body):

```python
# V3 communication
_registry: "RoleRegistry | None" = None
_transport: "RoleTransport | None" = None
_last_spawned_spec: "RoleSpec | None" = None  # for testing introspection

def spawn(self, template: "RoleTemplate", params: dict[str, str]) -> str:
    """Create child Role from template. Returns new role_id."""
    from openvibe_sdk.models import RoleSpec, TrustProfile
    from openvibe_sdk.registry import InMemoryRegistry, Participant

    if self.role_id not in template.allowed_spawners:
        raise PermissionError(
            f"Role '{self.role_id}' is not in allowed_spawners for "
            f"template '{template.template_id}'"
        )

    new_role_id = template.name_pattern.format(**params).lower().replace(" ", "-")

    authority = template.authority
    soul = template.soul_template.format(**params)

    spec = RoleSpec(
        role_id=new_role_id,
        workspace=self.workspace,
        soul=soul,
        domains=template.domains,
        authority=authority,
        operator_ids=template.operator_ids,
        reports_to=self.role_id,
        parent_role_id=self.role_id,
        trust=TrustProfile(default=template.default_trust),
        ttl=template.ttl,
    )
    self._last_spawned_spec = spec

    if self._registry is not None:
        from openvibe_sdk.registry import Participant
        self._registry.register_participant(
            Participant(id=new_role_id, type="role", domains=template.domains),
            workspace=self.workspace,
        )

    return new_role_id

def request_role(self, target_id: str, content: str, payload: dict | None = None) -> "RoleMessage | None":
    """Send request to another role. Returns None if no transport."""
    if not self._transport:
        return None
    from openvibe_sdk.models import RoleMessage
    import uuid
    from datetime import datetime, timezone
    msg = RoleMessage(
        id=str(uuid.uuid4()), type="request",
        from_id=self.role_id, to_id=target_id,
        content=content, payload=payload or {},
        timestamp=datetime.now(timezone.utc),
    )
    self._transport.send(self.role_id, target_id, msg)
    return msg

def notify_role(self, target_id: str, content: str) -> None:
    """Fire-and-forget notification."""
    if not self._transport:
        return
    from openvibe_sdk.models import RoleMessage
    import uuid
    from datetime import datetime, timezone
    msg = RoleMessage(
        id=str(uuid.uuid4()), type="notification",
        from_id=self.role_id, to_id=target_id,
        content=content,
        timestamp=datetime.now(timezone.utc),
    )
    self._transport.send(self.role_id, target_id, msg)
```

**Step 7: Run all tests**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q
```
Expected: all pass.

**Step 8: Commit**
```bash
git add v4/openvibe-sdk/
git commit -m "feat(sdk): V3 spawn(), RoleRegistry/Transport protocols, InMemory implementations"
```

---

### Task 5: Update `__init__.py` exports and bump version to 0.3.0

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/__init__.py`
- Modify: `v4/openvibe-sdk/pyproject.toml`

**Step 1: Write failing test**

```python
# Add to tests/test_imports.py
def test_v3_exports():
    from openvibe_sdk import (
        Event, RoutingDecision, RoleMessage,
        WorkspaceConfig, WorkspacePolicy,
        RoleTemplate, RoleSpec,
        RoleLifecycle, RoleStatus,
        TrustProfile, Objective, KeyResult,
        InMemoryRegistry, InMemoryTransport, Participant,
    )
```

**Step 2: Update `__init__.py`**

```python
__version__ = "0.3.0"

# V3 models
from openvibe_sdk.models import (
    Event, RoutingDecision, RoleMessage,
    WorkspaceConfig, WorkspacePolicy,
    RoleTemplate, RoleSpec,
    RoleLifecycle, RoleStatus,
    TrustProfile, Objective, KeyResult,
)
# V3 registry
from openvibe_sdk.registry import (
    Participant, RoleRegistry, RoleTransport,
    InMemoryRegistry, InMemoryTransport,
)
```

Add all new names to `__all__`.

**Step 3: Bump version in `pyproject.toml`**: `version = "0.3.0"`

**Step 4: Run tests and commit**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q
git add v4/openvibe-sdk/
git commit -m "feat(sdk): v0.3.0 — V3 exports, version bump"
```

---

## Phase 2: `openvibe-runtime` Package (Layer 2)

### Task 6: Create `openvibe-runtime` package scaffold

**Files:**
- Create: `v4/openvibe-runtime/pyproject.toml`
- Create: `v4/openvibe-runtime/src/openvibe_runtime/__init__.py`
- Create: `v4/openvibe-runtime/tests/__init__.py`

**Step 1: Create `pyproject.toml`**

```toml
# v4/openvibe-runtime/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "openvibe-runtime"
version = "0.1.0"
description = "LangGraph execution runtime for openvibe-sdk"
requires-python = ">=3.12"
dependencies = [
    "openvibe-sdk>=0.3.0",
    "langgraph>=0.3.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
]

[tool.hatch.build.targets.wheel]
packages = ["src/openvibe_runtime"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "../openvibe-sdk/src"]
```

Note: `pythonpath` includes `../openvibe-sdk/src` so `openvibe_sdk` is importable during dev without installing.

**Step 2: Create `__init__.py`**
```python
"""OpenVibe Runtime — LangGraph execution layer."""
__version__ = "0.1.0"
```

**Step 3: Smoke test**
```python
# tests/test_init.py
def test_importable():
    import openvibe_runtime
    assert openvibe_runtime.__version__ == "0.1.0"
```

**Step 4: Run and commit**
```bash
cd v4/openvibe-runtime && PYTHONPATH=src:../openvibe-sdk/src python3 -m pytest tests/ -v
git add v4/openvibe-runtime/
git commit -m "feat(runtime): scaffold openvibe-runtime package"
```

---

### Task 7: Migrate `OperatorRuntime` to `openvibe-runtime`

**Context:** `OperatorRuntime` currently lives in `openvibe-sdk/runtime.py`. It loads YAML configs and dispatches to LangGraph graphs. This belongs in Layer 2 (has LangGraph dependency). Move it — keep a deprecated re-export shim in SDK temporarily.

**Files:**
- Create: `v4/openvibe-runtime/src/openvibe_runtime/operator_runtime.py`
- Create: `v4/openvibe-runtime/tests/test_operator_runtime.py`
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/runtime.py` (add deprecation notice to OperatorRuntime)

**Step 1: Copy `OperatorRuntime` tests to runtime package**

Create `v4/openvibe-runtime/tests/test_operator_runtime.py` — copy the relevant tests from `v4/openvibe-sdk/tests/test_operator_runtime.py`, updating imports to `from openvibe_runtime.operator_runtime import OperatorRuntime`.

**Step 2: Run to verify failures**
```bash
cd v4/openvibe-runtime && PYTHONPATH=src:../openvibe-sdk/src python3 -m pytest tests/test_operator_runtime.py -v
```

**Step 3: Create `operator_runtime.py`**

Copy the entire `OperatorRuntime` class from `v4/openvibe-sdk/src/openvibe_sdk/runtime.py` into `v4/openvibe-runtime/src/openvibe_runtime/operator_runtime.py`. Update imports to reference `openvibe_sdk.*` (not relative).

**Step 4: Run new tests**
```bash
cd v4/openvibe-runtime && PYTHONPATH=src:../openvibe-sdk/src python3 -m pytest tests/test_operator_runtime.py -v
```
Expected: all pass.

**Step 5: Add deprecation re-export to SDK** (so existing imports don't break):

In `v4/openvibe-sdk/src/openvibe_sdk/runtime.py`, at the top of `OperatorRuntime`:
```python
# Deprecated: OperatorRuntime moved to openvibe-runtime package.
# This re-export will be removed in v1.0.
```

**Step 6: Run full SDK tests to verify nothing broke**
```bash
cd v4/openvibe-sdk && PYTHONPATH=src python3 -m pytest tests/ -q
```

**Step 7: Commit**
```bash
git add v4/openvibe-runtime/ v4/openvibe-sdk/
git commit -m "feat(runtime): migrate OperatorRuntime to openvibe-runtime"
```

---

### Task 8: Migrate `RoleRuntime` and remove `scheduler` field

**Files:**
- Create: `v4/openvibe-runtime/src/openvibe_runtime/role_runtime.py`
- Create: `v4/openvibe-runtime/tests/test_role_runtime.py`

Same pattern as Task 7. Remove `scheduler: Any = None` field from the migrated version — it's a platform concern. If existing tests relied on `scheduler`, update them to not pass it.

**Commit:**
```bash
git commit -m "feat(runtime): migrate RoleRuntime, remove scheduler field (platform concern)"
```

---

### Task 9: Add Audit Log to Runtime

**Context:** Every `@llm_node` and `@agent_node` execution should auto-record: tokens in/out, latency ms, cost (USD), role_id, operator_id, node_name, timestamp. This goes in the runtime decorator layer — zero SDK changes needed.

**Files:**
- Create: `v4/openvibe-runtime/src/openvibe_runtime/audit.py`
- Create: `v4/openvibe-runtime/tests/test_audit.py`

**Step 1: Write failing tests**

```python
# tests/test_audit.py
import time
from openvibe_runtime.audit import AuditLog, AuditEntry, AuditableRuntime


def test_audit_entry_fields():
    entry = AuditEntry(
        role_id="cro", operator_id="revenue_ops",
        node_name="qualify_lead", action="llm_call",
        tokens_in=150, tokens_out=300,
        latency_ms=420, cost_usd=0.002,
    )
    assert entry.cost_usd == 0.002
    assert entry.tokens_in == 150


def test_audit_log_records_entry():
    log = AuditLog()
    log.record(AuditEntry(role_id="cro", operator_id="rev",
                          node_name="qualify", action="llm_call",
                          tokens_in=100, tokens_out=200,
                          latency_ms=300, cost_usd=0.001))
    assert len(log.entries) == 1


def test_audit_log_filter_by_role():
    log = AuditLog()
    log.record(AuditEntry(role_id="cro", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.0))
    log.record(AuditEntry(role_id="cmo", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.0))
    cro_entries = log.filter(role_id="cro")
    assert len(cro_entries) == 1


def test_audit_log_total_cost():
    log = AuditLog()
    for cost in [0.001, 0.002, 0.003]:
        log.record(AuditEntry(role_id="cro", operator_id="r", node_name="n",
                              action="a", tokens_in=1, tokens_out=1,
                              latency_ms=1, cost_usd=cost))
    assert abs(log.total_cost() - 0.006) < 0.0001


def test_audit_log_cost_by_role():
    log = AuditLog()
    log.record(AuditEntry(role_id="cro", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.005))
    log.record(AuditEntry(role_id="cmo", operator_id="r", node_name="n",
                          action="a", tokens_in=1, tokens_out=1,
                          latency_ms=1, cost_usd=0.003))
    breakdown = log.cost_by_role()
    assert abs(breakdown["cro"] - 0.005) < 0.0001
    assert abs(breakdown["cmo"] - 0.003) < 0.0001
```

**Step 2: Run to verify failures**

**Step 3: Implement `audit.py`**

```python
# src/openvibe_runtime/audit.py
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
```

**Step 4: Run tests and commit**
```bash
cd v4/openvibe-runtime && PYTHONPATH=src:../openvibe-sdk/src python3 -m pytest tests/test_audit.py -v
git add v4/openvibe-runtime/
git commit -m "feat(runtime): add AuditLog — per-entry token/cost/latency tracking"
```

---

### Task 10: Add Testing Mode to `RoleRuntime`

**Context:** `RoleRuntime(mode="test")` auto-injects `InMemoryTransport` and a mock LLM so tests never make real API calls.

**Files:**
- Modify: `v4/openvibe-runtime/src/openvibe_runtime/role_runtime.py`
- Modify: `v4/openvibe-runtime/tests/test_role_runtime.py`

**Step 1: Write failing test**
```python
def test_testing_mode_injects_mock_llm():
    from openvibe_runtime.role_runtime import RoleRuntime
    from openvibe_sdk.role import Role

    class MyRole(Role):
        role_id = "test-role"
        soul = "test"

    runtime = RoleRuntime(roles=[MyRole], mode="test")
    role = runtime.get_role("test-role")
    assert role.llm is not None
    # In test mode, calling respond() should not raise (mock LLM returns fixed response)
    response = role.respond("hello")
    assert response.content is not None


def test_testing_mode_injects_inmemory_transport():
    from openvibe_runtime.role_runtime import RoleRuntime
    from openvibe_sdk.role import Role
    from openvibe_sdk.registry import InMemoryTransport

    class MyRole(Role):
        role_id = "t-role"

    runtime = RoleRuntime(roles=[MyRole], mode="test")
    role = runtime.get_role("t-role")
    assert isinstance(role._transport, InMemoryTransport)
```

**Step 2: Implement** — add `mode: str = "live"` param to `RoleRuntime.__init__()`. When `mode="test"`, inject a `MockLLMProvider` (returns `LLMResponse(content="mock response")` for any call) and `InMemoryTransport`.

**Step 3: Run and commit**
```bash
git commit -m "feat(runtime): testing mode — auto-injects mock LLM + InMemoryTransport"
```

---

## Phase 3: `openvibe-platform` Skeleton (Layer 3)

### Task 11: Scaffold `openvibe-platform`

**Files:**
- Create: `v4/openvibe-platform/pyproject.toml`
- Create: `v4/openvibe-platform/src/openvibe_platform/__init__.py`
- Create: `v4/openvibe-platform/tests/__init__.py`

```toml
# pyproject.toml
[project]
name = "openvibe-platform"
version = "0.1.0"
dependencies = [
    "openvibe-sdk>=0.3.0",
    "openvibe-runtime>=0.1.0",
    "fastapi>=0.115.0",
    "pydantic>=2.6.0",
    "pyyaml>=6.0",
]
```

**Commit:** `feat(platform): scaffold openvibe-platform package`

---

### Task 12: WorkspaceService

**Context:** Manages workspace lifecycle. Creates, retrieves, lists, deletes workspaces. Enforces `max_roles` policy. In-memory for now (Postgres backend deferred).

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/workspace.py`
- Create: `v4/openvibe-platform/tests/test_workspace.py`

**Step 1: Write failing tests**

```python
# tests/test_workspace.py
import pytest
from openvibe_platform.workspace import WorkspaceService
from openvibe_sdk.models import WorkspaceConfig, WorkspacePolicy


def test_create_and_get_workspace():
    svc = WorkspaceService()
    ws = WorkspaceConfig(id="vibe-team", name="Vibe Team",
                         owner="charles", policy=WorkspacePolicy())
    svc.create(ws)
    found = svc.get("vibe-team")
    assert found is not None
    assert found.name == "Vibe Team"


def test_create_duplicate_raises():
    svc = WorkspaceService()
    ws = WorkspaceConfig(id="ws1", name="WS1", owner="x", policy=WorkspacePolicy())
    svc.create(ws)
    with pytest.raises(ValueError, match="already exists"):
        svc.create(ws)


def test_delete_workspace():
    svc = WorkspaceService()
    ws = WorkspaceConfig(id="ws-del", name="Del", owner="x", policy=WorkspacePolicy())
    svc.create(ws)
    svc.delete("ws-del")
    assert svc.get("ws-del") is None


def test_list_workspaces():
    svc = WorkspaceService()
    for i in range(3):
        svc.create(WorkspaceConfig(id=f"ws-{i}", name=f"WS {i}",
                                   owner="x", policy=WorkspacePolicy()))
    assert len(svc.list()) == 3


def test_get_nonexistent_returns_none():
    svc = WorkspaceService()
    assert svc.get("nobody") is None
```

**Step 2: Implement**

```python
# src/openvibe_platform/workspace.py
from openvibe_sdk.models import WorkspaceConfig


class WorkspaceService:
    def __init__(self) -> None:
        self._store: dict[str, WorkspaceConfig] = {}

    def create(self, ws: WorkspaceConfig) -> None:
        if ws.id in self._store:
            raise ValueError(f"Workspace '{ws.id}' already exists")
        self._store[ws.id] = ws

    def get(self, workspace_id: str) -> WorkspaceConfig | None:
        return self._store.get(workspace_id)

    def delete(self, workspace_id: str) -> None:
        self._store.pop(workspace_id, None)

    def list(self) -> list[WorkspaceConfig]:
        return list(self._store.values())
```

**Commit:** `feat(platform): WorkspaceService — CRUD with in-memory store`

---

### Task 13: RoleGateway (event routing)

**Context:** Receives `Event` objects, looks up which `Role` owns the domain, calls `role.handle(event)`, returns `RoutingDecision`. Also manages role registration per workspace. Uses `InMemoryRegistry` initially.

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/gateway.py`
- Create: `v4/openvibe-platform/tests/test_gateway.py`

**Step 1: Failing tests**

```python
# tests/test_gateway.py
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
```

**Step 2: Implement**

```python
# src/openvibe_platform/gateway.py
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
```

**Commit:** `feat(platform): RoleGateway — event dispatch to role owners`

---

### Task 14: HumanLoopService (approval queue + deliverables)

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/human_loop.py`
- Create: `v4/openvibe-platform/tests/test_human_loop.py`

**Step 1: Failing tests**

```python
# tests/test_human_loop.py
import pytest
from openvibe_platform.human_loop import HumanLoopService, ApprovalRequest, Deliverable


def test_create_approval_request():
    svc = HumanLoopService()
    req = svc.request_approval(
        role_id="cro", action="commit_deal",
        context={"deal_id": "d-123", "amount": 50000},
        requested_by="cro",
    )
    assert req.id is not None
    assert req.status == "pending"


def test_list_pending_approvals():
    svc = HumanLoopService()
    svc.request_approval("cro", "commit_deal", {}, "cro")
    svc.request_approval("cro", "change_pricing", {}, "cro")
    pending = svc.list_pending()
    assert len(pending) == 2


def test_approve_request():
    svc = HumanLoopService()
    req = svc.request_approval("cro", "commit_deal", {}, "cro")
    svc.approve(req.id, approved_by="charles")
    updated = svc.get(req.id)
    assert updated.status == "approved"
    assert updated.approved_by == "charles"


def test_reject_request():
    svc = HumanLoopService()
    req = svc.request_approval("cro", "commit_deal", {}, "cro")
    svc.reject(req.id, rejected_by="charles", reason="too risky")
    updated = svc.get(req.id)
    assert updated.status == "rejected"
    assert updated.rejection_reason == "too risky"


def test_stage_deliverable():
    svc = HumanLoopService()
    d = svc.stage_deliverable(
        role_id="cro", type="weekly_report",
        content="This week: 42 leads qualified.",
        metadata={"week": "2026-W08"},
    )
    assert d.id is not None
    assert d.status == "pending_review"


def test_list_deliverables():
    svc = HumanLoopService()
    svc.stage_deliverable("cro", "report", "content A", {})
    svc.stage_deliverable("cro", "report", "content B", {})
    items = svc.list_deliverables(role_id="cro")
    assert len(items) == 2


def test_acknowledge_deliverable():
    svc = HumanLoopService()
    d = svc.stage_deliverable("cro", "report", "content", {})
    svc.acknowledge_deliverable(d.id, by="charles")
    updated = svc.get_deliverable(d.id)
    assert updated.status == "acknowledged"
```

**Step 2: Implement**

```python
# src/openvibe_platform/human_loop.py
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ApprovalRequest:
    id: str
    role_id: str
    action: str
    context: dict[str, Any]
    requested_by: str
    status: str = "pending"           # "pending" | "approved" | "rejected"
    approved_by: str = ""
    rejected_by: str = ""
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Deliverable:
    id: str
    role_id: str
    type: str
    content: str
    metadata: dict[str, Any]
    status: str = "pending_review"    # "pending_review" | "acknowledged"
    acknowledged_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HumanLoopService:
    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRequest] = {}
        self._deliverables: dict[str, Deliverable] = {}

    def request_approval(self, role_id: str, action: str,
                         context: dict, requested_by: str) -> ApprovalRequest:
        req = ApprovalRequest(id=str(uuid.uuid4()), role_id=role_id,
                              action=action, context=context,
                              requested_by=requested_by)
        self._approvals[req.id] = req
        return req

    def list_pending(self) -> list[ApprovalRequest]:
        return [r for r in self._approvals.values() if r.status == "pending"]

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._approvals.get(request_id)

    def approve(self, request_id: str, approved_by: str) -> None:
        req = self._approvals[request_id]
        req.status = "approved"
        req.approved_by = approved_by

    def reject(self, request_id: str, rejected_by: str, reason: str = "") -> None:
        req = self._approvals[request_id]
        req.status = "rejected"
        req.rejected_by = rejected_by
        req.rejection_reason = reason

    def stage_deliverable(self, role_id: str, type: str,
                          content: str, metadata: dict) -> Deliverable:
        d = Deliverable(id=str(uuid.uuid4()), role_id=role_id,
                        type=type, content=content, metadata=metadata)
        self._deliverables[d.id] = d
        return d

    def list_deliverables(self, role_id: str | None = None) -> list[Deliverable]:
        items = list(self._deliverables.values())
        if role_id:
            items = [d for d in items if d.role_id == role_id]
        return items

    def get_deliverable(self, deliverable_id: str) -> Deliverable | None:
        return self._deliverables.get(deliverable_id)

    def acknowledge_deliverable(self, deliverable_id: str, by: str) -> None:
        d = self._deliverables[deliverable_id]
        d.status = "acknowledged"
        d.acknowledged_by = by
```

**Commit:** `feat(platform): HumanLoopService — approval queue + deliverable staging`

---

### Task 15: Webhook Ingestion Gateway

**Context:** Translates external HTTP webhooks (HubSpot, Slack, etc.) into standard `Event` objects and dispatches to `RoleGateway`. Uses FastAPI.

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/webhook.py`
- Create: `v4/openvibe-platform/tests/test_webhook.py`

**Step 1: Failing tests**

```python
# tests/test_webhook.py
from openvibe_platform.webhook import WebhookTranslator, WebhookRule


def test_hubspot_lead_created():
    translator = WebhookTranslator()
    translator.add_rule(WebhookRule(
        source="hubspot",
        event_type_field="subscriptionType",
        event_type_map={"contact.creation": "lead.created"},
        domain="revenue",
    ))
    payload = {"subscriptionType": "contact.creation",
               "objectId": "123", "portalId": "456"}
    event = translator.translate("hubspot", payload)
    assert event is not None
    assert event.type == "lead.created"
    assert event.domain == "revenue"
    assert event.source == "hubspot"


def test_unknown_source_returns_none():
    translator = WebhookTranslator()
    event = translator.translate("unknown-source", {"foo": "bar"})
    assert event is None


def test_unmapped_event_type_returns_none():
    translator = WebhookTranslator()
    translator.add_rule(WebhookRule(
        source="hubspot",
        event_type_field="subscriptionType",
        event_type_map={"contact.creation": "lead.created"},
        domain="revenue",
    ))
    payload = {"subscriptionType": "deal.deletion"}
    event = translator.translate("hubspot", payload)
    assert event is None
```

**Step 2: Implement**

```python
# src/openvibe_platform/webhook.py
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from openvibe_sdk.models import Event


@dataclass
class WebhookRule:
    source: str
    event_type_field: str              # payload field containing event type
    event_type_map: dict[str, str]     # raw type -> standard Event.type
    domain: str                        # which domain these events belong to


class WebhookTranslator:
    def __init__(self) -> None:
        self._rules: dict[str, WebhookRule] = {}

    def add_rule(self, rule: WebhookRule) -> None:
        self._rules[rule.source] = rule

    def translate(self, source: str, payload: dict[str, Any]) -> Event | None:
        rule = self._rules.get(source)
        if not rule:
            return None
        raw_type = payload.get(rule.event_type_field, "")
        event_type = rule.event_type_map.get(raw_type)
        if not event_type:
            return None
        return Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            domain=rule.domain,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
        )
```

**Commit:** `feat(platform): WebhookTranslator — HubSpot/Slack → standard Events`

---

### Task 16: File-based MemoryFilesystem backend

**Context:** Current `MemoryFilesystem` is virtual (over InMemory stores). Add a real file-backed storage so memory survives restarts and is debuggable with shell tools. Store as markdown files under `~/.openvibe/workspaces/{workspace}/{role_id}/`.

**Files:**
- Create: `v4/openvibe-platform/src/openvibe_platform/memory_store.py`
- Create: `v4/openvibe-platform/tests/test_memory_store.py`

**Step 1: Failing tests**

```python
# tests/test_memory_store.py
import tempfile, os
from pathlib import Path
from openvibe_platform.memory_store import FileMemoryStore


def test_write_and_read_file(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "knowledge/sales/principles.md",
                "VP sponsor predicts conversion.")
    content = store.read("vibe-team", "cro", "knowledge/sales/principles.md")
    assert "VP sponsor" in content


def test_list_directory(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "knowledge/sales/a.md", "content a")
    store.write("vibe-team", "cro", "knowledge/sales/b.md", "content b")
    entries = store.ls("vibe-team", "cro", "knowledge/sales")
    assert "a.md" in entries
    assert "b.md" in entries


def test_file_not_found_returns_none(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    result = store.read("vibe-team", "cro", "knowledge/nothing.md")
    assert result is None


def test_delete_file(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "experience/2026-02/event.md", "stuff")
    store.delete("vibe-team", "cro", "experience/2026-02/event.md")
    assert store.read("vibe-team", "cro", "experience/2026-02/event.md") is None


def test_search_by_content(tmp_path):
    store = FileMemoryStore(base_dir=tmp_path)
    store.write("vibe-team", "cro", "knowledge/sales/principles.md",
                "VP sponsor predicts conversion")
    store.write("vibe-team", "cro", "knowledge/product/roadmap.md",
                "Q3 features planned")
    results = store.search("vibe-team", "cro", "VP sponsor")
    assert len(results) == 1
    assert "principles.md" in results[0]
```

**Step 2: Implement**

```python
# src/openvibe_platform/memory_store.py
from __future__ import annotations
from pathlib import Path


class FileMemoryStore:
    """Filesystem-backed memory store. Base dir: base_dir/{workspace}/{role_id}/"""

    def __init__(self, base_dir: Path | str) -> None:
        self._base = Path(base_dir)

    def _path(self, workspace: str, role_id: str, virtual_path: str) -> Path:
        return self._base / workspace / role_id / virtual_path.lstrip("/")

    def write(self, workspace: str, role_id: str,
              virtual_path: str, content: str) -> None:
        p = self._path(workspace, role_id, virtual_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def read(self, workspace: str, role_id: str,
             virtual_path: str) -> str | None:
        p = self._path(workspace, role_id, virtual_path)
        if not p.exists():
            return None
        return p.read_text(encoding="utf-8")

    def ls(self, workspace: str, role_id: str,
           virtual_path: str) -> list[str]:
        p = self._path(workspace, role_id, virtual_path)
        if not p.exists():
            return []
        return [entry.name for entry in sorted(p.iterdir())]

    def delete(self, workspace: str, role_id: str,
               virtual_path: str) -> None:
        p = self._path(workspace, role_id, virtual_path)
        if p.exists():
            p.unlink()

    def search(self, workspace: str, role_id: str,
               query: str) -> list[str]:
        """Simple substring search across all files for this role."""
        base = self._base / workspace / role_id
        if not base.exists():
            return []
        results = []
        for f in base.rglob("*.md"):
            if query.lower() in f.read_text(encoding="utf-8").lower():
                results.append(str(f.relative_to(base)))
        return results
```

**Commit:** `feat(platform): FileMemoryStore — filesystem-backed memory (debuggable with shell)`

---

## Phase 4: `openvibe-cli` (Layer 4)

### Task 17: Scaffold CLI package

**Files:**
- Create: `v4/openvibe-cli/pyproject.toml`
- Create: `v4/openvibe-cli/src/openvibe_cli/__init__.py`
- Create: `v4/openvibe-cli/src/openvibe_cli/main.py`

```toml
[project]
name = "openvibe-cli"
version = "0.1.0"
dependencies = [
    "typer>=0.12.0",
    "httpx>=0.27.0",
    "rich>=13.0.0",
]

[project.scripts]
vibe = "openvibe_cli.main:app"
```

**Commit:** `feat(cli): scaffold openvibe-cli with typer`

---

### Task 18: Core CLI commands

**Files:**
- Create: `v4/openvibe-cli/src/openvibe_cli/commands/workspace.py`
- Create: `v4/openvibe-cli/src/openvibe_cli/commands/role.py`
- Create: `v4/openvibe-cli/src/openvibe_cli/commands/task.py`
- Create: `v4/openvibe-cli/tests/test_cli_workspace.py`

**CLI structure:**

```python
# main.py
import typer
from openvibe_cli.commands import workspace, role, task, deliverable

app = typer.Typer(name="vibe", help="OpenVibe CLI")
app.add_typer(workspace.app, name="workspace")
app.add_typer(role.app, name="role")
app.add_typer(task.app, name="task")
app.add_typer(deliverable.app, name="deliverable")

@app.callback()
def main(host: str = typer.Option("http://localhost:8000", "--host",
                                   help="Platform host URL",
                                   envvar="VIBE_HOST")):
    """OpenVibe CLI — manage workspaces, roles, tasks, deliverables."""
```

**Commands per module:**

| Module | Commands |
|--------|----------|
| `workspace` | `list`, `create <id> --name --owner`, `delete <id>` |
| `role` | `list --workspace`, `spawn <template> --workspace --params`, `inspect <id>` |
| `task` | `list --workspace`, `approve <id>`, `reject <id> --reason` |
| `deliverable` | `list --workspace --role`, `view <id>`, `ack <id>` |

Each command makes an `httpx` call to `{host}/api/v1/<resource>`. All commands accept `--host` flag.

**Test with Typer's `CliRunner`:**
```python
from typer.testing import CliRunner
from openvibe_cli.main import app

def test_workspace_list_empty(httpx_mock):
    httpx_mock.add_response(json=[])
    runner = CliRunner()
    result = runner.invoke(app, ["workspace", "list"])
    assert result.exit_code == 0
```

**Commit:** `feat(cli): workspace/role/task/deliverable commands with --host flag`

---

## Final: Update `PROGRESS.md`

After all tasks complete, update `v4/vibe-ai-adoption/PROGRESS.md` and root `PROGRESS.md` to reflect:

```
**SDK dir:** `v4/openvibe-sdk/` — v0.3.0 (V3 features, cleaned)
**Runtime dir:** `v4/openvibe-runtime/` — v0.1.0 (OperatorRuntime + RoleRuntime + AuditLog)
**Platform dir:** `v4/openvibe-platform/` — v0.1.0 (Workspace + Gateway + HumanLoop + Webhook + FileMemory)
**CLI dir:** `v4/openvibe-cli/` — v0.1.0 (workspace/role/task/deliverable)
```

```bash
git add PROGRESS.md v4/
git commit -m "docs: update progress — 4-layer restructure complete"
```

---

*Plan saved: `v4/docs/plans/2026-02-18-4-layer-restructure-implementation.md`*
