from vibe_ai_ops.shared.models import (
    AgentConfig, AgentOutput, AgentRun, Tier, TriggerType,
    ArchitectureType,
)


def test_agent_config_from_dict():
    data = {
        "id": "m3",
        "name": "Content Generation",
        "engine": "marketing",
        "tier": "deep_dive",
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "output_channel": "slack:#marketing-agents",
        "prompt_file": "marketing/m3_content_generation.md",
        "enabled": True,
    }
    config = AgentConfig(**data)
    assert config.id == "m3"
    assert config.tier == Tier.DEEP_DIVE
    assert config.trigger.type == TriggerType.CRON


def test_agent_output():
    output = AgentOutput(
        agent_id="m3",
        content="Generated blog post about...",
        destination="slack:#marketing-agents",
        tokens_in=500,
        tokens_out=2000,
        cost_usd=0.03,
        duration_seconds=4.5,
        metadata={"segment": "enterprise-fintech", "format": "blog"},
    )
    assert output.agent_id == "m3"
    assert output.cost_usd == 0.03


def test_agent_run_tracks_success():
    run = AgentRun(
        agent_id="m3",
        status="success",
        input_summary="Generate blog for enterprise-fintech",
        output_summary="1200-word blog post on AI in fintech",
        tokens_in=500,
        tokens_out=2000,
        cost_usd=0.03,
        duration_seconds=4.5,
    )
    assert run.status == "success"
    assert run.agent_id == "m3"


def test_agent_run_tracks_failure():
    run = AgentRun(
        agent_id="m3",
        status="error",
        input_summary="Generate blog for enterprise-fintech",
        error="Rate limited by Claude API",
        tokens_in=0,
        tokens_out=0,
        cost_usd=0.0,
        duration_seconds=1.2,
    )
    assert run.status == "error"
    assert run.error == "Rate limited by Claude API"


def test_agent_config_with_architecture():
    data = {
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
    }
    config = AgentConfig(**data)
    assert config.architecture == ArchitectureType.TEMPORAL_LANGGRAPH_CREWAI
    assert config.crew_config is not None
    assert len(config.crew_config["agents"]) == 3


def test_validation_agent_uses_simple_architecture():
    data = {
        "id": "m1",
        "name": "Segment Research",
        "engine": "marketing",
        "tier": "validation",
        "architecture": "temporal_crewai",
        "trigger": {"type": "cron", "schedule": "0 9 * * 1"},
        "output_channel": "slack:#marketing-agents",
        "prompt_file": "marketing/m1_segment_research.md",
    }
    config = AgentConfig(**data)
    assert config.architecture == ArchitectureType.TEMPORAL_CREWAI
    assert config.crew_config is None
