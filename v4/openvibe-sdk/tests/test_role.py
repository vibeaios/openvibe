"""Tests for Role + _RoleAwareLLM — identity layer."""

import tempfile
from pathlib import Path

import pytest

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.operator import Operator, llm_node
from openvibe_sdk.role import Role, _RoleAwareLLM


class FakeLLM:
    def __init__(self, content="output"):
        self.content = content
        self.last_system = None

    def call(self, *, system, messages, **kwargs):
        self.last_system = system
        return LLMResponse(content=self.content)


class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(model="sonnet", output_key="score")
    def qualify(self, state):
        """You are a lead qualifier."""
        return f"Score: {state['lead']}"


class ContentEngine(Operator):
    operator_id = "content_engine"

    @llm_node(model="haiku", output_key="draft")
    def write(self, state):
        """You are a writer."""
        return f"Write about: {state['topic']}"


class CRO(Role):
    role_id = "cro"
    soul = "You are the CRO. Data-driven and strategic."
    operators = [RevenueOps, ContentEngine]


class EmptyRole(Role):
    role_id = "empty"
    operators = []


def test_role_has_id_and_soul():
    role = CRO(llm=FakeLLM())
    assert role.role_id == "cro"
    assert role.soul == "You are the CRO. Data-driven and strategic."


def test_get_operator():
    role = CRO(llm=FakeLLM())
    op = role.get_operator("revenue_ops")
    assert isinstance(op, RevenueOps)


def test_get_operator_caches():
    role = CRO(llm=FakeLLM())
    op1 = role.get_operator("revenue_ops")
    op2 = role.get_operator("revenue_ops")
    assert op1 is op2


def test_get_operator_unknown():
    role = CRO(llm=FakeLLM())
    with pytest.raises(ValueError, match="has no operator"):
        role.get_operator("nonexistent")


def test_operator_gets_role_aware_llm():
    llm = FakeLLM()
    role = CRO(llm=llm)
    op = role.get_operator("revenue_ops")
    assert isinstance(op.llm, _RoleAwareLLM)


def test_role_aware_llm_injects_soul():
    llm = FakeLLM()
    role = CRO(llm=llm)
    op = role.get_operator("revenue_ops")
    op.qualify({"lead": "Acme"})
    system = llm.last_system
    assert "You are the CRO" in system
    assert "You are a lead qualifier." in system


def test_build_system_prompt_soul_only():
    role = CRO(llm=FakeLLM())
    prompt = role.build_system_prompt("Base prompt.")
    assert "You are the CRO" in prompt
    assert "Base prompt." in prompt


def test_build_system_prompt_no_soul():
    role = EmptyRole(llm=FakeLLM())
    prompt = role.build_system_prompt("Just base.")
    assert prompt == "Just base."


def test_soul_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        soul_path = Path(tmpdir) / "soul.md"
        soul_path.write_text("You are a visionary leader.")

        class FileRole(Role):
            role_id = "file_role"
            soul = str(soul_path)
            operators = []

        role = FileRole(llm=FakeLLM())
        prompt = role.build_system_prompt("Base.")
        assert "visionary leader" in prompt


def test_role_no_memory_no_crash():
    role = CRO(llm=FakeLLM())
    prompt = role.build_system_prompt("Base.", context="anything")
    assert "Base." in prompt
    assert "Relevant Memories" not in prompt


def test_soul_file_not_found_gives_clear_error():
    class BadSoulRole(Role):
        role_id = "bad_soul"
        soul = "/nonexistent/path/soul.md"
        operators = []

    role = BadSoulRole(llm=FakeLLM())
    with pytest.raises(FileNotFoundError, match="Soul file not found.*bad_soul"):
        role.build_system_prompt("Base.")
