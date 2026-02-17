"""Role -- identity layer (WHO the agent is)."""

from __future__ import annotations

from typing import Any

from openvibe_sdk.llm import LLMProvider, LLMResponse
from openvibe_sdk.memory import MemoryProvider
from openvibe_sdk.operator import Operator


class _RoleAwareLLM:
    """LLM wrapper that injects Role identity and memory into every call."""

    def __init__(self, role: Role, inner: LLMProvider) -> None:
        self._role = role
        self._inner = inner

    def call(
        self, *, system: str, messages: list[dict], **kwargs: Any
    ) -> LLMResponse:
        context = ""
        if messages:
            first_content = messages[0].get("content", "")
            context = (
                first_content
                if isinstance(first_content, str)
                else str(first_content)
            )
        augmented_system = self._role.build_system_prompt(system, context)
        return self._inner.call(
            system=augmented_system, messages=messages, **kwargs
        )


class Role:
    """Identity layer -- WHO the agent is.

    Subclass and set role_id, soul, and operators.
    """

    role_id: str = ""
    soul: str = ""
    operators: list[type[Operator]] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "operators" not in cls.__dict__:
            cls.operators = []

    def __init__(
        self,
        llm: LLMProvider | None = None,
        memory: MemoryProvider | None = None,
        config: dict | None = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.config = config or {}
        self._operator_instances: dict[str, Operator] = {}

    def get_operator(self, operator_id: str) -> Operator:
        """Get or create an Operator instance with Role-aware LLM."""
        if operator_id not in self._operator_instances:
            for op_class in self.operators:
                if op_class.operator_id == operator_id:
                    wrapped_llm = (
                        _RoleAwareLLM(self, self.llm) if self.llm else None
                    )
                    self._operator_instances[operator_id] = op_class(
                        llm=wrapped_llm
                    )
                    break
            else:
                raise ValueError(
                    f"Role '{self.role_id}' has no operator '{operator_id}'"
                )
        return self._operator_instances[operator_id]

    def build_system_prompt(
        self, base_prompt: str, context: str = ""
    ) -> str:
        """Augment system prompt with soul + recalled memories.

        When context is provided, tries a relevance-filtered recall first.
        Falls back to all memories for this role if the filter returns nothing.
        """
        soul_text = self._load_soul()
        memories = ""
        if self.memory and context:
            recalled = self.memory.recall(self.role_id, context)
            if not recalled:
                # Fall back to all memories for this role
                recalled = self.memory.recall(self.role_id, "")
            if recalled:
                memories = "\n## Relevant Memories\n" + "\n".join(
                    f"- {m.content}" for m in recalled
                )
        parts = [p for p in [soul_text, memories, base_prompt] if p]
        return "\n\n".join(parts)

    def _load_soul(self) -> str:
        if not self.soul:
            return ""
        if self.soul.endswith((".md", ".yaml", ".txt")):
            from openvibe_sdk.config import load_prompt

            return load_prompt(self.soul)
        return self.soul
