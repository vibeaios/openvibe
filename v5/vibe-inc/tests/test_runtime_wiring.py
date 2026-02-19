from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="done")


def test_runtime_loads_d2c_growth():
    from vibe_inc.main import create_runtime

    runtime = create_runtime(llm=FakeLLM())
    role = runtime.get_role("d2c_growth")
    assert role.role_id == "d2c_growth"


def test_runtime_activates_daily_optimize():
    from vibe_inc.main import create_runtime

    runtime = create_runtime(llm=FakeLLM())
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="meta_ad_ops",
        workflow_id="daily_optimize",
        input_data={"date": "2026-02-19"},
    )
    assert "optimization_result" in result


def test_runtime_activates_experiment_analyze():
    from vibe_inc.main import create_runtime

    runtime = create_runtime(llm=FakeLLM())
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="cro_ops",
        workflow_id="experiment_analyze",
        input_data={"product": "bot"},
    )
    assert "analysis" in result
