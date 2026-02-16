"""Tests for main entry point — build_system() with OperatorRuntime."""

from vibe_ai_ops.main import build_system, _WORKFLOW_REGISTRY


def test_build_system_loads_all_operators():
    system = build_system(config_path="config/operators.yaml")
    assert system["operator_count"] == 5
    assert len(system["operators"]) == 5


def test_build_system_returns_summary():
    system = build_system(config_path="config/operators.yaml")
    summary = system["summary"]
    assert summary["operators"] == 5
    assert summary["workflows"] > 0
    assert summary["nodes"] > 0
    assert summary["llm_nodes"] > 0
    assert summary["logic_nodes"] > 0


def test_build_system_registers_workflow_factories():
    system = build_system(config_path="config/operators.yaml")
    runtime = system["runtime"]
    # Company intel research should be registered
    factory = runtime.get_workflow_factory("company_intel", "research")
    assert factory is not None


def test_workflow_registry_covers_all_operators():
    operator_ids = set(op_id for op_id, _ in _WORKFLOW_REGISTRY)
    assert operator_ids == {
        "company_intel", "revenue_ops", "content_engine",
        "customer_success", "market_intel",
    }


def test_workflow_registry_has_22_workflows():
    assert len(_WORKFLOW_REGISTRY) == 22
