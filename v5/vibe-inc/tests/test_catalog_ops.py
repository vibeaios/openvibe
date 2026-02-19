from openvibe_sdk.llm import LLMResponse


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


class FakeLLM:
    def __init__(self, responses=None):
        self.responses = list(responses or [_text_response()])
        self.calls = []

    def call(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def test_catalog_ops_is_operator():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    from openvibe_sdk import Operator
    assert issubclass(CatalogOps, Operator)
    assert CatalogOps.operator_id == "catalog_ops"


def test_schema_audit_is_agent_node():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    assert hasattr(CatalogOps.schema_audit, "_is_agent_node")
    assert CatalogOps.schema_audit._is_agent_node is True


def test_field_mapping_is_agent_node():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    assert hasattr(CatalogOps.field_mapping, "_is_agent_node")
    assert CatalogOps.field_mapping._is_agent_node is True


def test_coverage_report_is_agent_node():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    assert hasattr(CatalogOps.coverage_report, "_is_agent_node")
    assert CatalogOps.coverage_report._is_agent_node is True


def test_schema_audit_output_key():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    llm = FakeLLM([_text_response("Audit complete")])
    op = CatalogOps(llm=llm)
    result = op.schema_audit({})
    assert "audit_result" in result


def test_field_mapping_output_key():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    llm = FakeLLM([_text_response("Mapping done")])
    op = CatalogOps(llm=llm)
    result = op.field_mapping({})
    assert "mapping_result" in result


def test_coverage_report_output_key():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    llm = FakeLLM([_text_response("Coverage: 85%")])
    op = CatalogOps(llm=llm)
    result = op.coverage_report({})
    assert "coverage_result" in result
