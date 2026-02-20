"""Integration tests: DataOps ↔ D2C Growth interaction.

Verifies that operators from both roles can be activated through the runtime,
and that the full workflow pipeline (activate → graph → operator → result) works
across all major operator types.
"""
from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="Integration test output")


def _runtime():
    from vibe_inc.main import create_runtime
    return create_runtime(llm=FakeLLM())


# --- Cross-role activation ---


def test_dataops_catalog_audit_activates():
    """DataOps catalog_audit workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="data_ops",
        operator_id="catalog_ops",
        workflow_id="catalog_audit",
        input_data={},
    )
    assert "audit_result" in result


def test_dataops_freshness_check_activates():
    """DataOps freshness_check workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="data_ops",
        operator_id="quality_ops",
        workflow_id="freshness_check",
        input_data={},
    )
    assert "freshness_result" in result


def test_dataops_data_query_activates():
    """DataOps data_query workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="data_ops",
        operator_id="access_ops",
        workflow_id="data_query",
        input_data={"query": "SELECT 1"},
    )
    assert "query_result" in result


def test_dataops_build_report_activates():
    """DataOps build_report workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="data_ops",
        operator_id="access_ops",
        workflow_id="build_report",
        input_data={"report_type": "weekly"},
    )
    assert "report_result" in result


# --- D2C Growth platform workflows ---


def test_google_campaign_create_activates():
    """GoogleAdOps campaign_create workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="google_ad_ops",
        workflow_id="campaign_create",
        input_data={"brief": {"product": "bot"}},
    )
    assert "campaign_result" in result


def test_amazon_daily_optimize_activates():
    """AmazonAdOps daily_optimize workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="amazon_ad_ops",
        workflow_id="daily_optimize",
        input_data={"date": "2026-02-19"},
    )
    assert "optimization_result" in result


def test_tiktok_creative_refresh_activates():
    """TikTokAdOps creative_refresh workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="tiktok_ad_ops",
        workflow_id="creative_refresh",
        input_data={},
    )
    assert "creative_result" in result


def test_linkedin_lead_quality_review_activates():
    """LinkedInAdOps lead_quality_review workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="linkedin_ad_ops",
        workflow_id="lead_quality_review",
        input_data={},
    )
    assert "lead_quality_result" in result


def test_pinterest_weekly_report_activates():
    """PinterestAdOps weekly_report workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="pinterest_ad_ops",
        workflow_id="weekly_report",
        input_data={"week": "2026-W08"},
    )
    assert "report" in result


def test_email_campaign_create_activates():
    """EmailOps campaign_create workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="email_ops",
        workflow_id="campaign_create",
        input_data={"brief": {"segment": "new_subscribers"}},
    )
    assert "campaign_result" in result


def test_cro_funnel_diagnose_activates():
    """CROps funnel_diagnose workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cro_ops",
        workflow_id="funnel_diagnose",
        input_data={"product": "bot"},
    )
    assert "diagnosis" in result


def test_cro_product_optimize_activates():
    """CROps product_optimize workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cro_ops",
        workflow_id="product_optimize",
        input_data={"product_id": "123"},
    )
    assert "product_result" in result


def test_cro_conversion_report_activates():
    """CROps conversion_report workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cro_ops",
        workflow_id="conversion_report",
        input_data={"period": "last_7_days"},
    )
    assert "conversion_report" in result


# --- Runtime structure tests ---


def test_cross_platform_unified_cac_report_activates():
    """CrossPlatformOps unified_cac_report workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cross_platform_ops",
        workflow_id="unified_cac_report",
        input_data={"period": "last_7_days"},
    )
    assert "report" in result


def test_cross_platform_budget_rebalance_activates():
    """CrossPlatformOps budget_rebalance workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cross_platform_ops",
        workflow_id="budget_rebalance",
        input_data={"total_budget": 10000.0},
    )
    assert "rebalance_result" in result


def test_cross_platform_health_check_activates():
    """CrossPlatformOps platform_health_check workflow runs through runtime."""
    runtime = _runtime()
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cross_platform_ops",
        workflow_id="platform_health_check",
        input_data={},
    )
    assert "health_result" in result


def test_runtime_has_both_roles():
    """Runtime should have both D2C Growth and DataOps roles."""
    runtime = _runtime()
    role_ids = [r.role_id for r in runtime.list_roles()]
    assert "d2c_growth" in role_ids
    assert "data_ops" in role_ids


def test_runtime_d2c_growth_operator_count():
    """D2C Growth should have 8+ operators."""
    runtime = _runtime()
    d2c = next(r for r in runtime.list_roles() if r.role_id == "d2c_growth")
    # Meta, Google, Amazon, TikTok, LinkedIn, Pinterest, Email, CRO
    assert len(d2c.operators) >= 8
