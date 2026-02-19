from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="done")


def test_daily_optimize_graph_compiles():
    from vibe_inc.roles.d2c_growth.workflows import create_daily_optimize_graph
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    op = MetaAdOps(llm=FakeLLM())
    graph = create_daily_optimize_graph(op)
    assert graph is not None


def test_daily_optimize_graph_invokes():
    from vibe_inc.roles.d2c_growth.workflows import create_daily_optimize_graph
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    op = MetaAdOps(llm=FakeLLM())
    graph = create_daily_optimize_graph(op)
    result = graph.invoke({"date": "2026-02-19"})
    assert "optimization_result" in result


def test_campaign_create_graph_compiles():
    from vibe_inc.roles.d2c_growth.workflows import create_campaign_create_graph
    from vibe_inc.roles.d2c_growth.meta_ad_ops import MetaAdOps

    op = MetaAdOps(llm=FakeLLM())
    graph = create_campaign_create_graph(op)
    assert graph is not None


def test_experiment_analyze_graph_compiles():
    from vibe_inc.roles.d2c_growth.workflows import create_experiment_analyze_graph
    from vibe_inc.roles.d2c_growth.cro_ops import CROps

    op = CROps(llm=FakeLLM())
    graph = create_experiment_analyze_graph(op)
    assert graph is not None
