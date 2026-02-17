# OpenVibe SDK V2 — Memory Pyramid + Authority Design

> **Date:** 2026-02-17
> **Status:** Design
> **Builds on:** SDK V1 (implemented), Memory Architecture Vision (proposed)
> **Vision doc:** `proposed/MEMORY-ARCHITECTURE-VISION.md`

## Goal

Add structured memory (L1-L3), per-fact access control, declarative memory_scope on decorators, workspace/agent memory split, and authority config to the SDK. Foundation for the full memory architecture vision.

## Core Design Principle

**Recall precision through structured addressing, not search.** Each fact has rich metadata (entity, domain, tags). Each node declares what memory it needs via `memory_scope`. The system filters first, then searches within the filtered set.

```
Bad:  "search all memory for relevant stuff" → noisy, imprecise
Good: entity=acme_corp, domain=revenue, tags=[qualification] → precise
```

---

## Section 1: Memory Data Types

### 1.1 Classification

```python
# memory/types.py

class Classification(str, Enum):
    PUBLIC = "public"             # any agent/human
    INTERNAL = "internal"         # org members with domain clearance
    CONFIDENTIAL = "confidential" # domain-specific clearance required
    RESTRICTED = "restricted"     # named access only
```

### 1.2 Fact — atomic unit of knowledge

```python
@dataclass
class Fact:
    """Atomic unit of knowledge. Base unit of all memory."""

    id: str
    content: str                  # "Acme Corp has 200 employees"

    # Addressing (enables precise recall)
    entity: str = ""              # "acme_corp" — what this is about
    domain: str = ""              # "revenue" — what area
    tags: list[str] = field(default_factory=list)

    # Relevance signals
    confidence: float = 1.0
    importance: float = 0.0       # usage-boosted over time
    last_accessed: datetime | None = None
    access_count: int = 0

    # Access control
    classification: Classification = Classification.INTERNAL

    # Provenance
    source: str = ""              # agent_id or "human"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    supersedes: str | None = None
```

### 1.3 Episode — L2 structured execution record

```python
@dataclass
class Episode:
    """L2: Structured record of a node execution."""

    id: str
    agent_id: str
    operator_id: str
    node_name: str
    timestamp: datetime
    action: str                   # "qualify_lead"
    input_summary: str            # truncated input (max 200 chars)
    output_summary: str           # truncated output (max 200 chars)
    outcome: dict                 # full result
    duration_ms: int
    tokens_in: int
    tokens_out: int

    # Addressing (same dimensions as Fact)
    entity: str = ""
    domain: str = ""
    tags: list[str] = field(default_factory=list)
```

### 1.4 Insight — L3 pattern from episodes

```python
@dataclass
class Insight:
    """L3: Pattern discovered across episodes."""

    id: str
    agent_id: str
    content: str                  # "Webinar leads convert 2x vs cold"
    confidence: float             # 0.0-1.0
    evidence_count: int
    source_episode_ids: list[str]
    created_at: datetime
    last_confirmed: datetime | None = None
    status: str = "active"        # "active" | "weakening" | "retired"

    # Addressing
    entity: str = ""
    domain: str = ""
    tags: list[str] = field(default_factory=list)
```

---

## Section 2: Access Control

### 2.1 ClearanceProfile

```python
# memory/access.py

CLASSIFICATION_RANK: dict[Classification, int] = {
    Classification.PUBLIC: 0,
    Classification.INTERNAL: 1,
    Classification.CONFIDENTIAL: 2,
    Classification.RESTRICTED: 3,
}

@dataclass
class ClearanceProfile:
    """Per-agent/human permission config."""

    agent_id: str
    domain_clearance: dict[str, Classification]
    # e.g. {"revenue": CONFIDENTIAL, "marketing": INTERNAL}

    def can_access(self, fact: Fact) -> bool:
        """Check if this profile can access a fact."""
        if fact.classification == Classification.PUBLIC:
            return True
        clearance = self.domain_clearance.get(fact.domain)
        if not clearance:
            return False
        return CLASSIFICATION_RANK[clearance] >= CLASSIFICATION_RANK[fact.classification]
```

### 2.2 AccessFilter

```python
class AccessFilter:
    """Filter a list of facts by clearance."""

    def __init__(self, clearance: ClearanceProfile):
        self._clearance = clearance

    def filter(self, facts: list[Fact]) -> list[Fact]:
        return [f for f in facts if self._clearance.can_access(f)]
```

---

## Section 3: Store Protocols

### 3.1 FactStore

```python
# memory/stores.py

class FactStore(Protocol):
    """Protocol for atomic fact storage."""

    def store(self, fact: Fact) -> None: ...

    def query(
        self,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        query: str = "",
        min_confidence: float = 0.0,
        limit: int = 10,
    ) -> list[Fact]: ...

    def get(self, fact_id: str) -> Fact | None: ...

    def update(self, fact: Fact) -> None: ...

    def delete(self, fact_id: str) -> None: ...
```

### 3.2 EpisodicStore

```python
class EpisodicStore(Protocol):
    """Protocol for L2 episode storage."""

    def store(self, episode: Episode) -> None: ...

    def query(
        self,
        agent_id: str,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[Episode]: ...
```

### 3.3 InsightStore

```python
class InsightStore(Protocol):
    """Protocol for L3 insight storage."""

    def store(self, insight: Insight) -> None: ...

    def query(
        self,
        agent_id: str,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        query: str = "",
        limit: int = 10,
    ) -> list[Insight]: ...

    def update(self, insight: Insight) -> None: ...

    def find_similar(self, agent_id: str, content: str) -> Insight | None: ...
```

### 3.4 InMemory Implementations

All three get InMemory implementations (dict/list-based, keyword matching for search):
- `InMemoryFactStore`
- `InMemoryEpisodicStore`
- `InMemoryInsightStore`

These live in `memory/in_memory.py` alongside the existing `InMemoryStore` (V1 compat).

---

## Section 4: WorkspaceMemory

```python
# memory/workspace.py

class WorkspaceMemory:
    """Shared org-level fact store with access control.

    Wraps a FactStore and filters results by clearance.
    V2: InMemoryFactStore backend. V3+: Postgres/pgvector.
    """

    def __init__(self, fact_store: FactStore | None = None):
        self._store = fact_store or InMemoryFactStore()

    def store_fact(self, fact: Fact) -> None:
        self._store.store(fact)

    def query(
        self,
        clearance: ClearanceProfile,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        query: str = "",
        limit: int = 10,
    ) -> list[Fact]:
        # Over-fetch to account for filtering
        candidates = self._store.query(
            entity=entity, domain=domain, tags=tags,
            query=query, limit=limit * 3,
        )
        filtered = [f for f in candidates if clearance.can_access(f)]
        # Boost access_count for recall tracking
        for f in filtered[:limit]:
            f.access_count += 1
            f.last_accessed = datetime.now(timezone.utc)
        return filtered[:limit]

    def update_fact(self, fact: Fact) -> None:
        self._store.update(fact)
```

---

## Section 5: AgentMemory

```python
# memory/agent_memory.py

class AgentMemory:
    """Per-agent memory: L2 episodes + L3 insights + workspace reference.

    Implements V1 MemoryProvider protocol for backward compatibility.
    """

    def __init__(
        self,
        agent_id: str,
        workspace: WorkspaceMemory | None = None,
        episodic: EpisodicStore | None = None,
        insights: InsightStore | None = None,
    ):
        self.agent_id = agent_id
        self.workspace = workspace
        self._episodic = episodic or InMemoryEpisodicStore()
        self._insights = insights or InMemoryInsightStore()

    # --- L2: Episodes ---

    def record_episode(self, episode: Episode) -> None:
        episode.agent_id = self.agent_id
        self._episodic.store(episode)

    def recall_episodes(
        self, entity=None, domain=None, tags=None, since=None, limit=10,
    ) -> list[Episode]:
        return self._episodic.query(
            self.agent_id, entity=entity, domain=domain,
            tags=tags, since=since, limit=limit,
        )

    # --- L3: Insights ---

    def recall_insights(
        self, entity=None, domain=None, tags=None, query="", limit=10,
    ) -> list[Insight]:
        return self._insights.query(
            self.agent_id, entity=entity, domain=domain,
            tags=tags, query=query, limit=limit,
        )

    def store_insight(self, insight: Insight) -> None:
        insight.agent_id = self.agent_id
        self._insights.store(insight)

    # --- Reflection: L2 → L3 ---

    def reflect(self, llm, role_context: str = "") -> list[Insight]:
        """Analyze recent episodes, extract new insights via LLM."""
        recent = self._episodic.query(self.agent_id, limit=50)
        if not recent:
            return []

        episodes_text = "\n".join(
            f"- [{e.domain}] {e.action}: {e.output_summary}" for e in recent
        )
        response = llm.call(
            system=(
                f"{role_context}\n"
                "You are reflecting on recent work experiences.\n"
                "Extract patterns and insights as a JSON array:\n"
                '[{"content": "...", "confidence": 0.0-1.0, '
                '"domain": "...", "tags": [...]}]'
            ),
            messages=[{
                "role": "user",
                "content": f"Recent episodes:\n{episodes_text}\n\nWhat patterns do you see?",
            }],
            model="sonnet",
            temperature=0.3,
        )

        new_insights = _parse_insights(response.content, self.agent_id)
        for insight in new_insights:
            existing = self._insights.find_similar(self.agent_id, insight.content)
            if existing:
                existing.confidence = min(1.0, existing.confidence + 0.1)
                existing.evidence_count += 1
                existing.last_confirmed = datetime.now(timezone.utc)
                self._insights.update(existing)
            else:
                self._insights.store(insight)

        return new_insights

    # --- Sync: Agent → Workspace ---

    def publish_to_workspace(self, min_confidence: float = 0.5) -> list[Fact]:
        """Push high-confidence insights as facts to workspace."""
        if not self.workspace:
            return []

        insights = self._insights.query(self.agent_id, limit=100)
        published = []
        for insight in insights:
            if insight.confidence < min_confidence:
                continue
            fact = Fact(
                id=f"pub_{insight.id}",
                content=insight.content,
                source=self.agent_id,
                confidence=insight.confidence,
                entity=insight.entity,
                domain=insight.domain,
                tags=insight.tags,
                classification=Classification.INTERNAL,
            )
            self.workspace.store_fact(fact)
            published.append(fact)
        return published

    # --- V1 MemoryProvider backward compat ---

    def store(self, namespace: str, key: str, value: Any) -> None:
        """V1 compat: store as insight."""
        insight = Insight(
            id=key,
            agent_id=namespace,
            content=str(value),
            confidence=1.0,
            evidence_count=1,
            source_episode_ids=[],
            created_at=datetime.now(timezone.utc),
        )
        self._insights.store(insight)

    def recall(self, namespace: str, query: str, limit: int = 10) -> list[MemoryEntry]:
        """V1 compat: recall as MemoryEntry list."""
        insights = self._insights.query(namespace, query=query, limit=limit)
        return [
            MemoryEntry(key=i.id, content=i.content, namespace=namespace)
            for i in insights
        ]

    def delete(self, namespace: str, key: str) -> None:
        """V1 compat: no-op (insights don't support delete in V2)."""
        pass
```

---

## Section 6: MemoryAssembler

```python
# memory/assembler.py

class MemoryAssembler:
    """Builds memory context string for LLM calls.

    Assembles from agent insights (L3) + workspace facts + recent episodes (L2).
    Filters by clearance. Respects token budget.
    """

    def __init__(
        self,
        agent_memory: AgentMemory,
        clearance: ClearanceProfile,
    ):
        self._memory = agent_memory
        self._clearance = clearance

    def assemble(
        self,
        scope: dict,
        token_budget: int = 2000,
    ) -> str:
        """Build memory context from scope.

        scope keys: entity, domain, tags, query (all optional).
        """
        entity = scope.get("entity")
        domain = scope.get("domain")
        tags = scope.get("tags")
        query = scope.get("query", "")

        parts: list[str] = []

        # Priority 1: Agent insights (L3) — highest signal
        insights = self._memory.recall_insights(
            entity=entity, domain=domain, tags=tags,
            query=query, limit=5,
        )
        if insights:
            lines = [f"- {i.content} (confidence: {i.confidence:.1f})" for i in insights]
            parts.append("## Insights\n" + "\n".join(lines))

        # Priority 2: Workspace facts — filtered by clearance
        if self._memory.workspace:
            facts = self._memory.workspace.query(
                clearance=self._clearance,
                entity=entity, domain=domain, tags=tags,
                query=query, limit=10,
            )
            if facts:
                lines = [f"- {f.content}" for f in facts]
                parts.append("## Context\n" + "\n".join(lines))

        # Priority 3: Recent episodes (L2)
        episodes = self._memory.recall_episodes(
            entity=entity, domain=domain, tags=tags, limit=3,
        )
        if episodes:
            lines = [f"- {e.action}: {e.output_summary}" for e in episodes]
            parts.append("## Recent Activity\n" + "\n".join(lines))

        result = "\n\n".join(parts)

        # Token budget (rough: 4 chars per token)
        max_chars = token_budget * 4
        if len(result) > max_chars:
            result = result[:max_chars]

        return result
```

---

## Section 7: memory_scope on Decorators

The V2 killer feature. Nodes declare what memory they need:

```python
@llm_node(
    model="sonnet",
    output_key="score",
    memory_scope={
        "domain": "revenue",
        "entity": lambda state: state.get("company"),
        "tags": ["qualification"],
    },
)
def qualify(self, state):
    """You are a lead qualifier."""
    return f"Score: {state['lead']}"
```

### Implementation in decorator wrapper

```python
def llm_node(
    model="haiku",
    temperature=0.7,
    max_tokens=4096,
    output_key=None,
    memory_scope=None,         # NEW V2
):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self: Operator, state: dict) -> dict:
            system_prompt = (method.__doc__ or "").strip()
            user_message = method(self, state)

            # V2: Resolve memory_scope and assemble context
            if memory_scope and self._memory_assembler:
                resolved_scope = {}
                for key, val in memory_scope.items():
                    resolved_scope[key] = val(state) if callable(val) else val
                memory_context = self._memory_assembler.assemble(resolved_scope)
                if memory_context:
                    system_prompt = f"{system_prompt}\n\n{memory_context}"

            start_time = time.monotonic()
            response = self.llm.call(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                model=model, max_tokens=max_tokens, temperature=temperature,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            result = _try_json_parse(response.content)
            if output_key:
                state[output_key] = result

            # V2: Auto-record episode
            if self._episode_recorder:
                resolved = {}
                if memory_scope:
                    for key, val in memory_scope.items():
                        resolved[key] = val(state) if callable(val) else val
                episode = Episode(
                    id=f"ep_{_short_id()}",
                    agent_id="",  # set by recorder
                    operator_id=self.operator_id,
                    node_name=method.__name__,
                    timestamp=datetime.now(timezone.utc),
                    action=method.__name__,
                    input_summary=str(user_message)[:200],
                    output_summary=str(result)[:200],
                    outcome={"output_key": output_key, "value": result} if output_key else {},
                    duration_ms=duration_ms,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    entity=resolved.get("entity", ""),
                    domain=resolved.get("domain", ""),
                    tags=resolved.get("tags", []),
                )
                self._episode_recorder(episode)

            return state
        wrapper._is_llm_node = True
        wrapper._node_config = {
            "model": model, "temperature": temperature,
            "output_key": output_key, "memory_scope": memory_scope,
        }
        return wrapper
    return decorator
```

Same pattern applies to `@agent_node`.

---

## Section 8: AuthorityConfig

```python
# models.py (add to existing)

class AuthorityConfig(BaseModel):
    """Defines what actions a Role can take autonomously."""

    autonomous: list[str] = Field(default_factory=list)
    needs_approval: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)

    def can_act(self, action: str) -> str:
        """Returns: 'autonomous' | 'needs_approval' | 'forbidden'."""
        if action in self.forbidden:
            return "forbidden"
        if action in self.needs_approval:
            return "needs_approval"
        if action in self.autonomous:
            return "autonomous"
        return "needs_approval"  # default: cautious
```

---

## Section 9: Role + Operator Changes

### Operator

```python
class Operator:
    operator_id: str = ""

    def __init__(
        self,
        llm=None,
        config=None,
        memory_assembler=None,   # NEW V2
    ):
        self.llm = llm
        self.config = config
        self._memory_assembler = memory_assembler
        self._episode_recorder = None  # set by Role
```

### Role

```python
class Role:
    role_id: str = ""
    soul: str = ""
    operators: list[type[Operator]] = []
    authority: AuthorityConfig | None = None       # NEW V2
    clearance: ClearanceProfile | None = None       # NEW V2

    def __init__(
        self,
        llm=None,
        memory=None,              # V1: MemoryProvider (backward compat)
        agent_memory=None,        # V2: AgentMemory
        config=None,
    ):
        self.llm = llm
        self.memory = memory
        self.agent_memory = agent_memory
        self.config = config or {}
        self._operator_instances = {}

    def get_operator(self, operator_id: str) -> Operator:
        if operator_id not in self._operator_instances:
            for op_class in self.operators:
                if op_class.operator_id == operator_id:
                    wrapped_llm = _RoleAwareLLM(self, self.llm) if self.llm else None

                    # V2: wire up memory assembler
                    assembler = None
                    if self.agent_memory and self.clearance:
                        assembler = MemoryAssembler(self.agent_memory, self.clearance)

                    op = op_class(llm=wrapped_llm, memory_assembler=assembler)

                    # V2: wire up episode recorder
                    if self.agent_memory:
                        op._episode_recorder = self.agent_memory.record_episode

                    self._operator_instances[operator_id] = op
                    break
            else:
                raise ValueError(f"Role '{self.role_id}' has no operator '{operator_id}'")
        return self._operator_instances[operator_id]

    def can_act(self, action: str) -> str:
        """Check authority for an action."""
        if not self.authority:
            return "autonomous"
        return self.authority.can_act(action)
```

### _RoleAwareLLM changes

V2: if agent_memory exists, MemoryAssembler handles memory injection via memory_scope on decorators. _RoleAwareLLM still injects soul but defers memory to the assembler.

```python
class _RoleAwareLLM:
    def call(self, *, system, messages, **kwargs):
        # Soul injection (unchanged from V1)
        soul_text = self._role._load_soul()
        if soul_text:
            system = f"{soul_text}\n\n{system}"

        # V1 memory injection (backward compat, only if no agent_memory)
        if self._role.memory and not self._role.agent_memory:
            context = messages[0].get("content", "") if messages else ""
            if isinstance(context, str) and context:
                recalled = self._role.memory.recall(self._role.role_id, context)
                if recalled:
                    mem_text = "\n## Relevant Memories\n" + "\n".join(
                        f"- {m.content}" for m in recalled
                    )
                    system = f"{system}\n\n{mem_text}"

        # V2: memory injection handled by MemoryAssembler in decorator
        # (via memory_scope on @llm_node/@agent_node)

        return self._inner.call(system=system, messages=messages, **kwargs)
```

---

## Section 10: Public API

```python
# __init__.py

from openvibe_sdk.operator import Operator, llm_node, agent_node
from openvibe_sdk.role import Role
from openvibe_sdk.runtime import OperatorRuntime, RoleRuntime
from openvibe_sdk.memory.types import Fact, Episode, Insight, Classification
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.workspace import WorkspaceMemory
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.models import AuthorityConfig

__all__ = [
    # V1
    "Operator", "llm_node", "agent_node",
    "Role", "OperatorRuntime", "RoleRuntime",
    # V2
    "Fact", "Episode", "Insight", "Classification",
    "ClearanceProfile", "WorkspaceMemory", "AgentMemory",
    "AuthorityConfig",
]
```

V2 adds 8 new exports (14 total).

---

## Section 11: Backward Compatibility

| V1 Code | V2 Behavior |
|---------|-------------|
| `Role(memory=InMemoryStore())` | Still works. _RoleAwareLLM falls back to V1 recall. |
| `@llm_node()` without memory_scope | Works exactly as V1. No memory assembly. |
| V1 tests (89 tests) | Must all pass without modification. |
| `MemoryProvider` protocol | Still exists, unchanged. AgentMemory implements it. |

---

## Section 12: Full Example

```python
from openvibe_sdk import (
    Operator, Role, RoleRuntime,
    llm_node, agent_node,
    Fact, Classification, ClearanceProfile,
    WorkspaceMemory, AgentMemory, AuthorityConfig,
)

# Workspace (shared)
workspace = WorkspaceMemory()
workspace.store_fact(Fact(
    id="f1", content="Acme Corp has 200 employees",
    entity="acme_corp", domain="customer",
    classification=Classification.INTERNAL,
    source="human",
))
workspace.store_fact(Fact(
    id="f2", content="Acme Corp scored 85 in qualification",
    entity="acme_corp", domain="revenue",
    classification=Classification.CONFIDENTIAL,
    source="revenue_ops",
))

# Operator with memory_scope
class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(
        model="sonnet",
        output_key="score",
        memory_scope={
            "domain": "revenue",
            "entity": lambda state: state.get("company"),
            "tags": ["qualification"],
        },
    )
    def qualify(self, state):
        """You are a lead qualifier."""
        return f"Score: {state['lead']}"

# Role with authority + clearance
class CRO(Role):
    role_id = "cro"
    soul = "You are the CRO. Data-driven and strategic."
    operators = [RevenueOps]
    authority = AuthorityConfig(
        autonomous=["qualify_lead", "trigger_nurture"],
        needs_approval=["change_pricing"],
        forbidden=["sign_contracts"],
    )
    clearance = ClearanceProfile(
        agent_id="cro",
        domain_clearance={
            "revenue": Classification.CONFIDENTIAL,
            "customer": Classification.CONFIDENTIAL,
            "marketing": Classification.INTERNAL,
        },
    )

# Wire up
agent_mem = AgentMemory(agent_id="cro", workspace=workspace)
role = CRO(
    llm=AnthropicProvider(),
    agent_memory=agent_mem,
)

# CRO can see both facts (has revenue:confidential clearance)
op = role.get_operator("revenue_ops")
result = op.qualify({"company": "acme_corp", "lead": "Acme Corp"})
# System prompt includes soul + memory_scope-assembled context
# Episode auto-recorded to agent_mem

# Check authority
assert role.can_act("qualify_lead") == "autonomous"
assert role.can_act("sign_contracts") == "forbidden"
```

---

## Section 13: File Structure at Completion

```
v4/openvibe-sdk/
├── src/openvibe_sdk/
│   ├── __init__.py              # 14 exports (V1: 6, V2: +8)
│   ├── operator.py              # + memory_assembler, episode_recorder, memory_scope
│   ├── role.py                  # + authority, clearance, agent_memory
│   ├── runtime.py               # + workspace wiring on RoleRuntime
│   ├── models.py                # + AuthorityConfig
│   ├── config.py                # unchanged
│   ├── tools.py                 # unchanged
│   ├── llm/
│   │   ├── __init__.py          # unchanged
│   │   └── anthropic.py         # unchanged
│   └── memory/
│       ├── __init__.py          # V1 compat (MemoryProvider, MemoryEntry)
│       ├── types.py             # NEW: Fact, Episode, Insight, Classification
│       ├── access.py            # NEW: ClearanceProfile, AccessFilter, CLASSIFICATION_RANK
│       ├── stores.py            # NEW: FactStore, EpisodicStore, InsightStore protocols
│       ├── workspace.py         # NEW: WorkspaceMemory
│       ├── agent_memory.py      # NEW: AgentMemory (L2+L3 + workspace ref + V1 compat)
│       ├── assembler.py         # NEW: MemoryAssembler
│       └── in_memory.py         # existing + InMemoryFactStore, InMemoryEpisodicStore, InMemoryInsightStore
└── tests/
    ├── (13 existing V1 tests)   # must all pass
    ├── test_fact_types.py       # NEW
    ├── test_access_control.py   # NEW
    ├── test_fact_store.py       # NEW
    ├── test_episodic_store.py   # NEW
    ├── test_insight_store.py    # NEW
    ├── test_workspace_memory.py # NEW
    ├── test_agent_memory.py     # NEW
    ├── test_assembler.py        # NEW
    ├── test_memory_scope.py     # NEW
    ├── test_auto_recording.py   # NEW
    ├── test_authority.py        # NEW
    ├── test_role_v2.py          # NEW
    └── test_integration_v2.py   # NEW
```

---

*Design: 2026-02-17*
