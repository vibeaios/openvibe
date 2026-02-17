"""In-memory store -- dict-based, for dev/test."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from openvibe_sdk.memory import MemoryEntry
from openvibe_sdk.memory.types import Episode, Fact, Insight


class InMemoryStore:
    """Simple in-memory MemoryProvider for development and testing."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, MemoryEntry]] = {}

    def store(self, namespace: str, key: str, value: Any) -> None:
        if namespace not in self._store:
            self._store[namespace] = {}
        self._store[namespace][key] = MemoryEntry(
            key=key, content=value, namespace=namespace
        )

    def recall(
        self, namespace: str, query: str, limit: int = 10
    ) -> list[MemoryEntry]:
        entries = list(self._store.get(namespace, {}).values())
        if query:
            entries = [
                e
                for e in entries
                if query.lower() in str(e.content).lower()
            ]
        return entries[:limit]

    def delete(self, namespace: str, key: str) -> None:
        if namespace in self._store:
            self._store[namespace].pop(key, None)


# --- V2 InMemory Store Implementations ---


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
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[Episode]:
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
