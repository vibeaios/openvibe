"""Role -- identity layer (WHO the agent is)."""

from __future__ import annotations

from typing import Any

from openvibe_sdk.llm import LLMProvider, LLMResponse
from openvibe_sdk.memory import MemoryProvider
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.assembler import MemoryAssembler
from openvibe_sdk.models import AuthorityConfig
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
    V2 adds: authority, clearance, agent_memory.
    """

    role_id: str = ""
    soul: str = ""
    operators: list[type[Operator]] = []
    authority: AuthorityConfig | None = None
    clearance: ClearanceProfile | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "operators" not in cls.__dict__:
            cls.operators = []

    def __init__(
        self,
        llm: LLMProvider | None = None,
        memory: MemoryProvider | None = None,
        agent_memory: AgentMemory | None = None,
        config: dict | None = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.agent_memory = agent_memory
        self.config = config or {}
        self._operator_instances: dict[str, Operator] = {}

    def can_act(self, action: str) -> str:
        """Check authority for an action.

        Returns: 'autonomous' | 'needs_approval' | 'forbidden'.
        If no authority config, everything is autonomous.
        """
        if not self.authority:
            return "autonomous"
        return self.authority.can_act(action)

    def get_operator(self, operator_id: str) -> Operator:
        """Get or create an Operator instance with Role-aware LLM."""
        if operator_id not in self._operator_instances:
            for op_class in self.operators:
                if op_class.operator_id == operator_id:
                    wrapped_llm = (
                        _RoleAwareLLM(self, self.llm) if self.llm else None
                    )

                    # V2: build memory assembler when agent_memory exists
                    assembler = None
                    if self.agent_memory:
                        clearance = self.clearance or ClearanceProfile(
                            agent_id=self.role_id,
                            domain_clearance={},
                        )
                        assembler = MemoryAssembler(
                            self.agent_memory, clearance
                        )

                    op = op_class(
                        llm=wrapped_llm, memory_assembler=assembler
                    )

                    # V2: wire up episode recorder
                    if self.agent_memory:
                        op._episode_recorder = self.agent_memory.record_episode

                    self._operator_instances[operator_id] = op
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

        V2: When agent_memory is set, skips V1 memory injection (memory
        context is assembled by decorators via MemoryAssembler instead).
        """
        soul_text = self._load_soul()
        memories = ""
        # V1 memory injection -- only when no agent_memory
        if self.memory and not self.agent_memory and context:
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

            try:
                return load_prompt(self.soul)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Soul file not found: {self.soul} "
                    f"(role '{self.role_id}')"
                )
        return self.soul
