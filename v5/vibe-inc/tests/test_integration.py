"""Integration test: full D2C Growth loop with FakeLLM."""
from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="Integration test output")


def test_full_loop_daily_optimize_then_experiment_analyze():
    """Simulate a daily loop: MetaAdOps optimize → CROps analyze."""
    from vibe_inc.main import create_runtime

    runtime = create_runtime(llm=FakeLLM())

    # Step 1: MetaAdOps daily optimize
    opt_result = runtime.activate(
        role_id="d2c_growth",
        operator_id="meta_ad_ops",
        workflow_id="daily_optimize",
        input_data={"date": "2026-02-19"},
    )
    assert "optimization_result" in opt_result

    # Step 2: CROps experiment analyze
    exp_result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cro_ops",
        workflow_id="experiment_analyze",
        input_data={"product": "bot"},
    )
    assert "analysis" in exp_result


def test_full_loop_campaign_create():
    """Simulate campaign creation workflow."""
    from vibe_inc.main import create_runtime

    runtime = create_runtime(llm=FakeLLM())

    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="meta_ad_ops",
        workflow_id="campaign_create",
        input_data={"brief": {
            "product": "bot",
            "narrative": "foundation",
            "audience": "smb_managers",
            "budget_daily": 100,
        }},
    )
    assert "campaign_result" in result
