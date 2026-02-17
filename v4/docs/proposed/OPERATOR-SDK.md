# OpenVibe Operator SDK — Design Document

> **Date:** 2026-02-16
> **Status:** Proposed
> **Author:** Charles (APOS)
> **Depends on:** Operator pattern (implemented), Inter-Operator Comms (proposed)

---

## 1. Problem

The current operator implementation is Vibe-specific. 5 operators, 22 workflows, 80 nodes — all hardcoded in Python with manual LangGraph `StateGraph` wiring, manual `call_claude()` calls, and manual YAML config. Each workflow requires ~80 lines of boilerplate.

To make this a product, we need:

1. **A Python SDK** — declarative operator definition in ~30 lines per workflow
2. **An HTTP API** — any language/platform can create, trigger, and monitor operators
3. **A pluggable runtime** — swap LLM providers, message buses, schedulers without changing operator code

## 2. Goals

| Goal | Metric |
|------|--------|
| Developer experience | `pip install openvibe` → running API in 10 lines |
| Operator definition | 60% less boilerplate vs current hand-wired approach |
| LLM portability | Support Claude, GPT, local models via single interface |
| Deployment flexibility | Single process (dev) to multi-server (prod) with no code changes |
| Dogfood first | Rewrite all 5 Vibe operators using the SDK before public release |

## 3. Non-Goals

- **Frontend/UI** — SDK is backend-only; UI is a separate concern
- **Multi-language SDK** — Python first; other languages access via HTTP API
- **Managed cloud service** — Self-hosted only in V1
- **Custom graph topologies** — Linear + conditional branching only; no arbitrary DAGs in V1

---

## 4. Architecture

### 4.1 Three-Layer Stack

```
┌─────────────────────────────────────────────┐
│  Layer 3: HTTP/gRPC API                      │
│  Any language/platform can call              │
│  POST /operators/{id}/activate               │
│  GET  /operators/{id}/runs/{run_id}          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 2: Python SDK                         │
│  Declarative operator definitions            │
│  @operator, @workflow, @node decorators      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Layer 1: Runtime                            │
│  Execution engine                            │
│  LangGraph + MessageBus + Scheduler          │
└─────────────────────────────────────────────┘
```

### 4.2 Component Dependency

```
openvibe (package)
├── primitives    ← decorators (@operator, @workflow, @node, @llm_node)
├── compiler      ← decorators → LangGraph StateGraph
├── runtime       ← OperatorRuntime (load, register, activate)
├── server        ← FastAPI HTTP API (wraps runtime)
├── llm/          ← pluggable: Anthropic, OpenAI, Ollama
├── bus/          ← pluggable: NATS, Redis, in-memory
└── scheduler/    ← pluggable: Temporal, APScheduler, none
```

### 4.3 Hard Dependencies vs Pluggable

| Component | Status | Reason |
|-----------|--------|--------|
| LangGraph | Hard dependency | Core value — state machines, checkpointing, HITL |
| FastAPI | Hard dependency | HTTP API layer |
| Pydantic | Hard dependency | Config validation, API schemas |
| LLM provider | Pluggable | Not all users use Claude |
| Message bus | Pluggable | Dev uses in-memory, prod uses NATS |
| Scheduler | Pluggable | Small projects don't need Temporal |
| Database | Pluggable | Postgres (prod), SQLite (dev), memory (test) |

---

## 5. SDK Design (Layer 2)

### 5.1 Primitives

Seven decorators that compose to express any operator:

```python
@operator(id, name, description)        # Define an operator
@workflow(id, trigger)                   # Define a workflow (→ LangGraph graph)
@node                                    # Logic node (pure Python, no LLM)
@llm_node(model, max_tokens)            # LLM node (auto-calls configured provider)
@conditional(routes={...})              # Conditional routing between nodes
@human_in_the_loop(timeout)             # HITL pause point
@durable(max_days)                      # Mark as long-running (Temporal durable)
```

### 5.2 Minimal Example

```python
from openvibe import operator, workflow, llm_node, serve

@operator(id="hello", name="Hello World")
class Hello:
    greeting: str = ""

    @workflow(id="greet", trigger="on_demand")
    class Greet:
        @llm_node(model="haiku")
        def say_hello(self, state):
            return {
                "system": "You are friendly.",
                "user": "Say hello!",
                "output_key": "greeting",
            }

# Run
serve(Hello, port=8000)
```

```bash
pip install openvibe
python hello.py
# → Server running at http://localhost:8000

curl -X POST http://localhost:8000/v1/operators/hello/activate \
  -d '{"trigger": "greet", "input": {}}'
# → {"run_id": "run_abc", "status": "running"}
```

### 5.3 Complete Example: Lead Qualification

```python
from openvibe import operator, workflow, node, llm_node, conditional

@operator(
    id="revenue_ops",
    name="Revenue Operations",
    description="Sales pipeline automation",
)
class RevenueOps:
    # State fields — auto-compiled to LangGraph TypedDict
    contact_id: str = ""
    source: str = ""
    company_data: str = ""
    fit_score: int = 0
    intent_score: int = 0
    urgency_score: int = 0
    composite_score: float = 0.0
    route: str = ""
    crm_updated: bool = False

    @workflow(id="lead_qualification", trigger="webhook:hubspot_new_lead")
    class LeadQualification:

        @llm_node(model="haiku")
        def enrich(self, state):
            return {
                "system": "You are a data enrichment specialist...",
                "user": f"Enrich this contact: {state['contact_id']}",
                "output_key": "company_data",
            }

        @llm_node(model="sonnet", output_format="json")
        def score(self, state):
            return {
                "system": "You are a lead scoring expert...",
                "user": f"Score this lead:\n{state['company_data']}",
                "output_keys": {
                    "fit_score": int,
                    "intent_score": int,
                    "urgency_score": int,
                },
            }

        @conditional(routes={
            "sales": lambda s: s["composite_score"] >= 80,
            "nurture": lambda s: 50 <= s["composite_score"] < 80,
            "educate": lambda s: s["composite_score"] < 50,
        })
        def route(self, state):
            score = (
                state["fit_score"] * 0.4
                + state["intent_score"] * 0.35
                + state["urgency_score"] * 0.25
            )
            return {"composite_score": score, "route": "pending"}

        @node
        def update_crm(self, state):
            # Pure logic — call HubSpot, update CRM
            return {"crm_updated": True}
```

### 5.4 Durable Workflow Example

```python
from openvibe import operator, workflow, llm_node, node, durable, human_in_the_loop
from datetime import timedelta

@operator(id="revenue_ops", name="Revenue Operations")
class RevenueOps:
    # ... state fields ...

    @workflow(id="nurture_sequence", trigger="event:lead.qualified")
    @durable(max_days=14)
    class NurtureSequence:

        @llm_node(model="sonnet")
        def assess_lead(self, state): ...

        @llm_node(model="sonnet")
        def generate_touch(self, state): ...

        @node
        def wait_for_engagement(self, state):
            """Temporal sleeps for 3 days, then checks engagement."""
            return {"wait_duration": timedelta(days=3)}

        @human_in_the_loop(
            timeout=timedelta(hours=24),
            prompt="Lead replied. Review and decide: continue or handoff?",
        )
        def sales_review(self, state): ...

        @conditional(routes={
            "upgrade": lambda s: s["engagement_score"] > 70,
            "continue": lambda s: s["engagement_score"] > 30,
            "archive": lambda s: s["engagement_score"] <= 30,
        })
        def evaluate(self, state): ...
```

### 5.5 Decorator → LangGraph Compilation

The compiler transforms decorated classes into LangGraph `StateGraph` objects:

```
@operator class        →  OperatorConfig (Pydantic model)
  class attributes     →  TypedDict state
  @workflow class      →  StateGraph
    @node method       →  graph.add_node(name, func)
    @llm_node method   →  graph.add_node(name, _wrap_llm(func))
    @conditional       →  graph.add_conditional_edges(name, routes)
    method order       →  graph.add_edge(prev, next)  [linear by default]
```

**Method declaration order = node execution order.** No explicit edge wiring needed for linear flows. `@conditional` creates branches; each branch rejoins at the next non-conditional node.

```python
# compiler.py (simplified)
def compile_workflow(workflow_cls, state_type) -> StateGraph:
    graph = StateGraph(state_type)
    nodes = _extract_nodes(workflow_cls)  # ordered by declaration

    for i, node in enumerate(nodes):
        if node.type == "llm":
            graph.add_node(node.name, _wrap_llm_node(node.func, node.config))
        elif node.type == "conditional":
            graph.add_conditional_edges(
                nodes[i - 1].name,
                node.route_fn,
                node.routes,
            )
        else:
            graph.add_node(node.name, node.func)

        # Linear edge from previous node (unless conditional handles it)
        if i > 0 and nodes[i - 1].type != "conditional":
            graph.add_edge(nodes[i - 1].name, node.name)

    graph.set_entry_point(nodes[0].name)
    graph.set_finish_point(nodes[-1].name)
    return graph.compile()
```

---

## 6. HTTP API Design (Layer 3)

### 6.1 Endpoints

#### Operators

```
POST   /v1/operators                              Register operator (from YAML)
GET    /v1/operators                              List all operators
GET    /v1/operators/{id}                         Operator details
DELETE /v1/operators/{id}                         Remove operator
```

#### Runs

```
POST   /v1/operators/{id}/activate                Trigger a workflow
GET    /v1/operators/{id}/runs                    List runs for operator
GET    /v1/operators/{id}/runs/{run_id}           Run status + output
POST   /v1/operators/{id}/runs/{run_id}/resume    HITL resume with input
DELETE /v1/operators/{id}/runs/{run_id}           Cancel run
```

#### Events

```
GET    /v1/events/stream                          SSE stream (real-time)
POST   /v1/events/subscribe                       Register webhook
GET    /v1/events/subscriptions                   List subscriptions
DELETE /v1/events/subscriptions/{id}              Remove subscription
```

#### Context (shared state)

```
GET    /v1/context/{bucket}/{key}                 Read shared context
PUT    /v1/context/{bucket}/{key}                 Write shared context
GET    /v1/context/{bucket}                       List keys in bucket
DELETE /v1/context/{bucket}/{key}                 Delete context entry
```

### 6.2 Request/Response Examples

**Activate a workflow:**

```bash
POST /v1/operators/company_intel/activate
Content-Type: application/json

{
  "trigger": "query",
  "input": {
    "company_name": "Stripe"
  }
}
```

```json
{
  "run_id": "run_2026-02-16_abc123",
  "operator_id": "company_intel",
  "workflow_id": "research",
  "status": "running",
  "created_at": "2026-02-16T10:30:00Z"
}
```

**Get run result:**

```bash
GET /v1/operators/company_intel/runs/run_2026-02-16_abc123
```

```json
{
  "run_id": "run_2026-02-16_abc123",
  "status": "completed",
  "operator_id": "company_intel",
  "workflow_id": "research",
  "output": {
    "company_name": "Stripe",
    "research": "Stripe is a financial infrastructure platform...",
    "analysis": "Enterprise-grade, high growth potential...",
    "decision": "high",
    "report": "## Company Intelligence Report: Stripe\n..."
  },
  "metrics": {
    "duration_seconds": 4.2,
    "tokens_in": 1250,
    "tokens_out": 3400,
    "cost_usd": 0.023,
    "nodes_executed": 4
  },
  "created_at": "2026-02-16T10:30:00Z",
  "completed_at": "2026-02-16T10:30:04Z"
}
```

**HITL resume:**

```bash
POST /v1/operators/revenue_ops/runs/run_xyz/resume
Content-Type: application/json

{
  "decision": "handoff_to_sales",
  "notes": "Lead is ready for direct contact."
}
```

### 6.3 Server Implementation

```python
# openvibe/server.py
from fastapi import FastAPI, HTTPException
from openvibe.runtime import OperatorRuntime

def create_app(operators: list = None, config_path: str = None) -> FastAPI:
    app = FastAPI(title="OpenVibe Operator API", version="0.1.0")
    runtime = OperatorRuntime()

    if operators:
        for op_cls in operators:
            runtime.register_from_class(op_cls)
    if config_path:
        runtime.load(config_path)

    @app.get("/v1/operators")
    async def list_operators():
        return runtime.list_operators()

    @app.post("/v1/operators/{operator_id}/activate")
    async def activate(operator_id: str, body: ActivateRequest):
        try:
            run = await runtime.activate_async(
                operator_id, body.trigger, body.input
            )
            return {"run_id": run.id, "status": run.status}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.get("/v1/operators/{operator_id}/runs/{run_id}")
    async def get_run(operator_id: str, run_id: str):
        run = runtime.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run.to_dict()

    return app

# Convenience function
def serve(*operators, port=8000, config_path=None):
    import uvicorn
    app = create_app(operators=list(operators), config_path=config_path)
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 7. Pluggable Providers

### 7.1 LLM Provider Protocol

```python
# openvibe/llm/__init__.py
from typing import Protocol

class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...

@dataclass
class LLMResponse:
    content: str
    tokens_in: int
    tokens_out: int
    model: str
    cost_usd: float
```

**Implementations:**

```python
# openvibe/llm/anthropic.py — default
class AnthropicProvider:
    def __init__(self, api_key=None):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def complete(self, system, user, model, max_tokens=4096):
        response = self.client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(content=response.content[0].text, ...)

# openvibe/llm/openai.py
class OpenAIProvider:
    async def complete(self, system, user, model, max_tokens=4096):
        response = self.client.chat.completions.create(
            model=model, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return LLMResponse(content=response.choices[0].message.content, ...)

# openvibe/llm/local.py
class OllamaProvider:
    async def complete(self, system, user, model, max_tokens=4096): ...
```

**Configuration:**

```python
from openvibe import configure
configure(llm="anthropic", api_key="sk-...")  # or
configure(llm="openai", api_key="sk-...")     # or
configure(llm="ollama", base_url="http://localhost:11434")
```

### 7.2 Message Bus Protocol

```python
# openvibe/bus/__init__.py
class MessageBusProtocol(Protocol):
    async def connect(self): ...
    async def publish(self, subject: str, data: bytes): ...
    async def subscribe(self, subject: str, handler: Callable): ...
    async def put_kv(self, bucket: str, key: str, value: bytes): ...
    async def get_kv(self, bucket: str, key: str) -> bytes | None: ...
```

**Implementations:**

| Implementation | Use Case |
|---------------|----------|
| `bus/memory.py` | Unit tests, single-process dev |
| `bus/nats.py` | Production, multi-server |
| `bus/redis.py` | Existing Redis infrastructure |

### 7.3 Scheduler Protocol

```python
# openvibe/scheduler/__init__.py
class SchedulerProtocol(Protocol):
    async def schedule(self, workflow_id: str, trigger: TriggerConfig): ...
    async def cancel(self, schedule_id: str): ...
    async def execute_durable(self, workflow_id: str, func, timeout_days: int): ...
```

**Implementations:**

| Implementation | Use Case |
|---------------|----------|
| `scheduler/none.py` | No scheduling, manual trigger only |
| `scheduler/apscheduler.py` | Lightweight cron, no durable execution |
| `scheduler/temporal.py` | Full durable execution, multi-day workflows |

---

## 8. Package Structure

```
openvibe/
├── __init__.py                 # Public API: @operator, @workflow, @node, etc.
├── primitives.py               # Decorator implementations
├── compiler.py                 # Decorators → LangGraph StateGraph
├── runtime.py                  # OperatorRuntime (load, register, activate)
├── server.py                   # FastAPI HTTP API
├── config.py                   # YAML config loader (alternative to decorators)
├── models.py                   # Pydantic models: OperatorConfig, RunResult, etc.
│
├── llm/
│   ├── __init__.py             # LLMProvider protocol + LLMResponse
│   ├── anthropic.py            # Claude (default)
│   ├── openai.py               # GPT-4, GPT-4o
│   └── ollama.py               # Local models via Ollama
│
├── bus/
│   ├── __init__.py             # MessageBusProtocol
│   ├── memory.py               # In-memory (testing)
│   ├── nats.py                 # NATS JetStream (production)
│   └── redis.py                # Redis Streams (alternative)
│
├── scheduler/
│   ├── __init__.py             # SchedulerProtocol
│   ├── none.py                 # No scheduling (manual only)
│   ├── apscheduler.py          # Lightweight cron
│   └── temporal.py             # Full durable execution
│
├── graph/
│   ├── __init__.py             # Graph utilities
│   └── checkpointer.py        # Postgres/SQLite/memory checkpointer
│
└── contrib/
    ├── hubspot.py              # HubSpot integration helpers
    ├── slack.py                # Slack notification helpers
    └── email.py                # Email helpers
```

### pyproject.toml

```toml
[project]
name = "openvibe"
version = "0.1.0"
description = "Declarative AI operator framework — define, deploy, orchestrate"
requires-python = ">=3.12"

dependencies = [
    "langgraph>=0.2.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "pydantic>=2.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
anthropic = ["anthropic>=0.40.0"]
openai = ["openai>=1.50.0"]
nats = ["nats-py>=2.9.0"]
redis = ["redis>=5.0.0"]
temporal = ["temporalio>=1.7.0"]
all = ["openvibe[anthropic,nats,temporal]"]
```

---

## 9. Configuration Modes

Two ways to define operators — decorators (Python-native) or YAML (config-driven):

### 9.1 Decorator Mode (recommended for developers)

```python
@operator(id="company_intel", name="Company Intelligence")
class CompanyIntel:
    company_name: str = ""
    research: str = ""

    @workflow(id="research", trigger="on_demand")
    class Research:
        @llm_node(model="haiku")
        def research(self, state): ...
```

### 9.2 YAML Mode (recommended for ops/non-developers)

```yaml
operators:
  - id: company_intel
    name: Company Intelligence
    workflows:
      - id: research
        trigger: on_demand
        nodes:
          - id: research
            type: llm
            model: haiku
            prompt_file: prompts/company_intel/research.md
          - id: analyze
            type: llm
            model: sonnet
            prompt_file: prompts/company_intel/analyze.md
          - id: decide
            type: logic
          - id: report
            type: llm
            model: haiku
            prompt_file: prompts/company_intel/report.md
```

YAML mode requires prompt files and a `logic_handlers.py` file for logic nodes. Less flexible but no Python knowledge needed.

### 9.3 Hybrid Mode

```python
# Load operators from YAML, extend with Python handlers
runtime = OperatorRuntime()
runtime.load("operators.yaml")

# Register custom logic handlers
@runtime.handler("company_intel", "research", "decide")
def decide(state):
    keywords = ["enterprise", "series"]
    priority = "high" if any(k in state["analysis"].lower() for k in keywords) else "normal"
    return {"decision": priority}
```

---

## 10. Model Selection Strategy

### 10.1 Model Aliases

SDK uses aliases, resolved at runtime to actual model IDs:

| Alias | Default Resolution | Use Case |
|-------|-------------------|----------|
| `haiku` | `claude-haiku-4-5-20251001` | Fast, cheap: enrichment, formatting |
| `sonnet` | `claude-sonnet-4-5-20250929` | Balanced: analysis, scoring |
| `opus` | `claude-opus-4-6` | Deep reasoning (rare) |
| `fast` | Provider's fastest model | Latency-critical |
| `smart` | Provider's most capable | Quality-critical |

Aliases are provider-aware:

```python
configure(llm="openai")
# haiku → gpt-4o-mini, sonnet → gpt-4o, opus → o3
```

### 10.2 Per-Node Override

```python
@llm_node(model="sonnet")           # use alias
@llm_node(model="claude-opus-4-6")  # use exact model ID
```

---

## 11. Observability

### 11.1 Built-in Metrics

Every run automatically tracks:

```python
@dataclass
class RunMetrics:
    duration_seconds: float
    tokens_in: int
    tokens_out: int
    cost_usd: float
    nodes_executed: int
    nodes_failed: int
    llm_calls: int
```

### 11.2 Tracing Integration

```python
configure(
    tracing="langsmith",       # or "langfuse" or "none"
    tracing_project="my-ops",
)
```

### 11.3 Event Hooks

```python
@runtime.on("run.started")
def on_start(event): print(f"Started: {event.run_id}")

@runtime.on("run.completed")
def on_complete(event): print(f"Done: {event.run_id} in {event.duration}s")

@runtime.on("node.error")
def on_error(event): alert_slack(f"Node failed: {event.node_id}")
```

---

## 12. Deployment Modes

### 12.1 Development (single process)

```python
from openvibe import serve
serve(CompanyIntel, RevenueOps, port=8000)
# → All operators in one process
# → In-memory bus, no scheduler, SQLite checkpointer
```

### 12.2 Staging (Docker Compose)

```yaml
services:
  openvibe:
    image: openvibe:latest
    environment:
      OPENVIBE_LLM: anthropic
      OPENVIBE_BUS: nats
      OPENVIBE_SCHEDULER: temporal
    depends_on:
      - nats
      - postgres

  nats:
    image: nats:latest
    command: ["-js"]

  postgres:
    image: postgres:16
```

### 12.3 Production (multi-server)

```
Server A: openvibe serve --operators content_engine,market_intel --port 8000
Server B: openvibe serve --operators revenue_ops,customer_success,company_intel --port 8000

Shared: NATS cluster (3 nodes) + Temporal Cloud + Postgres
```

Operators communicate via NATS. Temporal routes workflows to the correct server. No code changes between modes.

---

## 13. Migration Path

### Phase 1: Extract SDK primitives from existing code

Move current `operators/base.py` logic into SDK structure. Decorator implementations wrap existing `call_claude()` + `StateGraph` patterns.

### Phase 2: Rewrite Vibe operators using SDK

Rewrite all 5 Vibe operators using `@operator` / `@workflow` / `@llm_node` decorators. Validate that the SDK can express all 22 workflows and 80 nodes.

### Phase 3: Add HTTP API layer

Wrap runtime with FastAPI. All Vibe operators accessible via REST.

### Phase 4: Add pluggable providers

Extract Anthropic-specific code behind `LLMProvider` protocol. Add OpenAI + Ollama implementations.

### Phase 5: Package and publish

`pip install openvibe` with optional dependencies.

---

## 14. Open Questions

| Question | Options | Leaning |
|----------|---------|---------|
| Package name | `openvibe` vs `vibe-operators` vs `operator-sdk` | `openvibe` (matches repo) |
| Async-first or sync? | All async vs sync with async option | Async-first (LangGraph is async) |
| State persistence | Auto-persist all state vs opt-in | Opt-in via `checkpointed=True` |
| Error recovery | Auto-retry LLM nodes vs explicit | Auto-retry with configurable limit |
| YAML vs decorators as primary | YAML-first vs decorator-first | Decorators (Python-native DX) |

---

*Source of truth: This file (SDK design) + `INTER-OPERATOR-COMMS.md` (messaging) + `OPERATOR-DESIGN.md` (current implementation)*
