# Operator Pattern — Design Document

> Date: 2026-02-16
> Status: Validated (first Operator built + deployed)
> Context: Emerged from designing the smoke test for the 3-layer stack

---

## The Problem

V3 built 20 AI agents across 3 layers (Temporal + LangGraph + CrewAI). But the architecture had a naming and structural confusion:

```yaml
# agents.yaml — flat, 1:1:1 mapping
s1:
  name: Lead Qualification
  trigger: webhook
  # one agent = one trigger = one crew
```

This breaks when you need a **persistent role** like a CRO (Chief Revenue Officer) that:
- Has multiple triggers (daily briefing, weekly forecast, deal alerts)
- Maintains persistent memory across all activations
- Assembles different agent teams depending on the situation
- Exists permanently in the org chart

The word "agent" was being used for two completely different things:
1. A **temporary worker** assembled to do a task (CrewAI Agent)
2. A **permanent role** with identity, memory, and triggers

---

## The Distinction

| Concept | What it is | Lifecycle | Example |
|---------|-----------|-----------|---------|
| **Agent** (CrewAI) | A temporary worker with a role, goal, backstory | Created → does task → dissolved | "Company Research Analyst" |
| **Operator** (new) | A persistent unit with identity, state, triggers | Always exists, assembles agents as needed | "Revenue Operations" |

**Key insight:** An Operator is not an agent. An Operator *assembles* agents.

Analogy:
- Agent = contractor hired for a specific job
- Operator = a permanent position/workstation in the org — the desk is always there, people (agents) come and go

---

## Operator Definition

An Operator has 5 components:

```
┌─────────────────────────────────────────┐
│  Operator                                │
│                                         │
│  1. Identity — who is this              │
│  2. State — what it remembers           │
│  3. Triggers — when it wakes up         │
│  4. Workflows — what steps to follow    │
│  5. Crew strategies — which agents      │
└─────────────────────────────────────────┘
```

### 1. Identity

```yaml
operator:
  id: cro
  name: "Revenue Operations"
  owner: "VP Sales"
  output_channels: ["slack:#revenue"]
```

### 2. State (LangGraph + Postgres)

Persistent memory that survives across all activations:

```python
class CROState(TypedDict):
    pipeline_total: float
    pipeline_by_stage: dict
    forecast_q2: float
    deals_at_risk: list[dict]
    recent_decisions: list[dict]
    weekly_summary: str
```

Every trigger reads the same state. Every execution updates it. This is the Operator's "memory."

### 3. Triggers (Temporal)

Multiple triggers, each mapped to a workflow:

```yaml
triggers:
  - type: cron
    schedule: "0 8 * * *"
    workflow: daily_briefing
  - type: cron
    schedule: "0 9 * * 1"
    workflow: weekly_forecast
  - type: event
    source: hubspot:deal_changed
    workflow: deal_alert
  - type: on_demand
    workflow: query
```

### 4. Workflows (LangGraph)

Each trigger runs a different workflow (LangGraph graph). All workflows share the same state:

```
daily_briefing:  read_state → pull_data → analyze → write_briefing → send
weekly_forecast: read_state → pull_data → forecast → strategize → report
deal_alert:      read_state → assess_severity → analyze → alert_or_log
query:           read_state → understand_question → reason → respond
```

### 5. Crew Strategies (CrewAI)

Different triggers assemble different agent teams:

```yaml
crew_strategies:
  daily_briefing:
    agents: [Pipeline Analyst, Brief Writer]
    model: claude-haiku   # fast + cheap
    process: sequential

  weekly_forecast:
    agents: [Revenue Forecaster, Sales Strategist, Report Writer]
    model: claude-sonnet   # deep analysis
    process: hierarchical
    knowledge: [deal_history, market_data]
    memory: true

  deal_alert:
    agents: [Deal Forensics Analyst]
    model: claude-sonnet
    tools: [hubspot, slack_search]
```

---

## How "Persistent" Actually Works

A common misconception: "persistent agent" = a process running 24/7.

Reality: **persistent = durable state + scheduled triggers.**

| What you think | What actually happens |
|---------------|----------------------|
| Agent runs 24/7 | Temporal scheduler wakes it on cron/event |
| Agent is always thinking | Only thinks when triggered. Cost = 0 between triggers |
| Agent remembers everything | LangGraph state in Postgres, loaded on each activation |
| Agent acts proactively | Cron + webhook triggers = "proactive" behavior |
| Agent has judgment | CrewAI + accumulated state + knowledge = informed judgment |

This is exactly how a real CRO works — they don't stare at a screen 24/7. They check data in the morning, have a weekly meeting, get called when a deal goes sideways, and answer questions when asked. Between these events, their "memory" persists.

---

## Architecture Mapping

How each Operator component maps to the 3-layer stack:

```
Operator Component    →  Technology Layer
─────────────────────────────────────────
Identity              →  Config (YAML)
State                 →  LangGraph State + Postgres checkpointer
Triggers              →  Temporal schedules + webhooks + signals
Workflows             →  LangGraph graphs (nodes + edges)
Crew strategies       →  CrewAI (Agents + Tasks + Crews)
AI execution          →  Claude API (via CrewAI)
```

Full chain when a trigger fires:

```
Temporal (trigger fires)
  → Temporal Workflow (durable execution envelope)
    → Temporal Activity (retryable unit of work)
      → LangGraph Graph (multi-step workflow with state)
        → CrewAI Crew (assembled agent team)
          → Claude API (actual AI reasoning)
        → State updated in Postgres
      → Activity returns result
    → Workflow logs completion
  → Next trigger waits
```

---

## First Implementation: Company Intel Operator

The first Operator built as a smoke test for the full 3-layer chain:

```yaml
operator:
  id: company_intel
  name: "Company Intelligence"
  trigger: on_demand
  workflow:
    nodes:
      1. research  → CrewAI: Research Analyst → Claude
      2. analyze   → CrewAI: Strategic Analyst → Claude
      3. decide    → Pure logic: determine prospect_quality
      4. report    → Pure logic: format output
    edges: research → analyze → decide → report
```

Files:
- `operators/company_intel.py` — LangGraph graph + CrewAI crew factories
- `temporal/activities/company_intel_activity.py` — Temporal activity (bridge)
- `temporal/workflows/company_intel_workflow.py` — Temporal workflow (trigger)
- `smoke_e2e.py` — trigger script

This validates: Temporal → LangGraph → CrewAI → Claude works end-to-end.

---

## Current vs Target Architecture

### Current (V3 Phase 6)

```
agents.yaml (flat: 1 agent = 1 trigger = 1 crew)
    ↓
main.py → build_system() (config → crews)
    ↓
temporal/worker.py (activities)
```

20 agents, but no concept of persistent roles. Each "agent" is actually a standalone task.

### Target (Operator Pattern)

```
operators.yaml (rich: 1 operator = N triggers + shared state + M crews)
    ↓
OperatorRuntime.register() (parse config → register schedules + state + crews)
    ↓
temporal/worker.py (workflows + activities)
```

Fewer operators (maybe 5-8), each with multiple triggers and workflows. Agents are assembled dynamically by operators.

### Migration Path

The 20 existing agents can be grouped into operators:

| Operator | Current Agents | Triggers |
|----------|---------------|----------|
| Revenue Operations | S1 (Lead Qual), S2 (Outreach), S3 (Engagement), S4 (Pipeline), S5 (Nurture) | webhook:new_lead, cron:daily, cron:weekly, event:deal_changed |
| Content Engine | M1 (Segment), M2 (Brief), M3 (Content Gen), M4 (Repurpose), M5 (Distribution), M6 (Analytics) | cron:weekly, event:content_published |
| Customer Success | C1-C5 | event:customer_signal, cron:daily |
| Market Intelligence | R1-R4 | cron:weekly, on_demand |

---

## CrewAI Capabilities Reference

For context on what's possible at the agent layer:

### Multi-Agent Crews

```python
Crew(
    agents=[researcher, strategist, writer],
    tasks=[research_task, strategy_task, brief_task],
    process=Process.sequential,      # pipeline: A → B → C
    # or Process.hierarchical,       # manager delegates dynamically
)
```

### Task Chaining

```python
strategy_task = Task(
    description="Develop approach based on research",
    agent=strategist,
    context=[research_task],  # receives researcher's output
)
```

### Tools

```python
Agent(
    role="Research Analyst",
    tools=[
        SerperDevTool(),        # web search
        WebsiteSearchTool(),    # scrape websites
        HubSpotLookupTool(),    # CRM queries
    ],
)
```

### Knowledge (RAG)

```python
Crew(
    knowledge_sources=[
        TextFileKnowledgeSource(file_paths=["docs/*.md"]),
        PDFKnowledgeSource(file_paths=["sales/*.pdf"]),
    ],
)
```

### Memory

```python
Crew(
    memory=True,  # short-term + long-term + entity memory
)
```

### Hierarchical Mode

```python
Crew(
    process=Process.hierarchical,
    manager_llm="anthropic/claude-sonnet-4-5-20250929",
    # Auto-creates a manager agent that delegates to workers
)
```

---

## Open Questions

1. **Operator config format** — YAML? Python dataclass? Both (YAML parsed into dataclass)?
2. **State schema evolution** — How to migrate state when the schema changes?
3. **Cross-operator communication** — Can operators trigger each other? (e.g., Revenue Ops escalates to Customer Success)
4. **Human-in-the-loop** — How does an Operator pause for human approval mid-workflow?
5. **Observability** — LangFuse tracing at which level? Per-operator? Per-node? Per-agent?

---

## Related Documents

- `DESIGN.md` — Original 3-layer architecture + 3 design workflows
- `PROGRESS.md` — Project status (98 tests, 20 agents, 3 workflows)
- `v3/docs/THESIS.md` — "Cognition is becoming infrastructure"
- `operators/company_intel.py` — First Operator implementation

---

*Created: 2026-02-16*
