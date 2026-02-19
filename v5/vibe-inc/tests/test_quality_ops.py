from openvibe_sdk.llm import LLMResponse


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


class FakeLLM:
    def __init__(self, responses=None):
        self.responses = list(responses or [_text_response()])
        self.calls = []

    def call(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def test_quality_ops_is_operator():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    from openvibe_sdk import Operator
    assert issubclass(QualityOps, Operator)
    assert QualityOps.operator_id == "quality_ops"


def test_freshness_monitor_is_agent_node():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    assert hasattr(QualityOps.freshness_monitor, "_is_agent_node")
    assert QualityOps.freshness_monitor._is_agent_node is True


def test_discrepancy_report_is_agent_node():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    assert hasattr(QualityOps.discrepancy_report, "_is_agent_node")
    assert QualityOps.discrepancy_report._is_agent_node is True


def test_credibility_assessment_is_agent_node():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    assert hasattr(QualityOps.credibility_assessment, "_is_agent_node")
    assert QualityOps.credibility_assessment._is_agent_node is True


def test_freshness_monitor_output_key():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    llm = FakeLLM([_text_response("All tables fresh")])
    op = QualityOps(llm=llm)
    result = op.freshness_monitor({})
    assert "freshness_result" in result


def test_discrepancy_report_output_key():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    llm = FakeLLM([_text_response("No discrepancies")])
    op = QualityOps(llm=llm)
    result = op.discrepancy_report({})
    assert "discrepancy_result" in result


def test_credibility_assessment_output_key():
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    llm = FakeLLM([_text_response("High credibility")])
    op = QualityOps(llm=llm)
    result = op.credibility_assessment({})
    assert "credibility_result" in result
