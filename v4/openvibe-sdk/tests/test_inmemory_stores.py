"""Tests for InMemory V2 store implementations."""

from datetime import datetime, timezone

from openvibe_sdk.memory.stores import EpisodicStore, FactStore, InsightStore
from openvibe_sdk.memory.types import Episode, Fact, Insight
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
