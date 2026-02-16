"""Tests for operators/base.py — call_claude() and OperatorRuntime."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import yaml

from vibe_ai_ops.operators.base import OperatorRuntime, call_claude
from vibe_ai_ops.shared.claude_client import ClaudeResponse


@patch("vibe_ai_ops.operators.base._client", None)
@patch("vibe_ai_ops.operators.base.ClaudeClient")
def test_call_claude_initializes_client(mock_cls):
    mock_instance = MagicMock()
    mock_instance.send.return_value = ClaudeResponse(
        content="Hello", tokens_in=10, tokens_out=20, model="claude-haiku-4-5-20251001"
    )
    mock_cls.return_value = mock_instance

    result = call_claude("system", "user")
    assert result.content == "Hello"
    assert result.tokens_in == 10
    mock_cls.assert_called_once()
    mock_instance.send.assert_called_once_with(
        "system", "user", "claude-haiku-4-5-20251001", 4096, 0.7
    )


@patch("vibe_ai_ops.operators.base._client", None)
@patch("vibe_ai_ops.operators.base.ClaudeClient")
def test_call_claude_custom_model(mock_cls):
    mock_instance = MagicMock()
    mock_instance.send.return_value = ClaudeResponse(
        content="Deep analysis", tokens_in=100, tokens_out=500,
        model="claude-sonnet-4-5-20250929",
    )
    mock_cls.return_value = mock_instance

    result = call_claude("system", "user", model="claude-sonnet-4-5-20250929", max_tokens=8192)
    assert result.content == "Deep analysis"
    mock_instance.send.assert_called_once_with(
        "system", "user", "claude-sonnet-4-5-20250929", 8192, 0.7
    )


def _write_operator_yaml(tmpdir: str) -> str:
    config = {
        "operators": [
            {
                "id": "test_op",
                "name": "Test Operator",
                "triggers": [
                    {"id": "t1", "type": "on_demand", "workflow": "wf1"},
                ],
                "workflows": [
                    {
                        "id": "wf1",
                        "nodes": [{"id": "n1", "type": "logic"}],
                    },
                ],
            },
            {
                "id": "disabled_op",
                "name": "Disabled",
                "enabled": False,
                "triggers": [
                    {"id": "t1", "type": "on_demand", "workflow": "wf1"},
                ],
                "workflows": [
                    {"id": "wf1", "nodes": [{"id": "n1"}]},
                ],
            },
        ]
    }
    path = os.path.join(tmpdir, "operators.yaml")
    with open(path, "w") as f:
        yaml.dump(config, f)
    return path


def test_runtime_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load(enabled_only=True)

        assert len(runtime.operators) == 1
        assert "test_op" in runtime.operators
        assert "disabled_op" not in runtime.operators


def test_runtime_list_operators():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load(enabled_only=False)

        ops = runtime.list_operators()
        assert len(ops) == 2


def test_runtime_get_operator():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load()

        op = runtime.get_operator("test_op")
        assert op is not None
        assert op.name == "Test Operator"
        assert runtime.get_operator("nonexistent") is None


def test_runtime_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load(enabled_only=False)

        s = runtime.summary()
        assert s["operators"] == 2
        assert s["workflows"] == 2
        assert s["triggers"] == 2
        assert s["nodes"] == 2
        assert s["logic_nodes"] == 2
        assert s["llm_nodes"] == 0


def test_runtime_register_and_activate():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load()

        # Register a mock graph factory
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {"result": "done"}
        runtime.register_workflow("test_op", "wf1", lambda: mock_graph)

        result = runtime.activate("test_op", "t1", {"input": "data"})
        assert result == {"result": "done"}
        mock_graph.invoke.assert_called_once_with({"input": "data"})


def test_runtime_activate_unknown_operator():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load()

        import pytest
        with pytest.raises(ValueError, match="Unknown operator"):
            runtime.activate("nonexistent", "t1", {})


def test_runtime_activate_unknown_trigger():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_operator_yaml(tmpdir)
        runtime = OperatorRuntime(config_path=path)
        runtime.load()

        import pytest
        with pytest.raises(ValueError, match="Unknown trigger"):
            runtime.activate("test_op", "bad_trigger", {})
