"""Tests for Temporal activities — operator activity + dataclasses."""

import pytest
from unittest.mock import patch

from vibe_ai_ops.temporal.activities.agent_activity import (
    AgentActivityInput,
    AgentActivityOutput,
)
from vibe_ai_ops.temporal.activities.operator_activity import (
    OperatorActivityInput,
    OperatorActivityOutput,
)


@pytest.mark.asyncio
async def test_agent_activity_input_model():
    inp = AgentActivityInput(
        agent_id="m1",
        agent_config_path="config/agents.yaml",
        input_data={"segments": ["enterprise-fintech"]},
    )
    assert inp.agent_id == "m1"


def test_operator_activity_input_model():
    inp = OperatorActivityInput(
        operator_id="revenue_ops",
        trigger_id="new_lead",
        input_data={"contact_id": "c-123"},
    )
    assert inp.operator_id == "revenue_ops"
    assert inp.trigger_id == "new_lead"


def test_operator_activity_output_model():
    out = OperatorActivityOutput(
        operator_id="revenue_ops",
        trigger_id="new_lead",
        status="success",
        result={"route": "sales"},
        duration_seconds=2.5,
    )
    assert out.status == "success"
    assert out.result["route"] == "sales"
