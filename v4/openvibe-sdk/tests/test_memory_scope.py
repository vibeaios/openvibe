import json
import time
from datetime import datetime, timezone

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.operator import Operator, agent_node, llm_node
from openvibe_sdk.memory.types import Episode


class FakeLLM:
    def __init__(self, content="output"):
        self.content = content
        self.last_system = None

    def call(self, *, system, messages, **kwargs):
        self.last_system = system
        return LLMResponse(content=self.content, tokens_in=10, tokens_out=20)


class FakeAssembler:
    def __init__(self, context="## Insights\n- VP sponsor predicts conversion"):
        self.context = context
        self.last_scope = None

    def assemble(self, scope, token_budget=2000):
        self.last_scope = scope
        return self.context


# --- memory_scope on @llm_node ---

class ScopedOp(Operator):
    operator_id = "scoped"

    @llm_node(
        model="sonnet",
        output_key="score",
        memory_scope={
            "domain": "revenue",
            "entity": lambda state: state.get("company"),
            "tags": ["qualification"],
        },
    )
    def qualify(self, state):
        """You are a lead qualifier."""
        return f"Score: {state['lead']}"


def test_memory_scope_resolved_and_assembled():
    llm = FakeLLM()
    assembler = FakeAssembler()
    op = ScopedOp(llm=llm, memory_assembler=assembler)
    op.qualify({"lead": "Acme", "company": "acme_corp"})

    # Scope should be resolved (lambda called)
    assert assembler.last_scope["domain"] == "revenue"
    assert assembler.last_scope["entity"] == "acme_corp"
    assert assembler.last_scope["tags"] == ["qualification"]


def test_memory_scope_injected_into_system_prompt():
    llm = FakeLLM()
    assembler = FakeAssembler(context="## Insights\n- Test insight")
    op = ScopedOp(llm=llm, memory_assembler=assembler)
    op.qualify({"lead": "Acme", "company": "acme_corp"})

    assert "Test insight" in llm.last_system
    assert "You are a lead qualifier." in llm.last_system


def test_no_memory_scope_backward_compat():
    """@llm_node without memory_scope works exactly as V1."""

    class SimpleOp(Operator):
        @llm_node(model="haiku", output_key="out")
        def process(self, state):
            """You are a processor."""
            return "process this"

    llm = FakeLLM("done")
    op = SimpleOp(llm=llm)
    result = op.process({"input": "x"})
    assert result["out"] == "done"
    assert llm.last_system == "You are a processor."


def test_no_assembler_memory_scope_ignored():
    """If no assembler wired, memory_scope is silently ignored."""
    llm = FakeLLM()
    op = ScopedOp(llm=llm)  # no memory_assembler
    result = op.qualify({"lead": "Acme", "company": "acme_corp"})
    assert "score" in result
    assert llm.last_system == "You are a lead qualifier."


# --- Episode auto-recording ---

def test_episode_auto_recorded():
    recorded = []

    def recorder(ep):
        recorded.append(ep)

    llm = FakeLLM('{"score": 85}')
    op = ScopedOp(llm=llm, memory_assembler=FakeAssembler())
    op._episode_recorder = recorder
    op.qualify({"lead": "Acme", "company": "acme_corp"})

    assert len(recorded) == 1
    ep = recorded[0]
    assert isinstance(ep, Episode)
    assert ep.operator_id == "scoped"
    assert ep.node_name == "qualify"
    assert ep.domain == "revenue"
    assert ep.tokens_in == 10
    assert ep.tokens_out == 20


def test_no_recorder_no_error():
    llm = FakeLLM()
    op = ScopedOp(llm=llm)
    op.qualify({"lead": "Acme", "company": "acme_corp"})
    # Should not raise


# --- memory_scope on @agent_node ---

class AgentScopedOp(Operator):
    operator_id = "agent_scoped"

    @agent_node(
        tools=[],
        output_key="research",
        memory_scope={"domain": "revenue"},
    )
    def investigate(self, state):
        """You are a research analyst."""
        return f"Research: {state['topic']}"


def test_agent_node_memory_scope():
    llm = FakeLLM("research results")
    assembler = FakeAssembler(context="## Insights\n- Agent insight")
    op = AgentScopedOp(llm=llm, memory_assembler=assembler)
    result = op.investigate({"topic": "AI"})

    assert assembler.last_scope["domain"] == "revenue"
    assert "Agent insight" in llm.last_system
    assert result["research"] == "research results"


def test_agent_node_episode_recorded():
    recorded = []

    def recorder(ep):
        recorded.append(ep)

    llm = FakeLLM("done")
    op = AgentScopedOp(llm=llm)
    op._episode_recorder = recorder
    op.investigate({"topic": "AI"})

    assert len(recorded) == 1
    assert recorded[0].node_name == "investigate"
