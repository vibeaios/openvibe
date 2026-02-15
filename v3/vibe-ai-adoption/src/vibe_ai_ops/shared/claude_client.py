from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic


# Pricing per 1M tokens (as of 2026-02)
MODEL_PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
}


@dataclass
class ClaudeResponse:
    content: str
    tokens_in: int
    tokens_out: int
    model: str = "claude-sonnet-4-5-20250929"

    @property
    def cost_usd(self) -> float:
        pricing = MODEL_PRICING.get(self.model, {"input": 3.0, "output": 15.0})
        return (
            self.tokens_in * pricing["input"] / 1_000_000
            + self.tokens_out * pricing["output"] / 1_000_000
        )


class ClaudeClient:
    def __init__(self, api_key: str | None = None):
        self._client = Anthropic(api_key=api_key)

    def send(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ClaudeResponse:
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return ClaudeResponse(
            content=response.content[0].text,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=model,
        )
