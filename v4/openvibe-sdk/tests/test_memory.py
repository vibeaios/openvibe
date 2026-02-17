import typing

from openvibe_sdk.memory import MemoryEntry, MemoryProvider
from openvibe_sdk.memory.in_memory import InMemoryStore


def test_memory_provider_is_protocol():
    assert issubclass(type(MemoryProvider), type(typing.Protocol))


def test_memory_entry_creation():
    entry = MemoryEntry(key="k1", content="hello", namespace="ns")
    assert entry.key == "k1"
    assert entry.content == "hello"
    assert entry.namespace == "ns"
    assert entry.created_at is not None


def test_in_memory_store_implements_protocol():
    store = InMemoryStore()
    assert isinstance(store, MemoryProvider)


def test_store_and_recall():
    store = InMemoryStore()
    store.store("ns", "k1", "value1")
    store.store("ns", "k2", "value2")
    results = store.recall("ns", "")
    assert len(results) == 2


def test_recall_with_query_filter():
    store = InMemoryStore()
    store.store("ns", "k1", "webinar leads convert 2x")
    store.store("ns", "k2", "enterprise needs VP sponsor")
    store.store("ns", "k3", "cold email has low response")
    results = store.recall("ns", "webinar")
    assert len(results) == 1
    assert results[0].content == "webinar leads convert 2x"


def test_recall_respects_limit():
    store = InMemoryStore()
    for i in range(20):
        store.store("ns", f"k{i}", f"memory {i}")
    results = store.recall("ns", "", limit=5)
    assert len(results) == 5


def test_recall_empty_namespace():
    store = InMemoryStore()
    results = store.recall("nonexistent", "")
    assert results == []


def test_delete():
    store = InMemoryStore()
    store.store("ns", "k1", "value1")
    store.delete("ns", "k1")
    results = store.recall("ns", "")
    assert len(results) == 0


def test_delete_nonexistent_key():
    store = InMemoryStore()
    store.delete("ns", "missing")  # should not raise


def test_namespace_isolation():
    store = InMemoryStore()
    store.store("ns1", "k1", "first")
    store.store("ns2", "k1", "second")
    r1 = store.recall("ns1", "")
    r2 = store.recall("ns2", "")
    assert len(r1) == 1
    assert r1[0].content == "first"
    assert len(r2) == 1
    assert r2[0].content == "second"
