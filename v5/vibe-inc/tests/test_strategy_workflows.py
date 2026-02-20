"""Tests for D2C Strategy workflow factories."""
from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="workflow output")


def test_define_framework_graph_runs():
    """define_framework graph compiles and produces framework_result."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine
    from vibe_inc.roles.d2c_strategy.workflows import create_define_framework_graph

    op = PositioningEngine(llm=FakeLLM())
    graph = create_define_framework_graph(op)
    result = graph.invoke({"product": "bot"})
    assert "framework_result" in result


def test_validate_story_graph_runs():
    """validate_story graph compiles and produces validation_result."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine
    from vibe_inc.roles.d2c_strategy.workflows import create_validate_story_graph

    op = PositioningEngine(llm=FakeLLM())
    graph = create_validate_story_graph(op)
    result = graph.invoke({"product": "bot", "experiment_id": "exp-001"})
    assert "validation_result" in result


def test_refine_icp_graph_runs():
    """refine_icp graph compiles and produces icp_result."""
    from vibe_inc.roles.d2c_strategy.positioning import PositioningEngine
    from vibe_inc.roles.d2c_strategy.workflows import create_refine_icp_graph

    op = PositioningEngine(llm=FakeLLM())
    graph = create_refine_icp_graph(op)
    result = graph.invoke({"product": "dot"})
    assert "icp_result" in result


def test_weekly_scan_graph_runs():
    """weekly_scan graph compiles and produces scan_result."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel
    from vibe_inc.roles.d2c_strategy.workflows import create_weekly_scan_graph

    op = CompetitiveIntel(llm=FakeLLM())
    graph = create_weekly_scan_graph(op)
    result = graph.invoke({"period": "last_7d"})
    assert "scan_result" in result


def test_threat_assess_graph_runs():
    """threat_assess graph compiles and produces threat_result."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel
    from vibe_inc.roles.d2c_strategy.workflows import create_threat_assess_graph

    op = CompetitiveIntel(llm=FakeLLM())
    graph = create_threat_assess_graph(op)
    result = graph.invoke({"competitor": "Limitless", "move": "Price cut"})
    assert "threat_result" in result
