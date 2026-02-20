from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="done")


def test_workflow_enrollment_graph_compiles():
    from vibe_inc.roles.d2c_growth.crm_workflows import create_workflow_enrollment_graph
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps

    op = CRMOps(llm=FakeLLM())
    graph = create_workflow_enrollment_graph(op)
    assert graph is not None


def test_deal_progression_graph_compiles():
    from vibe_inc.roles.d2c_growth.crm_workflows import create_deal_progression_graph
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps

    op = CRMOps(llm=FakeLLM())
    graph = create_deal_progression_graph(op)
    assert graph is not None


def test_enrichment_audit_graph_compiles():
    from vibe_inc.roles.d2c_growth.crm_workflows import create_enrichment_audit_graph
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps

    op = CRMOps(llm=FakeLLM())
    graph = create_enrichment_audit_graph(op)
    assert graph is not None


def test_pipeline_health_graph_compiles():
    from vibe_inc.roles.d2c_growth.crm_workflows import create_pipeline_health_graph
    from vibe_inc.roles.d2c_growth.crm_ops import CRMOps

    op = CRMOps(llm=FakeLLM())
    graph = create_pipeline_health_graph(op)
    assert graph is not None
