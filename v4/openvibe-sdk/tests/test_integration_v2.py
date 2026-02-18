"""Integration test -- full V2 stack with memory, access control, filesystem."""

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
        entity="acme_corp",
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


def test_role_runtime_auto_creates_agent_memory():
    """RoleRuntime auto-creates AgentMemory when role has clearance."""
    llm = IntegrationLLM()
    workspace = WorkspaceMemory()

    runtime = RoleRuntime(
        roles=[CRO],
        llm=llm,
        workspace=workspace,
    )

    role = runtime.get_role("cro")
    assert role.agent_memory is not None
    assert role.agent_memory.agent_id == "cro"
    assert role.agent_memory.workspace is workspace
