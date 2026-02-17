"""Tests for Revenue Ops engagement workflow."""

import json
from unittest.mock import patch

from vibe_ai_ops.operators.revenue_ops.workflows.engagement import (
    create_engagement_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str, model: str = "claude-sonnet-4-5-20250929") -> ClaudeResponse:
    return ClaudeResponse(content=content, tokens_in=100, tokens_out=300, model=model)


@patch("vibe_ai_ops.operators.revenue_ops.workflows.engagement.call_claude")
def test_full_engagement_flow(mock_claude):
    """Full graph: research → generate → personalize → format."""
    sequence = [
        {"touch": 1, "channel": "email", "subject": "Hi", "body": "...", "wait_days": 0},
        {"touch": 2, "channel": "linkedin", "subject": "Follow up", "body": "...", "wait_days": 3},
    ]
    personalized = [
        {"touch": 1, "channel": "email", "subject": "Hi CTO", "body": "Personalized...", "wait_days": 0},
        {"touch": 2, "channel": "linkedin", "subject": "Follow up CTO", "body": "Personalized...", "wait_days": 3},
    ]

    mock_claude.side_effect = [
        _mock_response("Research: CTO of mid-size SaaS, focused on AI adoption."),
        _mock_response(json.dumps(sequence)),
        _mock_response(json.dumps(personalized), model="claude-haiku-4-5-20251001"),
    ]

    graph = create_engagement_graph()
    result = graph.invoke({
        "contact_id": "c-123",
        "buyer_profile": {"name": "Jane", "title": "CTO"},
        "segment": "mid-market-saas",
    })

    assert result["final_plan"]["status"] == "ready"
    assert result["final_plan"]["contact_id"] == "c-123"
    assert len(result["personalized_sequence"]) == 2
    assert mock_claude.call_count == 3


@patch("vibe_ai_ops.operators.revenue_ops.workflows.engagement.call_claude")
def test_engagement_fallback_on_bad_json(mock_claude):
    """When generate_sequence returns invalid JSON, falls back to raw content."""
    mock_claude.side_effect = [
        _mock_response("Research notes about the buyer."),
        _mock_response("Not valid JSON at all"),
        _mock_response("Also not JSON"),
    ]

    graph = create_engagement_graph()
    result = graph.invoke({"contact_id": "c-456", "buyer_profile": {}})

    # Fallback: single touch with raw content
    assert len(result["outreach_sequence"]) == 1
    assert result["outreach_sequence"][0]["channel"] == "email"
    # Personalize fallback: returns original sequence unchanged
    assert result["final_plan"]["status"] == "ready"


@patch("vibe_ai_ops.operators.revenue_ops.workflows.engagement.call_claude")
def test_engagement_research_notes_stored(mock_claude):
    """Research notes from first node are available in state."""
    mock_claude.side_effect = [
        _mock_response("Detailed research about buyer's challenges."),
        _mock_response(json.dumps([{"touch": 1, "channel": "email", "subject": "Hi", "body": ".", "wait_days": 0}])),
        _mock_response(json.dumps([{"touch": 1, "channel": "email", "subject": "Hi", "body": ".", "wait_days": 0}])),
    ]

    graph = create_engagement_graph()
    result = graph.invoke({"contact_id": "c-789", "buyer_profile": {}})

    assert "Detailed research" in result["research_notes"]
