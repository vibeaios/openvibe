"""Tests for main entry point — build_system()."""
import os
from unittest.mock import patch

from vibe_ai_ops.main import build_system, CREW_REGISTRY


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_build_system_loads_all_agents():
    system = build_system(config_path="config/agents.yaml")
    assert system["agent_count"] == 20
    assert len(system["configs"]) == 20


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_build_system_builds_schedule_specs():
    system = build_system(config_path="config/agents.yaml")
    # Only cron-triggered agents get schedules
    cron_agents = [c for c in system["configs"] if c.trigger.type.value == "cron"]
    assert len(system["schedules"]) == len(cron_agents)
    assert len(system["schedules"]) > 0


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"})
def test_build_system_creates_crews_for_registered_agents():
    system = build_system(config_path="config/agents.yaml")
    # All agents with crew registries should have crews built
    assert len(system["crews"]) > 0
    # Every registered agent ID should have a crew
    for agent_id in system["crews"]:
        assert agent_id in CREW_REGISTRY


def test_crew_registry_has_all_engines():
    # Registry should cover all 4 engines
    engines = set()
    for agent_id in CREW_REGISTRY:
        if agent_id.startswith("m"):
            engines.add("marketing")
        elif agent_id.startswith("s"):
            engines.add("sales")
        elif agent_id.startswith("c"):
            engines.add("cs")
        elif agent_id.startswith("r"):
            engines.add("intelligence")
    assert engines == {"marketing", "sales", "cs", "intelligence"}


def test_crew_registry_has_20_agents():
    assert len(CREW_REGISTRY) == 20
