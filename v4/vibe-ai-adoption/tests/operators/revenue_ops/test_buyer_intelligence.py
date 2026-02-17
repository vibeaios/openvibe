"""Tests for Revenue Ops buyer intelligence workflow."""

from unittest.mock import patch

from vibe_ai_ops.operators.revenue_ops.workflows.buyer_intelligence import (
    create_buyer_intel_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str) -> ClaudeResponse:
    return ClaudeResponse(
        content=content, tokens_in=100, tokens_out=200,
        model="claude-haiku-4-5-20251001",
    )


@patch("vibe_ai_ops.operators.revenue_ops.workflows.buyer_intelligence.call_claude")
def test_full_buyer_intel_flow(mock_claude):
    """Full graph: scan → analyze → brief."""
    mock_claude.side_effect = [
        _mock_response("Analysis: 3 high-intent signals detected from enterprise accounts."),
        _mock_response("Brief:\n- 3 enterprise accounts showing buying signals\n- Action: Prioritize outreach"),
    ]

    graph = create_buyer_intel_graph()
    result = graph.invoke({
        "active_deals": [{"dealname": "Acme Corp", "amount": "50000"}],
        "recent_scores": [{"contact_id": "c1", "score": 85}],
    })

    assert "signals" in result
    assert "analysis" in result
    assert "brief" in result
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.revenue_ops.workflows.buyer_intelligence.call_claude")
def test_buyer_intel_empty_state(mock_claude):
    """Works with empty state — scan generates default signals."""
    mock_claude.side_effect = [
        _mock_response("No significant signals detected."),
        _mock_response("Brief: No actionable intelligence this cycle."),
    ]

    graph = create_buyer_intel_graph()
    result = graph.invoke({})

    assert len(result["signals"]) == 2  # default scan produces 2 signal groups
    assert "No significant signals" in result["analysis"]


@patch("vibe_ai_ops.operators.revenue_ops.workflows.buyer_intelligence.call_claude")
def test_buyer_intel_preserves_custom_signals(mock_claude):
    """When signals are pre-populated, scan preserves them."""
    mock_claude.side_effect = [
        _mock_response("Strong signals from Anthropic."),
        _mock_response("Brief: Anthropic is a hot lead."),
    ]

    custom_signals = [{"source": "linkedin", "signal": "CTO liked our post"}]
    graph = create_buyer_intel_graph()
    result = graph.invoke({"signals": custom_signals})

    assert result["signals"] == custom_signals
