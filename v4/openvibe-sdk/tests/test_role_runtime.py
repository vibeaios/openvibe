from unittest.mock import MagicMock

import pytest

from openvibe_sdk.llm import LLMResponse
from openvibe_sdk.operator import Operator, llm_node
from openvibe_sdk.role import Role
from openvibe_sdk.runtime import RoleRuntime


class FakeLLM:
    def __init__(self, content="result"):
        self.content = content
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.calls.append({"system": system, "messages": messages, **kwargs})
        return LLMResponse(content=self.content)


class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(model="sonnet", output_key="score")
    def qualify(self, state):
        """You qualify leads."""
        return f"Score: {state.get('lead', '')}"


class ContentEngine(Operator):
    operator_id = "content_engine"

    @llm_node(model="haiku", output_key="draft")
    def write(self, state):
        """You write content."""
        return f"Write about: {state.get('topic', '')}"


class CRO(Role):
    role_id = "cro"
    soul = "You are the CRO."
    operators = [RevenueOps, ContentEngine]


class CMO(Role):
    role_id = "cmo"
    soul = "You are the CMO."
    operators = [ContentEngine]


def test_role_runtime_registers_roles():
    runtime = RoleRuntime(roles=[CRO, CMO], llm=FakeLLM())
    assert len(runtime.list_roles()) == 2


def test_get_role():
    runtime = RoleRuntime(roles=[CRO], llm=FakeLLM())
    role = runtime.get_role("cro")
    assert role.role_id == "cro"


def test_get_role_unknown():
    runtime = RoleRuntime(roles=[CRO], llm=FakeLLM())
    with pytest.raises(ValueError, match="Unknown role"):
        runtime.get_role("nonexistent")


def test_activate():
    llm = FakeLLM(content="85")
    runtime = RoleRuntime(roles=[CRO], llm=llm)

    def qualify_factory(operator):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = operator.qualify({"lead": "Acme"})
        return mock_graph

    runtime.register_workflow("revenue_ops", "qualify", qualify_factory)
    result = runtime.activate("cro", "revenue_ops", "qualify", {"lead": "Acme"})
    assert result["score"] == 85


def test_activate_unknown_role():
    runtime = RoleRuntime(roles=[CRO], llm=FakeLLM())
    with pytest.raises(ValueError, match="Unknown role"):
        runtime.activate("missing", "revenue_ops", "qualify", {})


def test_activate_unknown_operator():
    runtime = RoleRuntime(roles=[CRO], llm=FakeLLM())
    runtime.register_workflow("missing_op", "wf", lambda op: MagicMock())
    with pytest.raises(ValueError, match="has no operator"):
        runtime.activate("cro", "missing_op", "wf", {})


def test_activate_unknown_workflow():
    runtime = RoleRuntime(roles=[CRO], llm=FakeLLM())
    with pytest.raises(ValueError, match="No workflow"):
        runtime.activate("cro", "revenue_ops", "missing_wf", {})


