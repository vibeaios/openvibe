"""Tests for Customer Success operator — all 6 workflows."""

import json
from unittest.mock import patch

from vibe_ai_ops.operators.customer_success.workflows.onboarding import (
    create_onboarding_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.success_advisory import (
    create_success_advisory_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.health_monitoring import (
    create_health_monitoring_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.expansion_scan import (
    create_expansion_scan_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.customer_voice import (
    create_customer_voice_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.urgent_review import (
    create_urgent_review_graph,
)
from vibe_ai_ops.shared.claude_client import ClaudeResponse


def _mock_response(content: str, model: str = "claude-haiku-4-5-20251001") -> ClaudeResponse:
    return ClaudeResponse(content=content, tokens_in=100, tokens_out=300, model=model)


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.customer_success.workflows.onboarding.call_claude")
def test_onboarding_flow(mock_claude):
    """Full onboarding: creates plan, sets milestones, sends welcome."""
    mock_claude.return_value = _mock_response(
        "30-day onboarding plan: Week 1 setup, Week 2 core features, "
        "Week 3 advanced workflows, Week 4 review."
    )

    graph = create_onboarding_graph()
    result = graph.invoke({"customer_id": "cust-1", "customer_name": "Acme Corp"})

    assert result["welcome_sent"] is True
    assert result["onboarding_plan"] != ""
    assert len(result["milestones"]) == 4
    assert result["milestones"][0]["status"] == "pending"
    mock_claude.assert_called_once()


@patch("vibe_ai_ops.operators.customer_success.workflows.onboarding.call_claude")
def test_onboarding_milestones_structure(mock_claude):
    """Milestones have week, milestone, and status fields."""
    mock_claude.return_value = _mock_response("Onboarding plan content.")

    graph = create_onboarding_graph()
    result = graph.invoke({"customer_id": "cust-2", "customer_name": "Beta Inc"})

    for ms in result["milestones"]:
        assert "week" in ms
        assert "milestone" in ms
        assert "status" in ms


# ---------------------------------------------------------------------------
# Success Advisory
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.customer_success.workflows.success_advisory.call_claude")
def test_success_advisory_flow(mock_claude):
    """Full advisory: reviews accounts, identifies actions, generates playbooks."""
    mock_claude.side_effect = [
        _mock_response("Priority actions: renew contract, schedule QBR."),
        _mock_response("Playbook: Step 1 - Schedule call. Step 2 - Review metrics."),
    ]

    graph = create_success_advisory_graph()
    result = graph.invoke({
        "customer_id": "cust-3",
        "customer_name": "Gamma LLC",
        "accounts": [{"id": "cust-3", "name": "Gamma LLC", "health": "good"}],
    })

    assert result["actions"] != ""
    assert result["playbooks"] != ""
    assert mock_claude.call_count == 2


# ---------------------------------------------------------------------------
# Health Monitoring
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.customer_success.workflows.health_monitoring.call_claude")
def test_health_monitoring_healthy(mock_claude):
    """Healthy customer produces no risks."""
    mock_claude.return_value = _mock_response(
        "Overall health: healthy. Usage is strong, NPS is 9/10."
    )

    graph = create_health_monitoring_graph()
    result = graph.invoke({"customer_id": "cust-4", "customer_name": "Delta Co"})

    assert result["health_score"] != ""
    assert result["risks"] == []


@patch("vibe_ai_ops.operators.customer_success.workflows.health_monitoring.call_claude")
def test_health_monitoring_at_risk(mock_claude):
    """At-risk customer produces a warning risk flag."""
    mock_claude.return_value = _mock_response(
        "Overall health: at-risk. Usage declining, support tickets rising."
    )

    graph = create_health_monitoring_graph()
    result = graph.invoke({"customer_id": "cust-5", "customer_name": "Epsilon Inc"})

    assert len(result["risks"]) == 1
    assert result["risks"][0]["level"] == "warning"


@patch("vibe_ai_ops.operators.customer_success.workflows.health_monitoring.call_claude")
def test_health_monitoring_critical(mock_claude):
    """Critical customer produces a critical-level risk flag."""
    mock_claude.return_value = _mock_response(
        "Overall health: critical. Multiple outages, 0 logins in 30 days."
    )

    graph = create_health_monitoring_graph()
    result = graph.invoke({"customer_id": "cust-5b", "customer_name": "Sigma Corp"})

    assert len(result["risks"]) == 1
    assert result["risks"][0]["level"] == "critical"


# ---------------------------------------------------------------------------
# Expansion Scan
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.customer_success.workflows.expansion_scan.call_claude")
def test_expansion_scan_flow(mock_claude):
    """Full expansion: analyzes usage, identifies opportunities, drafts proposals."""
    mock_claude.side_effect = [
        _mock_response("Opportunity: upsell to enterprise tier, add 20 seats."),
        _mock_response("Proposal: Upgrade to Enterprise for $X/mo. Next step: schedule demo."),
    ]

    graph = create_expansion_scan_graph()
    result = graph.invoke({
        "customer_id": "cust-6",
        "customer_name": "Zeta Corp",
        "usage_data": {"current_plan": "standard", "seat_utilization": "95%"},
    })

    assert result["opportunities"] != ""
    assert result["proposals"] != ""
    assert mock_claude.call_count == 2


# ---------------------------------------------------------------------------
# Customer Voice
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.customer_success.workflows.customer_voice.call_claude")
def test_customer_voice_flow(mock_claude):
    """Full voice: collects feedback, analyzes themes, generates report."""
    mock_claude.side_effect = [
        _mock_response("Themes: 1) Onboarding friction, 2) Feature requests, 3) Positive support."),
        _mock_response("VoC Report: Key finding — onboarding needs improvement. Recommendation: simplify setup."),
    ]

    graph = create_customer_voice_graph()
    result = graph.invoke({
        "customer_id": "cust-7",
        "customer_name": "Eta Ltd",
        "feedback": [
            {"source": "nps", "score": 7, "comment": "Setup was confusing"},
            {"source": "support", "ticket": "T-100", "comment": "Great support team"},
        ],
    })

    assert result["themes"] != ""
    assert result["voice_report"] != ""
    assert mock_claude.call_count == 2


# ---------------------------------------------------------------------------
# Urgent Review
# ---------------------------------------------------------------------------


@patch("vibe_ai_ops.operators.customer_success.workflows.urgent_review.call_claude")
def test_urgent_review_flow(mock_claude):
    """Full urgent review: assesses, recommends, alerts."""
    mock_claude.side_effect = [
        _mock_response(
            "Severity: critical. Customer threatening to churn due to outage.",
            model="claude-sonnet-4-5-20250929",
        ),
        _mock_response(
            "Action: 1) Call customer in next hour. 2) Offer service credit. 3) Daily check-ins.",
            model="claude-sonnet-4-5-20250929",
        ),
    ]

    graph = create_urgent_review_graph()
    result = graph.invoke({
        "customer_id": "cust-8",
        "customer_name": "Theta Inc",
        "deal_id": "deal-999",
        "reason": "Customer reported 4-hour outage, threatening to cancel",
    })

    assert result["alert_sent"] is True
    assert result["situation"] != ""
    assert result["recommendation"] != ""
    assert mock_claude.call_count == 2


@patch("vibe_ai_ops.operators.customer_success.workflows.urgent_review.call_claude")
def test_urgent_review_uses_sonnet(mock_claude):
    """Urgent review uses sonnet model for higher quality assessment."""
    mock_claude.side_effect = [
        _mock_response("Severity: high.", model="claude-sonnet-4-5-20250929"),
        _mock_response("Action plan.", model="claude-sonnet-4-5-20250929"),
    ]

    graph = create_urgent_review_graph()
    result = graph.invoke({
        "customer_id": "cust-9",
        "customer_name": "Iota Inc",
        "reason": "Contract renewal at risk",
    })

    # Verify both LLM calls used sonnet (check call args)
    for call in mock_claude.call_args_list:
        assert call.kwargs.get("model") == "claude-sonnet-4-5-20250929"
