from openvibe_sdk.llm import LLMResponse


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


class FakeAgentLLM:
    """Fake LLM that returns pre-configured responses in sequence."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call(self, *, system, messages, **kwargs):
        self.calls.append({"system": system, "messages": messages, **kwargs})
        return self.responses.pop(0)


# --- campaign_create ---

def test_campaign_create_is_agent_node():
    from vibe_inc.roles.d2c_growth.pinterest_ad_ops import PinterestAdOps
    assert hasattr(PinterestAdOps.campaign_create, "_is_agent_node")
    assert PinterestAdOps.campaign_create._is_agent_node is True
    assert "pinterest_ads_create" in PinterestAdOps.campaign_create._node_config["tools"]


def test_campaign_create_output_key():
    from vibe_inc.roles.d2c_growth.pinterest_ad_ops import PinterestAdOps

    llm = FakeAgentLLM([_text_response("Campaign created: Bot Pinterest")])
    op = PinterestAdOps(llm=llm)
    result = op.campaign_create({"brief": {"product": "bot", "objective": "CONVERSIONS"}})

    assert "campaign_result" in result
    assert result["campaign_result"] == "Campaign created: Bot Pinterest"


# --- daily_optimize ---

def test_daily_optimize_is_agent_node():
    from vibe_inc.roles.d2c_growth.pinterest_ad_ops import PinterestAdOps
    assert hasattr(PinterestAdOps.daily_optimize, "_is_agent_node")
    assert "pinterest_ads_report" in PinterestAdOps.daily_optimize._node_config["tools"]


def test_daily_optimize_uses_outbound_clicks():
    """daily_optimize system prompt must reference OUTBOUND clicks, not generic CTR."""
    from vibe_inc.roles.d2c_growth.pinterest_ad_ops import PinterestAdOps

    llm = FakeAgentLLM([_text_response("Optimized")])
    op = PinterestAdOps(llm=llm)
    op.daily_optimize({"date": "2026-02-20"})

    system_prompt = llm.calls[0]["system"]
    assert "OUTBOUND" in system_prompt


# --- creative_refresh ---

def test_creative_refresh_output_key():
    from vibe_inc.roles.d2c_growth.pinterest_ad_ops import PinterestAdOps

    llm = FakeAgentLLM([_text_response("Pins healthy, no fatigue detected")])
    op = PinterestAdOps(llm=llm)
    result = op.creative_refresh({"lookback_days": 30})

    assert "creative_result" in result


# --- weekly_report ---

def test_weekly_report_output_key():
    from vibe_inc.roles.d2c_growth.pinterest_ad_ops import PinterestAdOps

    llm = FakeAgentLLM([_text_response("Weekly: Bot CPA $320, Dot CPA $260")])
    op = PinterestAdOps(llm=llm)
    result = op.weekly_report({"week": "2026-W08"})

    assert "report" in result
