"""CRO Role integration test — exercises the full SDK stack.

Defines a realistic CRO (Chief Revenue Officer) Role with:
- Soul (inline), authority, clearance, operator with @llm_node
- Tests the complete lifecycle: respond, operator workflow, memory,
  reflection, authority, memory_fs navigation
"""

from datetime import datetime, timezone

from openvibe_sdk import (
    AgentMemory,
    AuthorityConfig,
    ClearanceProfile,
    Classification,
    Episode,
    Insight,
    Operator,
    Role,
    RoleRuntime,
    llm_node,
)
from openvibe_sdk.llm import LLMResponse


# --- Fake LLM ---

class FakeLLM:
    """Records calls and returns configurable responses."""

    def __init__(self, responses=None):
        self.calls: list[dict] = []
        self._responses = list(responses or ["ok"])
        self._index = 0

    def call(self, *, system, messages, **kwargs):
        self.calls.append({
            "system": system,
            "messages": messages,
            "kwargs": kwargs,
        })
        content = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return LLMResponse(content=content, tokens_in=10, tokens_out=20)


# --- Operator ---

class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(model="sonnet", output_key="qualification")
    def qualify_lead(self, state):
        """You are a lead qualification expert. Score the lead 0-100."""
        return f"Company: {state.get('company', '?')}, Revenue: {state.get('revenue', '?')}"


# --- Role ---

CRO_SOUL = (
    "You are the CRO of Vibe. Data-driven, aggressive but measured.\n"
    "You care about pipeline velocity, CAC payback, and net revenue retention."
)

class CRO(Role):
    role_id = "cro"
    soul = CRO_SOUL
    operators = [RevenueOps]
    authority = AuthorityConfig(
        autonomous=["qualify_lead", "review_pipeline"],
        needs_approval=["change_pricing", "discount_deal"],
        forbidden=["sign_contracts"],
    )
    clearance = ClearanceProfile(
        agent_id="cro",
        domain_clearance={
            "sales": Classification.CONFIDENTIAL,
            "finance": Classification.INTERNAL,
        },
    )


# === Tests ===


def test_cro_respond_injects_soul():
    """respond() should inject soul into system prompt."""
    llm = FakeLLM(["Pipeline is strong at $2.1M weighted."])
    mem = AgentMemory(agent_id="cro")
    cro = CRO(llm=llm, agent_memory=mem)

    response = cro.respond("How's the pipeline looking?")

    assert response.content == "Pipeline is strong at $2.1M weighted."
    assert "CRO" in llm.calls[0]["system"]
    assert "pipeline velocity" in llm.calls[0]["system"]


def test_cro_respond_recalls_knowledge():
    """respond() should inject recalled insights into system prompt."""
    llm = FakeLLM(["Yes, webinar leads convert better."])
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins-webinar", agent_id="cro",
        content="Webinar leads convert at 2x the rate of cold outbound",
        confidence=0.85, evidence_count=12, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="sales",
    ))

    cro = CRO(llm=llm, agent_memory=mem)
    cro.respond("webinar leads")

    # Insight should appear in system prompt
    assert "webinar" in llm.calls[0]["system"].lower()


def test_cro_respond_records_episode():
    """respond() should auto-record an episode in agent_memory."""
    llm = FakeLLM(["NRR is 115%."])
    mem = AgentMemory(agent_id="cro")
    cro = CRO(llm=llm, agent_memory=mem)

    cro.respond("What's our net revenue retention?")

    episodes = mem.recall_episodes()
    assert len(episodes) == 1
    ep = episodes[0]
    assert ep.action == "respond"
    assert "revenue retention" in ep.input_summary.lower()
    assert "115" in ep.output_summary


def test_cro_operator_qualify_lead():
    """get_operator() + call node should produce a qualification score."""
    llm = FakeLLM(["85 — Strong fit, VP sponsor, $500K ACV potential"])
    mem = AgentMemory(agent_id="cro")
    cro = CRO(llm=llm, agent_memory=mem)

    op = cro.get_operator("revenue_ops")
    state = {"company": "Acme Corp", "revenue": "$50M ARR"}
    result = op.qualify_lead(state)

    assert "qualification" in result
    assert "85" in result["qualification"]


def test_cro_operator_records_episode():
    """Operator node called through Role should record episode via _episode_recorder."""
    llm = FakeLLM(["90 — Enterprise ready"])
    mem = AgentMemory(agent_id="cro")
    cro = CRO(llm=llm, agent_memory=mem)

    op = cro.get_operator("revenue_ops")
    op.qualify_lead({"company": "BigCo", "revenue": "$200M"})

    episodes = mem.recall_episodes()
    assert len(episodes) == 1
    assert episodes[0].operator_id == "revenue_ops"
    assert episodes[0].node_name == "qualify_lead"


def test_cro_authority():
    """can_act() should check authority levels."""
    cro = CRO(llm=FakeLLM())

    assert cro.can_act("qualify_lead") == "autonomous"
    assert cro.can_act("review_pipeline") == "autonomous"
    assert cro.can_act("change_pricing") == "needs_approval"
    assert cro.can_act("discount_deal") == "needs_approval"
    assert cro.can_act("sign_contracts") == "forbidden"
    # Unknown action defaults to needs_approval
    assert cro.can_act("fire_someone") == "needs_approval"


def test_cro_memory_fs_browse():
    """memory_fs should expose virtual filesystem navigation."""
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins1", agent_id="cro",
        content="Enterprise deals need executive sponsor",
        confidence=0.9, evidence_count=8, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="sales",
    ))
    cro = CRO(llm=FakeLLM(), agent_memory=mem)
    fs = cro.memory_fs

    # Root browse
    entries = fs.browse("/")
    assert "identity" in entries
    assert "knowledge" in entries
    assert "experience" in entries

    # Knowledge browse — should list domains
    domains = fs.browse("/knowledge")
    assert "sales" in domains

    # Knowledge domain browse — should list insight IDs
    insights = fs.browse("/knowledge/sales")
    assert "ins1" in insights


def test_cro_memory_fs_read_soul():
    """memory_fs should expose soul at /identity/soul.md."""
    mem = AgentMemory(agent_id="cro")
    cro = CRO(llm=FakeLLM(), agent_memory=mem)

    content = cro.memory_fs.read("/identity/soul.md")
    assert "CRO" in content
    assert "pipeline velocity" in content


def test_cro_memory_fs_directory():
    """memory_fs .directory should provide navigation summary."""
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins-cac", agent_id="cro",
        content="CAC payback under 12 months is healthy",
        confidence=0.8, evidence_count=5, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="finance",
    ))
    cro = CRO(llm=FakeLLM(), agent_memory=mem)
    fs = cro.memory_fs

    root_dir = fs.read("/.directory")
    assert "identity" in root_dir
    assert "knowledge" in root_dir
    assert "1 insight" in root_dir

    knowledge_dir = fs.read("/knowledge/.directory")
    assert "finance" in knowledge_dir
    assert "CAC payback" in knowledge_dir


def test_cro_memory_fs_search():
    """memory_fs search should find relevant insights."""
    mem = AgentMemory(agent_id="cro")
    mem.store_insight(Insight(
        id="ins-nrr", agent_id="cro",
        content="Net revenue retention above 120% indicates product-market fit",
        confidence=0.9, evidence_count=15, source_episode_ids=[],
        created_at=datetime.now(timezone.utc), domain="sales",
    ))
    cro = CRO(llm=FakeLLM(), agent_memory=mem)

    results = cro.memory_fs.search("revenue retention")
    assert len(results) >= 1
    assert any("120%" in r["content"] for r in results)


def test_cro_reflect():
    """reflect() should compress episodes into insights via LLM."""
    llm = FakeLLM(responses=[
        '[{"content": "Webinar leads close 2x faster than cold outbound", "confidence": 0.85}]'
    ])
    mem = AgentMemory(agent_id="cro")
    # Seed episodes for reflection
    for i in range(5):
        mem.record_episode(Episode(
            id=f"ep-{i}", agent_id="cro", operator_id="revenue_ops",
            node_name="qualify_lead", timestamp=datetime.now(timezone.utc),
            action="qualify_lead", input_summary=f"Lead {i} from webinar",
            output_summary=f"Score: {75 + i}", outcome={"score": 75 + i},
            duration_ms=100, tokens_in=10, tokens_out=20,
        ))

    cro = CRO(llm=llm, agent_memory=mem)
    insights = cro.reflect()

    assert len(insights) >= 1
    assert "webinar" in insights[0].content.lower()


def test_cro_list_operators():
    """list_operators() should return operator IDs."""
    cro = CRO(llm=FakeLLM())
    assert cro.list_operators() == ["revenue_ops"]


def test_cro_full_lifecycle():
    """Full lifecycle: respond → qualify → check memory → reflect."""
    # Step 1: CRO responds to a question
    llm = FakeLLM(responses=[
        "Pipeline looks healthy at $2M weighted.",      # respond()
        "85 — Strong VP sponsor, good timing",          # qualify_lead()
        '[{"content": "VP sponsors predict 85+ scores", "confidence": 0.8}]',  # reflect()
    ])
    mem = AgentMemory(agent_id="cro")
    cro = CRO(llm=llm, agent_memory=mem)

    # Step 1: Respond
    r1 = cro.respond("Pipeline update?")
    assert "2M" in r1.content

    # Step 2: Qualify a lead through operator
    op = cro.get_operator("revenue_ops")
    result = op.qualify_lead({"company": "Acme", "revenue": "$50M"})
    assert "85" in result["qualification"]

    # Step 3: Check episodes recorded
    episodes = mem.recall_episodes()
    assert len(episodes) == 2  # respond + qualify_lead
    actions = {ep.action for ep in episodes}
    assert "respond" in actions
    assert "qualify_lead" in actions

    # Step 4: Reflect on episodes
    insights = cro.reflect()
    assert len(insights) >= 1
    assert "VP" in insights[0].content

    # Step 5: Verify insight is now in memory
    stored = mem.recall_insights(query="VP sponsor")
    assert len(stored) >= 1


def test_cro_via_role_runtime():
    """RoleRuntime should wire up CRO correctly with all capabilities."""
    llm = FakeLLM(["Revenue is tracking ahead of plan."])
    runtime = RoleRuntime(roles=[CRO], llm=llm)
    cro = runtime.get_role("cro")

    # Runtime should have wired agent_memory
    assert cro.agent_memory is not None

    # respond() works
    response = cro.respond("Revenue update?")
    assert "tracking ahead" in response.content

    # memory_fs works
    assert cro.memory_fs is not None
    entries = cro.memory_fs.browse("/")
    assert "identity" in entries

    # authority works
    assert cro.can_act("qualify_lead") == "autonomous"

    # list_operators works
    assert cro.list_operators() == ["revenue_ops"]
