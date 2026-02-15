import os
from unittest.mock import patch

from vibe_ai_ops.crews.sales.s1_lead_qualification import (
    create_lead_qual_crew,
    LeadScore,
)
from vibe_ai_ops.shared.models import AgentConfig


def _make_config():
    return AgentConfig(
        id="s1", name="Lead Qualification", engine="sales",
        tier="deep_dive", architecture="temporal_langgraph_crewai",
        trigger={"type": "webhook", "event_source": "hubspot:new_lead"},
        output_channel="slack:#sales-agents",
        prompt_file="sales/s1_lead_qualification.md",
        temperature=0.3,
    )


def test_lead_score_composite():
    score = LeadScore(fit_score=80, intent_score=70, urgency_score=60,
                      reasoning="test", route="sales")
    expected = 0.4 * 80 + 0.35 * 70 + 0.25 * 60
    assert score.composite == expected


def test_lead_score_routing_logic():
    high = LeadScore(fit_score=90, intent_score=85, urgency_score=80,
                     reasoning="great", route="sales")
    assert high.composite >= 80

    mid = LeadScore(fit_score=60, intent_score=55, urgency_score=50,
                    reasoning="okay", route="nurture")
    assert 50 <= mid.composite < 80

    low = LeadScore(fit_score=30, intent_score=20, urgency_score=10,
                    reasoning="poor", route="education")
    assert low.composite < 50


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_lead_qual_crew():
    config = _make_config()
    crew = create_lead_qual_crew(config, system_prompt="You are a lead qualifier.")
    assert crew is not None
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
