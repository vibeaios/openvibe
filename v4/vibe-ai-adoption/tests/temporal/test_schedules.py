from vibe_ai_ops.temporal.schedules import parse_cron_to_temporal, build_schedule_specs
from vibe_ai_ops.shared.models import AgentConfig


def test_parse_cron_to_temporal():
    spec = parse_cron_to_temporal("0 9 * * 1")
    assert spec["minute"] == [0]
    assert spec["hour"] == [9]
    assert spec["day_of_week"] == [1]


def test_build_schedule_specs_filters_cron_agents():
    configs = [
        AgentConfig(
            id="m1", name="Segment Research", engine="marketing",
            tier="validation", architecture="temporal_crewai",
            trigger={"type": "cron", "schedule": "0 9 * * 1"},
            output_channel="slack:#test", prompt_file="test.md",
        ),
        AgentConfig(
            id="s1", name="Lead Qual", engine="sales",
            tier="deep_dive", architecture="temporal_langgraph_crewai",
            trigger={"type": "webhook", "event_source": "hubspot:new_lead"},
            output_channel="slack:#test", prompt_file="test.md",
        ),
    ]
    specs = build_schedule_specs(configs)
    assert len(specs) == 1
    assert specs[0]["agent_id"] == "m1"
