# Vibe AI Adoption - Design Document

> **Date:** 2026-02-15
> **Status:** Approved
> **Goal:** Validate Temporal + LangGraph + CrewAI 3-layer architecture by deeply verifying 3 workflows

---

## Architecture

### 3-Layer Stack

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
│  Layer 3: Agent Roles (CrewAI)                          │
│  - Role definition (role, goal, backstory)              │
│  - Tool binding (CRM API, research tools, etc.)         │
│  - Team collaboration (delegation, shared context)      │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python | LangGraph/CrewAI ecosystem is Python-native |
| Scheduler | Temporal Cloud | Durable execution, production-grade, avoid self-hosted ops |
| Workflow Engine | LangGraph | State persistence via Postgres checkpointer, HITL, LangChain ecosystem |
| Agent Framework | CrewAI | Fast role-based agent definition, low learning curve |
| LLM | Claude API (Sonnet 4.5) | Strong reasoning, long context |
| Observability | LangSmith | Native LangGraph integration, trace every LLM call |
| CRM | HubSpot API | Leads, contacts, enrichment |
| Notifications | Slack API | Alerts, reports, human escalation |
| Database | PostgreSQL | LangGraph checkpointer + workflow state |

### Infrastructure Cost (Monthly)

| Item | Cost |
|------|------|
| Temporal Cloud | $200-500 |
| Claude API | $2,000-5,000 |
| LangSmith | $400 |
| PostgreSQL (managed) | $100 |
| **Total** | **$3,000-6,000** |

---

## 3 Workflows to Validate

Each workflow tests a different architectural pattern:

### Workflow 1: Lead Qualification

**Pattern:** Webhook trigger → Linear pipeline → Single agent

```
Temporal: webhook on new HubSpot lead
    ↓
LangGraph Workflow:
    [Node 1] Data enrichment (company, role, tech stack)
    [Node 2] CrewAI agent evaluation (fit + intent + urgency)
    [Node 3] Scoring (0-100)
    [Conditional]
        ├── Score >= 80 → Route to Sales (high priority)
        ├── Score 50-79 → Enter Nurture sequence
        └── Score < 50 → Send educational content
    [Node 4] Update CRM + log
```

**CrewAI Agent:**
- Role: Lead Qualification Specialist
- Goal: Assess lead quality and intent quickly and accurately
- Tools: HubSpot enrichment, company research, scoring model

**Success Metrics:**
| Metric | Baseline | Target |
|--------|----------|--------|
| Qualification accuracy | Human benchmark | >= 85% match |
| Processing time | - | < 2 min/lead |
| Coverage | 20% (manual) | 100% |

**Validates:** Core plumbing works. Temporal triggers LangGraph, CrewAI executes, CRM updates.

---

### Workflow 2: Content Pipeline

**Pattern:** Cron trigger → Multi-node → 3 agents chained

```
Temporal: cron every Monday 9am
    ↓
LangGraph Workflow:
    [Node 1] Segment Research Agent → Identify top segments this week
    [Node 2] Content Generation Agent → 2 pieces per segment
    [Node 3] Content Repurposing Agent → Each piece → 10 formats
    [Node 4] Publish queue + scheduling
    ↓
Output: 200 content pieces scheduled
```

**CrewAI Agents:**
1. Segment Research Agent - Analyze market data, cluster customers, prioritize segments
2. Content Generation Agent - Blog posts, case studies, whitepapers per segment
3. Content Repurposing Agent - 1 piece → 10 formats (email, social, video script, etc.)

**Success Metrics:**
| Metric | Baseline | Target |
|--------|----------|--------|
| Content volume | 2/week | 20/week (10x) |
| Segments covered | 1 | 10 |
| Formats per piece | 1 | 10 |

**Validates:** Multi-agent orchestration. CrewAI team delegation. LangGraph passes output between nodes.

---

### Workflow 3: Nurture Sequence

**Pattern:** Event trigger → Long-running durable → Checkpoints + HITL

```
Temporal: lead enters nurture (from Lead Qual score 50-79)
    ↓
LangGraph Workflow (14-day durable):
    Day 1:
        ├── Send welcome email (personalized by segment)
        └── [Checkpoint] Wait for engagement signal

    Day 3:
        ├── Check engagement (opened? clicked?)
        ├── if opened → Send case study
        └── if not → Change subject line, resend
        └── [Checkpoint]

    Day 7:
        ├── Check cumulative engagement
        ├── if high → Upgrade to Sales (human handoff)
        └── if low → Continue nurture
        └── [Checkpoint]

    Day 14:
        ├── Final push
        └── if no response → Move to long-term nurture

    [Human-in-the-loop]:
        - Any time lead replies → Pause workflow
        - Wait for Sales confirmation → Resume or transfer to human
```

**CrewAI Agent:**
- Role: Nurture Specialist
- Goal: Warm up leads with personalized, behavior-driven outreach
- Tools: Email API, engagement tracker, CRM updater

**Success Metrics:**
| Metric | Baseline | Target |
|--------|----------|--------|
| Follow-up rate | 20% | 100% |
| Nurture → SQL rate | 5% | 15% |
| Avg response time | 24h | 1h |

**Validates:** The hardest pattern. Multi-day durable execution. Temporal keeps state across days. LangGraph checkpoints survive restarts. HITL pause/resume works. If this works, everything else is configuration.

---

## Build Sequence (8 Weeks)

```
Week 1-2: Phase 0 - Infrastructure
  ├── Temporal Cloud setup + hello world worker
  ├── Python project: LangGraph + Postgres checkpointer
  ├── CrewAI integrated as LangGraph node
  ├── LangSmith tracing configured
  ├── HubSpot API wrapper (basic: leads, contacts)
  └── Acceptance: full chain observable in LangSmith

Week 3-4: Workflow 1 - Lead Qualification
  ├── CrewAI Lead Qualification Agent
  ├── LangGraph workflow (enrich → score → route → update)
  ├── Temporal webhook trigger
  ├── HubSpot integration (read + write)
  └── Benchmark vs human qualification

Week 5-6: Workflow 2 - Content Pipeline
  ├── 3 CrewAI agents (research + generate + repurpose)
  ├── LangGraph multi-node workflow
  ├── Temporal weekly cron
  └── Output validation: quality + volume

Week 7-8: Workflow 3 - Nurture Sequence
  ├── CrewAI Nurture Agent
  ├── LangGraph 14-day workflow with checkpoints + HITL
  ├── Temporal durable execution
  ├── Email integration
  └── Full end-to-end test
```

### Decision Points

| Checkpoint | Week | Criteria | Action |
|------------|------|----------|--------|
| Infra complete | 2 | Full chain works + observable | Continue or fix |
| Lead Qual validated | 4 | >= 85% accuracy | Continue or iterate |
| Content Pipeline works | 6 | Multi-agent chain produces output | Continue or fix |
| Nurture validated | 8 | HITL + durable execution works | Full architecture proven |

---

## Project Structure (Actual)

```
vibe-ai-adoption/
├── PROGRESS.md                     # Source of truth for status
├── pyproject.toml
├── docker-compose.yml
├── src/vibe_ai_ops/
│   ├── main.py                     # build_system() + CREW_REGISTRY (20 agents)
│   ├── cli.py                      # list, info, summary
│   ├── shared/                     # Infrastructure clients
│   │   ├── models.py               # AgentConfig, AgentOutput, AgentRun
│   │   ├── config.py               # YAML config + prompt loader
│   │   ├── claude_client.py, hubspot_client.py, slack_client.py
│   │   ├── logger.py               # SQLite run logger
│   │   └── tracing.py              # LangSmith
│   ├── temporal/                   # Scheduling layer
│   │   ├── worker.py, schedules.py
│   │   ├── activities/agent_activity.py
│   │   └── workflows/nurture_workflow.py
│   ├── graphs/                     # Workflow layer (LangGraph)
│   │   ├── checkpointer.py
│   │   ├── marketing/
│   │   │   ├── m3_content_generation.py
│   │   │   └── content_pipeline.py  # M1→M3→M4 unified
│   │   └── sales/
│   │       ├── s1_lead_qualification.py
│   │       ├── s3_engagement.py
│   │       └── s5_nurture_sequence.py
│   ├── crews/                      # Agent layer (CrewAI)
│   │   ├── base.py                 # create_crew_agent(), create_validation_crew()
│   │   ├── marketing/ (m3 + validation_agents M1,M2,M4,M5,M6)
│   │   ├── sales/ (s1, s3 + validation_agents S2,S4,S5)
│   │   ├── cs/validation_agents.py (C1-C5)
│   │   └── intelligence/validation_agents.py (R1-R4)
│   └── config/
│       ├── agents.yaml             # 20 agent definitions
│       └── prompts/                # 20 system prompts
├── tests/                          # 98 tests, mirrors src structure
└── docs/
    ├── DESIGN.md                   # This file
    └── plans/
```

---

## What This Proves

If all 3 workflows work:

1. **Temporal** handles scheduling reliably (webhook, cron, long-running)
2. **LangGraph** manages workflow state with checkpoints and HITL
3. **CrewAI** defines agents that produce quality output via Claude
4. **The 3-layer architecture scales** from simple (Lead Qual) to complex (Nurture)
5. **LangSmith** provides full observability across the stack

This validates the foundation for all 20+ agents defined in the roadmap.

---

*Source of truth: `vibe-ai-adoption/PROGRESS.md` (status) + this file (design)*
