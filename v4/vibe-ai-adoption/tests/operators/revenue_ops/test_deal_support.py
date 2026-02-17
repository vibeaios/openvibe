"""Tests for Revenue Ops deal support workflow."""

from unittest.mock import MagicMock, patch

from vibe_ai_ops.operators.revenue_ops.workflows.deal_support import (
    create_deal_support_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str, model: str = "claude-sonnet-4-5-20250929") -> ClaudeResponse:
    return ClaudeResponse(content=content, tokens_in=100, tokens_out=300, model=model)


@patch("vibe_ai_ops.operators.revenue_ops.workflows.deal_support.call_claude")
@patch("vibe_ai_ops.operators.revenue_ops.workflows.deal_support.hubspot_client")
def test_full_deal_support_flow(mock_hs, mock_claude):
    """Full graph: pull_deals → assess_risk → generate_actions."""
    mock_hs.get_active_deals.return_value = [
        {"dealname": "Acme Corp", "amount": "50000", "dealstage": "proposal"},
        {"dealname": "Beta Inc", "amount": "25000", "dealstage": "negotiation"},
    ]
    mock_claude.side_effect = [
        _mock_response("Risk Assessment:\n- Acme Corp: HIGH (stalled 2 weeks)\n- Beta Inc: LOW"),
        _mock_response("Actions:\n1. Acme: Schedule executive call today\n2. Beta: Proceed normally",
                       model="claude-haiku-4-5-20251001"),
    ]

    graph = create_deal_support_graph()
    result = graph.invoke({})

    assert len(result["active_deals"]) == 2
    assert "Acme Corp" in result["risk_assessment"]
    assert "Actions" in result["actions"]
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.revenue_ops.workflows.deal_support.call_claude")
@patch("vibe_ai_ops.operators.revenue_ops.workflows.deal_support.hubspot_client")
def test_deal_support_empty_pipeline(mock_hs, mock_claude):
    """No active deals → assessment reflects empty state."""
    mock_hs.get_active_deals.return_value = []
    mock_claude.side_effect = [
        _mock_response("No active deals in pipeline."),
        _mock_response("No actions required."),
    ]

    graph = create_deal_support_graph()
    result = graph.invoke({})

    assert result["active_deals"] == []
    assert "No active deals" in result["risk_assessment"]
