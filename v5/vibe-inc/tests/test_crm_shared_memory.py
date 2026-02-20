import yaml
from pathlib import Path

_SHARED = Path(__file__).parent.parent / "shared_memory" / "crm"


def test_routing_rules_exists_and_has_signals():
    assert (_SHARED / "routing_rules.yaml").exists()
    data = yaml.safe_load((_SHARED / "routing_rules.yaml").read_text())
    assert "signals" in data
    assert "high_value_d2c" in data["signals"]
    assert "b2b_enriched" in data["signals"]
    assert "repeat_buyer" in data["signals"]
    # Each signal must have condition + workflow_id
    for signal_name, signal in data["signals"].items():
        assert "condition" in signal, f"{signal_name} missing condition"
        assert "workflow_id" in signal, f"{signal_name} missing workflow_id"


def test_pipeline_config_exists_and_has_stages():
    assert (_SHARED / "pipeline_config.yaml").exists()
    data = yaml.safe_load((_SHARED / "pipeline_config.yaml").read_text())
    assert "pipelines" in data
    assert "b2b" in data["pipelines"]
    b2b = data["pipelines"]["b2b"]
    assert "stages" in b2b
    assert "lead" in b2b["stages"]
    assert "closed_won" in b2b["stages"]
    assert b2b["stale_threshold_days"] == 14


def test_pipeline_config_has_product_targets():
    data = yaml.safe_load((_SHARED / "pipeline_config.yaml").read_text())
    assert "products" in data
    assert "bot" in data["products"]
    assert "dot" in data["products"]
    assert "board" in data["products"]
    assert data["products"]["bot"]["avg_deal_value"] == 3000
    assert data["products"]["board"]["typical_cycle_days"] == 90
