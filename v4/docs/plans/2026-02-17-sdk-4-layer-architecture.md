# OpenVibe SDK — 4-Layer Architecture

> Status: Design approved
> Date: 2026-02-17
> Builds on: `2026-02-17-operator-sdk-design.md` (Operator layer), `proposed/COGNITIVE-ARCHITECTURE.md` (Role layer vision)

## Goal

Build `openvibe-sdk` as a 4-layer framework: Infrastructure protocols (Layer 0), Primitives (Layer 1), Operators (Layer 2), Roles (Layer 3). Each layer depends only on the layer below. Infrastructure is decoupled via protocols.

## Architecture

```
Layer 3: Role (WHO — identity, memory, goals)
  ├── Role class (role_id, soul, operators, memory)
  ├── RoleRuntime (lifecycle, activate, wire infrastructure)
  └── Protocols: MemoryProvider, ScheduleProvider

Layer 2: Operator (WHAT — workflows, nodes)
  ├── Operator class (operator_id, llm, config)
  └── OperatorRuntime (YAML config, workflow dispatch)

Layer 1: Primitives (HOW nodes work)
  ├── @llm_node — single LLM call, auto parse + state update
  ├── @agent_node — Pi-style tool loop until done
  ├── Tool schema converter (function → Anthropic tool schema)
  └── LLMProvider protocol + AnthropicProvider

Layer 0: Infrastructure (protocols in SDK, implementations outside)
  ├── ScheduleProvider ← TemporalScheduler (optional extra)
  ├── MemoryProvider   ← InMemoryStore (dev) / PostgresMemory (prod)
  └── LLMProvider      ← AnthropicProvider (included)
```

Key design principle: **each layer depends only on the layer below, via protocols.**

- Role doesn't know about Temporal or Postgres — it talks to ScheduleProvider and MemoryProvider
- Operator doesn't know about Role — it just has workflows and nodes
- Primitives don't know about Operator — they're just decorators that produce LangGraph-compatible functions
- Infrastructure is swappable — test with InMemoryStore, production with Postgres

---

## Section 1: Layer 0 — Infrastructure Protocols

SDK defines protocols. Implementations live outside (or as optional extras).

### LLMProvider

```python
class LLMProvider(Protocol):
    def call(
        self,
        *,
        system: str,
        messages: list[dict],
        model: str = "haiku",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: list[dict] | None = None,
    ) -> LLMResponse: ...
```

Included implementation: `AnthropicProvider` (wraps `anthropic` SDK).

### MemoryProvider

```python
class MemoryProvider(Protocol):
    def store(self, namespace: str, key: str, value: Any) -> None: ...
    def recall(self, namespace: str, query: str, limit: int = 10) -> list[MemoryEntry]: ...
    def delete(self, namespace: str, key: str) -> None: ...
```

Included implementation: `InMemoryStore` (dict-based, for dev/test).
External: `PostgresMemory`, `RedisMemory` (not in SDK).

### ScheduleProvider

```python
class ScheduleProvider(Protocol):
    def schedule(self, role_id: str, trigger: TriggerConfig) -> str: ...
    def cancel(self, schedule_id: str) -> None: ...
    def list_active(self, role_id: str) -> list[ScheduleInfo]: ...
```

No included implementation. Temporal adapter lives in `openvibe-sdk[temporal]` or in application code.

---

## Section 2: Layer 1 — Primitives

### @llm_node

Single LLM call. Docstring = system prompt. Return value = user message. Auto JSON parse. State update via `output_key`.

```python
@llm_node(model="sonnet", temperature=0.3, output_key="score")
def score_lead(self, state):
    """You are a lead qualification specialist."""
    return f"Score this lead: {json.dumps(state['enriched_data'])}"
```

See `2026-02-17-operator-sdk-design.md` Section 2 for full spec.

### @agent_node

Pi-style while loop. Tools = plain functions, auto-converted to Anthropic schema. Loops until LLM responds with text (no tool calls).

```python
@agent_node(tools=[web_search, read_url], output_key="research")
def research(self, state):
    """You are a research analyst."""
    return f"Research {state['company_name']}"
```

See `2026-02-17-operator-sdk-design.md` Section 4 for full spec.

### Tool Schema Converter

```python
def web_search(query: str) -> str:
    """Search the web for information."""
    return search_api(query)

# Auto-converts to Anthropic tool schema:
# {"name": "web_search", "description": "Search the web...", "input_schema": {...}}
```

No `@tool` decorator needed. Function name + type hints + docstring.

### LLM Types

```python
@dataclass
class ToolCall:
    id: str
    name: str
    input: dict

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall]
    tokens_in: int
    tokens_out: int
    model: str
    stop_reason: str  # "end_turn" | "tool_use"
    raw_content: Any  # original API response content blocks

MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001",
    "opus": "claude-opus-4-6",
}
```

---

## Section 3: Layer 2 — Operator

### Operator Base Class

```python
class Operator:
    operator_id: str = ""

    def __init__(self, llm=None, config=None):
        self.llm = llm
        self.config = config
```

Decorated methods (`@llm_node`, `@agent_node`) are bound methods that work as LangGraph node functions. Graph building is standard LangGraph:

```python
op = CompanyIntel(llm=provider)
graph = StateGraph(CompanyIntelState)
graph.add_node("research", op.research)
graph.add_node("analyze", op.analyze)
graph.set_entry_point("research")
graph.add_edge("research", "analyze")
graph.add_edge("analyze", END)
compiled = graph.compile()
```

### OperatorRuntime

```python
runtime = OperatorRuntime.from_yaml("config/operators.yaml")
runtime.register_workflow("company_intel", "research", create_research_graph)
result = runtime.activate("company_intel", "t1", {"company_name": "Acme"})
```

Loads YAML config, indexes by operator ID, resolves trigger → workflow → graph factory → invoke.

See `2026-02-17-operator-sdk-design.md` Sections 3 and 5 for full spec.

---

## Section 4: Layer 3 — Role

### What Role adds over Operator

| Concept | Operator | Role |
|---------|----------|------|
| Identity | operator_id + name | soul (personality, communication style) |
| Memory | stateless between runs | persistent recall/store across activations |
| Scope | single set of workflows | owns 1..N Operators |
| LLM context | bare system prompt | soul + recalled memories + original prompt |
| Scheduling | external (Temporal) | via ScheduleProvider protocol |

### Role Base Class

```python
class Role:
    """Identity layer — WHO the agent is."""

    role_id: str = ""
    soul: str = ""                          # path to SOUL config or inline text
    operators: list[type[Operator]] = []    # Operator classes this Role can use

    def __init__(
        self,
        llm: LLMProvider = None,
        memory: MemoryProvider = None,
        config: dict = None,
    ):
        self.llm = llm
        self.memory = memory
        self.config = config or {}
        self._operator_instances: dict[str, Operator] = {}

    def get_operator(self, operator_id: str) -> Operator:
        """Get or create an Operator instance, injecting self.llm."""
        if operator_id not in self._operator_instances:
            for op_class in self.operators:
                if op_class.operator_id == operator_id:
                    self._operator_instances[operator_id] = op_class(llm=self.llm)
                    break
            else:
                raise ValueError(f"Role '{self.role_id}' has no operator '{operator_id}'")
        return self._operator_instances[operator_id]

    def build_system_prompt(self, base_prompt: str, context: str = "") -> str:
        """Augment system prompt with soul + recalled memories."""
        soul_text = self._load_soul()
        memories = ""
        if self.memory and context:
            recalled = self.memory.recall(self.role_id, context)
            if recalled:
                memories = "\n## Relevant Memories\n" + "\n".join(
                    f"- {m.content}" for m in recalled
                )
        parts = [p for p in [soul_text, memories, base_prompt] if p]
        return "\n\n".join(parts)

    def _load_soul(self) -> str:
        if not self.soul:
            return ""
        if self.soul.endswith(".md") or self.soul.endswith(".yaml"):
            from openvibe_sdk.config import load_prompt
            return load_prompt(self.soul)
        return self.soul  # inline text
```

### How soul injection works

Every `@llm_node` and `@agent_node` on an Operator owned by a Role gets the augmented prompt:

```python
# Without Role (bare Operator):
system_prompt = method.__doc__  # "You are a lead qualification specialist."

# With Role (Operator owned by Role):
system_prompt = role.build_system_prompt(
    base_prompt=method.__doc__,
    context=state_summary,
)
# Result:
# """
# You are the CRO. You are data-driven, aggressive but measured...
#
# ## Relevant Memories
# - Webinar leads convert 2x vs cold inbound
# - Enterprise deals need VP sponsor
#
# You are a lead qualification specialist.
# """
```

Implementation: when Role creates Operator instances, it wraps the LLM provider to inject soul + memory:

```python
class _RoleAwareLLM:
    """LLM wrapper that injects Role identity and memory into every call."""

    def __init__(self, role: Role, inner: LLMProvider):
        self._role = role
        self._inner = inner

    def call(self, *, system: str, messages: list, **kwargs) -> LLMResponse:
        context = messages[0]["content"] if messages else ""
        augmented_system = self._role.build_system_prompt(system, context)
        return self._inner.call(system=augmented_system, messages=messages, **kwargs)
```

This way Operators don't need to know about Role — they just call `self.llm` as normal, and the Role-aware wrapper handles augmentation.

### RoleRuntime

```python
class RoleRuntime:
    """Manages Roles + connects infrastructure."""

    def __init__(
        self,
        roles: list[type[Role]],
        llm: LLMProvider,
        memory: MemoryProvider | None = None,
        scheduler: ScheduleProvider | None = None,
        config_path: str | None = None,
    ):
        self.llm = llm
        self.memory = memory
        self.scheduler = scheduler
        self._roles: dict[str, Role] = {}

        for role_class in roles:
            role = role_class(llm=llm, memory=memory)
            self._roles[role.role_id] = role

    def get_role(self, role_id: str) -> Role:
        role = self._roles.get(role_id)
        if not role:
            raise ValueError(f"Unknown role: {role_id}")
        return role

    def activate(
        self,
        role_id: str,
        operator_id: str,
        workflow_id: str,
        input_data: dict,
    ) -> dict:
        """Activate: Role → Operator → workflow → result."""
        role = self.get_role(role_id)
        operator = role.get_operator(operator_id)
        # workflow execution via OperatorRuntime or direct graph invoke
        ...

    def start(self):
        """Register all triggers with scheduler (if available)."""
        if not self.scheduler:
            raise RuntimeError("No scheduler configured. Use activate() for manual execution.")
        for role in self._roles.values():
            for trigger in self._get_triggers(role):
                self.scheduler.schedule(role.role_id, trigger)

    def list_roles(self) -> list[Role]:
        return list(self._roles.values())
```

### Full example

```python
from openvibe_sdk import Role, Operator, llm_node, agent_node, RoleRuntime
from openvibe_sdk.llm.anthropic import AnthropicProvider
from openvibe_sdk.memory import InMemoryStore

# Tools
def search_hubspot(query: str) -> str:
    """Search HubSpot CRM for contacts and deals."""
    return hubspot_client.search(query)

# Layer 2: Operators
class RevenueOps(Operator):
    operator_id = "revenue_ops"

    @llm_node(model="sonnet", output_key="score")
    def qualify_lead(self, state):
        """You are a lead qualification specialist."""
        return f"Score this lead: {state['lead_data']}"

    @agent_node(tools=[search_hubspot], output_key="enriched")
    def enrich_lead(self, state):
        """You enrich lead data with CRM information."""
        return f"Enrich: {state['lead_data']}"

class ContentEngine(Operator):
    operator_id = "content_engine"

    @agent_node(tools=[search_web], output_key="draft")
    def write_case_study(self, state):
        """You are a B2B case study writer."""
        return f"Write case study for: {state['customer']}"

# Layer 3: Role
class CRO(Role):
    role_id = "cro"
    soul = "config/souls/cro.md"
    operators = [RevenueOps, ContentEngine]

# Wire up
runtime = RoleRuntime(
    roles=[CRO],
    llm=AnthropicProvider(),
    memory=InMemoryStore(),
)

# Activate
result = runtime.activate("cro", "revenue_ops", "qualify_lead", {"lead_data": "..."})
```

---

## Section 5: Package Structure

```
v4/openvibe-sdk/
├── pyproject.toml
├── src/openvibe_sdk/
│   ├── __init__.py           # Public API
│   ├── operator.py           # Operator + @llm_node + @agent_node
│   ├── role.py               # Role + _RoleAwareLLM
│   ├── runtime.py            # OperatorRuntime + RoleRuntime
│   ├── models.py             # OperatorConfig, WorkflowConfig, NodeConfig
│   ├── config.py             # YAML loader
│   ├── tools.py              # function_to_schema converter
│   ├── llm/
│   │   ├── __init__.py       # LLMResponse, ToolCall, LLMProvider protocol, resolve_model
│   │   └── anthropic.py      # AnthropicProvider
│   └── memory/
│       ├── __init__.py       # MemoryProvider protocol, MemoryEntry
│       └── in_memory.py      # InMemoryStore
└── tests/
```

### Public API

```python
from openvibe_sdk import (
    # Layer 3
    Role,
    RoleRuntime,
    # Layer 2
    Operator,
    OperatorRuntime,
    # Layer 1
    llm_node,
    agent_node,
)
```

6 exports. Protocols and types importable from submodules.

### Dependencies

```toml
[project]
dependencies = [
    "anthropic>=0.40.0",
    "langgraph>=0.3.0",
    "pydantic>=2.6.0",
    "pyyaml>=6.0",
]
```

4 dependencies. No Temporal, no database, no NATS.

---

## Section 6: V1 → V4 Roadmap

### V1 (current scope)

Build the 4-layer framework with minimal implementations:

| Layer | What's built |
|-------|-------------|
| Layer 0 | LLMProvider protocol + AnthropicProvider, MemoryProvider protocol + InMemoryStore, ScheduleProvider protocol (no implementation) |
| Layer 1 | @llm_node, @agent_node, tool schema converter, LLM types |
| Layer 2 | Operator, OperatorRuntime |
| Layer 3 | Role (soul + operators + memory recall/store), RoleRuntime (activate, start) |

### V2: Memory Pyramid + Authority

Add structured memory (L1-L3) and authority config.

```
New SDK exports: MemoryPyramid, Episode, Insight, AuthorityConfig
New protocols: RawLogStore, EpisodicStore, SemanticStore

Role additions:
  - role.authority: autonomous / needs_approval / forbidden
  - role.can_act(action_type) -> "autonomous" | "needs_approval" | "forbidden"

Memory additions:
  - L1 raw log: auto-append every LLM call
  - L2 episodes: auto-create per workflow completion
  - L3 insights: periodic reflection (L2 → L3 distillation via LLM)

Decorator additions:
  - @llm_node / @agent_node auto-record episodes (L2) on completion

Temporal integration:
  - TemporalScheduler(ScheduleProvider) — registers cron triggers
  - Reflection cron: daily role.memory.reflect()

Distillation pipeline:
  L1 → L2: real-time (every workflow completion)
  L2 → L3: daily (Temporal cron → role.memory.reflect())
```

### V3: Decision Engine + Goals

Add autonomous decision-making and OKR-driven prioritization.

```
New SDK exports: DecisionEngine, GoalSystem, OKR, Decision

Decision Engine:
  - 4-step evaluation: Domain → Authority → Confidence → Impact
  - Confidence assessment: query L3 insights + L2 similar episodes
  - Impact assessment: identity.impact_rules (config-driven)
  - Action matrix: Confidence × Impact → ACT / PROPOSE / ESCALATE

Goal System:
  - OKR config (from human/CEO)
  - Goal decomposition (LLM-driven)
  - Daily prioritization (LLM: context + OKRs → top 3)
  - Progress tracking (episodes roll up to OKR metrics)

Role additions:
  - role.decision_engine.evaluate(event) -> Decision
  - role.goals.prioritize(context) -> list[Priority]
```

### V4: Cognitive Loop + Collaboration

Full autonomous agent lifecycle and multi-agent collaboration.

```
New SDK exports: CognitiveLoop, Space, BeliefStore, MemoryAccessControl

Cognitive Loop:
  perceive → decide → act → observe → reflect → learn
  - Full event-driven lifecycle
  - Periodic reflection (L2 → L3) and learning (L3 → L4)

Beliefs (L4):
  - High-confidence insights proposed for promotion
  - Human approval gate
  - Beliefs influence all future decisions

Collaboration Spaces:
  - Shared environments for agents + humans
  - Cross-agent communication
  - Domain-based message routing

Memory Access Control:
  - Domain × Classification matrix
  - Clearance profiles per Role
  - Cross-agent memory queries filtered by clearance

Cross-agent delegation:
  - CRO → CMO: "need case study" (not direct operator trigger)
  - CMO applies brand beliefs → delegates to Content Engine
  - Domain owner controls quality
```

### Dependency Chain

```
V1  Role, Operator, @llm_node, @agent_node, protocols
     │
V2  ├── MemoryPyramid (L1→L2→L3), AuthorityConfig
     ├── Auto episode recording (hooks into decorators)
     ├── TemporalScheduler (optional extra)
     │
V3  ├── DecisionEngine (needs L2+L3 from V2)
     ├── GoalSystem (needs episodes from V2)
     │
V4  ├── CognitiveLoop (needs DecisionEngine from V3)
     ├── Spaces (needs event bus)
     ├── Beliefs L4 (needs L3 insights from V2)
     └── MemoryAccessControl (needs all above)
```

Each version is independently usable and backward compatible.

---

## Differentiation

vs agent-loop frameworks (Pi, OpenClaw, CrewAI):
- We add **workflow structure** (LangGraph) on top of agentic execution
- Bounded autonomy: agent acts within a node, not across the whole system
- Role layer adds identity + memory that agent frameworks lack

vs workflow frameworks (raw LangGraph, Prefect):
- `@llm_node` / `@agent_node` eliminate boilerplate
- Role layer adds cognitive capabilities on top of execution

vs cognitive architectures (research projects):
- Production-ready: Python package, not a paper
- Incremental: V1 is useful without the full cognitive stack
- Decoupled: swap Temporal, swap memory backend, swap LLM provider

---

*Design approved: 2026-02-17*
