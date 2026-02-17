# Operator SDK Design

> Status: Design approved, pending implementation
> Date: 2026-02-17
> Approach: C — Thin LangGraph Extension

## Goal

Extract reusable infrastructure from vibe-ai-adoption into a standalone SDK package (`openvibe-sdk`), adding `@llm_node` and `@agent_node` decorators to eliminate per-node boilerplate.

## Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Location | `v4/openvibe-sdk/` (same repo) | Easy to co-develop with vibe-ai-adoption |
| Package name | `openvibe-sdk` | Clear it's the SDK, not the product |
| V1 scope | Extract + decorators | Smallest useful thing |
| Approach | C — Thin LangGraph Extension | Don't fight LangGraph, extend it |
| Agentic | Pi-style simple agent loop | No elaborate state machines |

## Architecture

Two-layer control model:

```
Workflow layer (deterministic DAG — human controls)
┌──────────┐     ┌─────────┐     ┌────────┐     ┌────────┐
│ research │ ──→ │ analyze │ ──→ │ decide │ ──→ │ report │
└──────────┘     └─────────┘     └────────┘     └────────┘
     │
     ▼
Node layer (agent loop — LLM controls)
┌──────────────────────────────────┐
│  LLM: "I need to search first…"  │
│  → tool: web_search("Acme Corp") │
│  → LLM: "Now check financials…"  │
│  → tool: read_url(annual_report)  │
│  → LLM: "Done, here's my output" │
│  → return research_result         │
└──────────────────────────────────┘
```

**Outer layer:** LangGraph StateGraph — fixed nodes and edges, human-designed.
**Inner layer:** Optional agent loop within a node — LLM uses tools, loops until done.

Key insight: not agent-loop vs workflow-graph, but workflow-graph **with** agentic nodes where needed.

---

## Section 1: Package Structure

```
v4/openvibe-sdk/
├── pyproject.toml
├── src/openvibe_sdk/
│   ├── __init__.py                # Public API: Operator, llm_node, agent_node, OperatorRuntime
│   ├── operator.py                # Operator base class + @llm_node + @agent_node decorators
│   ├── runtime.py                 # OperatorRuntime (from base.py)
│   ├── models.py                  # OperatorConfig, WorkflowConfig, NodeConfig
│   ├── config.py                  # YAML loader
│   ├── llm/
│   │   ├── __init__.py            # LLMProvider protocol
│   │   └── anthropic.py           # ClaudeClient
│   └── observability/
│       ├── __init__.py
│       ├── logger.py
│       └── tracing.py
└── tests/
```

**What moves from vibe-ai-adoption:**
- `operators/base.py` → split into `operator.py` + `runtime.py`
- `shared/models.py` (OperatorConfig parts) → `models.py`
- `shared/config.py` → `config.py`
- `shared/claude_client.py` → `llm/anthropic.py`
- `shared/logger.py` → `observability/logger.py`
- `shared/tracing.py` → `observability/tracing.py`

**What stays in vibe-ai-adoption:**
- 22 workflows, 5 state schemas, prompts, Temporal wiring
- HubSpot/Slack clients (Vibe-specific integrations)
- vibe-ai-adoption depends on openvibe-sdk via `pip install -e ../openvibe-sdk`

---

## Section 2: `@llm_node` — Single LLM Call

Transforms 20+ lines of repeated boilerplate into 3 lines.

**Before:**
```python
def _score_lead(state):
    try:
        prompt = load_prompt("config/prompts/sales/s1_lead_qualification.md")
    except FileNotFoundError:
        prompt = "You are a lead qualification specialist."
    response = call_claude(
        system_prompt=prompt,
        user_message=f"Score this lead: {json.dumps(state['enriched_data'])}",
        model="claude-sonnet-4-5-20250929",
        temperature=0.3,
    )
    try:
        score = json.loads(response.content)
        state["score"] = score
    except (json.JSONDecodeError, TypeError):
        state["score"] = {"fit_score": 0, "intent_score": 0}
    return state
```

**After:**
```python
@llm_node(model="sonnet", temperature=0.3, output_key="score")
def score_lead(self, state):
    """You are a lead qualification specialist."""
    return f"Score this lead: {json.dumps(state['enriched_data'])}"
```

**Decorator handles:**
1. System prompt: docstring → `prompt_file` param → fallback
2. Claude call via `self.llm`
3. JSON auto-parse (if response is JSON)
4. `state[output_key] = result`
5. Error handling: parse fails → raw string, no crash
6. Tracing: input/output/tokens/latency

**Not in V1:** Pydantic schema validation, retry/fallback, streaming.

---

## Section 3: Operator Base Class + Runtime

**Operator base class:**
```python
from openvibe_sdk import Operator, llm_node

class CompanyIntel(Operator):
    """Senior research analyst for prospect intelligence."""

    operator_id = "company_intel"

    @llm_node(model="sonnet", output_key="research")
    def research(self, state):
        """You are a senior research analyst..."""
        return f"Research the company: {state['company_name']}"

    @llm_node(model="sonnet", output_key="analysis")
    def analyze(self, state):
        """You are a strategic analyst..."""
        return f"Analyze this research: {state['research']}"
```

**Operator provides:**
- `self.llm` — LLMProvider instance (default Anthropic)
- `self.config` — OperatorConfig from operators.yaml
- `self.logger` — structured logger with operator context

**OperatorRuntime:**
```python
from openvibe_sdk import OperatorRuntime

runtime = OperatorRuntime.from_yaml("config/operators.yaml")
result = runtime.activate("company_intel", "research", {"company_name": "Acme"})
```

Same as current OperatorRuntime, extracted from base.py into its own module.

**Not in V1:** Operator auto-discovery, workflow graph builder, HTTP serve.

---

## Section 4: `@agent_node` — Pi-Style Agent Loop

### Tools = just functions

```python
def web_search(query: str) -> str:
    """Search the web for information."""
    return search_api(query)

def read_url(url: str) -> str:
    """Read content from a URL."""
    return fetch(url)
```

No `@tool` decorator. Function name + type hints + docstring → SDK auto-converts to Anthropic tool schema.

### Agent loop = just a while loop

```python
@agent_node(tools=[web_search, read_url], output_key="research")
def research(self, state):
    """You are a research analyst."""
    return f"Research {state['company_name']}"
```

Internal implementation:

```python
def run_agent_node(llm, system, user_msg, tools):
    messages = [{"role": "user", "content": user_msg}]
    while True:
        response = llm.call(system=system, messages=messages, tools=tools)
        if not response.tool_calls:
            return response.text
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call)
            messages.append(tool_call)
            messages.append(result)
```

No max_steps by default. No state machine. Trust the model, loop until done.

### Only difference from `@llm_node`

`@llm_node` = call LLM once, get result.
`@agent_node` = call LLM, if it wants tools → execute → feed back → repeat until text output.

Same LLM client, same tracing, just a while loop + tool execution.

### Optional safety valve

```python
# Default: trust the model
@agent_node(tools=[web_search], output_key="research")

# If you need a limit:
@agent_node(tools=[web_search], output_key="research", max_steps=20)
```

---

## Section 5: Public API

```python
from openvibe_sdk import Operator, llm_node, agent_node, OperatorRuntime
```

Four exports. That's it.

| Export | What | One line |
|---|---|---|
| `Operator` | Base class | Inherit for `self.llm` + `self.config` |
| `llm_node` | Decorator | Single LLM call, auto parse + state update |
| `agent_node` | Decorator | LLM + tools loop until done |
| `OperatorRuntime` | Runtime | Load YAML config, dispatch activations |

### Dependencies

```toml
[project]
name = "openvibe-sdk"
dependencies = [
    "anthropic",
    "langgraph",
    "pydantic",
    "pyyaml",
]
```

Four dependencies. No FastAPI, no NATS, no APScheduler.

---

## Differentiation

vs Pi / OpenClaw (agent-loop-first):
- We add **workflow structure** on top of agentic execution
- Bounded autonomy: agent acts within a node, not across the whole system
- Predictable workflow + flexible nodes

vs LangGraph raw:
- `@llm_node` eliminates JSON parse / error handling / tracing boilerplate
- `@agent_node` adds Pi-style tool loop as a node type
- Operator pattern groups related workflows under identity + config

vs CrewAI / LangChain:
- No "crew" / "chain" abstractions — just Python functions with decorators
- LangGraph is the graph engine, we don't replace it

---

## Migration Path

1. **Create `v4/openvibe-sdk/`** with extracted code
2. **vibe-ai-adoption** adds `openvibe-sdk` as editable dependency
3. **New workflows** use `@llm_node` / `@agent_node`
4. **Existing 22 workflows** migrate gradually (not all at once)
5. **V2:** HTTP serve, pluggable providers (OpenAI/Ollama), human-in-the-loop

---

*Design approved: 2026-02-17*
