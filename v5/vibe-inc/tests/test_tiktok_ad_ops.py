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
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps
    assert hasattr(TikTokAdOps.campaign_create, "_is_agent_node")
    assert TikTokAdOps.campaign_create._is_agent_node is True
    assert "tiktok_ads_create" in TikTokAdOps.campaign_create._node_config["tools"]


def test_campaign_create_output_key():
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps

    llm = FakeAgentLLM([_text_response("Campaign created: Bot TikTok")])
    op = TikTokAdOps(llm=llm)
    result = op.campaign_create({"brief": {"product": "bot", "objective": "CONVERSIONS"}})

    assert "campaign_result" in result
    assert result["campaign_result"] == "Campaign created: Bot TikTok"


# --- daily_optimize ---

def test_daily_optimize_is_agent_node():
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps
    assert hasattr(TikTokAdOps.daily_optimize, "_is_agent_node")
    assert "tiktok_ads_report" in TikTokAdOps.daily_optimize._node_config["tools"]


def test_daily_optimize_has_learning_phase_guard():
    """daily_optimize docstring must include learning phase protection rule."""
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps

    llm = FakeAgentLLM([_text_response("Optimized")])
    op = TikTokAdOps(llm=llm)
    op.daily_optimize({"date": "2026-02-20"})

    system_prompt = llm.calls[0]["system"]
    assert "learning phase" in system_prompt.lower()


# --- creative_refresh ---

def test_creative_refresh_is_agent_node():
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps
    assert hasattr(TikTokAdOps.creative_refresh, "_is_agent_node")
    assert TikTokAdOps.creative_refresh._is_agent_node is True


# --- weekly_report ---

def test_weekly_report_output_key():
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps

    llm = FakeAgentLLM([_text_response("Weekly: Bot CPA $480")])
    op = TikTokAdOps(llm=llm)
    result = op.weekly_report({"week": "2026-W08"})

    assert "report" in result


# --- audience_management ---

def test_audience_management_output_key():
    from vibe_inc.roles.d2c_growth.tiktok_ad_ops import TikTokAdOps

    llm = FakeAgentLLM([_text_response("2 audiences refreshed")])
    op = TikTokAdOps(llm=llm)
    result = op.audience_management({"action": "review"})

    assert "audience_result" in result
