from __future__ import annotations

from slack_sdk import WebClient

from vibe_ai_ops.shared.models import AgentOutput


def format_agent_output(output: AgentOutput, agent_name: str) -> str:
    meta = ""
    if output.metadata:
        meta = " | ".join(f"{k}: {v}" for k, v in output.metadata.items())
        meta = f"\n_{meta}_"

    return (
        f"*[{agent_name}]* (`{output.agent_id}`) "
        f"| ${output.cost_usd:.2f} | {output.duration_seconds:.1f}s"
        f"{meta}\n\n{output.content}"
    )


class SlackOutput:
    def __init__(self, token: str | None = None):
        self._client = WebClient(token=token)

    def send(self, output: AgentOutput, agent_name: str = "Agent"):
        channel = output.destination.replace("slack:", "")
        text = format_agent_output(output, agent_name)
        self._client.chat_postMessage(channel=channel, text=text)

    def send_alert(self, channel: str, message: str):
        self._client.chat_postMessage(channel=channel, text=message)
