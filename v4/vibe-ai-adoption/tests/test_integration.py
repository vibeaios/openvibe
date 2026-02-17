"""Integration test: verify operators wire through all layers."""

from unittest.mock import patch

from vibe_ai_ops.operators.base import OperatorRuntime
from vibe_ai_ops.operators.company_intel.workflows.research import (
    create_company_intel_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse
from vibe_ai_ops.temporal.schedules import build_schedule_specs
from vibe_ai_ops.temporal.activities.company_intel_activity import CompanyIntelInput


def test_operator_runtime_activates_workflow():
    """OperatorRuntime → register → activate → LangGraph graph runs."""
    runtime = OperatorRuntime(config_path="config/operators.yaml")
    runtime.load(enabled_only=True)
    runtime.register_workflow("company_intel", "research", create_company_intel_graph)

    with patch(
        "vibe_ai_ops.operators.company_intel.workflows.research.call_claude"
    ) as mock_claude:
        mock_claude.return_value = ClaudeResponse(
            content="Test research output",
            tokens_in=100,
            tokens_out=200,
            model="claude-haiku-4-5-20251001",
        )
        result = runtime.activate(
            "company_intel", "query", {"company_name": "TestCo"}
        )

    assert result["company_name"] == "TestCo"
    assert "research" in result


def test_temporal_schedule_specs_from_agent_configs():
    """Temporal schedule specs still build from agent configs."""
    from vibe_ai_ops.shared.config import load_agent_configs

    configs = load_agent_configs("config/agents.yaml", enabled_only=True)
    specs = build_schedule_specs(configs)
    assert len(specs) > 0
    assert all("agent_id" in s for s in specs)


def test_temporal_activity_input_works():
    """Temporal activity input dataclass is valid."""
    inp = CompanyIntelInput(company_name="Stripe")
    assert inp.company_name == "Stripe"
