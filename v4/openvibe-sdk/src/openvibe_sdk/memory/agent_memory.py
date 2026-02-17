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

    # --- Reflection: L2 -> L3 ---

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

    # --- Sync: Agent -> Workspace ---

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
