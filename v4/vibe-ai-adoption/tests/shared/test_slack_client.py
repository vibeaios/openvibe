from vibe_ai_ops.shared.slack_client import SlackOutput, format_agent_output
from vibe_ai_ops.shared.models import AgentOutput


def test_format_agent_output():
    output = AgentOutput(
        agent_id="m3",
        content="# Blog Post: AI in Fintech\n\nContent here...",
        destination="slack:#marketing-agents",
        tokens_in=500,
        tokens_out=2000,
        cost_usd=0.03,
        duration_seconds=4.5,
        metadata={"segment": "enterprise-fintech"},
    )
    formatted = format_agent_output(output, agent_name="Content Generation")
    assert "Content Generation" in formatted
    assert "m3" in formatted
    assert "$0.03" in formatted
    assert "enterprise-fintech" in formatted


def test_slack_output_send(mocker):
    mock_webclient = mocker.patch("vibe_ai_ops.shared.slack_client.WebClient")
    mock_instance = mock_webclient.return_value

    client = SlackOutput(token="xoxb-test")
    output = AgentOutput(
        agent_id="m3",
        content="Test output",
        destination="slack:#marketing-agents",
    )
    client.send(output, agent_name="Content Generation")

    mock_instance.chat_postMessage.assert_called_once()
    call_kwargs = mock_instance.chat_postMessage.call_args[1]
    assert call_kwargs["channel"] == "#marketing-agents"
