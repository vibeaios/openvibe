import os
from unittest.mock import patch

from vibe_ai_ops.crews.marketing.m3_content_generation import create_content_gen_crew
from vibe_ai_ops.shared.models import AgentConfig


def _make_config():
    return AgentConfig(
        id="m3", name="Content Generation", engine="marketing",
        tier="deep_dive", architecture="temporal_langgraph_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * *"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m3_content_generation.md",
        max_tokens=8192,
    )


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_create_content_gen_crew():
    config = _make_config()
    crew = create_content_gen_crew(config, system_prompt="You generate content.")
    assert crew is not None
    assert len(crew.agents) == 3  # researcher, writer, editor
    assert len(crew.tasks) == 3  # research, write, edit


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_crew_agents_have_distinct_roles():
    config = _make_config()
    crew = create_content_gen_crew(config, system_prompt="Content gen.")
    roles = [a.role for a in crew.agents]
    assert "Content Researcher" in roles
    assert "Content Writer" in roles
    assert "Content Editor" in roles
