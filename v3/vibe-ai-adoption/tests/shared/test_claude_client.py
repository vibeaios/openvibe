import pytest
from unittest.mock import MagicMock

from vibe_ai_ops.shared.claude_client import ClaudeClient, ClaudeResponse


def test_claude_client_sends_message(mocker):
    mock_anthropic = mocker.patch("vibe_ai_ops.shared.claude_client.Anthropic")
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello from Claude")],
        usage=MagicMock(input_tokens=10, output_tokens=20),
    )

    client = ClaudeClient(api_key="test-key")
    response = client.send(
        system_prompt="You are a helpful assistant.",
        user_message="Say hello.",
        model="claude-sonnet-4-5-20250929",
    )

    assert isinstance(response, ClaudeResponse)
    assert response.content == "Hello from Claude"
    assert response.tokens_in == 10
    assert response.tokens_out == 20
    assert response.cost_usd > 0


def test_claude_client_calculates_cost():
    # Sonnet pricing: $3/M input, $15/M output
    response = ClaudeResponse(
        content="test",
        tokens_in=1000,
        tokens_out=1000,
        model="claude-sonnet-4-5-20250929",
    )
    assert response.cost_usd == pytest.approx(0.018, abs=0.001)


def test_claude_client_handles_error(mocker):
    mock_anthropic = mocker.patch("vibe_ai_ops.shared.claude_client.Anthropic")
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create.side_effect = Exception("API error")

    client = ClaudeClient(api_key="test-key")
    with pytest.raises(Exception, match="API error"):
        client.send(
            system_prompt="test",
            user_message="test",
        )
