"""Tests for daily report workflow graph."""
from unittest.mock import patch

from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="All metrics healthy.")


def test_daily_growth_report_graph_compiles():
    from vibe_inc.roles.d2c_growth.daily_report_workflows import create_daily_growth_report_graph
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    op = DailyReportOps(llm=FakeLLM())
    graph = create_daily_growth_report_graph(op)
    assert graph is not None


def test_daily_growth_report_graph_invokes_end_to_end():
    from vibe_inc.roles.d2c_growth.daily_report_workflows import create_daily_growth_report_graph
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    op = DailyReportOps(llm=FakeLLM())
    graph = create_daily_growth_report_graph(op)

    with patch("vibe_inc.roles.d2c_growth.daily_report_queries.analytics_query_sql",
               return_value={"rows": [], "columns": []}):
        result = graph.invoke({"date": "2026-02-23"})

    assert "report" in result
    assert "healthy" in result["report"].lower()


def test_daily_growth_report_state_contains_layer_data():
    from vibe_inc.roles.d2c_growth.daily_report_workflows import create_daily_growth_report_graph
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    op = DailyReportOps(llm=FakeLLM())
    graph = create_daily_growth_report_graph(op)

    with patch("vibe_inc.roles.d2c_growth.daily_report_queries.analytics_query_sql",
               return_value={"rows": [{"x": 1}], "columns": ["x"]}):
        result = graph.invoke({"date": "2026-02-23"})

    assert "l1_data" in result
    assert "l2_data" in result
    assert "l3_data" in result
