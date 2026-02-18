"""Tests for Role V2 — authority, clearance, agent_memory wiring."""

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


