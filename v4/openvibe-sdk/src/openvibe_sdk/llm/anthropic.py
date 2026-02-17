"""Anthropic LLM provider — wraps the anthropic SDK."""

from __future__ import annotations

from anthropic import Anthropic

from openvibe_sdk.llm import LLMResponse, ToolCall, resolve_model


class AnthropicProvider:
    """LLMProvider implementation using Anthropic's Claude API."""

    def __init__(self, api_key: str | None = None):
        self._client = Anthropic(api_key=api_key)

    def call(
        self,
        *,
        system: str,
        messages: list[dict],
        model: str = "haiku",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        resolved = resolve_model(model)
        kwargs: dict = dict(
            model=resolved,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        response = self._client.messages.create(**kwargs)

        content = ""
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, input=block.input)
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=resolved,
            stop_reason=response.stop_reason,
            raw_content=response.content,
        )
