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
