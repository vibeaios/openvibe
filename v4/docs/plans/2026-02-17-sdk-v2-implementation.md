# OpenVibe SDK V2 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add structured memory (L1-L3), filesystem interface, access control, memory_scope on decorators, auto episode recording, and authority config to the SDK. Foundation for the full Role Layer vision.

**Architecture:** Bottom-up — Memory types → Store protocols → InMemory stores → Access control → WorkspaceMemory → AgentMemory → MemoryFilesystem → MemoryAssembler → AuthorityConfig → Operator changes → Role changes → Integration. Each component depends only on layers below.

**Tech Stack:** Python 3.13, anthropic SDK, langgraph, pydantic, pyyaml, pytest

**Design docs (read before starting):**
- `v4/docs/plans/2026-02-17-sdk-v2-memory-design.md` — full V2 memory design
- `v4/docs/plans/2026-02-17-role-layer-design.md` — Role Layer vision (memory filesystem, S1/S2)
- `v4/docs/plans/2026-02-17-sdk-4-layer-architecture.md` — 4-layer architecture + V1→V4 roadmap

**Reference implementation:**
- `v4/openvibe-sdk/src/openvibe_sdk/` — SDK V1 (87 tests, 11 modules)
- `v4/openvibe-sdk/tests/` — 13 test files, all must still pass

---

## Task 1: Memory Types

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/types.py`
- Create: `v4/openvibe-sdk/tests/test_memory_types.py`

**Step 1: Write the failing tests**

`tests/test_memory_types.py`:
```python
import typing
from datetime import datetime, timezone

from openvibe_sdk.memory.types import (
    Classification,
    Episode,
    Fact,
    Insight,
    RetrievalTrace,
)


def test_classification_values():
    assert Classification.PUBLIC == "public"
    assert Classification.INTERNAL == "internal"
    assert Classification.CONFIDENTIAL == "confidential"
    assert Classification.RESTRICTED == "restricted"


def test_fact_creation():
    f = Fact(id="f1", content="Acme has 200 employees")
    assert f.id == "f1"
    assert f.content == "Acme has 200 employees"
    assert f.entity == ""
    assert f.domain == ""
    assert f.tags == []
    assert f.confidence == 1.0
    assert f.importance == 0.0
    assert f.access_count == 0
    assert f.classification == Classification.INTERNAL
    assert f.source == ""
    assert f.created_at is not None
    assert f.supersedes is None


def test_fact_with_addressing():
    f = Fact(
        id="f2",
        content="Acme scored 85",
        entity="acme_corp",
        domain="revenue",
        tags=["qualification", "scoring"],
        classification=Classification.CONFIDENTIAL,
        source="revenue_ops",
    )
    assert f.entity == "acme_corp"
    assert f.domain == "revenue"
    assert f.tags == ["qualification", "scoring"]
    assert f.classification == Classification.CONFIDENTIAL


def test_episode_creation():
    now = datetime.now(timezone.utc)
    ep = Episode(
        id="ep1",
        agent_id="cro",
        operator_id="revenue_ops",
        node_name="qualify",
        timestamp=now,
        action="qualify_lead",
        input_summary="Score lead Acme",
        output_summary='{"score": 85}',
        outcome={"score": 85},
        duration_ms=450,
        tokens_in=100,
        tokens_out=200,
    )
    assert ep.id == "ep1"
    assert ep.agent_id == "cro"
    assert ep.entity == ""
    assert ep.domain == ""
    assert ep.tags == []


def test_episode_with_addressing():
    now = datetime.now(timezone.utc)
    ep = Episode(
        id="ep2",
        agent_id="cro",
        operator_id="revenue_ops",
        node_name="qualify",
        timestamp=now,
        action="qualify_lead",
        input_summary="Score lead",
        output_summary="85",
        outcome={},
        duration_ms=100,
        tokens_in=10,
        tokens_out=20,
        entity="acme_corp",
        domain="revenue",
        tags=["qualification"],
    )
    assert ep.entity == "acme_corp"
    assert ep.domain == "revenue"


def test_insight_creation():
    now = datetime.now(timezone.utc)
    ins = Insight(
        id="ins1",
        agent_id="cro",
        content="Webinar leads convert 2x vs cold",
        confidence=0.8,
        evidence_count=5,
        source_episode_ids=["ep1", "ep2"],
        created_at=now,
    )
    assert ins.content == "Webinar leads convert 2x vs cold"
    assert ins.confidence == 0.8
    assert ins.status == "active"


def test_insight_defaults():
    now = datetime.now(timezone.utc)
    ins = Insight(
        id="ins2",
        agent_id="cro",
        content="test",
        confidence=0.5,
        evidence_count=1,
        source_episode_ids=[],
        created_at=now,
    )
    assert ins.last_confirmed is None
    assert ins.status == "active"
    assert ins.entity == ""
    assert ins.domain == ""
    assert ins.tags == []


def test_retrieval_trace():
    t = RetrievalTrace(
        action="search",
        path="/knowledge/sales/",
        query="VP sponsor",
        results_count=2,
        tokens_loaded=340,
    )
    assert t.action == "search"
    assert t.path == "/knowledge/sales/"
    assert t.duration_ms == 0
    assert t.timestamp is not None
```

**Step 2: Run tests to verify they fail**

```bash
cd v4/openvibe-sdk && source .venv/bin/activate
pytest tests/test_memory_types.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'openvibe_sdk.memory.types'`

**Step 3: Implement memory types**

`src/openvibe_sdk/memory/types.py`:
```python
"""Memory data types — Fact, Episode, Insight, Classification, RetrievalTrace."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Classification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class Fact:
    """Atomic unit of knowledge. Base unit of all memory."""

    id: str
    content: str

    # Addressing (enables precise recall)
    entity: str = ""
    domain: str = ""
    tags: list[str] = field(default_factory=list)

    # Relevance signals
    confidence: float = 1.0
    importance: float = 0.0
    last_accessed: datetime | None = None
    access_count: int = 0

    # Access control
    classification: Classification = Classification.INTERNAL

    # Provenance
    source: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    supersedes: str | None = None


@dataclass
class Episode:
    """L2: Structured record of a node execution."""

    id: str
    agent_id: str
    operator_id: str
    node_name: str
    timestamp: datetime
    action: str
    input_summary: str
    output_summary: str
    outcome: dict[str, Any]
    duration_ms: int
    tokens_in: int
    tokens_out: int

    # Addressing
    entity: str = ""
    domain: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Insight:
    """L3: Pattern discovered across episodes."""

    id: str
    agent_id: str
    content: str
    confidence: float
    evidence_count: int
    source_episode_ids: list[str]
    created_at: datetime
    last_confirmed: datetime | None = None
    status: str = "active"

    # Addressing
    entity: str = ""
    domain: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class RetrievalTrace:
    """Observable trace of a memory access."""

    action: str  # "browse" | "read" | "search" | "write"
    path: str
    query: str = ""
    results_count: int = 0
    tokens_loaded: int = 0
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    duration_ms: int = 0
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_memory_types.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/types.py v4/openvibe-sdk/tests/test_memory_types.py
git commit -m "feat(sdk): add V2 memory types — Fact, Episode, Insight, Classification, RetrievalTrace"
```

---

## Task 2: Store Protocols

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/stores.py`
- Create: `v4/openvibe-sdk/tests/test_store_protocols.py`

**Step 1: Write the failing tests**

`tests/test_store_protocols.py`:
```python
import typing

from openvibe_sdk.memory.stores import EpisodicStore, FactStore, InsightStore


def test_fact_store_is_protocol():
    assert issubclass(type(FactStore), type(typing.Protocol))


def test_episodic_store_is_protocol():
    assert issubclass(type(EpisodicStore), type(typing.Protocol))


def test_insight_store_is_protocol():
    assert issubclass(type(InsightStore), type(typing.Protocol))
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_store_protocols.py -v
```

Expected: FAIL

**Step 3: Implement store protocols**

`src/openvibe_sdk/memory/stores.py`:
```python
"""Store protocols for structured memory."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from openvibe_sdk.memory.types import Episode, Fact, Insight


@runtime_checkable
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


@runtime_checkable
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


@runtime_checkable
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

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_store_protocols.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/stores.py v4/openvibe-sdk/tests/test_store_protocols.py
git commit -m "feat(sdk): add FactStore, EpisodicStore, InsightStore protocols"
```

---

## Task 3: InMemory Store Implementations

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/memory/in_memory.py`
- Create: `v4/openvibe-sdk/tests/test_inmemory_stores.py`

**Step 1: Write the failing tests**

`tests/test_inmemory_stores.py`:
```python
from datetime import datetime, timezone, timedelta

from openvibe_sdk.memory.stores import EpisodicStore, FactStore, InsightStore
from openvibe_sdk.memory.types import Classification, Episode, Fact, Insight
from openvibe_sdk.memory.in_memory import (
    InMemoryEpisodicStore,
    InMemoryFactStore,
    InMemoryInsightStore,
)


# --- FactStore ---


def test_fact_store_implements_protocol():
    store = InMemoryFactStore()
    assert isinstance(store, FactStore)


def test_fact_store_and_get():
    store = InMemoryFactStore()
    f = Fact(id="f1", content="Acme has 200 employees", entity="acme", domain="customer")
    store.store(f)
    result = store.get("f1")
    assert result is not None
    assert result.content == "Acme has 200 employees"


def test_fact_store_get_missing():
    store = InMemoryFactStore()
    assert store.get("missing") is None


def test_fact_store_query_by_entity():
    store = InMemoryFactStore()
    store.store(Fact(id="f1", content="Acme info", entity="acme", domain="customer"))
    store.store(Fact(id="f2", content="Beta info", entity="beta", domain="customer"))
    results = store.query(entity="acme")
    assert len(results) == 1
    assert results[0].id == "f1"


def test_fact_store_query_by_domain():
    store = InMemoryFactStore()
    store.store(Fact(id="f1", content="Revenue data", domain="revenue"))
    store.store(Fact(id="f2", content="Marketing data", domain="marketing"))
    results = store.query(domain="revenue")
    assert len(results) == 1
    assert results[0].id == "f1"


def test_fact_store_query_by_tags():
    store = InMemoryFactStore()
    store.store(Fact(id="f1", content="Qualified lead", tags=["qualification", "lead"]))
    store.store(Fact(id="f2", content="Competitor info", tags=["competitor"]))
    results = store.query(tags=["qualification"])
    assert len(results) == 1
    assert results[0].id == "f1"


def test_fact_store_query_by_text():
    store = InMemoryFactStore()
    store.store(Fact(id="f1", content="VP sponsor predicts conversion"))
    store.store(Fact(id="f2", content="Cold email has low response"))
    results = store.query(query="VP sponsor")
    assert len(results) == 1
    assert results[0].id == "f1"


def test_fact_store_query_min_confidence():
    store = InMemoryFactStore()
    store.store(Fact(id="f1", content="High confidence", confidence=0.9))
    store.store(Fact(id="f2", content="Low confidence", confidence=0.3))
    results = store.query(min_confidence=0.5)
    assert len(results) == 1
    assert results[0].id == "f1"


def test_fact_store_query_limit():
    store = InMemoryFactStore()
    for i in range(20):
        store.store(Fact(id=f"f{i}", content=f"fact {i}"))
    results = store.query(limit=5)
    assert len(results) == 5


def test_fact_store_update():
    store = InMemoryFactStore()
    f = Fact(id="f1", content="Original")
    store.store(f)
    f.content = "Updated"
    store.update(f)
    result = store.get("f1")
    assert result.content == "Updated"


def test_fact_store_delete():
    store = InMemoryFactStore()
    store.store(Fact(id="f1", content="To delete"))
    store.delete("f1")
    assert store.get("f1") is None


# --- EpisodicStore ---


def _make_episode(id, agent_id="cro", entity="", domain="", tags=None, ts=None):
    return Episode(
        id=id,
        agent_id=agent_id,
        operator_id="test_op",
        node_name="test_node",
        timestamp=ts or datetime.now(timezone.utc),
        action="test_action",
        input_summary="input",
        output_summary="output",
        outcome={},
        duration_ms=100,
        tokens_in=10,
        tokens_out=20,
        entity=entity,
        domain=domain,
        tags=tags or [],
    )


def test_episodic_store_implements_protocol():
    store = InMemoryEpisodicStore()
    assert isinstance(store, EpisodicStore)


def test_episodic_store_and_query():
    store = InMemoryEpisodicStore()
    store.store(_make_episode("ep1", agent_id="cro"))
    store.store(_make_episode("ep2", agent_id="cro"))
    store.store(_make_episode("ep3", agent_id="cmo"))
    results = store.query("cro")
    assert len(results) == 2


def test_episodic_store_query_by_entity():
    store = InMemoryEpisodicStore()
    store.store(_make_episode("ep1", entity="acme"))
    store.store(_make_episode("ep2", entity="beta"))
    results = store.query("cro", entity="acme")
    assert len(results) == 1


def test_episodic_store_query_by_domain():
    store = InMemoryEpisodicStore()
    store.store(_make_episode("ep1", domain="revenue"))
    store.store(_make_episode("ep2", domain="marketing"))
    results = store.query("cro", domain="revenue")
    assert len(results) == 1


def test_episodic_store_query_since():
    store = InMemoryEpisodicStore()
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recent = datetime(2026, 2, 15, tzinfo=timezone.utc)
    store.store(_make_episode("ep1", ts=old))
    store.store(_make_episode("ep2", ts=recent))
    results = store.query("cro", since=datetime(2026, 2, 1, tzinfo=timezone.utc))
    assert len(results) == 1
    assert results[0].id == "ep2"


def test_episodic_store_query_limit():
    store = InMemoryEpisodicStore()
    for i in range(20):
        store.store(_make_episode(f"ep{i}"))
    results = store.query("cro", limit=5)
    assert len(results) == 5


# --- InsightStore ---


def _make_insight(id, agent_id="cro", content="test", confidence=0.8,
                  entity="", domain="", tags=None):
    return Insight(
        id=id,
        agent_id=agent_id,
        content=content,
        confidence=confidence,
        evidence_count=3,
        source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
        entity=entity,
        domain=domain,
        tags=tags or [],
    )


def test_insight_store_implements_protocol():
    store = InMemoryInsightStore()
    assert isinstance(store, InsightStore)


def test_insight_store_and_query():
    store = InMemoryInsightStore()
    store.store(_make_insight("ins1", content="Webinar leads convert 2x"))
    store.store(_make_insight("ins2", content="Cold email low response"))
    results = store.query("cro")
    assert len(results) == 2


def test_insight_store_query_by_domain():
    store = InMemoryInsightStore()
    store.store(_make_insight("ins1", domain="revenue"))
    store.store(_make_insight("ins2", domain="marketing"))
    results = store.query("cro", domain="revenue")
    assert len(results) == 1


def test_insight_store_query_by_text():
    store = InMemoryInsightStore()
    store.store(_make_insight("ins1", content="VP sponsor predicts conversion"))
    store.store(_make_insight("ins2", content="Email timing matters"))
    results = store.query("cro", query="VP sponsor")
    assert len(results) == 1


def test_insight_store_update():
    store = InMemoryInsightStore()
    ins = _make_insight("ins1", confidence=0.5)
    store.store(ins)
    ins.confidence = 0.9
    store.update(ins)
    results = store.query("cro")
    assert results[0].confidence == 0.9


def test_insight_store_find_similar():
    store = InMemoryInsightStore()
    store.store(_make_insight("ins1", content="Webinar leads convert 2x vs cold inbound"))
    found = store.find_similar("cro", "webinar leads convert")
    assert found is not None
    assert found.id == "ins1"


def test_insight_store_find_similar_no_match():
    store = InMemoryInsightStore()
    store.store(_make_insight("ins1", content="Completely different"))
    found = store.find_similar("cro", "webinar leads")
    assert found is None
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_inmemory_stores.py -v
```

Expected: FAIL

**Step 3: Implement InMemory stores**

Append to `src/openvibe_sdk/memory/in_memory.py` (keep existing InMemoryStore):

```python
# --- V2 InMemory Store Implementations ---

from openvibe_sdk.memory.types import Episode, Fact, Insight


class InMemoryFactStore:
    """In-memory FactStore for development and testing."""

    def __init__(self) -> None:
        self._facts: dict[str, Fact] = {}

    def store(self, fact: Fact) -> None:
        self._facts[fact.id] = fact

    def get(self, fact_id: str) -> Fact | None:
        return self._facts.get(fact_id)

    def query(
        self,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        query: str = "",
        min_confidence: float = 0.0,
        limit: int = 10,
    ) -> list[Fact]:
        results = list(self._facts.values())
        if entity:
            results = [f for f in results if f.entity == entity]
        if domain:
            results = [f for f in results if f.domain == domain]
        if tags:
            results = [f for f in results if any(t in f.tags for t in tags)]
        if query:
            q = query.lower()
            results = [f for f in results if q in f.content.lower()]
        if min_confidence > 0:
            results = [f for f in results if f.confidence >= min_confidence]
        return results[:limit]

    def update(self, fact: Fact) -> None:
        self._facts[fact.id] = fact

    def delete(self, fact_id: str) -> None:
        self._facts.pop(fact_id, None)


class InMemoryEpisodicStore:
    """In-memory EpisodicStore for development and testing."""

    def __init__(self) -> None:
        self._episodes: list[Episode] = []

    def store(self, episode: Episode) -> None:
        self._episodes.append(episode)

    def query(
        self,
        agent_id: str,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        since: "datetime | None" = None,
        limit: int = 50,
    ) -> list[Episode]:
        from datetime import datetime

        results = [e for e in self._episodes if e.agent_id == agent_id]
        if entity:
            results = [e for e in results if e.entity == entity]
        if domain:
            results = [e for e in results if e.domain == domain]
        if tags:
            results = [e for e in results if any(t in e.tags for t in tags)]
        if since:
            results = [e for e in results if e.timestamp >= since]
        return results[:limit]


class InMemoryInsightStore:
    """In-memory InsightStore for development and testing."""

    def __init__(self) -> None:
        self._insights: dict[str, Insight] = {}

    def store(self, insight: Insight) -> None:
        self._insights[insight.id] = insight

    def query(
        self,
        agent_id: str,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        query: str = "",
        limit: int = 10,
    ) -> list[Insight]:
        results = [i for i in self._insights.values() if i.agent_id == agent_id]
        if entity:
            results = [i for i in results if i.entity == entity]
        if domain:
            results = [i for i in results if i.domain == domain]
        if tags:
            results = [i for i in results if any(t in i.tags for t in tags)]
        if query:
            q = query.lower()
            results = [i for i in results if q in i.content.lower()]
        return results[:limit]

    def update(self, insight: Insight) -> None:
        self._insights[insight.id] = insight

    def find_similar(self, agent_id: str, content: str) -> Insight | None:
        q = content.lower()
        for ins in self._insights.values():
            if ins.agent_id == agent_id:
                # Simple word overlap similarity
                q_words = set(q.split())
                ins_words = set(ins.content.lower().split())
                overlap = len(q_words & ins_words)
                if overlap >= min(3, len(q_words)):
                    return ins
        return None
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_inmemory_stores.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/in_memory.py v4/openvibe-sdk/tests/test_inmemory_stores.py
git commit -m "feat(sdk): add InMemoryFactStore, InMemoryEpisodicStore, InMemoryInsightStore"
```

---

## Task 4: Access Control

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/access.py`
- Create: `v4/openvibe-sdk/tests/test_access_control.py`

**Step 1: Write the failing tests**

`tests/test_access_control.py`:
```python
from openvibe_sdk.memory.types import Classification, Fact
from openvibe_sdk.memory.access import (
    CLASSIFICATION_RANK,
    AccessFilter,
    ClearanceProfile,
)


def test_classification_rank_order():
    assert CLASSIFICATION_RANK[Classification.PUBLIC] == 0
    assert CLASSIFICATION_RANK[Classification.INTERNAL] == 1
    assert CLASSIFICATION_RANK[Classification.CONFIDENTIAL] == 2
    assert CLASSIFICATION_RANK[Classification.RESTRICTED] == 3


def test_clearance_public_always_accessible():
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    fact = Fact(id="f1", content="public info", classification=Classification.PUBLIC)
    assert profile.can_access(fact) is True


def test_clearance_internal_with_domain():
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.INTERNAL},
    )
    fact = Fact(
        id="f1", content="internal", domain="revenue",
        classification=Classification.INTERNAL,
    )
    assert profile.can_access(fact) is True


def test_clearance_denied_insufficient():
    profile = ClearanceProfile(
        agent_id="cmo",
        domain_clearance={"marketing": Classification.INTERNAL},
    )
    fact = Fact(
        id="f1", content="secret", domain="revenue",
        classification=Classification.CONFIDENTIAL,
    )
    assert profile.can_access(fact) is False


def test_clearance_denied_no_domain():
    profile = ClearanceProfile(
        agent_id="cmo",
        domain_clearance={"marketing": Classification.CONFIDENTIAL},
    )
    fact = Fact(
        id="f1", content="revenue data", domain="revenue",
        classification=Classification.INTERNAL,
    )
    assert profile.can_access(fact) is False


def test_clearance_confidential_can_access_internal():
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.CONFIDENTIAL},
    )
    fact = Fact(
        id="f1", content="internal data", domain="revenue",
        classification=Classification.INTERNAL,
    )
    assert profile.can_access(fact) is True


def test_access_filter():
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.CONFIDENTIAL},
    )
    facts = [
        Fact(id="f1", content="public", classification=Classification.PUBLIC),
        Fact(id="f2", content="revenue internal", domain="revenue",
             classification=Classification.INTERNAL),
        Fact(id="f3", content="marketing secret", domain="marketing",
             classification=Classification.CONFIDENTIAL),
    ]
    af = AccessFilter(profile)
    filtered = af.filter(facts)
    assert len(filtered) == 2
    assert {f.id for f in filtered} == {"f1", "f2"}
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_access_control.py -v
```

Expected: FAIL

**Step 3: Implement access control**

`src/openvibe_sdk/memory/access.py`:
```python
"""Access control — ClearanceProfile, AccessFilter."""

from __future__ import annotations

from dataclasses import dataclass, field

from openvibe_sdk.memory.types import Classification, Fact

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
    domain_clearance: dict[str, Classification] = field(default_factory=dict)

    def can_access(self, fact: Fact) -> bool:
        """Check if this profile can access a fact."""
        if fact.classification == Classification.PUBLIC:
            return True
        clearance = self.domain_clearance.get(fact.domain)
        if not clearance:
            return False
        return (
            CLASSIFICATION_RANK[clearance]
            >= CLASSIFICATION_RANK[fact.classification]
        )


class AccessFilter:
    """Filter a list of facts by clearance."""

    def __init__(self, clearance: ClearanceProfile) -> None:
        self._clearance = clearance

    def filter(self, facts: list[Fact]) -> list[Fact]:
        return [f for f in facts if self._clearance.can_access(f)]
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_access_control.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/access.py v4/openvibe-sdk/tests/test_access_control.py
git commit -m "feat(sdk): add ClearanceProfile + AccessFilter — domain-based access control"
```

---

## Task 5: WorkspaceMemory

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/workspace.py`
- Create: `v4/openvibe-sdk/tests/test_workspace_memory.py`

**Step 1: Write the failing tests**

`tests/test_workspace_memory.py`:
```python
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.types import Classification, Fact
from openvibe_sdk.memory.workspace import WorkspaceMemory


def test_store_and_query():
    ws = WorkspaceMemory()
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.CONFIDENTIAL},
    )
    ws.store_fact(Fact(
        id="f1", content="Acme data", domain="revenue",
        classification=Classification.INTERNAL,
    ))
    results = ws.query(clearance=profile, domain="revenue")
    assert len(results) == 1
    assert results[0].content == "Acme data"


def test_query_filters_by_clearance():
    ws = WorkspaceMemory()
    ws.store_fact(Fact(
        id="f1", content="Public info", classification=Classification.PUBLIC,
    ))
    ws.store_fact(Fact(
        id="f2", content="Revenue secret", domain="revenue",
        classification=Classification.CONFIDENTIAL,
    ))
    # CMO has no revenue clearance
    cmo_profile = ClearanceProfile(
        agent_id="cmo",
        domain_clearance={"marketing": Classification.INTERNAL},
    )
    results = ws.query(clearance=cmo_profile)
    assert len(results) == 1
    assert results[0].id == "f1"  # only public


def test_query_by_entity():
    ws = WorkspaceMemory()
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    ws.store_fact(Fact(id="f1", content="Acme info", entity="acme",
                       classification=Classification.PUBLIC))
    ws.store_fact(Fact(id="f2", content="Beta info", entity="beta",
                       classification=Classification.PUBLIC))
    results = ws.query(clearance=profile, entity="acme")
    assert len(results) == 1


def test_query_tracks_access():
    ws = WorkspaceMemory()
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    ws.store_fact(Fact(id="f1", content="tracked", classification=Classification.PUBLIC))
    results = ws.query(clearance=profile)
    assert results[0].access_count == 1
    assert results[0].last_accessed is not None


def test_update_fact():
    ws = WorkspaceMemory()
    f = Fact(id="f1", content="Original")
    ws.store_fact(f)
    f.content = "Updated"
    ws.update_fact(f)
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    results = ws.query(clearance=profile, query="Updated")
    assert len(results) == 1


def test_query_respects_limit():
    ws = WorkspaceMemory()
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    for i in range(20):
        ws.store_fact(Fact(id=f"f{i}", content=f"fact {i}",
                           classification=Classification.PUBLIC))
    results = ws.query(clearance=profile, limit=5)
    assert len(results) == 5
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_workspace_memory.py -v
```

Expected: FAIL

**Step 3: Implement WorkspaceMemory**

`src/openvibe_sdk/memory/workspace.py`:
```python
"""WorkspaceMemory — shared org-level fact store with access control."""

from __future__ import annotations

from datetime import datetime, timezone

from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.in_memory import InMemoryFactStore
from openvibe_sdk.memory.stores import FactStore
from openvibe_sdk.memory.types import Fact


class WorkspaceMemory:
    """Shared org-level fact store with access control.

    Wraps a FactStore and filters results by clearance.
    V2: InMemoryFactStore backend. V3+: Postgres/pgvector.
    """

    def __init__(self, fact_store: FactStore | None = None) -> None:
        self._store: FactStore = fact_store or InMemoryFactStore()

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
            entity=entity,
            domain=domain,
            tags=tags,
            query=query,
            limit=limit * 3,
        )
        filtered = [f for f in candidates if clearance.can_access(f)]
        # Track access
        now = datetime.now(timezone.utc)
        for f in filtered[:limit]:
            f.access_count += 1
            f.last_accessed = now
        return filtered[:limit]

    def update_fact(self, fact: Fact) -> None:
        self._store.update(fact)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_workspace_memory.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/workspace.py v4/openvibe-sdk/tests/test_workspace_memory.py
git commit -m "feat(sdk): add WorkspaceMemory — shared fact store with access control"
```

---

## Task 6: AgentMemory

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/agent_memory.py`
- Create: `v4/openvibe-sdk/tests/test_agent_memory.py`

**Step 1: Write the failing tests**

`tests/test_agent_memory.py`:
```python
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.memory import MemoryEntry
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.types import Classification, Episode, Fact, Insight
from openvibe_sdk.memory.workspace import WorkspaceMemory


def _make_episode(id, domain="revenue", output="result"):
    return Episode(
        id=id, agent_id="cro", operator_id="test_op", node_name="test",
        timestamp=datetime.now(timezone.utc), action="test_action",
        input_summary="input", output_summary=output,
        outcome={}, duration_ms=100, tokens_in=10, tokens_out=20,
        domain=domain,
    )


# --- Episode recording ---

def test_record_episode():
    mem = AgentMemory(agent_id="cro")
    ep = _make_episode("ep1")
    mem.record_episode(ep)
    results = mem.recall_episodes()
    assert len(results) == 1
    assert results[0].agent_id == "cro"  # auto-set


def test_recall_episodes_by_domain():
    mem = AgentMemory(agent_id="cro")
    mem.record_episode(_make_episode("ep1", domain="revenue"))
    mem.record_episode(_make_episode("ep2", domain="marketing"))
    results = mem.recall_episodes(domain="revenue")
    assert len(results) == 1


# --- Insight storage ---

def test_store_and_recall_insights():
    mem = AgentMemory(agent_id="cro")
    ins = Insight(
        id="ins1", agent_id="", content="Webinar leads convert 2x",
        confidence=0.8, evidence_count=3, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    )
    mem.store_insight(ins)
    results = mem.recall_insights(domain="revenue")
    assert len(results) == 1
    assert results[0].agent_id == "cro"  # auto-set


def test_recall_insights_by_query():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
    ))
    mem.store_insight(Insight(
        id="ins2", agent_id="cro", content="Email timing matters",
        confidence=0.7, evidence_count=2, source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
    ))
    results = mem.recall_insights(query="VP sponsor")
    assert len(results) == 1


# --- Reflect (L2 → L3) ---

def test_reflect_extracts_insights():
    mem = AgentMemory(agent_id="cro")
    mem.record_episode(_make_episode("ep1", output="lead qualified at 85"))
    mem.record_episode(_make_episode("ep2", output="lead qualified at 90"))

    fake_llm = MagicMock()
    fake_llm.call.return_value = LLMResponse(
        content=json.dumps([
            {"content": "High scores predict conversion", "confidence": 0.7,
             "domain": "revenue", "tags": ["qualification"]},
        ])
    )

    new_insights = mem.reflect(fake_llm)
    assert len(new_insights) == 1
    assert new_insights[0].content == "High scores predict conversion"

    # Insight is stored
    stored = mem.recall_insights()
    assert len(stored) == 1


def test_reflect_strengthens_existing():
    mem = AgentMemory(agent_id="cro")
    # Pre-existing insight
    mem.store_insight(Insight(
        id="ins1", agent_id="cro",
        content="High scores predict conversion",
        confidence=0.5, evidence_count=2, source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
    ))
    mem.record_episode(_make_episode("ep1", output="another high score"))

    fake_llm = MagicMock()
    fake_llm.call.return_value = LLMResponse(
        content=json.dumps([
            {"content": "high scores predict conversion", "confidence": 0.7,
             "domain": "", "tags": []},
        ])
    )

    mem.reflect(fake_llm)

    stored = mem.recall_insights()
    assert len(stored) == 1
    assert stored[0].confidence == 0.6  # 0.5 + 0.1
    assert stored[0].evidence_count == 3


def test_reflect_no_episodes():
    mem = AgentMemory(agent_id="cro")
    fake_llm = MagicMock()
    result = mem.reflect(fake_llm)
    assert result == []
    fake_llm.call.assert_not_called()


# --- Publish to workspace ---

def test_publish_to_workspace():
    ws = WorkspaceMemory()
    mem = AgentMemory(agent_id="cro", workspace=ws)
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="High confidence insight",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
    ))
    mem.store_insight(Insight(
        id="ins2", agent_id="cro", content="Low confidence",
        confidence=0.3, evidence_count=1, source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
    ))

    published = mem.publish_to_workspace(min_confidence=0.5)
    assert len(published) == 1
    assert published[0].content == "High confidence insight"
    assert published[0].source == "cro"


def test_publish_no_workspace():
    mem = AgentMemory(agent_id="cro")
    result = mem.publish_to_workspace()
    assert result == []


# --- V1 backward compat ---

def test_v1_compat_store_and_recall():
    mem = AgentMemory(agent_id="cro")
    mem.store("cro", "k1", "webinar leads convert 2x")
    results = mem.recall("cro", "webinar")
    assert len(results) == 1
    assert isinstance(results[0], MemoryEntry)
    assert results[0].content == "webinar leads convert 2x"


def test_v1_compat_recall_empty():
    mem = AgentMemory(agent_id="cro")
    results = mem.recall("cro", "nothing")
    assert results == []


def test_v1_compat_delete_noop():
    mem = AgentMemory(agent_id="cro")
    mem.delete("cro", "k1")  # should not raise
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_agent_memory.py -v
```

Expected: FAIL

**Step 3: Implement AgentMemory**

`src/openvibe_sdk/memory/agent_memory.py`:
```python
"""AgentMemory — per-agent L2 episodes + L3 insights + workspace reference."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from openvibe_sdk.memory import MemoryEntry
from openvibe_sdk.memory.in_memory import InMemoryEpisodicStore, InMemoryInsightStore
from openvibe_sdk.memory.stores import EpisodicStore, InsightStore
from openvibe_sdk.memory.types import Classification, Episode, Fact, Insight
from openvibe_sdk.memory.workspace import WorkspaceMemory


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


def _parse_insights(text: str, agent_id: str) -> list[Insight]:
    """Parse LLM response into Insight objects."""
    try:
        items = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    now = datetime.now(timezone.utc)
    insights = []
    for item in items:
        if not isinstance(item, dict) or "content" not in item:
            continue
        insights.append(Insight(
            id=f"ins_{_short_id()}",
            agent_id=agent_id,
            content=item["content"],
            confidence=float(item.get("confidence", 0.5)),
            evidence_count=1,
            source_episode_ids=[],
            created_at=now,
            domain=item.get("domain", ""),
            tags=item.get("tags", []),
        ))
    return insights


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
    ) -> None:
        self.agent_id = agent_id
        self.workspace = workspace
        self._episodic: EpisodicStore = episodic or InMemoryEpisodicStore()
        self._insights: InsightStore = insights or InMemoryInsightStore()

    # --- L2: Episodes ---

    def record_episode(self, episode: Episode) -> None:
        episode.agent_id = self.agent_id
        self._episodic.store(episode)

    def recall_episodes(
        self,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        since: datetime | None = None,
        limit: int = 10,
    ) -> list[Episode]:
        return self._episodic.query(
            self.agent_id,
            entity=entity,
            domain=domain,
            tags=tags,
            since=since,
            limit=limit,
        )

    # --- L3: Insights ---

    def recall_insights(
        self,
        entity: str | None = None,
        domain: str | None = None,
        tags: list[str] | None = None,
        query: str = "",
        limit: int = 10,
    ) -> list[Insight]:
        return self._insights.query(
            self.agent_id,
            entity=entity,
            domain=domain,
            tags=tags,
            query=query,
            limit=limit,
        )

    def store_insight(self, insight: Insight) -> None:
        insight.agent_id = self.agent_id
        self._insights.store(insight)

    # --- Reflection: L2 → L3 ---

    def reflect(self, llm: Any, role_context: str = "") -> list[Insight]:
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
        published: list[Fact] = []
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

    def recall(
        self, namespace: str, query: str, limit: int = 10
    ) -> list[MemoryEntry]:
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

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent_memory.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/agent_memory.py v4/openvibe-sdk/tests/test_agent_memory.py
git commit -m "feat(sdk): add AgentMemory — L2 episodes + L3 insights + reflect + V1 compat"
```

---

## Task 7: MemoryFilesystem

The filesystem interface from the Role Layer Design. Virtual paths map to store queries.

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/filesystem.py`
- Create: `v4/openvibe-sdk/tests/test_memory_filesystem.py`

**Step 1: Write the failing tests**

`tests/test_memory_filesystem.py`:
```python
from datetime import datetime, timezone

from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.filesystem import MemoryFilesystem
from openvibe_sdk.memory.types import Episode, Insight
from openvibe_sdk.memory.workspace import WorkspaceMemory
from openvibe_sdk.memory.types import Classification, Fact


# --- Browse ---

def test_browse_root():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem, soul="You are the CRO.")
    entries = fs.browse("/")
    assert "identity" in entries
    assert "knowledge" in entries
    assert "experience" in entries
    assert "references" in entries


def test_browse_identity():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem, soul="You are the CRO.")
    entries = fs.browse("/identity/")
    assert "soul.md" in entries


def test_browse_knowledge_lists_domains():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="Revenue insight",
        confidence=0.8, evidence_count=3, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    mem.store_insight(Insight(
        id="ins2", agent_id="cro", content="Marketing insight",
        confidence=0.7, evidence_count=2, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="marketing",
    ))
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    entries = fs.browse("/knowledge/")
    assert "revenue" in entries
    assert "marketing" in entries


def test_browse_knowledge_domain():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
        tags=["qualification"],
    ))
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    entries = fs.browse("/knowledge/revenue/")
    assert len(entries) >= 1


# --- Read ---

def test_read_identity_soul():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem, soul="You are the CRO.")
    content = fs.read("/identity/soul.md")
    assert content == "You are the CRO."


def test_read_knowledge_insight():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    content = fs.read("/knowledge/revenue/ins1")
    assert "VP sponsor predicts conversion" in content


def test_read_missing_returns_empty():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    content = fs.read("/knowledge/nonexistent/nothing")
    assert content == ""


# --- Search ---

def test_search_scoped():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    mem.store_insight(Insight(
        id="ins2", agent_id="cro", content="Brand voice matters",
        confidence=0.8, evidence_count=3, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="marketing",
    ))
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    results = fs.search("VP sponsor", scope="/knowledge/revenue/")
    assert len(results) == 1
    assert "VP sponsor" in results[0]["content"]


def test_search_global():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    results = fs.search("VP sponsor")
    assert len(results) >= 1


# --- Write ---

def test_write_knowledge():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    fs.write("/knowledge/revenue/new-principle", "Enterprise deals need VP sponsor")
    results = mem.recall_insights(domain="revenue")
    assert len(results) == 1
    assert "VP sponsor" in results[0].content


def test_write_experience():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    fs.write("/experience/2026-02/qualified-acme", "Qualified Acme Corp at 85")
    results = mem.recall_episodes()
    assert len(results) == 1


# --- Observable traces ---

def test_traces_recorded():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem, soul="CRO soul")
    fs.browse("/")
    fs.read("/identity/soul.md")
    fs.search("test")
    traces = fs.traces
    assert len(traces) == 3
    assert traces[0].action == "browse"
    assert traces[1].action == "read"
    assert traces[2].action == "search"


def test_clear_traces():
    mem = AgentMemory(agent_id="cro")
    fs = MemoryFilesystem(role_id="cro", agent_memory=mem)
    fs.browse("/")
    assert len(fs.traces) == 1
    fs.clear_traces()
    assert len(fs.traces) == 0
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_memory_filesystem.py -v
```

Expected: FAIL

**Step 3: Implement MemoryFilesystem**

`src/openvibe_sdk/memory/filesystem.py`:
```python
"""MemoryFilesystem — virtual filesystem interface over memory stores.

Provides browse/read/search/write that the LLM uses to navigate its own memory.
Maps virtual paths to AgentMemory store queries.

Path structure:
    /identity/soul.md         → soul text (read-only)
    /knowledge/{domain}/...   → insights (InsightStore)
    /experience/{date}/...    → episodes (EpisodicStore)
    /references/{domain}/...  → workspace facts (external sources)
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.types import Episode, Insight, RetrievalTrace


class MemoryFilesystem:
    """Virtual filesystem interface over memory stores."""

    # Directories available in V2
    _ROOT_DIRS = ["identity", "knowledge", "experience", "references"]

    def __init__(
        self,
        role_id: str,
        agent_memory: AgentMemory,
        soul: str = "",
    ) -> None:
        self._role_id = role_id
        self._memory = agent_memory
        self._soul = soul
        self._traces: list[RetrievalTrace] = []

    @property
    def traces(self) -> list[RetrievalTrace]:
        return list(self._traces)

    def clear_traces(self) -> None:
        self._traces.clear()

    def browse(self, path: str = "/") -> list[str]:
        """List entries at path."""
        start = time.monotonic()
        path = path.strip("/")
        parts = path.split("/") if path else []

        if not parts:
            entries = list(self._ROOT_DIRS)
        elif parts[0] == "identity":
            entries = ["soul.md"] if self._soul else []
        elif parts[0] == "knowledge":
            entries = self._browse_knowledge(parts[1:])
        elif parts[0] == "experience":
            entries = self._browse_experience(parts[1:])
        elif parts[0] == "references":
            entries = self._browse_references(parts[1:])
        else:
            entries = []

        duration_ms = int((time.monotonic() - start) * 1000)
        self._traces.append(RetrievalTrace(
            action="browse", path=f"/{path}/",
            results_count=len(entries), duration_ms=duration_ms,
        ))
        return entries

    def read(self, path: str) -> str:
        """Read content at path."""
        start = time.monotonic()
        path = path.strip("/")
        parts = path.split("/") if path else []
        content = ""

        if len(parts) >= 2 and parts[0] == "identity" and parts[1] == "soul.md":
            content = self._soul
        elif len(parts) >= 2 and parts[0] == "knowledge":
            content = self._read_knowledge(parts[1:])
        elif len(parts) >= 2 and parts[0] == "experience":
            content = self._read_experience(parts[1:])
        elif len(parts) >= 2 and parts[0] == "references":
            content = self._read_references(parts[1:])

        tokens = len(content) // 4  # rough estimate
        duration_ms = int((time.monotonic() - start) * 1000)
        self._traces.append(RetrievalTrace(
            action="read", path=f"/{path}",
            tokens_loaded=tokens, duration_ms=duration_ms,
        ))
        return content

    def search(self, query: str, scope: str = "/") -> list[dict[str, Any]]:
        """Search within scope. Returns [{path, content, score}]."""
        start = time.monotonic()
        scope = scope.strip("/")
        parts = scope.split("/") if scope else []
        results: list[dict[str, Any]] = []

        domain = parts[1] if len(parts) >= 2 and parts[0] == "knowledge" else None

        # Search insights
        insights = self._memory.recall_insights(
            domain=domain, query=query, limit=10,
        )
        for ins in insights:
            results.append({
                "path": f"/knowledge/{ins.domain or '_'}/{ins.id}",
                "content": ins.content,
                "confidence": ins.confidence,
            })

        # Search episodes
        if not parts or parts[0] in ("", "experience"):
            episodes = self._memory.recall_episodes(limit=5)
            for ep in episodes:
                if query.lower() in ep.output_summary.lower():
                    results.append({
                        "path": f"/experience/{ep.id}",
                        "content": ep.output_summary,
                    })

        duration_ms = int((time.monotonic() - start) * 1000)
        self._traces.append(RetrievalTrace(
            action="search", path=f"/{scope}",
            query=query, results_count=len(results),
            duration_ms=duration_ms,
        ))
        return results

    def write(self, path: str, content: str, **metadata: Any) -> None:
        """Write content at path. Path determines store type."""
        start = time.monotonic()
        path = path.strip("/")
        parts = path.split("/") if path else []

        if len(parts) >= 2 and parts[0] == "knowledge":
            domain = parts[1] if len(parts) >= 2 else ""
            tags = parts[2:-1] if len(parts) > 3 else []
            self._memory.store_insight(Insight(
                id=parts[-1] if len(parts) >= 3 else uuid.uuid4().hex[:8],
                agent_id=self._role_id,
                content=content,
                confidence=metadata.get("confidence", 0.5),
                evidence_count=1,
                source_episode_ids=[],
                created_at=datetime.now(timezone.utc),
                domain=domain,
                tags=tags,
            ))
        elif len(parts) >= 2 and parts[0] == "experience":
            self._memory.record_episode(Episode(
                id=parts[-1] if len(parts) >= 2 else uuid.uuid4().hex[:8],
                agent_id=self._role_id,
                operator_id=metadata.get("operator_id", ""),
                node_name=metadata.get("node_name", ""),
                timestamp=datetime.now(timezone.utc),
                action=parts[-1] if len(parts) >= 2 else "write",
                input_summary="",
                output_summary=content[:200],
                outcome={"content": content},
                duration_ms=0,
                tokens_in=0,
                tokens_out=0,
                domain=metadata.get("domain", ""),
            ))

        duration_ms = int((time.monotonic() - start) * 1000)
        self._traces.append(RetrievalTrace(
            action="write", path=f"/{path}",
            duration_ms=duration_ms,
        ))

    # --- Private helpers ---

    def _browse_knowledge(self, parts: list[str]) -> list[str]:
        """Browse /knowledge/ — lists domains, then insights within domain."""
        if not parts:
            # List all domains
            insights = self._memory.recall_insights(limit=100)
            domains = {i.domain for i in insights if i.domain}
            return sorted(domains)
        # List insights in domain
        domain = parts[0]
        insights = self._memory.recall_insights(domain=domain, limit=50)
        return [i.id for i in insights]

    def _browse_experience(self, parts: list[str]) -> list[str]:
        """Browse /experience/ — lists episodes."""
        episodes = self._memory.recall_episodes(limit=50)
        return [ep.id for ep in episodes]

    def _browse_references(self, parts: list[str]) -> list[str]:
        """Browse /references/ — lists workspace facts (external)."""
        if not self._memory.workspace:
            return []
        # Would need clearance to query — return empty for now
        return []

    def _read_knowledge(self, parts: list[str]) -> str:
        """Read /knowledge/{domain}/{id}."""
        if len(parts) < 2:
            return ""
        domain = parts[0]
        insight_id = parts[1]
        insights = self._memory.recall_insights(domain=domain, limit=100)
        for ins in insights:
            if ins.id == insight_id:
                return f"{ins.content}\n\nConfidence: {ins.confidence}\nEvidence: {ins.evidence_count}"
        return ""

    def _read_experience(self, parts: list[str]) -> str:
        """Read /experience/{id}."""
        if not parts:
            return ""
        ep_id = parts[-1]
        episodes = self._memory.recall_episodes(limit=100)
        for ep in episodes:
            if ep.id == ep_id:
                return (
                    f"Action: {ep.action}\n"
                    f"Input: {ep.input_summary}\n"
                    f"Output: {ep.output_summary}\n"
                    f"Duration: {ep.duration_ms}ms"
                )
        return ""

    def _read_references(self, parts: list[str]) -> str:
        """Read /references/{domain}/{id}."""
        return ""  # requires clearance — implement in V3
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_memory_filesystem.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/filesystem.py v4/openvibe-sdk/tests/test_memory_filesystem.py
git commit -m "feat(sdk): add MemoryFilesystem — virtual filesystem interface over memory stores"
```

---

## Task 8: MemoryAssembler

**Files:**
- Create: `v4/openvibe-sdk/src/openvibe_sdk/memory/assembler.py`
- Create: `v4/openvibe-sdk/tests/test_memory_assembler.py`

**Step 1: Write the failing tests**

`tests/test_memory_assembler.py`:
```python
from datetime import datetime, timezone

from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.assembler import MemoryAssembler
from openvibe_sdk.memory.types import Classification, Episode, Fact, Insight
from openvibe_sdk.memory.workspace import WorkspaceMemory


def test_assemble_insights():
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    assembler = MemoryAssembler(mem, profile)
    result = assembler.assemble({"domain": "revenue"})
    assert "VP sponsor" in result
    assert "Insights" in result


def test_assemble_workspace_facts():
    ws = WorkspaceMemory()
    ws.store_fact(Fact(
        id="f1", content="Acme has 200 employees",
        entity="acme", domain="customer",
        classification=Classification.PUBLIC,
    ))
    mem = AgentMemory(agent_id="cro", workspace=ws)
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    assembler = MemoryAssembler(mem, profile)
    result = assembler.assemble({"entity": "acme"})
    assert "200 employees" in result


def test_assemble_recent_episodes():
    mem = AgentMemory(agent_id="cro")
    mem.record_episode(Episode(
        id="ep1", agent_id="cro", operator_id="test", node_name="qualify",
        timestamp=datetime.now(timezone.utc), action="qualify_lead",
        input_summary="Score Acme", output_summary="Score: 85",
        outcome={}, duration_ms=100, tokens_in=10, tokens_out=20,
    ))
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    assembler = MemoryAssembler(mem, profile)
    result = assembler.assemble({})
    assert "Recent Activity" in result
    assert "qualify_lead" in result


def test_assemble_priority_order():
    """Insights come before facts come before episodes."""
    ws = WorkspaceMemory()
    ws.store_fact(Fact(
        id="f1", content="Fact content",
        classification=Classification.PUBLIC,
    ))
    mem = AgentMemory(agent_id="cro", workspace=ws)
    mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="Insight content",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc),
    ))
    mem.record_episode(Episode(
        id="ep1", agent_id="cro", operator_id="test", node_name="test",
        timestamp=datetime.now(timezone.utc), action="test",
        input_summary="in", output_summary="Episode content",
        outcome={}, duration_ms=100, tokens_in=10, tokens_out=20,
    ))
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    assembler = MemoryAssembler(mem, profile)
    result = assembler.assemble({})
    # Insights section should come first
    ins_pos = result.index("Insights")
    ctx_pos = result.index("Context")
    act_pos = result.index("Recent Activity")
    assert ins_pos < ctx_pos < act_pos


def test_assemble_token_budget():
    mem = AgentMemory(agent_id="cro")
    for i in range(50):
        mem.store_insight(Insight(
            id=f"ins{i}", agent_id="cro",
            content=f"A very long insight number {i} " * 20,
            confidence=0.9, evidence_count=5, source_episode_ids=[],
            created_at=datetime.now(timezone.utc),
        ))
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    assembler = MemoryAssembler(mem, profile)
    result = assembler.assemble({}, token_budget=100)
    assert len(result) <= 100 * 4  # 4 chars per token


def test_assemble_empty():
    mem = AgentMemory(agent_id="cro")
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    assembler = MemoryAssembler(mem, profile)
    result = assembler.assemble({})
    assert result == ""
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_memory_assembler.py -v
```

Expected: FAIL

**Step 3: Implement MemoryAssembler**

`src/openvibe_sdk/memory/assembler.py`:
```python
"""MemoryAssembler — builds memory context string for LLM calls.

Assembles from agent insights (L3) + workspace facts + recent episodes (L2).
Filters by clearance. Respects token budget.
"""

from __future__ import annotations

from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.agent_memory import AgentMemory


class MemoryAssembler:
    """Builds memory context string from scope.

    Priority: insights (L3) > workspace facts > recent episodes (L2).
    """

    def __init__(
        self,
        agent_memory: AgentMemory,
        clearance: ClearanceProfile,
    ) -> None:
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
            lines = [
                f"- {i.content} (confidence: {i.confidence:.1f})"
                for i in insights
            ]
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

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_memory_assembler.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/memory/assembler.py v4/openvibe-sdk/tests/test_memory_assembler.py
git commit -m "feat(sdk): add MemoryAssembler — scope-based context assembly with token budget"
```

---

## Task 9: AuthorityConfig

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/models.py`
- Create: `v4/openvibe-sdk/tests/test_authority.py`

**Step 1: Write the failing tests**

`tests/test_authority.py`:
```python
from openvibe_sdk.models import AuthorityConfig


def test_autonomous_action():
    auth = AuthorityConfig(
        autonomous=["qualify_lead", "trigger_nurture"],
        needs_approval=["change_pricing"],
        forbidden=["sign_contracts"],
    )
    assert auth.can_act("qualify_lead") == "autonomous"


def test_needs_approval_action():
    auth = AuthorityConfig(
        autonomous=["qualify_lead"],
        needs_approval=["change_pricing"],
        forbidden=[],
    )
    assert auth.can_act("change_pricing") == "needs_approval"


def test_forbidden_action():
    auth = AuthorityConfig(
        autonomous=[],
        needs_approval=[],
        forbidden=["sign_contracts"],
    )
    assert auth.can_act("sign_contracts") == "forbidden"


def test_unknown_defaults_to_needs_approval():
    auth = AuthorityConfig(autonomous=["qualify_lead"])
    assert auth.can_act("unknown_action") == "needs_approval"


def test_forbidden_takes_priority():
    auth = AuthorityConfig(
        autonomous=["do_thing"],
        forbidden=["do_thing"],
    )
    assert auth.can_act("do_thing") == "forbidden"
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_authority.py -v
```

Expected: FAIL — `ImportError: cannot import name 'AuthorityConfig' from 'openvibe_sdk.models'`

**Step 3: Add AuthorityConfig to models.py**

Append to `src/openvibe_sdk/models.py`:

```python
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

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_authority.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/models.py v4/openvibe-sdk/tests/test_authority.py
git commit -m "feat(sdk): add AuthorityConfig — action authorization for Roles"
```

---

## Task 10: Operator + Decorator Changes

Add `memory_scope` param to `@llm_node` and `@agent_node`. Add `memory_assembler` and `_episode_recorder` to Operator.

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/operator.py`
- Create: `v4/openvibe-sdk/tests/test_memory_scope.py`

**Step 1: Write the failing tests**

`tests/test_memory_scope.py`:
```python
import json
import time
from datetime import datetime, timezone

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.operator import Operator, agent_node, llm_node
from openvibe_sdk.memory.types import Episode


class FakeLLM:
    def __init__(self, content="output"):
        self.content = content
        self.last_system = None

    def call(self, *, system, messages, **kwargs):
        self.last_system = system
        return LLMResponse(content=self.content, tokens_in=10, tokens_out=20)


class FakeAssembler:
    def __init__(self, context="## Insights\n- VP sponsor predicts conversion"):
        self.context = context
        self.last_scope = None

    def assemble(self, scope, token_budget=2000):
        self.last_scope = scope
        return self.context


# --- memory_scope on @llm_node ---

class ScopedOp(Operator):
    operator_id = "scoped"

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


def test_memory_scope_resolved_and_assembled():
    llm = FakeLLM()
    assembler = FakeAssembler()
    op = ScopedOp(llm=llm, memory_assembler=assembler)
    op.qualify({"lead": "Acme", "company": "acme_corp"})

    # Scope should be resolved (lambda called)
    assert assembler.last_scope["domain"] == "revenue"
    assert assembler.last_scope["entity"] == "acme_corp"
    assert assembler.last_scope["tags"] == ["qualification"]


def test_memory_scope_injected_into_system_prompt():
    llm = FakeLLM()
    assembler = FakeAssembler(context="## Insights\n- Test insight")
    op = ScopedOp(llm=llm, memory_assembler=assembler)
    op.qualify({"lead": "Acme", "company": "acme_corp"})

    assert "Test insight" in llm.last_system
    assert "You are a lead qualifier." in llm.last_system


def test_no_memory_scope_backward_compat():
    """@llm_node without memory_scope works exactly as V1."""

    class SimpleOp(Operator):
        @llm_node(model="haiku", output_key="out")
        def process(self, state):
            """You are a processor."""
            return "process this"

    llm = FakeLLM(response_content="done") if False else FakeLLM("done")
    op = SimpleOp(llm=llm)
    result = op.process({"input": "x"})
    assert result["out"] == "done"
    assert llm.last_system == "You are a processor."


def test_no_assembler_memory_scope_ignored():
    """If no assembler wired, memory_scope is silently ignored."""
    llm = FakeLLM()
    op = ScopedOp(llm=llm)  # no memory_assembler
    result = op.qualify({"lead": "Acme", "company": "acme_corp"})
    assert "score" in result
    assert llm.last_system == "You are a lead qualifier."


# --- Episode auto-recording ---

def test_episode_auto_recorded():
    recorded = []

    def recorder(ep):
        recorded.append(ep)

    llm = FakeLLM('{"score": 85}')
    op = ScopedOp(llm=llm, memory_assembler=FakeAssembler())
    op._episode_recorder = recorder
    op.qualify({"lead": "Acme", "company": "acme_corp"})

    assert len(recorded) == 1
    ep = recorded[0]
    assert isinstance(ep, Episode)
    assert ep.operator_id == "scoped"
    assert ep.node_name == "qualify"
    assert ep.domain == "revenue"
    assert ep.tokens_in == 10
    assert ep.tokens_out == 20


def test_no_recorder_no_error():
    llm = FakeLLM()
    op = ScopedOp(llm=llm)
    op.qualify({"lead": "Acme", "company": "acme_corp"})
    # Should not raise


# --- memory_scope on @agent_node ---

class AgentScopedOp(Operator):
    operator_id = "agent_scoped"

    @agent_node(
        tools=[],
        output_key="research",
        memory_scope={"domain": "revenue"},
    )
    def investigate(self, state):
        """You are a research analyst."""
        return f"Research: {state['topic']}"


def test_agent_node_memory_scope():
    llm = FakeLLM("research results")
    assembler = FakeAssembler(context="## Insights\n- Agent insight")
    op = AgentScopedOp(llm=llm, memory_assembler=assembler)
    result = op.investigate({"topic": "AI"})

    assert assembler.last_scope["domain"] == "revenue"
    assert "Agent insight" in llm.last_system
    assert result["research"] == "research results"


def test_agent_node_episode_recorded():
    recorded = []

    def recorder(ep):
        recorded.append(ep)

    llm = FakeLLM("done")
    op = AgentScopedOp(llm=llm)
    op._episode_recorder = recorder
    op.investigate({"topic": "AI"})

    assert len(recorded) == 1
    assert recorded[0].node_name == "investigate"
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_memory_scope.py -v
```

Expected: FAIL

**Step 3: Modify operator.py**

Update `Operator.__init__` to accept `memory_assembler`:

```python
class Operator:
    operator_id: str = ""

    def __init__(self, llm=None, config=None, memory_assembler=None):
        self.llm = llm
        self.config = config
        self._memory_assembler = memory_assembler
        self._episode_recorder = None  # set by Role
```

Update `llm_node` decorator to support `memory_scope` and episode recording:

```python
def llm_node(
    model="haiku",
    temperature=0.7,
    max_tokens=4096,
    output_key=None,
    memory_scope=None,
):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, state):
            import time as _time
            import uuid as _uuid
            from datetime import datetime, timezone

            system_prompt = (method.__doc__ or "").strip()
            user_message = method(self, state)

            # V2: Resolve memory_scope and assemble context
            resolved_scope = {}
            if memory_scope and self._memory_assembler:
                for key, val in memory_scope.items():
                    resolved_scope[key] = val(state) if callable(val) else val
                memory_context = self._memory_assembler.assemble(resolved_scope)
                if memory_context:
                    system_prompt = f"{system_prompt}\n\n{memory_context}"

            start_time = _time.monotonic()
            response = self.llm.call(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                model=model, max_tokens=max_tokens, temperature=temperature,
            )
            duration_ms = int((_time.monotonic() - start_time) * 1000)

            result = _try_json_parse(response.content)
            if output_key:
                state[output_key] = result

            # V2: Auto-record episode
            if self._episode_recorder:
                if memory_scope:
                    for key, val in memory_scope.items():
                        if key not in resolved_scope:
                            resolved_scope[key] = val(state) if callable(val) else val
                from openvibe_sdk.memory.types import Episode
                episode = Episode(
                    id=f"ep_{_uuid.uuid4().hex[:8]}",
                    agent_id="",
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
                    entity=resolved_scope.get("entity", ""),
                    domain=resolved_scope.get("domain", ""),
                    tags=resolved_scope.get("tags", []),
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

Apply the same pattern to `agent_node` — add `memory_scope` param, resolve scope, assemble context into system prompt, and record episode after completion.

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_memory_scope.py -v
```

Expected: all PASS

**Step 5: Run ALL tests (V1 + V2)**

```bash
pytest tests/ -v
```

Expected: all PASS (V1 tests must not break)

**Step 6: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/operator.py v4/openvibe-sdk/tests/test_memory_scope.py
git commit -m "feat(sdk): add memory_scope + auto episode recording to decorators"
```

---

## Task 11: Role + _RoleAwareLLM Changes

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/role.py`
- Create: `v4/openvibe-sdk/tests/test_role_v2.py`

**Step 1: Write the failing tests**

`tests/test_role_v2.py`:
```python
from datetime import datetime, timezone

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.assembler import MemoryAssembler
from openvibe_sdk.memory.types import Classification, Insight
from openvibe_sdk.memory.workspace import WorkspaceMemory
from openvibe_sdk.models import AuthorityConfig
from openvibe_sdk.operator import Operator, llm_node
from openvibe_sdk.role import Role, _RoleAwareLLM


class FakeLLM:
    def __init__(self, content="output"):
        self.content = content
        self.last_system = None

    def call(self, *, system, messages, **kwargs):
        self.last_system = system
        return LLMResponse(content=self.content, tokens_in=10, tokens_out=20)


class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(
        model="sonnet", output_key="score",
        memory_scope={"domain": "revenue"},
    )
    def qualify(self, state):
        """You are a lead qualifier."""
        return f"Score: {state.get('lead', '')}"


class CRO(Role):
    role_id = "cro"
    soul = "You are the CRO. Data-driven."
    operators = [RevenueOps]
    authority = AuthorityConfig(
        autonomous=["qualify_lead"],
        needs_approval=["change_pricing"],
        forbidden=["sign_contracts"],
    )
    clearance = ClearanceProfile(
        agent_id="cro",
        domain_clearance={
            "revenue": Classification.CONFIDENTIAL,
            "customer": Classification.INTERNAL,
        },
    )


# --- Authority ---

def test_role_can_act_autonomous():
    role = CRO(llm=FakeLLM())
    assert role.can_act("qualify_lead") == "autonomous"


def test_role_can_act_forbidden():
    role = CRO(llm=FakeLLM())
    assert role.can_act("sign_contracts") == "forbidden"


def test_role_can_act_no_authority():
    class NoAuth(Role):
        role_id = "noauth"
        operators = []

    role = NoAuth(llm=FakeLLM())
    assert role.can_act("anything") == "autonomous"


# --- AgentMemory wiring ---

def test_operator_gets_memory_assembler():
    agent_mem = AgentMemory(agent_id="cro")
    agent_mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="Revenue insight",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    role = CRO(llm=FakeLLM(), agent_memory=agent_mem)
    op = role.get_operator("revenue_ops")
    assert op._memory_assembler is not None


def test_operator_gets_episode_recorder():
    agent_mem = AgentMemory(agent_id="cro")
    role = CRO(llm=FakeLLM(), agent_memory=agent_mem)
    op = role.get_operator("revenue_ops")
    assert op._episode_recorder is not None


def test_memory_scope_assembled_via_role():
    llm = FakeLLM()
    agent_mem = AgentMemory(agent_id="cro")
    agent_mem.store_insight(Insight(
        id="ins1", agent_id="cro", content="Test insight for revenue",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))
    role = CRO(llm=llm, agent_memory=agent_mem)
    op = role.get_operator("revenue_ops")
    op.qualify({"lead": "Acme"})

    # System prompt should have soul + memory_scope assembled content
    assert "CRO" in llm.last_system
    assert "Test insight for revenue" in llm.last_system


# --- _RoleAwareLLM: soul-only when agent_memory ---

def test_role_aware_llm_soul_only_with_agent_memory():
    """When agent_memory exists, _RoleAwareLLM injects soul only (not V1 memory)."""
    llm = FakeLLM()
    agent_mem = AgentMemory(agent_id="cro")
    role = CRO(llm=llm, agent_memory=agent_mem)
    op = role.get_operator("revenue_ops")
    op.qualify({"lead": "Acme"})

    # Should have soul but NOT "Relevant Memories" section
    assert "CRO" in llm.last_system
    assert "Relevant Memories" not in llm.last_system


# --- V1 backward compat ---

def test_v1_memory_still_works():
    """V1 Role(memory=InMemoryStore()) still works."""
    from openvibe_sdk.memory.in_memory import InMemoryStore

    llm = FakeLLM()
    memory = InMemoryStore()
    memory.store("cro", "m1", "Webinar leads convert 2x")

    class V1Role(Role):
        role_id = "cro"
        soul = "You are the CRO."
        operators = [RevenueOps]

    role = V1Role(llm=llm, memory=memory)
    op = role.get_operator("revenue_ops")
    op.qualify({"lead": "Acme"})

    # V1 behavior: _RoleAwareLLM injects memories
    assert "Webinar leads convert 2x" in llm.last_system
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_role_v2.py -v
```

Expected: FAIL

**Step 3: Modify role.py**

Add to `Role` class:
- `authority: AuthorityConfig | None` class attribute
- `clearance: ClearanceProfile | None` class attribute
- `agent_memory: AgentMemory | None` init param
- `can_act()` method
- Update `get_operator()` to wire memory_assembler + episode_recorder

Update `_RoleAwareLLM` to skip V1 memory injection when `agent_memory` exists.

```python
class Role:
    role_id: str = ""
    soul: str = ""
    operators: list[type[Operator]] = []
    authority: AuthorityConfig | None = None
    clearance: ClearanceProfile | None = None

    def __init__(self, llm=None, memory=None, agent_memory=None, config=None):
        self.llm = llm
        self.memory = memory
        self.agent_memory = agent_memory
        self.config = config or {}
        self._operator_instances = {}

    def can_act(self, action: str) -> str:
        if not self.authority:
            return "autonomous"
        return self.authority.can_act(action)

    def get_operator(self, operator_id):
        if operator_id not in self._operator_instances:
            for op_class in self.operators:
                if op_class.operator_id == operator_id:
                    wrapped_llm = _RoleAwareLLM(self, self.llm) if self.llm else None

                    # V2: wire up memory assembler
                    assembler = None
                    if self.agent_memory:
                        clearance = self.clearance or ClearanceProfile(
                            agent_id=self.role_id, domain_clearance={},
                        )
                        assembler = MemoryAssembler(self.agent_memory, clearance)

                    op = op_class(llm=wrapped_llm, memory_assembler=assembler)

                    # V2: wire up episode recorder
                    if self.agent_memory:
                        op._episode_recorder = self.agent_memory.record_episode

                    self._operator_instances[operator_id] = op
                    break
            else:
                raise ValueError(f"Role '{self.role_id}' has no operator '{operator_id}'")
        return self._operator_instances[operator_id]
```

Update `_RoleAwareLLM.call()`:
```python
def call(self, *, system, messages, **kwargs):
    # Soul injection (always)
    soul_text = self._role._load_soul()
    if soul_text:
        system = f"{soul_text}\n\n{system}"

    # V1 memory injection (only if no agent_memory)
    if self._role.memory and not self._role.agent_memory:
        context = messages[0].get("content", "") if messages else ""
        if isinstance(context, str) and context:
            recalled = self._role.memory.recall(self._role.role_id, context)
            if recalled:
                mem_text = "\n## Relevant Memories\n" + "\n".join(
                    f"- {m.content}" for m in recalled
                )
                system = f"{system}\n\n{mem_text}"

    return self._inner.call(system=system, messages=messages, **kwargs)
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_role_v2.py -v
```

Expected: all PASS

**Step 5: Run ALL tests**

```bash
pytest tests/ -v
```

Expected: all PASS (V1 + V2)

**Step 6: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/role.py v4/openvibe-sdk/tests/test_role_v2.py
git commit -m "feat(sdk): add authority, clearance, agent_memory to Role — V2 identity layer"
```

---

## Task 12: RoleRuntime + Public API + Integration

**Files:**
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/runtime.py`
- Modify: `v4/openvibe-sdk/src/openvibe_sdk/__init__.py`
- Create: `v4/openvibe-sdk/tests/test_integration_v2.py`

**Step 1: Update RoleRuntime**

Add `workspace` param to `RoleRuntime.__init__`. When constructing roles, pass workspace to `AgentMemory` if role has `agent_memory`.

```python
class RoleRuntime:
    def __init__(
        self,
        roles,
        llm,
        memory=None,
        workspace=None,
        scheduler=None,
    ):
        self.llm = llm
        self.memory = memory
        self.workspace = workspace
        self.scheduler = scheduler
        self._roles = {}

        for role_class in roles:
            # V2: auto-create AgentMemory if role declares clearance
            agent_mem = None
            if hasattr(role_class, 'clearance') and role_class.clearance:
                agent_mem = AgentMemory(
                    agent_id=role_class.role_id,
                    workspace=workspace,
                )
            role = role_class(llm=llm, memory=memory, agent_memory=agent_mem)
            self._roles[role.role_id] = role
```

**Step 2: Update public API**

`src/openvibe_sdk/__init__.py`:
```python
"""OpenVibe SDK — 4-layer framework for human+agent collaboration."""

from openvibe_sdk.operator import Operator, llm_node, agent_node
from openvibe_sdk.role import Role
from openvibe_sdk.runtime import OperatorRuntime, RoleRuntime

# V2 exports
from openvibe_sdk.memory.types import Fact, Episode, Insight, Classification
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.workspace import WorkspaceMemory
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.filesystem import MemoryFilesystem
from openvibe_sdk.models import AuthorityConfig

__all__ = [
    # V1
    "Operator", "llm_node", "agent_node",
    "Role", "OperatorRuntime", "RoleRuntime",
    # V2
    "Fact", "Episode", "Insight", "Classification",
    "ClearanceProfile", "WorkspaceMemory", "AgentMemory",
    "MemoryFilesystem", "AuthorityConfig",
]
```

**Step 3: Write integration test**

`tests/test_integration_v2.py`:
```python
"""Integration test — full V2 stack with memory, access control, filesystem."""

from datetime import datetime, timezone

from openvibe_sdk import (
    Operator, Role, RoleRuntime,
    llm_node, agent_node,
    Fact, Classification, ClearanceProfile,
    WorkspaceMemory, AgentMemory, MemoryFilesystem,
    AuthorityConfig,
)
from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.memory.types import Insight


class IntegrationLLM:
    def __init__(self):
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.calls.append({"system": system, "messages": messages, **kwargs})
        return LLMResponse(content='{"score": 85}', tokens_in=10, tokens_out=20)


class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(
        model="sonnet", output_key="score",
        memory_scope={
            "domain": "revenue",
            "entity": lambda state: state.get("company"),
        },
    )
    def qualify(self, state):
        """You are a lead qualifier."""
        return f"Score: {state['lead']}"


class CRO(Role):
    role_id = "cro"
    soul = "You are the CRO. Data-driven and strategic."
    operators = [RevenueOps]
    authority = AuthorityConfig(
        autonomous=["qualify_lead"],
        forbidden=["sign_contracts"],
    )
    clearance = ClearanceProfile(
        agent_id="cro",
        domain_clearance={
            "revenue": Classification.CONFIDENTIAL,
            "customer": Classification.INTERNAL,
        },
    )


def test_full_v2_stack():
    """Test full V2: Role + memory_scope + access control + episode recording."""
    llm = IntegrationLLM()

    # Workspace with shared facts
    workspace = WorkspaceMemory()
    workspace.store_fact(Fact(
        id="f1", content="Acme Corp has 200 employees",
        entity="acme_corp", domain="customer",
        classification=Classification.PUBLIC,
    ))

    # Agent memory with insights
    agent_mem = AgentMemory(agent_id="cro", workspace=workspace)
    agent_mem.store_insight(Insight(
        id="ins1", agent_id="cro",
        content="VP sponsor predicts conversion",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))

    # Role with agent memory
    role = CRO(llm=llm, agent_memory=agent_mem)
    op = role.get_operator("revenue_ops")

    # Execute
    result = op.qualify({"lead": "Acme Corp", "company": "acme_corp"})

    # Verify output
    assert result["score"] == {"score": 85}

    # Verify soul injection
    assert "CRO" in llm.calls[0]["system"]

    # Verify memory_scope assembled (insight injected)
    assert "VP sponsor" in llm.calls[0]["system"]

    # Verify episode was recorded
    episodes = agent_mem.recall_episodes()
    assert len(episodes) == 1
    assert episodes[0].operator_id == "revenue_ops"
    assert episodes[0].node_name == "qualify"
    assert episodes[0].domain == "revenue"

    # Verify authority
    assert role.can_act("qualify_lead") == "autonomous"
    assert role.can_act("sign_contracts") == "forbidden"


def test_memory_filesystem_integration():
    """Test MemoryFilesystem on top of AgentMemory."""
    agent_mem = AgentMemory(agent_id="cro")
    agent_mem.store_insight(Insight(
        id="ins1", agent_id="cro",
        content="Revenue insight",
        confidence=0.9, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="revenue",
    ))

    fs = MemoryFilesystem(
        role_id="cro",
        agent_memory=agent_mem,
        soul="You are the CRO.",
    )

    # Browse
    root = fs.browse("/")
    assert "knowledge" in root

    # Read soul
    soul = fs.read("/identity/soul.md")
    assert "CRO" in soul

    # Search knowledge
    results = fs.search("revenue insight", scope="/knowledge/")
    assert len(results) >= 1

    # Write new knowledge
    fs.write("/knowledge/revenue/new-principle", "Test principle")
    insights = agent_mem.recall_insights(domain="revenue")
    assert len(insights) == 2

    # Traces recorded
    assert len(fs.traces) == 4


def test_v2_public_api_exports():
    """Verify all 15 exports are available."""
    from openvibe_sdk import (
        # V1 (6)
        Operator, llm_node, agent_node,
        Role, OperatorRuntime, RoleRuntime,
        # V2 (9)
        Fact, Episode, Insight, Classification,
        ClearanceProfile, WorkspaceMemory, AgentMemory,
        MemoryFilesystem, AuthorityConfig,
    )
    for export in [Operator, llm_node, agent_node, Role, OperatorRuntime,
                   RoleRuntime, Fact, Episode, Insight, Classification,
                   ClearanceProfile, WorkspaceMemory, AgentMemory,
                   MemoryFilesystem, AuthorityConfig]:
        assert export is not None


def test_v1_backward_compat():
    """V1 code must still work without any V2 features."""
    from openvibe_sdk.memory.in_memory import InMemoryStore

    class SimpleLLM:
        def __init__(self):
            self.last_system = None
        def call(self, *, system, messages, **kwargs):
            self.last_system = system
            return LLMResponse(content="v1 output")

    class SimpleOp(Operator):
        operator_id = "simple"
        @llm_node(model="haiku", output_key="out")
        def process(self, state):
            """You are simple."""
            return "process"

    class SimpleRole(Role):
        role_id = "simple"
        soul = "Simple soul."
        operators = [SimpleOp]

    llm = SimpleLLM()
    memory = InMemoryStore()
    memory.store("simple", "m1", "V1 memory")
    role = SimpleRole(llm=llm, memory=memory)
    op = role.get_operator("simple")
    result = op.process({"x": 1})

    assert result["out"] == "v1 output"
    assert "Simple soul" in llm.last_system
    assert "V1 memory" in llm.last_system
```

**Step 4: Run ALL tests**

```bash
pytest tests/ -v
```

Expected: all PASS. Target: ~190+ tests (87 V1 + ~105 V2).

**Step 5: Commit**

```bash
git add v4/openvibe-sdk/src/openvibe_sdk/__init__.py v4/openvibe-sdk/src/openvibe_sdk/runtime.py v4/openvibe-sdk/tests/test_integration_v2.py
git commit -m "feat(sdk): V2 complete — RoleRuntime + 15 exports + integration tests"
```

---

## Summary

| Task | What | New Files | Tests |
|------|------|-----------|-------|
| 1 | Memory types (Fact, Episode, Insight, Classification, RetrievalTrace) | types.py | 8 |
| 2 | Store protocols (FactStore, EpisodicStore, InsightStore) | stores.py | 3 |
| 3 | InMemory store implementations | in_memory.py (mod) | 24 |
| 4 | Access control (ClearanceProfile, AccessFilter) | access.py | 7 |
| 5 | WorkspaceMemory (shared facts + clearance) | workspace.py | 6 |
| 6 | AgentMemory (L2+L3 + reflect + sync + V1 compat) | agent_memory.py | 12 |
| 7 | MemoryFilesystem (browse/read/search/write + traces) | filesystem.py | 13 |
| 8 | MemoryAssembler (scope-based context assembly) | assembler.py | 6 |
| 9 | AuthorityConfig | models.py (mod) | 5 |
| 10 | Operator + decorator changes (memory_scope, episodes) | operator.py (mod) | 9 |
| 11 | Role + _RoleAwareLLM changes | role.py (mod) | 7 |
| 12 | RoleRuntime + Public API + Integration | runtime.py (mod), __init__.py (mod) | 4 |

**Total: ~104 new tests, 12 tasks, 12 commits.**
**Combined with V1: ~191 tests.**

### New file structure

```
src/openvibe_sdk/memory/
├── __init__.py          # V1 compat (MemoryProvider, MemoryEntry)
├── in_memory.py         # V1 InMemoryStore + V2 InMemoryFactStore/Episodic/Insight
├── types.py             # NEW: Fact, Episode, Insight, Classification, RetrievalTrace
├── stores.py            # NEW: FactStore, EpisodicStore, InsightStore protocols
├── access.py            # NEW: ClearanceProfile, AccessFilter
├── workspace.py         # NEW: WorkspaceMemory
├── agent_memory.py      # NEW: AgentMemory (L2+L3 + reflect + V1 compat)
├── filesystem.py        # NEW: MemoryFilesystem (browse/read/search/write)
└── assembler.py         # NEW: MemoryAssembler
```

### Public API (15 exports)

```python
from openvibe_sdk import (
    # V1 (6)
    Operator, llm_node, agent_node,
    Role, OperatorRuntime, RoleRuntime,
    # V2 (9)
    Fact, Episode, Insight, Classification,
    ClearanceProfile, WorkspaceMemory, AgentMemory,
    MemoryFilesystem, AuthorityConfig,
)
```

---

*Plan created: 2026-02-17*
