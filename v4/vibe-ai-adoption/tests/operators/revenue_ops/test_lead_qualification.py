"""Tests for Revenue Ops lead qualification workflow."""

import json
from unittest.mock import MagicMock, patch

from vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification import (
    create_lead_qual_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str) -> ClaudeResponse:
    return ClaudeResponse(
        content=content, tokens_in=100, tokens_out=300,
        model="claude-sonnet-4-5-20250929",
    )


@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.call_claude")
@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.hubspot_client")
def test_sales_route(mock_hs, mock_claude):
    """High-scoring lead routes to sales."""
    mock_hs.get_contact.return_value = {"company": "Anthropic", "jobtitle": "CTO"}
    mock_hs.update_contact.return_value = None
    mock_claude.return_value = _mock_response(json.dumps({
        "fit_score": 90, "intent_score": 85, "urgency_score": 70,
        "reasoning": "Strong fit", "route": "sales",
    }))

    graph = create_lead_qual_graph()
    result = graph.invoke({"contact_id": "test-123", "source": "website"})

    assert result["route"] == "sales"
    assert result["crm_updated"] is True
    assert result["score"]["fit_score"] == 90


@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.call_claude")
@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.hubspot_client")
def test_nurture_route(mock_hs, mock_claude):
    """Mid-scoring lead routes to nurture."""
    mock_hs.get_contact.return_value = {"company": "Startup", "jobtitle": "Dev"}
    mock_hs.update_contact.return_value = None
    mock_claude.return_value = _mock_response(json.dumps({
        "fit_score": 60, "intent_score": 55, "urgency_score": 40,
        "reasoning": "Moderate fit", "route": "nurture",
    }))

    graph = create_lead_qual_graph()
    result = graph.invoke({"contact_id": "test-456"})
    assert result["route"] == "nurture"


@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.call_claude")
@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.hubspot_client")
def test_disqualify_low_fit(mock_hs, mock_claude):
    """Very low fit_score disqualifies regardless of other scores."""
    mock_hs.get_contact.return_value = {"company": "N/A"}
    mock_hs.update_contact.return_value = None
    mock_claude.return_value = _mock_response(json.dumps({
        "fit_score": 10, "intent_score": 90, "urgency_score": 90,
        "reasoning": "Poor fit", "route": "disqualify",
    }))

    graph = create_lead_qual_graph()
    result = graph.invoke({"contact_id": "test-789"})
    assert result["route"] == "disqualify"


@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.call_claude")
@patch("vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification.hubspot_client")
def test_education_route(mock_hs, mock_claude):
    """Low composite score routes to education."""
    mock_hs.get_contact.return_value = {}
    mock_hs.update_contact.return_value = None
    mock_claude.return_value = _mock_response(json.dumps({
        "fit_score": 30, "intent_score": 30, "urgency_score": 30,
        "reasoning": "Low interest", "route": "education",
    }))

    graph = create_lead_qual_graph()
    result = graph.invoke({"contact_id": "test-000"})
    assert result["route"] == "education"
