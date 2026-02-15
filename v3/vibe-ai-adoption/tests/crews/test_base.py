import os
from unittest.mock import patch

from vibe_ai_ops.crews.base import create_crew_agent, create_validation_crew
from vibe_ai_ops.shared.models import AgentConfig


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_crew_agent():
    config = AgentConfig(
        id="m1", name="Segment Research", engine="marketing",
        tier="validation", architecture="temporal_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1_segment_research.md",
    )

    agent = create_crew_agent(
        config=config,
        role="Market Research Specialist",
        goal="Identify and analyze micro-segments for targeted marketing",
        backstory="You are Vibe's expert market researcher.",
    )

    assert agent.role == "Market Research Specialist"
    assert agent.goal == "Identify and analyze micro-segments for targeted marketing"


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_validation_crew():
    config = AgentConfig(
        id="m1", name="Segment Research", engine="marketing",
        tier="validation", architecture="temporal_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1_segment_research.md",
    )

    crew = create_validation_crew(
        config=config,
        role="Market Research Specialist",
        goal="Identify and analyze micro-segments",
        backstory="You are Vibe's expert market researcher.",
        task_description="Research the {segment} micro-segment.",
        expected_output="A detailed segment profile with firmographics, pain points, and messaging angles.",
    )

    assert crew is not None
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
