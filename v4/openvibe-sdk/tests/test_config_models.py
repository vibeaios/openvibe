import tempfile
from pathlib import Path

from openvibe_sdk.models import (
    NodeConfig, NodeType, OperatorConfig, TriggerConfig, TriggerType, WorkflowConfig,
)
from openvibe_sdk.config import load_operator_configs, load_prompt


def test_trigger_config():
    t = TriggerConfig(id="t1", type=TriggerType.CRON, schedule="0 9 * * 1-5", workflow="research")
    assert t.id == "t1"
    assert t.type == TriggerType.CRON
    assert t.workflow == "research"


def test_node_config_defaults():
    n = NodeConfig(id="n1")
    assert n.type == NodeType.LOGIC
    assert n.model is None


def test_workflow_config():
    wf = WorkflowConfig(id="research", nodes=[NodeConfig(id="n1", type=NodeType.LLM, model="sonnet"), NodeConfig(id="n2")])
    assert len(wf.nodes) == 2
    assert wf.checkpointed is True


def test_operator_config():
    op = OperatorConfig(
        id="company_intel", name="Company Intel",
        triggers=[TriggerConfig(id="t1", type=TriggerType.ON_DEMAND, workflow="research")],
        workflows=[WorkflowConfig(id="research", nodes=[NodeConfig(id="n1", type=NodeType.LLM)])],
    )
    assert op.id == "company_intel"
    assert len(op.triggers) == 1
    assert len(op.workflows) == 1
    assert op.enabled is True


def test_load_operator_configs_from_yaml():
    yaml_content = """
operators:
  - id: test_op
    name: Test Operator
    triggers:
      - id: t1
        type: on_demand
        workflow: wf1
    workflows:
      - id: wf1
        nodes:
          - id: n1
            type: llm
  - id: disabled_op
    name: Disabled Op
    enabled: false
    triggers: []
    workflows: []
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "operators.yaml"
        path.write_text(yaml_content)
        all_configs = load_operator_configs(str(path), enabled_only=False)
        assert len(all_configs) == 2
        enabled = load_operator_configs(str(path), enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].id == "test_op"


def test_load_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "prompt.md"
        path.write_text("You are a test agent.")
        content = load_prompt(str(path))
        assert content == "You are a test agent."
