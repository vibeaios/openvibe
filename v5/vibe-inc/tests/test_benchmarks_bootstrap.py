import yaml
from pathlib import Path

_SHARED = Path(__file__).parent.parent / "shared_memory" / "performance"


# --- Email Benchmarks ---

def test_email_benchmarks_exists():
    assert (_SHARED / "email_benchmarks.yaml").exists()


def test_email_has_campaign_targets():
    data = yaml.safe_load((_SHARED / "email_benchmarks.yaml").read_text())
    assert "campaigns" in data
    assert data["campaigns"]["open_rate_target"] == 0.25
    assert data["campaigns"]["click_rate_target"] == 0.035


def test_email_has_flow_benchmarks():
    data = yaml.safe_load((_SHARED / "email_benchmarks.yaml").read_text())
    assert "flows" in data
    assert "welcome" in data["flows"]
    assert "abandoned_cart" in data["flows"]
    assert "post_purchase" in data["flows"]
    assert "winback" in data["flows"]


def test_email_has_list_health():
    data = yaml.safe_load((_SHARED / "email_benchmarks.yaml").read_text())
    assert "list_health" in data
    assert data["list_health"]["suppression_threshold_days"] == 180


def test_email_has_product_targets():
    data = yaml.safe_load((_SHARED / "email_benchmarks.yaml").read_text())
    assert "products" in data
    assert "bot" in data["products"]
    assert "dot" in data["products"]


# --- CRO Benchmarks ---

def test_cro_benchmarks_exists():
    assert (_SHARED / "cro_benchmarks.yaml").exists()


def test_cro_has_funnel_targets():
    data = yaml.safe_load((_SHARED / "cro_benchmarks.yaml").read_text())
    assert "funnel" in data
    assert data["funnel"]["overall_cvr"] == 0.01
    assert data["funnel"]["pdp_scroll_to_cta"] == 0.70


def test_cro_has_experiment_standards():
    data = yaml.safe_load((_SHARED / "cro_benchmarks.yaml").read_text())
    assert "experiments" in data
    assert data["experiments"]["min_sample_size"] == 20000
    assert data["experiments"]["min_confidence"] == 0.95


def test_cro_has_product_cvr_targets():
    data = yaml.safe_load((_SHARED / "cro_benchmarks.yaml").read_text())
    assert "products" in data
    assert data["products"]["bot"]["target_cvr"] == 0.012
    assert data["products"]["dot"]["target_cvr"] == 0.015


def test_cro_has_discount_limits():
    data = yaml.safe_load((_SHARED / "cro_benchmarks.yaml").read_text())
    assert "discounts" in data
    assert data["discounts"]["min_margin_after_discount"] == 0.40
