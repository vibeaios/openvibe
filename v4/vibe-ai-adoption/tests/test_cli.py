"""Tests for CLI — operator-based interface."""

from vibe_ai_ops.cli import list_operators, get_operator_info, get_system_summary


def test_list_operators():
    operators = list_operators(config_path="config/operators.yaml")
    assert len(operators) == 5
    assert all("id" in op and "name" in op for op in operators)


def test_list_operators_includes_all_five():
    operators = list_operators(config_path="config/operators.yaml")
    ids = {op["id"] for op in operators}
    assert ids == {
        "company_intel", "revenue_ops", "content_engine",
        "customer_success", "market_intel",
    }


def test_get_operator_info():
    info = get_operator_info("revenue_ops", config_path="config/operators.yaml")
    assert info is not None
    assert info["id"] == "revenue_ops"
    assert info["name"] == "Revenue Operations"
    assert len(info["workflows"]) == 5
    assert info["total_nodes"] > 0


def test_get_operator_info_not_found():
    info = get_operator_info("x99", config_path="config/operators.yaml")
    assert info is None


def test_get_system_summary():
    summary = get_system_summary(config_path="config/operators.yaml")
    assert summary["operators"] == 5
    assert summary["workflows"] > 0
    assert summary["nodes"] > 0
    assert summary["llm_nodes"] > 0
    assert summary["logic_nodes"] > 0
