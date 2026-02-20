"""Tests for D2C Strategy shared memory configuration files."""
import yaml
from pathlib import Path

_MEMORY_DIR = Path(__file__).resolve().parents[1] / "shared_memory"


def test_competitor_registry_loads():
    """competitor_registry.yaml should load and contain all three product categories."""
    data = yaml.safe_load((_MEMORY_DIR / "competitive/competitor_registry.yaml").read_text())
    assert "bot" in data
    assert "dot" in data
    assert "board" in data
    # Each category has competitors list
    assert len(data["bot"]["competitors"]) >= 3
    assert len(data["dot"]["competitors"]) >= 3
    assert len(data["board"]["competitors"]) >= 2


def test_competitor_registry_has_required_fields():
    """Each competitor entry should have name, url, category, threat_level."""
    data = yaml.safe_load((_MEMORY_DIR / "competitive/competitor_registry.yaml").read_text())
    for product in ("bot", "dot", "board"):
        for comp in data[product]["competitors"]:
            assert "name" in comp, f"Missing name in {product} competitor"
            assert "url" in comp, f"Missing url for {comp.get('name', '?')}"
            assert "threat_level" in comp, f"Missing threat_level for {comp.get('name', '?')}"


def test_market_signals_template_loads():
    """market-signals.yaml should load as a valid template."""
    data = yaml.safe_load((_MEMORY_DIR / "competitive/market-signals.yaml").read_text())
    assert "signals" in data
    assert "major" in data["signals"]
    assert "minor" in data["signals"]
    assert "risk_summary" in data
