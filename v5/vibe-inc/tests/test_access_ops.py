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


def test_access_ops_is_operator():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    from openvibe_sdk import Operator
    assert issubclass(AccessOps, Operator)
    assert AccessOps.operator_id == "access_ops"


def test_route_query_is_agent_node():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    assert hasattr(AccessOps.route_query, "_is_agent_node")
    assert AccessOps.route_query._is_agent_node is True


def test_build_report_is_agent_node():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    assert hasattr(AccessOps.build_report, "_is_agent_node")
    assert AccessOps.build_report._is_agent_node is True


def test_cache_refresh_is_agent_node():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    assert hasattr(AccessOps.cache_refresh, "_is_agent_node")
    assert AccessOps.cache_refresh._is_agent_node is True


def test_route_query_output_key():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    llm = FakeLLM([_text_response("Query routed to fct_ads_ad_metrics")])
    op = AccessOps(llm=llm)
    result = op.route_query({"question": "What is our CAC by platform?"})
    assert "query_result" in result


def test_build_report_output_key():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    llm = FakeLLM([_text_response("Report generated")])
    op = AccessOps(llm=llm)
    result = op.build_report({"report_type": "weekly_performance"})
    assert "report_result" in result


def test_cache_refresh_output_key():
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    llm = FakeLLM([_text_response("Cache refreshed")])
    op = AccessOps(llm=llm)
    result = op.cache_refresh({})
    assert "cache_result" in result
