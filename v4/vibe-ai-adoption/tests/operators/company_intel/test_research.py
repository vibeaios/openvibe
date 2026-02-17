"""Tests for Company Intel research workflow — no CrewAI, uses call_claude()."""

import json
from unittest.mock import patch

from vibe_ai_ops.operators.company_intel.workflows.research import (
    create_company_intel_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str) -> ClaudeResponse:
    return ClaudeResponse(
        content=content, tokens_in=100, tokens_out=200, model="claude-haiku-4-5-20251001"
    )


@patch("vibe_ai_ops.operators.company_intel.workflows.research.call_claude")
def test_full_graph_high_prospect(mock_claude):
    """Full graph run: research → analyze → decide → report."""
    mock_claude.side_effect = [
        _mock_response("Anthropic is an AI safety company. Series C. ~500 employees."),
        _mock_response(json.dumps({
            "prospect_quality": "high",
            "reasoning": "Large AI company, strong fit",
            "pain_points": ["scaling", "coordination"],
            "approach_angle": "AI-powered automation",
        })),
    ]

    graph = create_company_intel_graph()
    result = graph.invoke({"company_name": "Anthropic"})

    assert result["prospect_quality"] == "high"
    assert result["completed"] is True
    assert "Anthropic" in result["report"]
    assert "HIGH" in result["report"]
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.company_intel.workflows.research.call_claude")
def test_low_prospect_detection(mock_claude):
    mock_claude.side_effect = [
        _mock_response("Small local bakery, 3 employees."),
        _mock_response(json.dumps({
            "prospect_quality": "low",
            "reasoning": "Too small for our product",
            "pain_points": [],
            "approach_angle": "N/A",
        })),
    ]

    graph = create_company_intel_graph()
    result = graph.invoke({"company_name": "Bob's Bakery"})
    assert result["prospect_quality"] == "low"


@patch("vibe_ai_ops.operators.company_intel.workflows.research.call_claude")
def test_fallback_on_invalid_json(mock_claude):
    """When analysis isn't valid JSON, decide node falls back to keyword matching."""
    mock_claude.side_effect = [
        _mock_response("Tech company, medium size."),
        _mock_response("This company has high potential for AI adoption."),
    ]

    graph = create_company_intel_graph()
    result = graph.invoke({"company_name": "TechCorp"})
    # Keyword fallback: "high" found in analysis
    assert result["prospect_quality"] == "high"


@patch("vibe_ai_ops.operators.company_intel.workflows.research.call_claude")
def test_fallback_defaults_to_medium(mock_claude):
    """When analysis has no quality keywords, defaults to medium."""
    mock_claude.side_effect = [
        _mock_response("Unknown company."),
        _mock_response("Unable to determine prospect quality."),
    ]

    graph = create_company_intel_graph()
    result = graph.invoke({"company_name": "Mystery Inc"})
    assert result["prospect_quality"] == "medium"


@patch("vibe_ai_ops.operators.company_intel.workflows.research.call_claude")
def test_report_format(mock_claude):
    mock_claude.side_effect = [
        _mock_response("Stripe processes payments."),
        _mock_response(json.dumps({
            "prospect_quality": "medium",
            "reasoning": "Good but competitive space",
            "pain_points": ["complexity"],
            "approach_angle": "Simplification",
        })),
    ]

    graph = create_company_intel_graph()
    result = graph.invoke({"company_name": "Stripe"})

    report = result["report"]
    assert "=== Company Intelligence Report ===" in report
    assert "Company: Stripe" in report
    assert "Prospect Quality: MEDIUM" in report
    assert "--- Research ---" in report
    assert "--- Analysis ---" in report
