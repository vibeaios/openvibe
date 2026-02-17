import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from openvibe_sdk.runtime import OperatorRuntime


YAML_CONTENT = """
operators:
  - id: op1
    name: Operator One
    triggers:
      - id: t1
        type: on_demand
        workflow: wf1
      - id: t2
        type: cron
        schedule: "0 9 * * *"
        workflow: wf2
    workflows:
      - id: wf1
        nodes:
          - id: n1
            type: llm
          - id: n2
            type: logic
      - id: wf2
        nodes:
          - id: n3
            type: llm
  - id: op2
    name: Operator Two
    enabled: false
    triggers: []
    workflows: []
"""


def _write_yaml(tmpdir):
    path = Path(tmpdir) / "operators.yaml"
    path.write_text(YAML_CONTENT)
    return str(path)


def test_from_yaml():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path, enabled_only=True)
        assert "op1" in runtime.operators
        assert "op2" not in runtime.operators


def test_from_yaml_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path, enabled_only=False)
        assert "op1" in runtime.operators
        assert "op2" in runtime.operators


def test_list_operators():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path)
        ops = runtime.list_operators()
        assert len(ops) == 1
        assert ops[0].id == "op1"


def test_get_operator():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path)
        op = runtime.get_operator("op1")
        assert op is not None
        assert op.name == "Operator One"
        assert runtime.get_operator("nonexistent") is None


def test_register_and_get_workflow():
    runtime = OperatorRuntime()
    factory = MagicMock()
    runtime.register_workflow("op1", "wf1", factory)
    assert runtime.get_workflow_factory("op1", "wf1") is factory
    assert runtime.get_workflow_factory("op1", "missing") is None


def test_activate():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path)
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"output": "result"}
        factory = MagicMock(return_value=mock_graph)
        runtime.register_workflow("op1", "wf1", factory)
        result = runtime.activate("op1", "t1", {"input": "test"})
        assert result == {"output": "result"}
        factory.assert_called_once()
        mock_graph.invoke.assert_called_once_with({"input": "test"})


def test_activate_unknown_operator():
    runtime = OperatorRuntime()
    with pytest.raises(ValueError, match="Unknown operator"):
        runtime.activate("missing", "t1", {})


def test_activate_unknown_trigger():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path)
        with pytest.raises(ValueError, match="Unknown trigger"):
            runtime.activate("op1", "missing_trigger", {})


def test_activate_no_factory():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path)
        with pytest.raises(ValueError, match="No graph factory"):
            runtime.activate("op1", "t1", {})


def test_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_yaml(tmpdir)
        runtime = OperatorRuntime.from_yaml(path)
        s = runtime.summary()
        assert s["operators"] == 1
        assert s["workflows"] == 2
        assert s["triggers"] == 2
        assert s["nodes"] == 3
        assert s["llm_nodes"] == 2
        assert s["logic_nodes"] == 1
