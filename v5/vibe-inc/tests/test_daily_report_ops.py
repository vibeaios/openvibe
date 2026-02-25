"""Tests for DailyReportOps operator."""
from unittest.mock import patch

from openvibe_sdk.llm import LLMResponse


MOCK_L1 = {"yesterday": [{"total_revenue": 15000}], "avg_7d": [], "avg_28d": [], "ad_spend": []}
MOCK_L2 = {"yesterday": [], "avg_7d": [], "amazon": [], "worst_cpa_campaigns": []}
MOCK_L3 = {"sessions_yesterday": [], "sessions_7d": [], "funnel_yesterday": [], "funnel_7d": []}


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


class FakeAgentLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.calls.append({"system": system, "messages": messages, **kwargs})
        return self.responses.pop(0)


# --- interpret ---


def test_interpret_is_agent_node():
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    assert hasattr(DailyReportOps.interpret, "_is_agent_node")
    assert DailyReportOps.interpret._is_agent_node is True
    assert "read_memory" in DailyReportOps.interpret._node_config["tools"]


def test_interpret_output_key():
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    llm = FakeAgentLLM([_text_response("🔴 Bot CAC $520...")])
    op = DailyReportOps(llm=llm)
    result = op.interpret({"l1_data": MOCK_L1, "l2_data": MOCK_L2, "l3_data": MOCK_L3})

    assert "report" in result
    assert "Bot CAC" in result["report"]


def test_interpret_prompt_contains_framework_keywords():
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    llm = FakeAgentLLM([_text_response("report")])
    op = DailyReportOps(llm=llm)
    op.interpret({"l1_data": MOCK_L1, "l2_data": MOCK_L2, "l3_data": MOCK_L3})

    system_prompt = llm.calls[0]["system"].lower()
    assert "net new cac" in system_prompt
    assert "benchmark" in system_prompt


def test_interpret_user_message_contains_data():
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    llm = FakeAgentLLM([_text_response("report")])
    op = DailyReportOps(llm=llm)
    op.interpret({"l1_data": MOCK_L1, "l2_data": MOCK_L2, "l3_data": MOCK_L3})

    user_msg = llm.calls[0]["messages"][-1]["content"].lower()
    assert "l1" in user_msg
    assert "l2" in user_msg
    assert "l3" in user_msg


# --- fetch_data ---


def test_fetch_data_calls_all_three_layers():
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    with patch("vibe_inc.roles.d2c_growth.daily_report_ops.fetch_l1", return_value=MOCK_L1) as m1, \
         patch("vibe_inc.roles.d2c_growth.daily_report_ops.fetch_l2", return_value=MOCK_L2) as m2, \
         patch("vibe_inc.roles.d2c_growth.daily_report_ops.fetch_l3", return_value=MOCK_L3) as m3:
        llm = FakeAgentLLM([])
        op = DailyReportOps(llm=llm)
        result = op.fetch_data({"date": "2026-02-23"})

    m1.assert_called_once_with("2026-02-23")
    m2.assert_called_once_with("2026-02-23")
    m3.assert_called_once_with("2026-02-23")
    assert result["l1_data"] == MOCK_L1
    assert result["l2_data"] == MOCK_L2
    assert result["l3_data"] == MOCK_L3


def test_fetch_data_passes_none_when_no_date():
    from vibe_inc.roles.d2c_growth.daily_report_ops import DailyReportOps

    with patch("vibe_inc.roles.d2c_growth.daily_report_ops.fetch_l1", return_value=MOCK_L1), \
         patch("vibe_inc.roles.d2c_growth.daily_report_ops.fetch_l2", return_value=MOCK_L2), \
         patch("vibe_inc.roles.d2c_growth.daily_report_ops.fetch_l3", return_value=MOCK_L3):
        llm = FakeAgentLLM([])
        op = DailyReportOps(llm=llm)
        result = op.fetch_data({})

    assert "l1_data" in result
    assert "l2_data" in result
    assert "l3_data" in result
