"""Tests for Operator Pydantic models."""

import pytest
from pydantic import ValidationError

from vibe_ai_ops.shared.models import (
    NodeConfig,
    NodeType,
    OperatorConfig,
    OperatorTriggerConfig,
    TriggerType,
    WorkflowConfig,
)


def test_node_config_defaults():
    node = NodeConfig(id="route")
    assert node.type == NodeType.LOGIC
    assert node.model is None
    assert node.prompt_file is None


def test_node_config_llm():
    node = NodeConfig(
        id="score",
        type=NodeType.LLM,
        model="claude-sonnet-4-5-20250929",
        prompt_file="sales/s1_lead_qualification.md",
    )
    assert node.type == NodeType.LLM
    assert node.model == "claude-sonnet-4-5-20250929"


def test_workflow_config_defaults():
    wf = WorkflowConfig(
        id="lead_qualification",
        nodes=[NodeConfig(id="route")],
    )
    assert wf.checkpointed is True
    assert wf.durable is False
    assert wf.timeout_minutes == 5
    assert wf.max_duration_days is None


def test_workflow_config_durable():
    wf = WorkflowConfig(
        id="nurture_sequence",
        durable=True,
        max_duration_days=42,
        nodes=[NodeConfig(id="assess"), NodeConfig(id="generate")],
    )
    assert wf.durable is True
    assert wf.max_duration_days == 42
    assert len(wf.nodes) == 2


def test_operator_trigger_config():
    trigger = OperatorTriggerConfig(
        id="new_lead",
        type=TriggerType.WEBHOOK,
        source="hubspot:new_lead",
        workflow="lead_qualification",
    )
    assert trigger.type == TriggerType.WEBHOOK
    assert trigger.source == "hubspot:new_lead"
    assert trigger.workflow == "lead_qualification"


def test_operator_config_full():
    config = OperatorConfig(
        id="revenue_ops",
        name="Revenue Operations",
        owner="VP Sales",
        description="Full pipeline",
        output_channels=["slack:#sales-agents"],
        state_schema="vibe_ai_ops.operators.revenue_ops.state.RevenueOpsState",
        triggers=[
            OperatorTriggerConfig(
                id="new_lead",
                type=TriggerType.WEBHOOK,
                source="hubspot:new_lead",
                workflow="lead_qualification",
            ),
            OperatorTriggerConfig(
                id="daily_intel",
                type=TriggerType.CRON,
                schedule="0 7 * * *",
                workflow="buyer_intelligence",
            ),
        ],
        workflows=[
            WorkflowConfig(
                id="lead_qualification",
                nodes=[
                    NodeConfig(id="enrich", type=NodeType.LLM, model="claude-haiku-4-5-20251001"),
                    NodeConfig(id="route"),
                ],
            ),
        ],
    )
    assert config.id == "revenue_ops"
    assert len(config.triggers) == 2
    assert len(config.workflows) == 1
    assert config.workflows[0].nodes[0].type == NodeType.LLM
    assert config.enabled is True


def test_operator_config_minimal():
    config = OperatorConfig(
        id="test_op",
        name="Test",
        triggers=[
            OperatorTriggerConfig(
                id="t1", type=TriggerType.ON_DEMAND, workflow="wf1"
            ),
        ],
        workflows=[
            WorkflowConfig(id="wf1", nodes=[NodeConfig(id="n1")]),
        ],
    )
    assert config.owner == ""
    assert config.output_channels == []
    assert config.state_schema == ""


def test_operator_trigger_requires_workflow():
    with pytest.raises(ValidationError):
        OperatorTriggerConfig(
            id="bad",
            type=TriggerType.CRON,
            schedule="0 * * * *",
            # missing workflow
        )


def test_node_type_enum_values():
    assert NodeType.LOGIC.value == "logic"
    assert NodeType.LLM.value == "llm"
