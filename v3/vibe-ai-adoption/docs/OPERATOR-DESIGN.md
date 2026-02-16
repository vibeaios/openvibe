# Operator Design Document

> Date: 2026-02-16
> Status: Implemented (CrewAI removed — all nodes are logic or llm)
> Prerequisite: `OPERATOR-PATTERN.md` (concept discovery), `DESIGN.md` (3-layer architecture)
> Scope: Formal design for the Operator abstraction — the missing layer between business roles and the 3-layer stack

---

## 1. Why Operators

The V3 system had 20 AI agents across a 3-layer stack (Temporal + LangGraph + CrewAI). The architecture treated each agent as an independent unit: 1 agent = 1 trigger = 1 crew. **CrewAI has been removed** — all LLM calls now use `call_claude()` directly.

This breaks when modeling real business roles:

```
Current: 20 flat agents, each independently triggered
         s1 ─── webhook ─── lead_qual_crew
         s2 ─── cron 7am ─── buyer_intel_crew
         s3 ─── event ────── engagement_crew
         ...each isolated, no shared state

Target:  4-5 Operators, each a persistent role with shared memory
         Revenue Ops ─┬─ webhook:new_lead → lead qualification
                      ├─ event:lead_qualified → engagement
                      ├─ event:lead_nurture → nurture sequence
                      ├─ cron:daily → buyer intelligence
                      └─ cron:weekdays → deal support
                      (all share pipeline state, deal history, etc.)
```

**The word "agent" was overloaded.** It meant both:
1. A temporary worker assembled for a task (CrewAI Agent) — contractor
2. A permanent role in the org with identity and memory (Operator) — workstation

Operators resolve this by introducing a clean separation.

---

## 2. Concept Hierarchy

```
Operator  (persistent role — "Revenue Operations")
  │
  ├── State         (what it remembers across all activations)
  │
  ├── Trigger 1 ──→ Workflow A ──→ Node 1 (pure logic)
  │                               ──→ Node 2 (direct Claude call)
  │                               ──→ Node 3 (CrewAI crew: Agent + Agent)
  ├── Trigger 2 ──→ Workflow B ──→ Node 1 (direct Claude call)
  │                               ──→ Node 2 (pure logic)
  └── Trigger 3 ──→ Workflow A (reuse)
```

| Concept | What It Is | Lifecycle | Layer |
|---------|-----------|-----------|-------|
| **Operator** | Persistent role with identity, state, triggers | Always exists | Config + Runtime |
| **Trigger** | When to activate (cron, webhook, event, on-demand) | Registered once, fires repeatedly | Temporal |
| **Workflow** | Multi-step execution graph with state | Created per activation, checkpointed | LangGraph |
| **Node** | One step in a workflow — can be logic, LLM call, or crew | Created per activation | LangGraph |
| **Crew** | Multi-agent team for complex reasoning within a node | Created → executes → dissolved | CrewAI |
| **Agent** | Temporary worker with role/goal/backstory inside a crew | Created → executes → dissolved | CrewAI |

Key relationships:
- **Operator 1:N Triggers** — one role, many activation conditions
- **Trigger 1:1 Workflow** — each trigger maps to exactly one workflow
- **Workflow 1:N Nodes** — multi-step graph
- **Node has 3 implementation types:**
  - **Pure logic** — no LLM (routing, formatting, CRM writes)
  - **Direct LLM** — single Claude API call (simple reasoning, summarization)
  - **CrewAI Crew** — multi-agent collaboration (complex tasks needing role specialization)
- **Crew 1:N Agents** — only used when a node needs multi-agent collaboration
- **All workflows within an operator share the same state**

**CrewAI is not always needed.** Most nodes are pure logic or direct LLM calls. CrewAI is reserved for nodes where multi-agent collaboration genuinely improves output quality (e.g., researcher + strategist + writer producing content together).

---

## 3. Operator Definition

An Operator has 5 components:

### 3.1 Identity

Who this Operator is in the organization.

```yaml
id: revenue_ops
name: "Revenue Operations"
owner: "VP Sales"
description: "Manages the full revenue pipeline — from lead to close"
output_channels:
  - "slack:#sales-agents"
  - "slack:#revenue-intelligence"
```

### 3.2 State

What the Operator remembers across all activations. Stored in Postgres via LangGraph checkpointer. Every trigger reads the same state. Every workflow execution updates it.

```python
class RevenueOpsState(TypedDict, total=False):
    # Persistent memory
    pipeline_total: float
    pipeline_by_stage: dict[str, float]
    active_deals: list[dict]
    deals_at_risk: list[dict]
    recent_scores: list[dict]         # last N lead scores

    # Per-activation (workflow-specific, reset each run)
    _trigger: str                     # which trigger fired
    _workflow: str                    # which workflow is executing
    _activation_id: str              # unique ID for this run

    # Schema tracking
    _schema_version: int             # for migrations
```

**`total=False`** — all fields optional. New activations start with existing persisted state + workflow-specific inputs.

### 3.3 Triggers

When and why this Operator activates. Each trigger maps to one workflow.

```yaml
triggers:
  - id: new_lead
    type: webhook
    source: hubspot:new_lead
    workflow: lead_qualification
    description: "New lead enters HubSpot"

  - id: lead_qualified
    type: event
    source: self:lead_qualified       # self-referencing event
    workflow: engagement

  - id: lead_nurture
    type: event
    source: self:lead_nurture
    workflow: nurture_sequence

  - id: daily_intel
    type: cron
    schedule: "0 7 * * *"
    workflow: buyer_intelligence

  - id: deal_support
    type: cron
    schedule: "0 7 * * 1-5"
    workflow: deal_support
```

### 3.4 Workflows

What steps to execute when a trigger fires. Each workflow is a LangGraph graph. All workflows within an Operator share the same state schema.

```yaml
workflows:
  lead_qualification:
    description: "Score and route incoming leads"
    nodes: [enrich, score, route, update_crm]
    checkpointed: true
    timeout_minutes: 5

  engagement:
    description: "Generate personalized outreach for qualified leads"
    nodes: [research_buyer, generate_sequence, personalize, format]
    checkpointed: true
    timeout_minutes: 10

  nurture_sequence:
    description: "Multi-day drip nurture for warm leads"
    nodes: [assess, generate, record, evaluate]
    durable: true                     # uses Temporal sleep for multi-day
    max_duration_days: 42
    timeout_minutes: 5                # per iteration

  buyer_intelligence:
    description: "Daily scan of buyer signals and market moves"
    nodes: [scan, analyze, brief]
    timeout_minutes: 3

  deal_support:
    description: "Weekday deal analysis and risk assessment"
    nodes: [pull_deals, assess_risk, generate_actions]
    timeout_minutes: 3
```

### 3.5 Node Implementation Strategies

Each node in a workflow has one of three implementation types. The choice depends on the node's complexity:

```
Node complexity            →  Implementation
───────────────────────────────────────────────
No LLM needed              →  Pure logic (Python function)
Single reasoning task       →  Direct Claude API call
Multi-role collaboration    →  CrewAI Crew (2+ agents)
```

#### Type 1: Pure Logic

No LLM call. Used for routing, formatting, data transformation, CRM/API writes.

```python
def route(state: RevenueOpsState) -> RevenueOpsState:
    """Route lead based on score — no AI needed."""
    score = state.get("lead_score", 0)
    if score >= 80:
        state["route"] = "qualified"
    elif score >= 40:
        state["route"] = "nurture"
    else:
        state["route"] = "disqualify"
    return state
```

#### Type 2: Direct Claude API Call

Single LLM call via the Anthropic SDK. Used when one prompt produces one output — no need for CrewAI's role/goal abstraction.

```python
import anthropic

@observe(name="analyze-node")
def analyze(state: RevenueOpsState) -> RevenueOpsState:
    """Analyze buyer signals — single Claude call, no CrewAI overhead."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system="You are a buyer signal analyst. Be concise.",
        messages=[{
            "role": "user",
            "content": f"Analyze these signals for {state['company_name']}:\n{state['signals']}"
        }],
    )
    state["analysis"] = response.content[0].text
    return state
```

#### Type 3: CrewAI Crew

Multi-agent collaboration. Used when the task benefits from distinct roles working together — e.g., researcher feeds strategist feeds writer.

```python
@observe(name="content-generation-node")
def generate_content(state: ContentEngineState) -> ContentEngineState:
    """Generate content — 3 agents collaborate for higher quality."""
    researcher = Agent(
        role="Content Researcher",
        goal="Find data and insights on the topic",
        llm="anthropic/claude-sonnet-4-5-20250929",
    )
    writer = Agent(
        role="Content Writer",
        goal="Write compelling content from research",
        llm="anthropic/claude-sonnet-4-5-20250929",
    )
    editor = Agent(
        role="Content Editor",
        goal="Polish and tighten the draft",
        llm="anthropic/claude-haiku-4-5-20251001",
    )

    research_task = Task(description="...", agent=researcher)
    write_task = Task(description="...", agent=writer, context=[research_task])
    edit_task = Task(description="...", agent=editor, context=[write_task])

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, write_task, edit_task],
        process=Process.sequential,
    )
    result = crew.kickoff(inputs={"topic": state["topic"]})
    state["content"] = str(result)
    return state
```

#### When to Use Which

| Signal | Type | Why |
|--------|------|-----|
| No LLM needed | Pure logic | Don't pay for tokens on deterministic work |
| One prompt → one output | Direct Claude | CrewAI adds overhead without multi-agent benefit |
| 1 agent + 1 task crew | **Direct Claude** | A single-agent Crew is just a wrapper around an LLM call |
| 2+ roles collaborating | CrewAI Crew | Role specialization + task chaining improves output |
| Hierarchical delegation | CrewAI Crew | Manager agent distributing subtasks |
| Needs tool use (web search, CRM) | CrewAI Crew | CrewAI's tool binding per agent is valuable |

#### Expected Distribution

For a typical Operator with ~15 nodes across 5 workflows:

| Node Type | ~Count | % | Cost |
|-----------|--------|---|------|
| Pure logic | ~5 | 33% | $0 (no LLM) |
| Direct Claude | ~6 | 40% | Low (single call, often Haiku) |
| CrewAI Crew | ~4 | 27% | Higher (multi-agent, often Sonnet) |

**Most nodes don't need CrewAI.** CrewAI is for the ~25-30% of nodes where multi-agent collaboration genuinely adds value.

#### Node Config in YAML

Nodes declare their implementation type so the runtime knows how to execute them:

```yaml
workflows:
  lead_qualification:
    nodes:
      - id: enrich
        type: llm                        # direct Claude call
        model: claude-haiku-4-5-20251001
        prompt_file: prompts/enrich.md
      - id: score
        type: crew                       # CrewAI multi-agent
        crew:
          agents:
            - role: "Lead Scoring Analyst"
              goal: "Score lead fit, intent, and urgency"
              model: claude-sonnet-4-5-20250929
            - role: "ICP Matcher"
              goal: "Match lead against ideal customer profile"
              model: claude-haiku-4-5-20251001
          process: sequential
      - id: route
        type: logic                      # pure Python, no LLM
      - id: update_crm
        type: logic
```

---

## 4. Architecture Mapping

How each Operator component maps to the technology stack:

```
Operator Component    →  Technology Layer
───────────────────────────────────────────
Identity              →  Config YAML + Pydantic model
State                 →  LangGraph TypedDict + Postgres checkpointer
Triggers              →  Temporal Schedules (cron) / Webhooks / Signals
Workflows             →  LangGraph StateGraph (nodes + edges)
Nodes (logic)         →  Pure Python functions
Nodes (llm)           →  Anthropic SDK (direct Claude API call)
Nodes (crew)          →  CrewAI Crew (multi-agent collaboration)
Observability         →  LangFuse traces + spans
```

### Execution Chain

When a trigger fires, this is the full chain:

```
1. Temporal Schedule/Webhook/Signal fires
   ↓
2. Temporal Workflow starts (durable envelope)
   ├── loads Operator state from Postgres
   ↓
3. Temporal Activity executes (retryable unit)
   ↓
4. LangGraph Graph runs (multi-step workflow with state)
   ├── Node 1: pure logic (no LLM)
   ├── Node 2: direct Claude API call
   ├── Node 3: CrewAI crew (multi-agent)
   └── Node 4: pure logic (format output)
   ↓
5. State updated in Postgres (checkpointed)
   ↓
6. Output delivered (Slack, HubSpot, etc.)
   ↓
7. Temporal Workflow logs completion
   ↓
8. LangFuse trace flushed
```

### What Each Layer Owns

| Layer | Responsibility | Does NOT Do |
|-------|---------------|-------------|
| **Temporal** | When to run, durability, retries, multi-day waits | Business logic, AI reasoning |
| **LangGraph** | Workflow state, step sequencing, routing, checkpointing | Scheduling, agent personality |
| **Anthropic SDK** | Single LLM calls for straightforward reasoning | Multi-agent coordination, state management |
| **CrewAI** | Multi-agent roles, delegation, tool use per agent | State persistence, scheduling, simple single-prompt tasks |

**Note on the "3-layer stack":** The original architecture was Temporal + LangGraph + CrewAI. With the Operator pattern, the stack becomes **Temporal + LangGraph + (Anthropic SDK | CrewAI)**. CrewAI is no longer mandatory — it's one of three node implementation options. LangGraph remains the workflow backbone for all nodes.

---

## 5. Decisions on Open Questions

### 5.1 Config Format

**Decision: YAML declaration + Pydantic runtime models.**

YAML for:
- Human-readable, git-tracked declarations
- Easy to review diffs
- Consistent with existing `agents.yaml` pattern

Pydantic for:
- Type validation at load time
- IDE support and autocomplete
- Runtime type safety

```python
# models.py — new Operator models

class NodeType(str, Enum):
    LOGIC = "logic"                            # pure Python, no LLM
    LLM = "llm"                                # direct Claude API call
    CREW = "crew"                              # CrewAI multi-agent

class TriggerConfig(BaseModel):
    id: str
    type: TriggerType                          # cron | webhook | event | on_demand
    schedule: str | None = None                # cron expression
    source: str | None = None                  # event source
    workflow: str                              # which workflow to run
    description: str = ""

class CrewAgentConfig(BaseModel):
    role: str
    goal: str
    backstory: str = ""
    model: str = "claude-sonnet-4-5-20250929"
    tools: list[str] = Field(default_factory=list)

class CrewConfig(BaseModel):
    agents: list[CrewAgentConfig]
    process: str = "sequential"                # sequential | hierarchical
    memory: bool = False
    knowledge_sources: list[str] = Field(default_factory=list)

class NodeConfig(BaseModel):
    id: str
    type: NodeType = NodeType.LOGIC
    model: str | None = None                   # for NodeType.LLM
    prompt_file: str | None = None             # for NodeType.LLM
    crew: CrewConfig | None = None             # for NodeType.CREW

class WorkflowConfig(BaseModel):
    id: str
    description: str = ""
    nodes: list[NodeConfig]
    checkpointed: bool = True
    durable: bool = False                      # multi-day (Temporal sleep)
    max_duration_days: int | None = None
    timeout_minutes: int = 5
    hitl_nodes: list[str] = Field(default_factory=list)  # node IDs that pause for human

class OperatorConfig(BaseModel):
    id: str
    name: str
    owner: str = ""
    description: str = ""
    output_channels: list[str] = Field(default_factory=list)
    state_schema: str                          # dotted path to TypedDict class
    triggers: list[TriggerConfig]
    workflows: list[WorkflowConfig]
    enabled: bool = True
```

File: `config/operators.yaml` replaces `config/agents.yaml`.

Note: `CrewStrategyConfig` is gone. Crew configuration now lives **inside the node** that uses it (`NodeConfig.crew`). This makes it explicit: CrewAI is a node-level implementation choice, not a workflow-level one.

### 5.2 State Schema Evolution

**Decision: Additive-only by default + versioned migration for breaking changes.**

Rules:
1. **Adding fields** — always safe. Use `TypedDict(total=False)` so all fields are optional with defaults.
2. **Renaming fields** — breaking change. Requires migration function.
3. **Removing fields** — breaking change. Requires migration function.
4. **Changing field types** — breaking change. Requires migration function.

Implementation:

```python
# operators/revenue_ops/state.py

class RevenueOpsState(TypedDict, total=False):
    _schema_version: int              # current: 1
    pipeline_total: float
    pipeline_by_stage: dict
    # ... all fields optional

# operators/revenue_ops/migrations.py

MIGRATIONS = {
    # (from_version, to_version): migration_function
    (1, 2): migrate_v1_to_v2,
}

def migrate_v1_to_v2(state: dict) -> dict:
    """Example: rename 'pipeline_total' → 'pipeline_value'."""
    state["pipeline_value"] = state.pop("pipeline_total", 0.0)
    state["_schema_version"] = 2
    return state

def ensure_current_schema(state: dict, target_version: int) -> dict:
    """Run all necessary migrations to bring state to current version."""
    current = state.get("_schema_version", 1)
    while current < target_version:
        migrator = MIGRATIONS.get((current, current + 1))
        if not migrator:
            raise ValueError(f"No migration from v{current} to v{current+1}")
        state = migrator(state)
        current += 1
    return state
```

The OperatorRuntime calls `ensure_current_schema()` on every state load. This is the same pattern as database migrations — versioned, sequential, testable.

### 5.3 Cross-Operator Communication

**Decision: Temporal Signals for direct communication + Event triggers for loose coupling.**

Two patterns:

**Pattern A: Event-Driven (Loose Coupling)**

An Operator emits a named event. Other Operators that have triggers listening for that event will activate.

```
Revenue Ops scores a lead → emits "lead:qualified"
  → Revenue Ops' own trigger catches it → runs engagement workflow
  → Customer Success could also listen (if configured)
```

Implementation: Temporal Workflow emits a signal or starts a child workflow. The routing is config-driven:

```yaml
# revenue_ops triggers
- id: lead_qualified
  type: event
  source: self:lead_qualified           # same operator
  workflow: engagement

# customer_success triggers
- id: revenue_escalation
  type: event
  source: revenue_ops:deal_at_risk      # cross-operator
  workflow: urgent_review
```

**Pattern B: Direct Signal (Tight Coupling)**

One Operator's workflow directly signals another Operator's running workflow. Used for urgent, synchronous coordination.

```python
# Inside a Revenue Ops workflow node:
async def escalate_to_cs(state):
    await workflow.signal_external_workflow(
        workflow_id="customer_success_daily",
        signal="urgent_review",
        args={"deal_id": state["deal_id"], "reason": "at_risk"},
    )
```

**When to use which:**

| Situation | Pattern | Why |
|-----------|---------|-----|
| Lead qualified → engagement | Event (self) | Natural workflow progression |
| Content generated → repurpose | Event (self) | Pipeline chain |
| Deal at risk → CS alert | Event (cross) | Loose coupling, CS decides how to handle |
| Urgent escalation mid-workflow | Direct Signal | Need immediate response |

### 5.4 Human-in-the-Loop (HITL)

**Decision: LangGraph interrupt for graph-level pause + Temporal Signal for durable wait + Slack for UI.**

The full HITL pattern:

```
1. LangGraph graph reaches a HITL node
   ↓
2. Node posts approval request to Slack
   (with action buttons: Approve / Reject / Modify)
   ↓
3. Graph state checkpointed to Postgres
   ↓
4. Temporal Activity returns "waiting_for_approval"
   ↓
5. Temporal Workflow waits for signal (durable — survives restarts)
   ↓
   ... hours or days pass ...
   ↓
6. Human clicks Approve in Slack
   → Slack webhook fires
   → API endpoint receives webhook
   → Sends Temporal Signal to workflow
   ↓
7. Temporal Workflow resumes
   → Loads checkpointed LangGraph state
   → Continues from HITL node
```

Config declares which nodes require human approval:

```yaml
workflows:
  engagement:
    nodes: [research_buyer, generate_sequence, personalize, format, send]
    hitl_nodes: ["send"]              # pause before sending outreach
```

Implementation in the LangGraph graph:

```python
def create_engagement_graph(checkpointer=None):
    workflow = StateGraph(EngagementState)

    workflow.add_node("research_buyer", research_buyer)
    workflow.add_node("generate_sequence", generate_sequence)
    workflow.add_node("personalize", personalize)
    workflow.add_node("format", format_output)
    workflow.add_node("send", send_outreach)

    # Edges
    workflow.set_entry_point("research_buyer")
    workflow.add_edge("research_buyer", "generate_sequence")
    workflow.add_edge("generate_sequence", "personalize")
    workflow.add_edge("personalize", "format")
    workflow.add_edge("format", "send")
    workflow.add_edge("send", END)

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["send"],     # pause here for approval
    )
```

**HITL scope per Operator:**

| Operator | HITL Nodes | Why |
|----------|-----------|-----|
| Revenue Ops | `send_outreach`, `update_deal_stage` | Don't auto-send emails or change CRM stages |
| Content Engine | `publish` | Review content before publishing |
| Customer Success | `send_escalation` | Review before escalating to customer |
| Market Intelligence | None (read-only) | Only produces reports, no actions |

### 5.5 Observability

**Decision: LangFuse hierarchical tracing — Operator → Workflow → Node → (LLM call | Crew) → Generation.**

Trace structure showing all three node types:

```
Trace: operator=revenue_ops, trigger=new_lead, activation_id=abc123
  │
  ├── Span: workflow=lead_qualification
  │     │
  │     ├── Span: node=enrich [type=llm]
  │     │     └── Generation: claude-haiku (tokens: 150/500, $0.0002)
  │     │
  │     ├── Span: node=score [type=crew]
  │     │     └── Span: crew (2 agents, sequential)
  │     │           ├── Generation: claude-sonnet — Lead Scoring Analyst (tokens: 200/800)
  │     │           └── Generation: claude-haiku — ICP Matcher (tokens: 100/400)
  │     │
  │     ├── Span: node=route [type=logic]         ← no LLM, 0 tokens
  │     │
  │     └── Span: node=update_crm [type=logic]    ← no LLM, 0 tokens
  │
  ├── Metadata:
  │     operator: revenue_ops
  │     trigger: new_lead
  │     workflow: lead_qualification
  │     duration_s: 8.3
  │     total_tokens: 1650
  │     total_cost_usd: 0.005
  │     node_types: {logic: 2, llm: 1, crew: 1}
  │     status: success
  │     prospect_quality: high
```

Implementation uses `@observe` decorator (already proven in `company_intel.py`):

```python
from langfuse import observe

@observe(name="lead-qualification")
def run_lead_qualification(state: RevenueOpsState) -> RevenueOpsState:
    """Top-level workflow function — creates the trace."""
    graph = create_lead_qual_graph()
    return graph.invoke(state)

# Type: llm — direct Claude call, one span + one generation
@observe(name="enrich-node")
def enrich(state: RevenueOpsState) -> RevenueOpsState:
    client = anthropic.Anthropic()
    response = client.messages.create(model="claude-haiku-4-5-20251001", ...)
    state["enriched"] = response.content[0].text
    return state

# Type: crew — multi-agent, one span + nested generations
@observe(name="score-node")
def score(state: RevenueOpsState) -> RevenueOpsState:
    crew = create_scoring_crew()
    result = crew.kickoff(inputs={"lead": state["lead_data"]})
    state["score"] = parse_score(str(result))
    return state

# Type: logic — no LLM, span only (useful for duration tracking)
@observe(name="route-node")
def route(state: RevenueOpsState) -> RevenueOpsState:
    state["route"] = "qualified" if state["score"] >= 80 else "nurture"
    return state
```

**Dashboards:**

| Dashboard | What It Shows | Audience |
|-----------|-------------|----------|
| Operator Overview | All operators, activation counts, error rates | Engineering |
| Cost Tracking | Token usage + cost per operator/workflow | Finance |
| Latency | P50/P95 duration per workflow | Engineering |
| Business Metrics | Lead scores, content produced, deals supported | Business |

---

## 6. The Four Operators

### 6.1 Revenue Operations

**Purpose:** Manages the full revenue pipeline — from new lead to closed deal.

```yaml
operator:
  id: revenue_ops
  name: "Revenue Operations"
  owner: "VP Sales"
  output_channels: ["slack:#sales-agents"]

  triggers:
    - id: new_lead
      type: webhook
      source: hubspot:new_lead
      workflow: lead_qualification

    - id: lead_qualified
      type: event
      source: self:lead_qualified
      workflow: engagement

    - id: lead_nurture
      type: event
      source: self:lead_nurture
      workflow: nurture_sequence

    - id: daily_intel
      type: cron
      schedule: "0 7 * * *"
      workflow: buyer_intelligence

    - id: weekday_deals
      type: cron
      schedule: "0 7 * * 1-5"
      workflow: deal_support

  workflows:
    - id: lead_qualification
      timeout_minutes: 5
      nodes:
        - id: enrich
          type: llm
          model: claude-haiku-4-5-20251001
        - id: score
          type: crew
          crew:
            agents:
              - { role: "Lead Scoring Analyst", goal: "Score fit + intent + urgency", model: claude-sonnet-4-5-20250929 }
              - { role: "ICP Matcher", goal: "Match against ideal customer profile", model: claude-haiku-4-5-20251001 }
            process: sequential
        - id: route
          type: logic
        - id: update_crm
          type: logic

    - id: engagement
      timeout_minutes: 10
      hitl_nodes: [format]
      nodes:
        - id: research_buyer
          type: llm
          model: claude-sonnet-4-5-20250929
        - id: generate_sequence
          type: crew
          crew:
            agents:
              - { role: "Outreach Copywriter", goal: "Write personalized outreach", model: claude-sonnet-4-5-20250929 }
              - { role: "Sales Strategist", goal: "Determine engagement approach", model: claude-sonnet-4-5-20250929 }
            process: sequential
        - id: personalize
          type: llm
          model: claude-haiku-4-5-20251001
        - id: format
          type: logic

    - id: nurture_sequence
      durable: true
      max_duration_days: 42
      nodes:
        - { id: assess, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: generate, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: record, type: logic }
        - { id: evaluate, type: logic }

    - id: buyer_intelligence
      timeout_minutes: 3
      nodes:
        - { id: scan, type: logic }
        - { id: analyze, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: brief, type: llm, model: claude-haiku-4-5-20251001 }

    - id: deal_support
      timeout_minutes: 3
      nodes:
        - { id: pull_deals, type: logic }
        - { id: assess_risk, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: generate_actions, type: llm, model: claude-haiku-4-5-20251001 }
```

**Maps from:** S1 (Lead Qual), S2 (Buyer Intel), S3 (Engagement), S4 (Deal Support), S5 (Nurture)

**State:** pipeline data, deal history, lead scores, engagement outcomes

**Node type breakdown:** 20 nodes total — 8 logic, 8 llm, 4 crew

### 6.2 Content Engine

**Purpose:** Produces, repurposes, and distributes marketing content.

```yaml
operator:
  id: content_engine
  name: "Content Engine"
  owner: "Marketing Lead"
  output_channels: ["slack:#marketing-agents"]

  triggers:
    - id: weekly_research
      type: cron
      schedule: "0 9 * * 1"
      workflow: segment_research

    - id: message_testing
      type: cron
      schedule: "0 10 * * 1,4"
      workflow: message_testing

    - id: daily_content
      type: cron
      schedule: "0 9 * * *"
      workflow: content_generation

    - id: content_ready
      type: event
      source: self:content_generated
      workflow: repurposing

    - id: repurposed_ready
      type: event
      source: self:content_repurposed
      workflow: distribution

    - id: weekly_optimization
      type: cron
      schedule: "0 8 * * 5"
      workflow: journey_optimization

  workflows:
    - id: segment_research
      timeout_minutes: 5
      nodes:
        - { id: gather_data, type: logic }
        - { id: analyze_segments, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: report, type: llm, model: claude-haiku-4-5-20251001 }

    - id: message_testing
      timeout_minutes: 5
      nodes:
        - { id: generate_variants, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: evaluate, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: recommend, type: logic }

    - id: content_generation
      timeout_minutes: 10
      nodes:
        - { id: research, type: llm, model: claude-sonnet-4-5-20250929 }
        - id: draft
          type: crew
          crew:
            agents:
              - { role: "Content Writer", goal: "Write compelling content from research", model: claude-sonnet-4-5-20250929 }
              - { role: "Content Editor", goal: "Polish and tighten the draft", model: claude-haiku-4-5-20251001 }
            process: sequential
        - { id: polish, type: llm, model: claude-haiku-4-5-20251001 }

    - id: repurposing
      timeout_minutes: 5
      nodes:
        - { id: analyze_content, type: logic }
        - { id: adapt_formats, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: finalize, type: logic }

    - id: distribution
      timeout_minutes: 3
      hitl_nodes: [schedule_posts]
      nodes:
        - { id: select_channels, type: logic }
        - { id: schedule_posts, type: logic }
        - { id: report, type: llm, model: claude-haiku-4-5-20251001 }

    - id: journey_optimization
      timeout_minutes: 5
      nodes:
        - { id: collect_metrics, type: logic }
        - { id: analyze_funnel, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: recommend, type: llm, model: claude-haiku-4-5-20251001 }
```

**Maps from:** M1 (Segment Research), M2 (Message Testing), M3 (Content Gen), M4 (Repurposing), M5 (Distribution), M6 (Journey Optimization)

**State:** content calendar, segment profiles, distribution metrics, A/B test results

**Node type breakdown:** 18 nodes total — 7 logic, 10 llm, 1 crew (content_generation.draft)

### 6.3 Customer Success

**Purpose:** Manages customer health, onboarding, expansion, and voice-of-customer.

```yaml
operator:
  id: customer_success
  name: "Customer Success"
  owner: "CS Lead"
  output_channels: ["slack:#cs-agents"]

  triggers:
    - id: deal_won
      type: webhook
      source: hubspot:deal_won
      workflow: onboarding

    - id: weekly_advisory
      type: cron
      schedule: "0 10 * * 2"
      workflow: success_advisory

    - id: daily_health
      type: cron
      schedule: "0 2 * * *"
      workflow: health_monitoring

    - id: weekly_expansion
      type: cron
      schedule: "0 9 * * 3"
      workflow: expansion_scan

    - id: weekly_voice
      type: cron
      schedule: "0 8 * * 5"
      workflow: customer_voice

    - id: revenue_escalation
      type: event
      source: revenue_ops:deal_at_risk
      workflow: urgent_review

  workflows:
    - id: onboarding
      timeout_minutes: 5
      hitl_nodes: [send_welcome]
      nodes:
        - { id: create_plan, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: setup_milestones, type: logic }
        - { id: send_welcome, type: logic }

    - id: success_advisory
      timeout_minutes: 5
      nodes:
        - { id: review_accounts, type: logic }
        - { id: identify_actions, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: generate_playbooks, type: llm, model: claude-sonnet-4-5-20250929 }

    - id: health_monitoring
      timeout_minutes: 3
      nodes:
        - { id: pull_signals, type: logic }
        - { id: score_health, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: flag_risks, type: logic }

    - id: expansion_scan
      timeout_minutes: 5
      nodes:
        - { id: analyze_usage, type: logic }
        - { id: identify_opportunities, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: draft_proposals, type: llm, model: claude-sonnet-4-5-20250929 }

    - id: customer_voice
      timeout_minutes: 5
      nodes:
        - { id: collect_feedback, type: logic }
        - { id: analyze_themes, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: report, type: llm, model: claude-haiku-4-5-20251001 }

    - id: urgent_review
      timeout_minutes: 3
      nodes:
        - { id: assess_situation, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: recommend_action, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: alert_team, type: logic }
```

**Maps from:** C1 (Onboarding), C2 (Success Advisor), C3 (Health Intel), C4 (Expansion), C5 (Customer Voice)

**State:** customer health scores, onboarding progress, expansion signals, churn risks

**Note:** Has a cross-operator trigger (`revenue_ops:deal_at_risk`) — demonstrates the event-driven pattern from 5.3.

**Node type breakdown:** 18 nodes total — 8 logic, 10 llm, 0 crew (CS workflows are straightforward — no multi-agent collaboration needed)

### 6.4 Market Intelligence

**Purpose:** Monitors funnel, forecasts revenue, analyzes conversations, answers ad-hoc queries.

```yaml
operator:
  id: market_intel
  name: "Market Intelligence"
  owner: "CEO / Strategy"
  output_channels: ["slack:#revenue-intelligence"]

  triggers:
    - id: daily_funnel
      type: cron
      schedule: "0 6 * * *"
      workflow: funnel_monitor

    - id: weekday_forecast
      type: cron
      schedule: "0 7 * * 1-5"
      workflow: deal_risk_forecast

    - id: weekly_conversations
      type: cron
      schedule: "0 8 * * 1"
      workflow: conversation_analysis

    - id: query
      type: on_demand
      workflow: nl_query

  workflows:
    - id: funnel_monitor
      timeout_minutes: 3
      nodes:
        - { id: pull_metrics, type: logic }
        - { id: detect_anomalies, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: brief, type: llm, model: claude-haiku-4-5-20251001 }

    - id: deal_risk_forecast
      timeout_minutes: 5
      nodes:
        - { id: pull_deals, type: logic }
        - { id: model_risk, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: forecast, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: report, type: llm, model: claude-haiku-4-5-20251001 }

    - id: conversation_analysis
      timeout_minutes: 10
      nodes:
        - { id: pull_transcripts, type: logic }
        - { id: extract_patterns, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: summarize, type: llm, model: claude-haiku-4-5-20251001 }

    - id: nl_query
      timeout_minutes: 3
      nodes:
        - { id: parse_question, type: llm, model: claude-haiku-4-5-20251001 }
        - { id: query_data, type: logic }
        - { id: reason, type: llm, model: claude-sonnet-4-5-20250929 }
        - { id: respond, type: llm, model: claude-haiku-4-5-20251001 }
```

**Maps from:** R1 (Funnel Monitor), R2 (Deal Risk & Forecast), R3 (Conversation Analysis), R4 (NL Revenue Interface)

**State:** funnel metrics, forecast models, conversation insights, query history

**Node type breakdown:** 13 nodes total — 4 logic, 9 llm, 0 crew (intelligence is analysis + reporting — single-prompt tasks)

### 6.5 Company Intelligence (Standalone)

The smoke-test Operator. Simpler than the four above — single trigger, single workflow, on-demand only.

```yaml
operator:
  id: company_intel
  name: "Company Intelligence"
  owner: "Sales / Strategy"
  output_channels: ["slack:#revenue-intelligence"]

  triggers:
    - id: query
      type: on_demand
      workflow: research

  workflows:
    - id: research
      timeout_minutes: 5
      nodes:
        - { id: research, type: crew, crew: { agents: [{ role: "Company Research Analyst", goal: "Produce concise company brief", model: claude-haiku-4-5-20251001 }], process: sequential } }
        - { id: analyze, type: crew, crew: { agents: [{ role: "Strategic Sales Analyst", goal: "Assess prospect quality", model: claude-haiku-4-5-20251001 }], process: sequential } }
        - { id: decide, type: logic }
        - { id: report, type: logic }
```

**Already implemented:** `operators/company_intel.py` — validates the full chain.

**Note on current implementation:** The existing `company_intel.py` uses single-agent CrewAI crews for `research` and `analyze` nodes. These could be simplified to direct Claude calls (type: `llm`) since a 1-agent crew is just a wrapper. Keeping as `crew` for now since it's the validated smoke test — can be simplified later.

### 6.6 Node Type Summary (All Operators)

| Operator | Total Nodes | Logic | LLM | Crew | CrewAI Agents |
|----------|------------|-------|-----|------|---------------|
| Revenue Ops | 20 | 8 (40%) | 8 (40%) | 4 (20%) | 8 across 4 crews |
| Content Engine | 18 | 7 (39%) | 10 (56%) | 1 (5%) | 2 in 1 crew |
| Customer Success | 18 | 8 (44%) | 10 (56%) | 0 | 0 |
| Market Intelligence | 13 | 4 (31%) | 9 (69%) | 0 | 0 |
| Company Intel | 4 | 2 (50%) | 0 | 2 (50%) | 2 (1 per crew) |
| **Total** | **73** | **29 (40%)** | **37 (51%)** | **7 (9%)** | **12** |

**Key insight:** Only 9% of nodes use CrewAI. The vast majority (91%) are pure logic or direct Claude calls. CrewAI is valuable but surgical — used only where multi-agent collaboration genuinely improves output.

**What this means for implementation:**
- CrewAI is a dependency, not the backbone
- Most development work is writing LangGraph nodes with direct Claude calls
- CrewAI complexity is confined to ~7 nodes across the entire system

---

## 7. Migration Path

### From 20 Agents to 5 Operators

| Phase | What | Impact |
|-------|------|--------|
| **Phase 0** | Write `operators.yaml` config alongside existing `agents.yaml` | No code change |
| **Phase 1** | Implement `OperatorConfig` Pydantic models | Models only |
| **Phase 2** | Build `OperatorRuntime` — loads config, registers with Temporal | New runtime, existing code untouched |
| **Phase 3** | Refactor existing graphs/crews into operator directories | Move files, update imports |
| **Phase 4** | Add shared state per operator | New state schemas, checkpointer wiring |
| **Phase 5** | Wire cross-operator events | Temporal signals between operators |
| **Phase 6** | Add HITL nodes where needed | Graph interrupt + Slack integration |
| **Phase 7** | Retire `agents.yaml` and flat agent model | Cleanup |

### Directory Structure (Target)

```
src/vibe_ai_ops/
├── operators/                          # Operator implementations
│   ├── base.py                         # OperatorRuntime + base classes
│   ├── revenue_ops/
│   │   ├── __init__.py
│   │   ├── state.py                    # RevenueOpsState TypedDict
│   │   ├── migrations.py              # State schema migrations
│   │   └── workflows/
│   │       ├── lead_qualification.py   # LangGraph graph — nodes: 2 logic + 1 llm + 1 crew
│   │       ├── engagement.py           # LangGraph graph — nodes: 1 logic + 2 llm + 1 crew
│   │       ├── nurture_sequence.py     # LangGraph graph — nodes: 2 logic + 2 llm
│   │       ├── buyer_intelligence.py   # LangGraph graph — nodes: 1 logic + 2 llm
│   │       └── deal_support.py         # LangGraph graph — nodes: 1 logic + 2 llm
│   ├── content_engine/
│   │   ├── state.py
│   │   └── workflows/                  # 6 workflows — mostly llm nodes, 1 crew node
│   ├── customer_success/
│   │   ├── state.py
│   │   └── workflows/                  # 6 workflows — all logic + llm, no crew
│   ├── market_intel/
│   │   ├── state.py
│   │   └── workflows/                  # 4 workflows — all logic + llm, no crew
│   └── company_intel/                  # Already exists (smoke test)
│       └── ...
├── temporal/                           # Scheduling layer (shared)
│   ├── worker.py                       # Registers all operator workflows + activities
│   ├── schedules.py                    # Cron → Temporal schedule builder
│   └── activities/
│       └── operator_activity.py        # Generic: loads operator, runs workflow
├── shared/                             # Infrastructure (unchanged)
│   ├── models.py                       # + OperatorConfig, NodeType, etc.
│   ├── config.py                       # + load_operator_configs()
│   └── ...
└── config/
    ├── operators.yaml                  # Replaces agents.yaml
    └── prompts/                        # Unchanged — referenced by llm-type nodes
```

**No separate `crews/` directories.** CrewAI crew definitions live inside the workflow files that use them (as factory functions within the node implementation). A workflow file contains all its nodes — logic, LLM, and crew — in one place.

### What Changes, What Stays

| Component | Status | Notes |
|-----------|--------|-------|
| `config/agents.yaml` | **Replaced** by `operators.yaml` | Flat → grouped by operator |
| `shared/models.py` | **Extended** | Add OperatorConfig, NodeType, NodeConfig, etc. |
| `main.py` | **Replaced** by `operators/base.py` OperatorRuntime | New entry point |
| `temporal/worker.py` | **Updated** | Register operator workflows instead of flat activities |
| `graphs/*` | **Absorbed** into `operators/*/workflows/` | Graph = workflow file, nodes include all 3 types |
| `crews/*` | **Absorbed** into workflow files | Crew factory functions live in the workflow that uses them |
| `shared/*` | **Unchanged** | Clients, logger, tracing stay |
| `config/prompts/*` | **Unchanged** | Referenced by `llm`-type nodes |

---

## 8. OperatorRuntime

The central runtime that manages all operators.

```python
# operators/base.py

class OperatorRuntime:
    """Loads operator configs, registers with Temporal, manages lifecycle."""

    def __init__(self, config_path: str = "config/operators.yaml"):
        self.operators: dict[str, OperatorConfig] = {}
        self.state_schemas: dict[str, type] = {}
        self.workflow_factories: dict[str, Callable] = {}

    def register(self, operator_id: str) -> None:
        """Register an operator: load config, validate, wire temporal schedules."""
        config = self.operators[operator_id]

        # 1. Validate state schema exists and is loadable
        # 2. Register each trigger as a Temporal schedule/webhook
        # 3. Map each workflow to its LangGraph graph factory
        #    (graph factory builds nodes based on NodeConfig.type:
        #     logic → Python function, llm → Claude call, crew → CrewAI)

    def activate(self, operator_id: str, trigger_id: str, input_data: dict) -> None:
        """Activate an operator: load state, run workflow, save state."""
        config = self.operators[operator_id]
        trigger = next(t for t in config.triggers if t.id == trigger_id)

        # 1. Load persisted state from Postgres
        # 2. Run schema migration if needed
        # 3. Merge input_data into state
        # 4. Execute the LangGraph graph for trigger.workflow
        #    Each node executes based on its type:
        #    - logic: call Python function directly
        #    - llm: call anthropic.messages.create()
        #    - crew: build CrewAI Crew, call kickoff()
        # 5. Save updated state back to Postgres
        # 6. Emit events if any (for cross-operator communication)
        # 7. Flush LangFuse trace

    def list_operators(self) -> list[OperatorConfig]:
        """List all registered operators."""
        return list(self.operators.values())

    def get_state(self, operator_id: str) -> dict:
        """Read an operator's current persisted state."""
        ...
```

---

## 9. Key Design Principles

### 9.1 Operators Are Not Agents

| | Operator | Agent (CrewAI) |
|---|---------|---------------|
| Lifecycle | Permanent — always registered | Temporary — created per task |
| State | Persistent (Postgres) | Ephemeral (in-memory) |
| Identity | Fixed ID, name, owner | Dynamic role/goal/backstory |
| Triggers | Multiple (cron, webhook, event) | None (invoked by workflow) |
| Analogy | Workstation / Department | Contractor / Temp worker |

### 9.2 Shared State Is the Operator's Memory

All workflows within an Operator read and write the same state. This is how the Operator "remembers":

- Revenue Ops' lead_qualification workflow scores a lead at 85
- Later, buyer_intelligence reads `recent_scores` and sees that lead
- deal_support sees updated `pipeline_by_stage` from lead_qualification

Without shared state, each workflow is isolated — identical to the current flat model.

### 9.3 Operators Don't Run 24/7

An Operator is **not** a long-running process. It is:
- A config (identity, triggers, workflows, crews)
- A state schema (persisted in Postgres)
- A set of Temporal schedules (fire on cron/event)

Between activations, cost = $0. The "persistence" comes from durable state, not from running processes.

### 9.4 CrewAI Is Optional, Not Default

The original "3-layer stack" implied every node uses CrewAI. In practice:

| What you might think | What's actually true |
|---------------------|---------------------|
| Every node needs CrewAI | ~70% of nodes are pure logic or direct Claude calls |
| CrewAI Agent = Operator Agent | CrewAI Agent = temporary worker inside a node |
| 1 agent + 1 task Crew adds value | It's just a wrapper around `anthropic.messages.create()` |
| More agents = better | More agents = more tokens + latency. Use only when needed |

**Use CrewAI when:**
- 2+ roles need to collaborate (researcher → strategist → writer)
- Hierarchical delegation (manager distributes subtasks)
- Per-agent tool binding (one agent searches web, another queries CRM)

**Use direct Claude API when:**
- Single prompt → single output
- No role specialization needed
- Speed/cost matters (direct call is faster than CrewAI overhead)

**Use pure logic when:**
- Routing, formatting, data transformation
- API writes (CRM, Slack)
- Deterministic decisions (score thresholds)

The stack is now **Temporal + LangGraph + (Python | Anthropic SDK | CrewAI)** per node.

### 9.5 Configuration Drives Everything

No operator logic is hardcoded. The config declares:
- Which triggers to listen to
- Which workflows to run
- Which node types to use (logic, llm, crew)
- Which nodes need human approval

Adding a new trigger to an Operator = adding 3 lines of YAML + implementing the workflow graph.

---

## 10. Cost Model

### Per-Activation Cost

| Component | Cost Driver | Typical |
|-----------|-----------|---------|
| Temporal | Per-workflow execution | ~$0.001 |
| LangGraph | Negligible (in-process) | ~$0 |
| Logic nodes | Zero (no LLM) | $0 |
| LLM nodes | Per-token, single call | $0.001-0.01 per node |
| Crew nodes | Per-token, multi-call | $0.01-0.05 per node |
| Postgres | Storage + queries | ~$0.001 |
| LangFuse | Per-trace | ~$0.001 |

**Dominant cost: Claude API tokens.** Crew nodes cost 3-5x more than LLM nodes (multiple agent calls). This is why most nodes should be logic or direct LLM — reserve crews for high-value multi-agent tasks.

### Estimated Monthly Cost (All 5 Operators)

| Operator | Activations/Month | Avg Tokens/Activation | Model Mix | Est. Cost |
|----------|-------------------|----------------------|-----------|-----------|
| Revenue Ops | ~200 | ~3,000 | Haiku + Sonnet | $50-150 |
| Content Engine | ~100 | ~5,000 | Sonnet | $100-300 |
| Customer Success | ~150 | ~2,000 | Haiku + Sonnet | $30-100 |
| Market Intel | ~120 | ~3,000 | Haiku + Sonnet | $40-120 |
| Company Intel | ~20 | ~2,000 | Haiku | $5-15 |
| **Total** | **~590** | | | **$225-685** |

This is significantly lower than the original estimate ($2,000-5,000/mo) because:
1. Model mix: Haiku for fast/cheap tasks, Sonnet for deep analysis
2. Not all agents run daily (some are weekly, event-driven, or on-demand)
3. Operators share state instead of duplicating work

---

## 11. Glossary

| Term | Definition |
|------|-----------|
| **Operator** | A persistent unit with identity, state, triggers, and workflows |
| **Trigger** | A Temporal schedule, webhook, event, or on-demand entry point |
| **Workflow** | A LangGraph StateGraph — multi-step execution with checkpointing |
| **Node** | One step in a workflow — implemented as logic, LLM call, or CrewAI crew |
| **Logic node** | Pure Python function — no LLM call (routing, formatting, API writes) |
| **LLM node** | Direct `anthropic.messages.create()` call — single prompt, single output |
| **Crew node** | CrewAI multi-agent collaboration — 2+ agents working together |
| **Agent** | A temporary CrewAI worker with role/goal/backstory — exists only inside a crew node |
| **Crew** | A CrewAI team of agents assembled for one crew node execution |
| **Activation** | One execution of an Operator (trigger fires → workflow runs → state updates) |
| **HITL** | Human-in-the-loop — workflow pauses at designated nodes for human approval |
| **Durable workflow** | A multi-day workflow using Temporal sleep (e.g., nurture sequence) |

---

## 12. Related Documents

- `OPERATOR-PATTERN.md` — Concept discovery document (how the pattern emerged)
- `DESIGN.md` — Original 3-layer architecture + 3 design workflows
- `PROGRESS.md` — Project status (98 tests, 20 agents → 5 operators)
- `v3/docs/THESIS.md` — "Cognition is becoming infrastructure"
- `operators/company_intel.py` — First Operator implementation (validates full chain)

---

*Created: 2026-02-16*
