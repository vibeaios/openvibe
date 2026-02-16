import os
import tempfile

import yaml

from vibe_ai_ops.shared.config import load_agent_configs, load_operator_configs, load_prompt


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


# --- Operator config tests ---


def test_load_operator_configs():
    config_data = {
        "operators": [
            {
                "id": "company_intel",
                "name": "Company Intelligence",
                "triggers": [
                    {"id": "query", "type": "on_demand", "workflow": "research"},
                ],
                "workflows": [
                    {
                        "id": "research",
                        "nodes": [
                            {"id": "research", "type": "llm", "model": "claude-haiku-4-5-20251001"},
                            {"id": "decide", "type": "logic"},
                        ],
                    },
                ],
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_operator_configs(f.name)

    assert len(configs) == 1
    assert configs[0].id == "company_intel"
    assert len(configs[0].workflows[0].nodes) == 2
    assert configs[0].workflows[0].nodes[0].type.value == "llm"
    os.unlink(f.name)


def test_load_operator_configs_filters_disabled():
    config_data = {
        "operators": [
            {
                "id": "active",
                "name": "Active",
                "enabled": True,
                "triggers": [{"id": "t", "type": "on_demand", "workflow": "w"}],
                "workflows": [{"id": "w", "nodes": [{"id": "n"}]}],
            },
            {
                "id": "inactive",
                "name": "Inactive",
                "enabled": False,
                "triggers": [{"id": "t", "type": "on_demand", "workflow": "w"}],
                "workflows": [{"id": "w", "nodes": [{"id": "n"}]}],
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_operator_configs(f.name, enabled_only=True)

    assert len(configs) == 1
    assert configs[0].id == "active"
    os.unlink(f.name)


def test_load_real_operators_yaml():
    """Validate the real operators.yaml parses correctly."""
    configs = load_operator_configs("config/operators.yaml")
    assert len(configs) == 5

    ids = {c.id for c in configs}
    assert ids == {"company_intel", "revenue_ops", "content_engine", "customer_success", "market_intel"}

    # Revenue ops has 5 triggers and 5 workflows
    rev_ops = next(c for c in configs if c.id == "revenue_ops")
    assert len(rev_ops.triggers) == 5
    assert len(rev_ops.workflows) == 5
