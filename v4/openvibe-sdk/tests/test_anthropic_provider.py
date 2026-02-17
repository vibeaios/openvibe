from unittest.mock import MagicMock

from openvibe_sdk.llm import LLMResponse, ToolCall
from openvibe_sdk.llm.anthropic import AnthropicProvider


def _mock_text_response(text="Hello", model="claude-haiku-4-5-20251001"):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.usage.input_tokens = 10
    response.usage.output_tokens = 20
    response.stop_reason = "end_turn"
    return response


def _mock_tool_response():
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "I'll search for that."
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "toolu_123"
    tool_block.name = "web_search"
    tool_block.input = {"query": "OpenVibe"}
    response = MagicMock()
    response.content = [text_block, tool_block]
    response.usage.input_tokens = 15
    response.usage.output_tokens = 30
    response.stop_reason = "tool_use"
    return response


def test_call_text_response(mocker):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_text_response("Test output")
    mocker.patch("openvibe_sdk.llm.anthropic.Anthropic", return_value=mock_client)
    provider = AnthropicProvider(api_key="test-key")
    result = provider.call(
        system="You are helpful.",
        messages=[{"role": "user", "content": "Hello"}],
        model="haiku",
    )
    assert isinstance(result, LLMResponse)
    assert result.content == "Test output"
    assert result.tool_calls == []
    assert result.tokens_in == 10
    assert result.tokens_out == 20
    assert result.stop_reason == "end_turn"
    assert result.model == "claude-haiku-4-5-20251001"


def test_call_resolves_model_alias(mocker):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_text_response()
    mocker.patch("openvibe_sdk.llm.anthropic.Anthropic", return_value=mock_client)
    provider = AnthropicProvider()
    provider.call(system="test", messages=[{"role": "user", "content": "hi"}], model="sonnet")
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"


def test_call_with_tools(mocker):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_tool_response()
    mocker.patch("openvibe_sdk.llm.anthropic.Anthropic", return_value=mock_client)
    tools = [{"name": "web_search", "description": "Search", "input_schema": {}}]
    provider = AnthropicProvider()
    result = provider.call(system="test", messages=[{"role": "user", "content": "search"}], tools=tools)
    assert result.content == "I'll search for that."
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "web_search"
    assert result.tool_calls[0].id == "toolu_123"
    assert result.tool_calls[0].input == {"query": "OpenVibe"}
    assert result.stop_reason == "tool_use"
    call_kwargs = mock_client.messages.create.call_args[1]
    assert "tools" in call_kwargs


def test_call_without_tools_omits_param(mocker):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_text_response()
    mocker.patch("openvibe_sdk.llm.anthropic.Anthropic", return_value=mock_client)
    provider = AnthropicProvider()
    provider.call(system="test", messages=[{"role": "user", "content": "hi"}])
    call_kwargs = mock_client.messages.create.call_args[1]
    assert "tools" not in call_kwargs
