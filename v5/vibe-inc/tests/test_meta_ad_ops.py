from openvibe_sdk.llm import LLMResponse, ToolCall


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


def _tool_response(tool_name, tool_input=None):
    return LLMResponse(
        content="I'll use a tool.",
        tool_calls=[ToolCall(id="tc_1", name=tool_name, input=tool_input or {})],
        stop_reason="tool_use",
    )


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
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps
    assert hasattr(MetaAdOps.campaign_create, "_is_agent_node")
    assert MetaAdOps.campaign_create._is_agent_node is True
    assert "meta_ads_create" in MetaAdOps.campaign_create._node_config["tools"]


def test_campaign_create_uses_brief():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    llm = FakeAgentLLM([_text_response("Campaign created: Bot Foundation")])
    op = MetaAdOps(llm=llm)
    result = op.campaign_create({"brief": {"product": "bot", "narrative": "foundation"}})

    assert result["campaign_result"] == "Campaign created: Bot Foundation"
    assert len(llm.calls) == 1
    assert "brief" in llm.calls[0]["messages"][-1]["content"]


def test_campaign_create_docstring_is_system_prompt():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    llm = FakeAgentLLM([_text_response()])
    op = MetaAdOps(llm=llm)
    op.campaign_create({"brief": {}})

    assert "meta ads" in llm.calls[0]["system"].lower()


# --- daily_optimize ---

def test_daily_optimize_is_agent_node():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps
    assert hasattr(MetaAdOps.daily_optimize, "_is_agent_node")
    assert "meta_ads_read" in MetaAdOps.daily_optimize._node_config["tools"]


def test_daily_optimize_reads_performance():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    llm = FakeAgentLLM([_text_response("Optimized: paused 2 underperformers")])
    op = MetaAdOps(llm=llm)
    result = op.daily_optimize({"date": "2026-02-19"})

    assert "optimization_result" in result
    assert len(llm.calls) == 1


def test_daily_optimize_has_rules_tool():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps
    assert "meta_ads_rules" in MetaAdOps.daily_optimize._node_config["tools"]


# --- weekly_report ---

def test_weekly_report_is_agent_node():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps
    assert hasattr(MetaAdOps.weekly_report, "_is_agent_node")


def test_weekly_report_output_key():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    llm = FakeAgentLLM([_text_response("Weekly: Bot CAC $380, Dot CAC $270")])
    op = MetaAdOps(llm=llm)
    result = op.weekly_report({"week": "2026-W08"})

    assert "report" in result


# --- audience_refresh (new) ---

def test_audience_refresh_is_agent_node():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps
    assert hasattr(MetaAdOps.audience_refresh, "_is_agent_node")
    assert MetaAdOps.audience_refresh._is_agent_node is True
    assert "meta_audiences" in MetaAdOps.audience_refresh._node_config["tools"]


def test_audience_refresh_output_key():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    llm = FakeAgentLLM([_text_response("3 audiences refreshed")])
    op = MetaAdOps(llm=llm)
    result = op.audience_refresh({"action": "review"})

    assert "audience_result" in result


# --- creative_fatigue_check (new) ---

def test_creative_fatigue_check_is_agent_node():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps
    assert hasattr(MetaAdOps.creative_fatigue_check, "_is_agent_node")
    assert MetaAdOps.creative_fatigue_check._is_agent_node is True


def test_creative_fatigue_check_output_key():
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    llm = FakeAgentLLM([_text_response("2 creatives showing fatigue")])
    op = MetaAdOps(llm=llm)
    result = op.creative_fatigue_check({"lookback_days": 14})

    assert "fatigue_result" in result
