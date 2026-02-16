"""Tests for Revenue Ops nurture sequence workflow."""

import json
from unittest.mock import patch

from vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence import (
    create_nurture_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str) -> ClaudeResponse:
    return ClaudeResponse(
        content=content, tokens_in=100, tokens_out=300,
        model="claude-sonnet-4-5-20250929",
    )


@patch("vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence.call_claude")
def test_continue_route(mock_claude):
    """Low score, few touches → continue."""
    mock_claude.return_value = _mock_response(json.dumps({
        "content": "Educational email about AI adoption",
        "channel": "email",
        "updated_score": 35,
    }))

    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "n-1",
        "lead_score": 30,
        "touches_completed": 0,
        "lead_data": {"name": "Test Lead"},
    })

    assert result["route"] == "continue"
    assert result["touches_completed"] == 1
    assert result["current_stage"] == "educational"
    assert len(result["touch_history"]) == 1


@patch("vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence.call_claude")
def test_escalate_high_score(mock_claude):
    """Score >= 80 → escalate to sales."""
    mock_claude.return_value = _mock_response(json.dumps({
        "content": "Product demo invitation",
        "channel": "email",
        "updated_score": 85,
    }))

    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "n-2",
        "lead_score": 75,
        "touches_completed": 3,
        "lead_data": {},
    })

    assert result["route"] == "escalate"
    assert "ready for sales" in result["escalation_reason"]


@patch("vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence.call_claude")
def test_complete_max_touches(mock_claude):
    """Max touches reached → complete."""
    mock_claude.return_value = _mock_response(json.dumps({
        "content": "Final follow-up",
        "channel": "email",
    }))

    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "n-3",
        "lead_score": 40,
        "touches_completed": 9,
        "max_touches": 10,
        "lead_data": {},
    })

    assert result["route"] == "complete"
    assert result["touches_completed"] == 10


@patch("vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence.call_claude")
def test_stage_progression(mock_claude):
    """Different scores map to different stages."""
    mock_claude.return_value = _mock_response(json.dumps({
        "content": "Awareness content",
        "channel": "email",
    }))

    # Score 65 → product_aware
    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "n-4",
        "lead_score": 65,
        "touches_completed": 2,
        "lead_data": {},
    })
    assert result["current_stage"] == "product_aware"


@patch("vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence.call_claude")
def test_touch_history_tracking(mock_claude):
    """Touch history accumulates across invocations."""
    mock_claude.return_value = _mock_response(json.dumps({
        "content": "Follow-up email",
        "channel": "linkedin",
    }))

    existing_history = [
        {"touch_number": 1, "stage": "educational", "channel": "email", "content_preview": "First touch"},
    ]

    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "n-5",
        "lead_score": 45,
        "touches_completed": 1,
        "touch_history": existing_history,
        "lead_data": {},
    })

    assert len(result["touch_history"]) == 2
    assert result["touch_history"][1]["touch_number"] == 2
    assert result["touch_history"][1]["channel"] == "linkedin"
