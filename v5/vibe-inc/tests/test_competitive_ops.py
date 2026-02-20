"""Tests for CompetitiveIntel operator."""
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


def test_competitive_intel_has_two_nodes():
    """CompetitiveIntel should have weekly_scan and threat_assess."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel

    assert CompetitiveIntel.operator_id == "competitive_intel"
    llm = FakeLLM()
    op = CompetitiveIntel(llm=llm)
    assert hasattr(op, "weekly_scan")
    assert hasattr(op, "threat_assess")


def test_weekly_scan_tools():
    """weekly_scan should use web_search, web_fetch, read_memory, write_memory."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel

    cfg = CompetitiveIntel.weekly_scan._node_config
    assert "web_search" in cfg["tools"]
    assert "web_fetch" in cfg["tools"]
    assert "read_memory" in cfg["tools"]
    assert "write_memory" in cfg["tools"]


def test_threat_assess_tools_no_write():
    """threat_assess should use web tools + read_memory but NOT write_memory (analysis only)."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel

    cfg = CompetitiveIntel.threat_assess._node_config
    assert "web_search" in cfg["tools"]
    assert "read_memory" in cfg["tools"]
    assert "write_memory" not in cfg["tools"]


def test_weekly_scan_runs():
    """weekly_scan agent node executes with FakeLLM."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel

    llm = FakeLLM(content="Scan complete.")
    op = CompetitiveIntel(llm=llm)
    result = op.weekly_scan({"period": "last_7d"})
    assert result is not None
    assert len(llm.calls) == 1


def test_threat_assess_runs():
    """threat_assess agent node executes with FakeLLM."""
    from vibe_inc.roles.d2c_strategy.competitive import CompetitiveIntel

    llm = FakeLLM(content="Threat assessed.")
    op = CompetitiveIntel(llm=llm)
    result = op.threat_assess({"competitor": "Owl Labs", "move": "New AI feature"})
    assert result is not None
    assert "threat_result" in result
