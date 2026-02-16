"""Tests for Market Intelligence operator — all 4 workflows."""

from unittest.mock import patch

from vibe_ai_ops.operators.market_intel.workflows.funnel_monitor import (
    create_funnel_monitor_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.deal_risk_forecast import (
    create_deal_risk_forecast_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.conversation_analysis import (
    create_conversation_analysis_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.nl_query import (
    create_nl_query_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str) -> ClaudeResponse:
    return ClaudeResponse(
        content=content, tokens_in=50, tokens_out=100,
        model="claude-haiku-4-5-20251001",
    )


# ---------------------------------------------------------------------------
# Funnel Monitor
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.market_intel.workflows.funnel_monitor.call_claude")
def test_funnel_monitor_flow(mock_claude):
    """Full flow: pull_metrics → detect_anomalies → brief."""
    mock_claude.side_effect = [
        _mock_response("No anomalies detected. Conversion rates are within normal range."),
        _mock_response("Brief: Funnel healthy. All stages performing within expected bands."),
    ]

    graph = create_funnel_monitor_graph()
    result = graph.invoke({"funnel_metrics": {"leads": 100, "mqls": 30, "sqls": 10, "deals": 3}})

    assert "anomalies" in result
    assert "funnel_brief" in result
    assert mock_claude.call_count == 2
    # Logic node should have computed conversion rates
    assert "lead_to_mql_rate" in result["funnel_metrics"]


@patch("vibe_ai_ops.operators.market_intel.workflows.funnel_monitor.call_claude")
def test_funnel_monitor_empty_metrics(mock_claude):
    """Empty metrics should still flow through without errors."""
    mock_claude.side_effect = [
        _mock_response("No data to analyze."),
        _mock_response("Brief: Insufficient data for funnel assessment."),
    ]

    graph = create_funnel_monitor_graph()
    result = graph.invoke({"funnel_metrics": {}})

    assert "anomalies" in result
    assert "funnel_brief" in result
    assert mock_claude.call_count == 2


# ---------------------------------------------------------------------------
# Deal Risk Forecast
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.market_intel.workflows.deal_risk_forecast.call_claude")
def test_deal_risk_forecast_flow(mock_claude):
    """Full flow: pull_deals → model_risk → forecast → report."""
    mock_claude.side_effect = [
        _mock_response("Deal 1: high risk due to stagnation. Deal 2: low risk."),
        _mock_response("Expected revenue: $150K. Best case: $220K. Worst: $80K."),
        _mock_response("Pipeline report: $150K expected. 1 deal at risk of slipping."),
    ]

    deals = [
        {"name": "Acme Corp", "amount": 100000, "stage": "proposal", "days_in_stage": 45},
        {"name": "Globex", "amount": 50000, "stage": "closing", "days_in_stage": 5},
    ]
    graph = create_deal_risk_forecast_graph()
    result = graph.invoke({"deals": deals})

    assert "risk_model" in result
    assert "forecast" in result
    assert "forecast_report" in result
    assert mock_claude.call_count == 3
    # Logic node should have flagged stale deal
    assert result["deals"][0]["is_stale"] is True
    assert result["deals"][1]["is_stale"] is False


@patch("vibe_ai_ops.operators.market_intel.workflows.deal_risk_forecast.call_claude")
def test_deal_risk_forecast_empty_pipeline(mock_claude):
    """Empty pipeline should flow through gracefully."""
    mock_claude.side_effect = [
        _mock_response("No active deals to assess."),
        _mock_response("Forecast: $0 pipeline. No revenue expected."),
        _mock_response("Report: Pipeline is empty. Immediate action needed on lead gen."),
    ]

    graph = create_deal_risk_forecast_graph()
    result = graph.invoke({"deals": []})

    assert "forecast_report" in result
    assert mock_claude.call_count == 3


# ---------------------------------------------------------------------------
# Conversation Analysis
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.market_intel.workflows.conversation_analysis.call_claude")
def test_conversation_analysis_flow(mock_claude):
    """Full flow: pull_transcripts → extract_patterns → summarize."""
    mock_claude.side_effect = [
        _mock_response("Themes: pricing concerns (3/5 calls), competitor X mentioned (2/5)."),
        _mock_response("Summary: Pricing is the top objection. Competitor X gaining traction."),
    ]

    transcripts = [
        {"text": "Customer asked about pricing tiers and competitor X."},
        {"text": "Discussed implementation timeline and budget constraints."},
    ]
    graph = create_conversation_analysis_graph()
    result = graph.invoke({"transcripts": transcripts})

    assert "patterns" in result
    assert "conversation_summary" in result
    assert mock_claude.call_count == 2
    # Logic node should have assigned IDs and word counts
    assert result["transcripts"][0]["id"] == "transcript-1"
    assert "word_count" in result["transcripts"][0]


@patch("vibe_ai_ops.operators.market_intel.workflows.conversation_analysis.call_claude")
def test_conversation_analysis_single_transcript(mock_claude):
    """Single transcript analysis."""
    mock_claude.side_effect = [
        _mock_response("Single call: positive sentiment, strong buying signal."),
        _mock_response("Summary: One call analyzed — buyer is ready to move forward."),
    ]

    graph = create_conversation_analysis_graph()
    result = graph.invoke({"transcripts": [{"text": "Ready to sign, send the contract."}]})

    assert "conversation_summary" in result
    assert mock_claude.call_count == 2


# ---------------------------------------------------------------------------
# NL Query
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.market_intel.workflows.nl_query.call_claude")
def test_nl_query_flow(mock_claude):
    """Full flow: parse_question → query_data → reason → respond."""
    mock_claude.side_effect = [
        _mock_response("Intent: pipeline total, filter: current quarter, type: number"),
        _mock_response("The pipeline total is derived from the sum of all active deals."),
        _mock_response("Your current pipeline total is $500K across 12 active deals."),
    ]

    graph = create_nl_query_graph()
    result = graph.invoke({
        "question": "What's our pipeline total this quarter?",
        "query_results": {"pipeline_total": 500000, "deal_count": 12},
    })

    assert "parsed_intent" in result
    assert "reasoning" in result
    assert "answer" in result
    assert mock_claude.call_count == 3


@patch("vibe_ai_ops.operators.market_intel.workflows.nl_query.call_claude")
def test_nl_query_no_data(mock_claude):
    """NL query with no pre-loaded data uses stub results."""
    mock_claude.side_effect = [
        _mock_response("Intent: win rate, filter: last month, type: number"),
        _mock_response("Cannot determine exact win rate without live data."),
        _mock_response("I don't have live data connected yet to answer that precisely."),
    ]

    graph = create_nl_query_graph()
    result = graph.invoke({"question": "What was our win rate last month?"})

    assert "answer" in result
    # query_data logic node should have created stub results
    assert result["query_results"]["source"] == "simulated"
    assert mock_claude.call_count == 3
