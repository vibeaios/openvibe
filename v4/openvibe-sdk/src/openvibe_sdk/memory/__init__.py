"""Memory protocols and stores."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


@dataclass
class MemoryEntry:
    """A single memory entry."""

    key: str
    content: Any
    namespace: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class MemoryProvider(Protocol):
    """Protocol for memory backends."""

    def store(self, namespace: str, key: str, value: Any) -> None: ...

    def recall(
        self, namespace: str, query: str, limit: int = 10
    ) -> list[MemoryEntry]: ...

    def delete(self, namespace: str, key: str) -> None: ...
