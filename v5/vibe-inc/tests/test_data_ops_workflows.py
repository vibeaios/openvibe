from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, **kwargs):
        return LLMResponse(content="done", stop_reason="end_turn")


def test_catalog_audit_workflow_compiles():
    from vibe_inc.roles.data_ops.workflows import create_catalog_audit_graph
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    op = CatalogOps(llm=FakeLLM())
    graph = create_catalog_audit_graph(op)
    assert graph is not None


def test_freshness_check_workflow_compiles():
    from vibe_inc.roles.data_ops.workflows import create_freshness_check_graph
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    op = QualityOps(llm=FakeLLM())
    graph = create_freshness_check_graph(op)
    assert graph is not None


def test_data_query_workflow_compiles():
    from vibe_inc.roles.data_ops.workflows import create_data_query_graph
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    op = AccessOps(llm=FakeLLM())
    graph = create_data_query_graph(op)
    assert graph is not None


def test_build_report_workflow_compiles():
    from vibe_inc.roles.data_ops.workflows import create_build_report_graph
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    op = AccessOps(llm=FakeLLM())
    graph = create_build_report_graph(op)
    assert graph is not None


def test_runtime_registers_data_ops():
    from vibe_inc.main import create_runtime
    runtime = create_runtime(llm=FakeLLM())
    role = runtime.get_role("data_ops")
    assert role.role_id == "data_ops"
