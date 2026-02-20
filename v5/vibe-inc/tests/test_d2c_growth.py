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


def test_d2c_growth_has_operators():
    from vibe_inc.roles.d2c_growth import D2CGrowth
    assert D2CGrowth.role_id == "d2c_growth"
    op_ids = [op.operator_id for op in D2CGrowth.operators]
    assert "meta_ad_ops" in op_ids
    assert "google_ad_ops" in op_ids
    assert "amazon_ad_ops" in op_ids
    assert "tiktok_ad_ops" in op_ids
    assert "linkedin_ad_ops" in op_ids
    assert "pinterest_ad_ops" in op_ids
    assert "email_ops" in op_ids
    assert "cro_ops" in op_ids
    assert "cross_platform_ops" in op_ids
    assert "crm_ops" in op_ids


def test_d2c_growth_has_soul():
    from vibe_inc.roles.d2c_growth import D2CGrowth
    assert D2CGrowth.soul != ""
    assert "Net New CAC" in D2CGrowth.soul


def test_d2c_growth_get_operator():
    from vibe_inc.roles.d2c_growth import D2CGrowth

    role = D2CGrowth(llm=FakeLLM())
    meta_ad_ops = role.get_operator("meta_ad_ops")
    assert meta_ad_ops.operator_id == "meta_ad_ops"


def test_d2c_growth_soul_injected_in_prompt():
    from vibe_inc.roles.d2c_growth import D2CGrowth

    llm = FakeLLM()
    role = D2CGrowth(llm=llm)
    meta_ad_ops = role.get_operator("meta_ad_ops")
    meta_ad_ops.campaign_create({"brief": {"product": "bot"}})

    # Soul should be in the system prompt
    assert "Net New CAC" in llm.last_system
