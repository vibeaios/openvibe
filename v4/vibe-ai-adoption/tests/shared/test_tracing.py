import os
from unittest.mock import patch

from vibe_ai_ops.shared.tracing import init_tracing, get_tracer


@patch.dict(os.environ, {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_API_KEY": "ls__test",
    "LANGCHAIN_PROJECT": "vibe-ai-ops-test",
})
def test_init_tracing_returns_config():
    config = init_tracing()
    assert config["enabled"] is True
    assert config["project"] == "vibe-ai-ops-test"


@patch.dict(os.environ, {}, clear=True)
def test_init_tracing_disabled_without_env():
    config = init_tracing()
    assert config["enabled"] is False


def test_get_tracer_returns_callable():
    tracer = get_tracer("test-agent")
    assert callable(tracer)
