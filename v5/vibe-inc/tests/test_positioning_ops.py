"""Tests for PositioningEngine operator."""
from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def __init__(self, content="ok"):
        self.content = content
        self.last_system = None
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.last_system = system
        self.calls.append({"system": system, "messages": messages, **kwargs})
        return LLMResponse(content=self.content)


def test_positioning_engine_has_three_nodes():
    """PositioningEngine should have define_framework, validate_story, refine_icp."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    assert PositioningEngine.operator_id == "positioning_engine"
    llm = FakeLLM()
    op = PositioningEngine(llm=llm)
    assert hasattr(op, "define_framework")
    assert hasattr(op, "validate_story")
    assert hasattr(op, "refine_icp")


def test_define_framework_tools():
    """define_framework should use read_memory and write_memory."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    cfg = PositioningEngine.define_framework._node_config
    assert "read_memory" in cfg["tools"]
    assert "write_memory" in cfg["tools"]


def test_validate_story_tools():
    """validate_story should use ga4_read, read_memory, and write_memory."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    cfg = PositioningEngine.validate_story._node_config
    assert "ga4_read" in cfg["tools"]
    assert "read_memory" in cfg["tools"]
    assert "write_memory" in cfg["tools"]


def test_refine_icp_output_key():
    """refine_icp should write to icp_result."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    cfg = PositioningEngine.refine_icp._node_config
    assert cfg["output_key"] == "icp_result"


def test_define_framework_runs():
    """define_framework agent node executes with FakeLLM."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    llm = FakeLLM(content="Framework defined.")
    op = PositioningEngine(llm=llm)
    result = op.define_framework({"product": "bot"})
    assert result is not None
    assert len(llm.calls) == 1


def test_validate_story_runs():
    """validate_story agent node executes with FakeLLM."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    llm = FakeLLM(content="Story validated.")
    op = PositioningEngine(llm=llm)
    result = op.validate_story({"product": "bot", "experiment_id": "exp-001"})
    assert result is not None


def test_refine_icp_runs():
    """refine_icp agent node executes with FakeLLM."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    llm = FakeLLM(content="ICP refined.")
    op = PositioningEngine(llm=llm)
    result = op.refine_icp({"product": "dot"})
    assert result is not None


def test_refine_icp_docstring_mentions_approval():
    """refine_icp docstring should mention human approval for ICP redefinition."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine

    assert "human approval" in PositioningEngine.refine_icp.__doc__
