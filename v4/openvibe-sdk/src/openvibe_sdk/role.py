"""Role -- identity layer (WHO the agent is)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from openvibe_sdk.llm import LLMProvider, LLMResponse
from openvibe_sdk.memory.access import ClearanceProfile
from openvibe_sdk.memory.agent_memory import AgentMemory
from openvibe_sdk.memory.assembler import MemoryAssembler
from openvibe_sdk.memory.filesystem import MemoryFilesystem
from openvibe_sdk.memory.types import Episode, Insight
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
        agent_memory: AgentMemory | None = None,
        config: dict | None = None,
    ) -> None:
        self.llm = llm
        self.agent_memory = agent_memory
        self.config = config or {}
        self._operator_instances: dict[str, Operator] = {}
        self._memory_fs: MemoryFilesystem | None = None

    def can_act(self, action: str) -> str:
        """Check authority for an action.

        Returns: 'autonomous' | 'needs_approval' | 'forbidden'.
        If no authority config, everything is autonomous.
        """
        if not self.authority:
            return "autonomous"
        return self.authority.can_act(action)

    def respond(self, message: str, context: str = "") -> LLMResponse:
        """Respond to a message with soul + memory context (V2 only)."""
        if not self.llm:
            raise ValueError(f"Role '{self.role_id}' has no LLM configured")

        parts: list[str] = []
        soul_text = self._load_soul()
        if soul_text:
            parts.append(soul_text)

        if self.agent_memory:
            insights = self.agent_memory.recall_insights(query=message, limit=5)
            if insights:
                lines = [f"- {i.content}" for i in insights]
                parts.append("## Knowledge\n" + "\n".join(lines))

        system = "\n\n".join(parts)
        response = self.llm.call(
            system=system,
            messages=[{"role": "user", "content": message}],
        )

        if self.agent_memory:
            self.agent_memory.record_episode(Episode(
                id=str(uuid.uuid4()),
                agent_id=self.role_id,
                operator_id="",
                node_name="respond",
                timestamp=datetime.now(timezone.utc),
                action="respond",
                input_summary=message[:200],
                output_summary=(response.content or "")[:200],
                outcome={},
                duration_ms=0,
                tokens_in=getattr(response, "tokens_in", 0),
                tokens_out=getattr(response, "tokens_out", 0),
            ))

        return response

    @property
    def memory_fs(self) -> MemoryFilesystem | None:
        """Virtual filesystem over this Role's memory. None if no agent_memory."""
        if not self.agent_memory:
            return None
        if self._memory_fs is None:
            self._memory_fs = MemoryFilesystem(
                role_id=self.role_id,
                agent_memory=self.agent_memory,
                soul=self._load_soul(),
            )
        return self._memory_fs

    def reflect(self) -> list[Insight]:
        """Compress recent episodes into insights via LLM."""
        if not self.agent_memory or not self.llm:
            return []
        return self.agent_memory.reflect(self.llm)

    def list_operators(self) -> list[str]:
        """List operator IDs this Role can use."""
        return [op.operator_id for op in self.operators]

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

    def build_system_prompt(self, base_prompt: str, context: str = "") -> str:
        """Augment system prompt with soul."""
        soul_text = self._load_soul()
        parts = [p for p in [soul_text, base_prompt] if p]
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
