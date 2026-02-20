"""Tests for D2C Strategy role."""
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


def test_d2c_strategy_has_operators():
    """D2CStrategy should have PositioningEngine and CompetitiveIntel."""
    from vibe_inc.roles.d2c_strategy import D2CStrategy

    assert D2CStrategy.role_id == "d2c_strategy"
    op_ids = [op.operator_id for op in D2CStrategy.operators]
    assert "positioning_engine" in op_ids
    assert "competitive_intel" in op_ids


def test_d2c_strategy_has_soul():
    """D2CStrategy should have a non-empty soul with key principles."""
    from vibe_inc.roles.d2c_strategy import D2CStrategy

    assert D2CStrategy.soul != ""
    assert "Positioning is a bet" in D2CStrategy.soul
    assert "ICP clarity" in D2CStrategy.soul


def test_d2c_strategy_get_operator():
    """D2CStrategy should resolve operators by id."""
    from vibe_inc.roles.d2c_strategy import D2CStrategy

    llm = FakeLLM()
    role = D2CStrategy(llm=llm)
    pos = role.get_operator("positioning_engine")
    assert pos is not None
    comp = role.get_operator("competitive_intel")
    assert comp is not None


def test_d2c_strategy_soul_injected_in_prompt():
    """Soul should appear in agent system prompt when node executes."""
    from vibe_inc.roles.d2c_strategy import D2CStrategy

    llm = FakeLLM()
    role = D2CStrategy(llm=llm)
    pos = role.get_operator("positioning_engine")
    pos.define_framework({"product": "bot"})

    assert "Positioning is a bet" in llm.last_system
