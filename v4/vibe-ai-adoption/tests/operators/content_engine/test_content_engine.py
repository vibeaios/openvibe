"""Tests for Content Engine operator — all 6 workflows."""

import json
from unittest.mock import patch

from vibe_ai_ops.operators.content_engine.workflows.segment_research import (
    create_segment_research_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.message_testing import (
    create_message_testing_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.content_generation import (
    create_content_generation_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.repurposing import (
    create_repurposing_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.distribution import (
    create_distribution_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.journey_optimization import (
    create_journey_optimization_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str) -> ClaudeResponse:
    return ClaudeResponse(
        content=content, tokens_in=100, tokens_out=200,
        model="claude-haiku-4-5-20251001",
    )


# ---------------------------------------------------------------------------
# Segment Research
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.content_engine.workflows.segment_research.call_claude")
def test_segment_research_flow(mock_claude):
    """Full graph: gather_data → analyze_segments → report."""
    mock_claude.side_effect = [
        _mock_response("Enterprise segment has strong pain points in automation."),
        _mock_response("Report:\n- Enterprise: high priority\n- SMB: secondary"),
    ]

    graph = create_segment_research_graph()
    result = graph.invoke({"segment_data": [{"name": "enterprise", "size": 500}]})

    assert "segment_analysis" in result
    assert "segment_report" in result
    assert result["segment_data"][0]["name"] == "enterprise"
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.content_engine.workflows.segment_research.call_claude")
def test_segment_research_normalizes_data(mock_claude):
    """gather_data normalizes segments with default fields."""
    mock_claude.side_effect = [
        _mock_response("Analysis complete."),
        _mock_response("Report complete."),
    ]

    graph = create_segment_research_graph()
    result = graph.invoke({"segment_data": [{"name": "startup"}]})

    seg = result["segment_data"][0]
    assert seg["name"] == "startup"
    assert seg["size"] == 0
    assert seg["characteristics"] == []


# ---------------------------------------------------------------------------
# Message Testing
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.content_engine.workflows.message_testing.call_claude")
def test_message_testing_flow(mock_claude):
    """Full graph: generate_variants → evaluate → recommend."""
    variants = [
        {"variant": "A", "headline": "Ship faster", "body": "...", "cta": "Try now", "tone": "urgent"},
        {"variant": "B", "headline": "Build better", "body": "...", "cta": "Learn more", "tone": "calm"},
    ]
    mock_claude.side_effect = [
        _mock_response(json.dumps(variants)),
        _mock_response("Variant A: 8/10 - strong CTA. Variant B: 6/10 - weaker urgency."),
    ]

    graph = create_message_testing_graph()
    result = graph.invoke({"topic": "AI workspace"})

    assert len(result["message_variants"]) == 2
    assert "evaluation" in result
    assert "Recommended variant: A" in result["recommendation"]
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.content_engine.workflows.message_testing.call_claude")
def test_message_testing_json_fallback(mock_claude):
    """When variant generation returns invalid JSON, falls back gracefully."""
    mock_claude.side_effect = [
        _mock_response("Here are some great messages for you!"),  # invalid JSON
        _mock_response("Evaluation: the single variant looks ok."),
    ]

    graph = create_message_testing_graph()
    result = graph.invoke({"topic": "product launch"})

    assert len(result["message_variants"]) == 1
    assert result["message_variants"][0]["variant"] == "A"


# ---------------------------------------------------------------------------
# Content Generation
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.content_engine.workflows.content_generation.call_claude")
def test_content_generation_flow(mock_claude):
    """Full graph: research → draft → polish."""
    mock_claude.side_effect = [
        _mock_response("Key facts: AI adoption grew 40% in 2025."),
        _mock_response("# Why AI Matters\n\nDraft content here..."),
        _mock_response("# Why AI Matters Now\n\nPolished content here..."),
    ]

    graph = create_content_generation_graph()
    result = graph.invoke({"topic": "AI adoption trends"})

    assert "research" in result
    assert "draft" in result
    assert "polished_content" in result
    assert "AI" in result["polished_content"]
    assert mock_claude.call_count == 3


# ---------------------------------------------------------------------------
# Repurposing
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.content_engine.workflows.repurposing.call_claude")
def test_repurposing_flow(mock_claude):
    """Full graph: analyze_content → adapt_formats → finalize."""
    adapted = {"social_post": "AI is changing everything.", "email_snippet": "Dear reader, AI..."}
    mock_claude.return_value = _mock_response(json.dumps(adapted))

    graph = create_repurposing_graph()
    result = graph.invoke({
        "source_content": "A long article about AI that has many words " * 20,
        "content_formats": ["social_post", "email_snippet"],
    })

    assert "adapted_content" in result
    assert "social_post" in result["adapted_content"]
    assert "email_snippet" in result["adapted_content"]
    assert mock_claude.call_count == 1


@patch("vibe_ai_ops.operators.content_engine.workflows.repurposing.call_claude")
def test_repurposing_auto_detects_formats(mock_claude):
    """When no formats specified, analyze_content auto-selects based on length."""
    mock_claude.return_value = _mock_response(json.dumps({
        "social_post": "Short post.", "email_snippet": "Email version.",
        "blog_summary": "Summary.", "newsletter_section": "Newsletter.",
    }))

    # >500 words triggers all 4 formats
    long_content = "word " * 600
    graph = create_repurposing_graph()
    result = graph.invoke({"source_content": long_content})

    assert "newsletter_section" in result["content_formats"]
    assert "blog_summary" in result["content_formats"]


# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.content_engine.workflows.distribution.call_claude")
def test_distribution_flow(mock_claude):
    """Full graph: select_channels → schedule_posts → report."""
    mock_claude.return_value = _mock_response(
        "Distribution Plan:\n- LinkedIn: 9am\n- Email: 1pm\nExpected reach: 5000"
    )

    graph = create_distribution_graph()
    result = graph.invoke({
        "adapted_content": {"social_post": "Post content", "email_snippet": "Email content"},
    })

    assert len(result["channels"]) > 0
    assert len(result["schedule"]) > 0
    assert "distribution_report" in result
    assert mock_claude.call_count == 1


# ---------------------------------------------------------------------------
# Journey Optimization
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.content_engine.workflows.journey_optimization.call_claude")
def test_journey_optimization_flow(mock_claude):
    """Full graph: collect_metrics → analyze_funnel → recommend."""
    mock_claude.side_effect = [
        _mock_response("Major drop-off at consideration stage (70% to 20%)."),
        _mock_response("Recommendations:\n1. Add case studies at consideration\n2. Simplify pricing page"),
    ]

    graph = create_journey_optimization_graph()
    result = graph.invoke({
        "funnel_metrics": {
            "stages": {
                "awareness": {"visitors": 1000, "conversions": 700},
                "consideration": {"visitors": 700, "conversions": 140},
                "decision": {"visitors": 140, "conversions": 70},
                "purchase": {"visitors": 70, "conversions": 35},
            },
        },
    })

    assert "funnel_analysis" in result
    assert "optimization_recommendations" in result
    # Check conversion rates were calculated
    assert result["funnel_metrics"]["stages"]["awareness"]["conversion_rate"] == 70.0
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.content_engine.workflows.journey_optimization.call_claude")
def test_journey_optimization_empty_metrics(mock_claude):
    """Works with empty funnel metrics — defaults are created."""
    mock_claude.side_effect = [
        _mock_response("No data to analyze yet."),
        _mock_response("Recommendation: Set up tracking first."),
    ]

    graph = create_journey_optimization_graph()
    result = graph.invoke({})

    stages = result["funnel_metrics"]["stages"]
    assert "awareness" in stages
    assert stages["awareness"]["conversion_rate"] == 0.0
