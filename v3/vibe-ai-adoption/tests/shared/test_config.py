import os
import tempfile

import yaml

from vibe_ai_ops.shared.config import load_agent_configs, load_prompt


def test_load_agent_configs():
    config_data = {
        "agents": [
            {
                "id": "m3",
                "name": "Content Generation",
                "engine": "marketing",
                "tier": "deep_dive",
                "architecture": "temporal_langgraph_crewai",
                "trigger": {"type": "cron", "schedule": "0 9 * * *"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m3_content_generation.md",
                "crew_config": {
                    "agents": ["researcher", "writer", "editor"],
                    "process": "sequential",
                },
            },
            {
                "id": "m1",
                "name": "Segment Research",
                "engine": "marketing",
                "tier": "validation",
                "architecture": "temporal_crewai",
                "trigger": {"type": "cron", "schedule": "0 9 * * 1"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m1_segment_research.md",
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_agent_configs(f.name)

    assert len(configs) == 2
    assert configs[0].id == "m3"
    assert configs[0].architecture.value == "temporal_langgraph_crewai"
    os.unlink(f.name)


def test_load_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = os.path.join(tmpdir, "test_prompt.md")
        with open(prompt_path, "w") as f:
            f.write("You are a marketing agent.\n\nGenerate content for {{segment}}.")
        content = load_prompt(prompt_path)
        assert "marketing agent" in content


def test_load_configs_filters_disabled():
    config_data = {
        "agents": [
            {
                "id": "m3", "name": "Content Gen", "engine": "marketing",
                "tier": "deep_dive", "architecture": "temporal_langgraph_crewai",
                "trigger": {"type": "cron", "schedule": "0 9 * * *"},
                "output_channel": "slack:#test", "prompt_file": "test.md",
                "enabled": True,
            },
            {
                "id": "m4", "name": "Content Repurposing", "engine": "marketing",
                "tier": "validation", "architecture": "temporal_crewai",
                "trigger": {"type": "event", "event_source": "m3:complete"},
                "output_channel": "slack:#test", "prompt_file": "test.md",
                "enabled": False,
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_agent_configs(f.name, enabled_only=True)

    assert len(configs) == 1
    assert configs[0].id == "m3"
    os.unlink(f.name)
