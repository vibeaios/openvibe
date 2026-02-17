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


# --- Reflect (L2 -> L3) ---

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
