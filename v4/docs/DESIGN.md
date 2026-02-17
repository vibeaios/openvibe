# OpenVibe — Architecture & Design

> Current implementation status. Reflects what's actually built and running.
> Last updated: 2026-02-16
> Status: Implemented (5 operators, 22 workflows, 80 nodes, 116 tests)

---

## Architecture Overview

2-layer stack: **Temporal** (scheduling) + **LangGraph** (stateful workflows) + **Anthropic SDK** (Claude API calls).

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Scheduler (Temporal)                          │
│  - Durable execution, multi-day workflows               │
│  - Auto-retry, timeout handling                         │
│  - Webhook + cron + event triggers                      │
│  - Dashboard for visibility                             │
└─────────────────────┬───────────────────────────────────┘
                      │ triggers
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Workflow Engine (LangGraph)                   │
│  - State machine + Postgres checkpointer               │
│  - Branching, looping, conditional logic                │
│  - Human-in-the-loop (pause/resume)                    │
│  - Error recovery, retry paths                          │
└─────────────────────┬───────────────────────────────────┘
                      │ executes
                      ▼
┌─────────────────────────────────────────────────────────┐
│  LLM Calls (Anthropic SDK)                              │
│  - Direct Claude API via call_claude()                  │
│  - Model selection per node (haiku/sonnet)              │
│  - Cost tracking via ClaudeClient                       │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.13 | LangGraph/Anthropic SDK ecosystem is Python-native |
| Scheduler | Temporal | Durable execution, production-grade |
| Workflow Engine | LangGraph | State persistence via Postgres checkpointer, HITL |
| LLM | Anthropic SDK | Direct Claude API calls via `call_claude()` wrapper |
| Models | Haiku 4.5 (default), Sonnet 4.5 (scoring/analysis) | Cost vs quality tradeoff per node |
| Observability | LangSmith | Native LangGraph integration |
| CRM | HubSpot API | Leads, contacts, enrichment |
| Notifications | Slack API | Alerts, reports, human escalation |
| Database | PostgreSQL | LangGraph checkpointer + workflow state |

---

## Operator Pattern

The system is organized around **operators** — persistent roles with identity, state, triggers, and workflows. Each operator owns a business domain.

### Concept Hierarchy

```
Operator (persistent role)
├── State (TypedDict, shared across workflows)
├── Triggers (webhook, cron, event, on_demand)
└── Workflows (LangGraph state machines)
    └── Nodes (logic or llm)
```

### Node Types

| Type | What | Example |
|------|------|---------|
| `logic` | Pure Python, no LLM | Route lead by score, format report |
| `llm` | Single `call_claude()` call | Research company, score lead, generate content |

All LLM nodes use `call_claude()` from `operators/base.py` — a thin wrapper around `ClaudeClient` that tracks tokens and cost.

### call_claude()

```python
def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> ClaudeResponse:
```

This single function replaces all previous crew.kickoff() calls.

---

## 5 Operators

| Operator | Workflows | Nodes | Triggers | Owner |
|----------|-----------|-------|----------|-------|
| Company Intel | 1 | 4 | 1 (on_demand) | Sales / Strategy |
| Revenue Ops | 5 | 18 | 5 (webhook, event, cron) | VP Sales |
| Content Engine | 6 | 18 | 6 (cron, event) | VP Marketing |
| Customer Success | 6 | 18 | 6 (cron, event, webhook) | VP CS |
| Market Intelligence | 4 | 13 | 4 (cron, on_demand) | VP Sales |
| **Total** | **22** | **80** | **22** | |

### Node Distribution

| Type | Count | % |
|------|-------|---|
| LLM | 49 | 61% |
| Logic | 31 | 39% |
| **Total** | **80** | 100% |

---

## Operator Details

### Company Intel (Smoke Test)

```
Trigger: on_demand query
Workflow: research
  research [llm] → analyze [llm] → decide [logic] → report [logic]
```

### Revenue Ops (Most Complex)

```
Trigger: webhook (new HubSpot lead)
  lead_qualification: enrich [llm] → score [llm] → route [logic] → update_crm [logic]

Trigger: event (lead qualified)
  engagement: research_buyer [llm] → generate_sequence [llm] → personalize [llm] → format [logic]

Trigger: event (lead nurture)
  nurture_sequence: 7 nodes with conditional routing, multi-day durable

Trigger: cron (7am daily)
  buyer_intelligence: scan [llm] → analyze [llm] → brief [logic]

Trigger: cron (7am weekdays)
  deal_support: pull_deals [llm] → assess_risk [llm] → generate_actions [logic]
```

### Content Engine

```
6 workflows: segment_research, message_testing, content_generation,
             repurposing, distribution, journey_optimization
18 nodes total, triggered by cron and events
```

### Customer Success

```
6 workflows: onboarding, success_advisory, health_monitoring,
             expansion_scan, customer_voice, urgent_review
18 nodes total, triggered by cron, events, and webhooks
```

### Market Intelligence

```
4 workflows: funnel_monitor, deal_risk_forecast,
             conversation_analysis, nl_query
13 nodes total, triggered by cron and on_demand
```

---

## OperatorRuntime

Central runtime that loads config, registers graph factories, and dispatches activations.

```python
# main.py — build_system()
runtime = OperatorRuntime(config_path="config/operators.yaml")
runtime.load(enabled_only=True)

# Register all 22 workflow factories
for (op_id, wf_id), factory in _WORKFLOW_REGISTRY.items():
    runtime.register_workflow(op_id, wf_id, factory)

# Activate: trigger → workflow → run graph
result = runtime.activate("revenue_ops", "new_lead", input_data)
```

### Configuration

All operators defined in `config/operators.yaml`:

```yaml
operators:
  - id: company_intel
    name: "Company Intelligence"
    owner: "Sales / Strategy"
    triggers:
      - id: query
        type: on_demand
        workflow: research
    workflows:
      - id: research
        nodes:
          - { id: research, type: llm, model: claude-haiku-4-5-20251001 }
          - { id: analyze, type: llm, model: claude-haiku-4-5-20251001 }
          - { id: decide, type: logic }
          - { id: report, type: logic }
```

### Data Models

```python
# shared/models.py
class OperatorConfig(BaseModel):
    id: str
    name: str
    owner: str
    triggers: list[OperatorTriggerConfig]
    workflows: list[WorkflowConfig]
    enabled: bool = True

class NodeType(str, Enum):
    LOGIC = "logic"
    LLM = "llm"
```

---

## File Structure

```
v4/vibe-ai-adoption/
├── PROGRESS.md                             # Status tracker
├── pyproject.toml
├── docker-compose.yml
├── smoke_e2e.py                            # E2E: Temporal → LangGraph → Claude API
├── src/vibe_ai_ops/
│   ├── main.py                             # build_system() → OperatorRuntime + 22 workflows
│   ├── cli.py                              # list, info, summary
│   ├── operators/
│   │   ├── base.py                         # call_claude() + OperatorRuntime
│   │   ├── company_intel/
│   │   │   ├── state.py
│   │   │   └── workflows/research.py
│   │   ├── revenue_ops/
│   │   │   ├── state.py
│   │   │   └── workflows/ (5 files)
│   │   ├── content_engine/
│   │   │   ├── state.py
│   │   │   └── workflows/ (6 files)
│   │   ├── customer_success/
│   │   │   ├── state.py
│   │   │   └── workflows/ (6 files)
│   │   └── market_intel/
│   │       ├── state.py
│   │       └── workflows/ (4 files)
│   ├── shared/
│   │   ├── models.py                       # OperatorConfig, WorkflowConfig, NodeConfig
│   │   ├── config.py                       # YAML config + prompt loader
│   │   ├── claude_client.py                # ClaudeClient (token/cost tracking)
│   │   ├── hubspot_client.py
│   │   ├── slack_client.py
│   │   ├── logger.py                       # SQLite run logger
│   │   └── tracing.py                      # LangSmith
│   ├── temporal/
│   │   ├── worker.py
│   │   ├── schedules.py
│   │   ├── activities/operator_activity.py  # Generic: run_operator()
│   │   └── workflows/nurture_workflow.py    # Durable multi-day
│   └── config/
│       ├── operators.yaml                   # 5 operators, 22 workflows, 80 nodes
│       ├── agents.yaml                      # Legacy (Temporal schedules only)
│       └── prompts/                         # 20 system prompts
├── tests/                                   # 116 tests, mirrors src structure
└── docs/                                    # Moved to v4/docs/
```

---

## Infrastructure

### Required for Development

- Python 3.13 + venv
- Docker (for Temporal + Postgres)

### Required for Production (T25-T26)

| Component | Requirement |
|-----------|-------------|
| Temporal | Docker Compose or Temporal Cloud |
| PostgreSQL | LangGraph checkpointer |
| `.env` | `ANTHROPIC_API_KEY`, `HUBSPOT_API_KEY`, `SLACK_BOT_TOKEN` |

### Estimated Monthly Cost

| Item | Cost |
|------|------|
| Temporal Cloud | $200-500 |
| Claude API | $225-685 (all 5 operators) |
| LangSmith | $400 |
| PostgreSQL (managed) | $100 |
| **Total** | **$925-1,685** |

---

## Remaining Work

| Task | Description | Requires |
|------|-------------|----------|
| T25 | Smoke test with real APIs | `.env` with API keys + `docker compose up` |
| T26 | Go live | Temporal Cloud or local Docker, real HubSpot/Slack |

### Proposed (Not Yet Built)

See `v4/docs/proposed/`:
- **Cognitive Architecture** — Agent identity, 5-level memory, decision authority
- **Inter-Operator Comms** — NATS event bus + KV store for operator coordination
- **Operator SDK** — Declarative framework: 7 decorators, HTTP API, pluggable providers

---

*Source of truth for implementation status: `v4/vibe-ai-adoption/PROGRESS.md`*
