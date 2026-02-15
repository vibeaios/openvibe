import os
from unittest.mock import patch

from vibe_ai_ops.crews.marketing.validation_agents import (
    create_m1_crew,
    create_m2_crew,
    create_m4_crew,
    create_m5_crew,
    create_m6_crew,
    MARKETING_CREW_REGISTRY,
)
from vibe_ai_ops.shared.models import AgentConfig


def _make_config(agent_id: str, name: str):
    return AgentConfig(
        id=agent_id, name=name, engine="marketing",
        tier="validation", architecture="temporal_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file=f"marketing/{agent_id}_{name.lower().replace(' ', '_')}.md",
    )


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_m1_crew():
    crew = create_m1_crew(_make_config("m1", "Segment Research"), "You research segments.")
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_m2_crew():
    crew = create_m2_crew(_make_config("m2", "Message Testing"), "You test messages.")
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_m4_crew():
    crew = create_m4_crew(_make_config("m4", "Content Repurposing"), "You repurpose content.")
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_m5_crew():
    crew = create_m5_crew(_make_config("m5", "Distribution"), "You distribute content.")
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_m6_crew():
    crew = create_m6_crew(_make_config("m6", "Journey Optimization"), "You optimize journeys.")
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1


def test_registry_has_all_validation_agents():
    assert set(MARKETING_CREW_REGISTRY.keys()) == {"m1", "m2", "m4", "m5", "m6"}
