# Vibe AI Ops - Progress Tracker

> Started: 2026-02-15
> Status: **Operator pattern implemented. CrewAI removed. 116 tests passing.**
> Stack: Temporal + LangGraph + Anthropic SDK (no CrewAI)

---

## Architecture

2-layer stack: **Temporal** (scheduling) + **LangGraph** (stateful workflows) + **Anthropic SDK** (Claude API calls)

**Operator pattern:** 5 persistent operators with identity, shared state, triggers, and config-driven workflows. See `docs/OPERATOR-DESIGN.md`.

## Quick Stats

| Metric | Count |
|--------|-------|
| Operators | 5 |
| Workflows | 22 |
| Triggers | 22 |
| Total nodes | 80 |
| LLM nodes | 49 |
| Logic nodes | 31 |
| Tests passing | 116 |

---

## 5 Operators

| Operator | Workflows | Nodes | Triggers | Status |
|----------|-----------|-------|----------|--------|
| Company Intel | 1 | 4 | 1 | DONE |
| Revenue Ops | 5 | 18 | 5 | DONE |
| Content Engine | 6 | 18 | 6 | DONE |
| Customer Success | 6 | 18 | 6 | DONE |
| Market Intelligence | 4 | 13 | 4 | DONE |

---

## What Changed (from 20-agent model)

### Removed
- `crews/` directory (entire) — replaced by `operators/*/workflows/`
- `graphs/` directory (entire) — absorbed into `operators/*/workflows/`
- `crewai` + `crewai-tools` dependencies
- `CREW_REGISTRY` in main.py
- `config/agents.yaml` as primary config (kept for backward compat with schedules)

### Added
- `operators/base.py` — `call_claude()` (replaces all crew.kickoff() calls) + `OperatorRuntime`
- `config/operators.yaml` — 5 operators, 22 workflows, 80 nodes
- `operators/company_intel/` — 1 workflow, 4 nodes
- `operators/revenue_ops/` — 5 workflows, 18 nodes (migrated from s1, s3, s5 + 2 new)
- `operators/content_engine/` — 6 workflows, 18 nodes
- `operators/customer_success/` — 6 workflows, 18 nodes
- `operators/market_intel/` — 4 workflows, 13 nodes
- `temporal/activities/operator_activity.py` — generic activity for any operator
- `shared/models.py` — OperatorConfig, WorkflowConfig, NodeConfig, NodeType

### Rewritten
- `main.py` — loads operators.yaml, creates OperatorRuntime, registers 22 workflow factories
- `cli.py` — `list` shows operators, `info <id>` shows details, `summary` shows node counts
- `temporal/worker.py` — registers run_operator activity
- `temporal/workflows/nurture_workflow.py` — imports from new operator path

---

## File Index

```
src/vibe_ai_ops/
├── main.py                             # build_system() → OperatorRuntime + 22 workflows
├── cli.py                              # list, info, summary (operator-based)
├── operators/
│   ├── base.py                         # call_claude() + OperatorRuntime
│   ├── company_intel/
│   │   ├── state.py                    # CompanyIntelState
│   │   └── workflows/research.py       # 4 nodes: research→analyze→decide→report
│   ├── revenue_ops/
│   │   ├── state.py                    # RevenueOpsState (shared across 5 workflows)
│   │   └── workflows/
│   │       ├── lead_qualification.py   # 4 nodes: enrich→score→route→update_crm
│   │       ├── engagement.py           # 4 nodes: research→generate→personalize→format
│   │       ├── nurture_sequence.py     # 7 nodes with conditional routing
│   │       ├── buyer_intelligence.py   # 3 nodes: scan→analyze→brief
│   │       └── deal_support.py         # 3 nodes: pull_deals→assess_risk→generate_actions
│   ├── content_engine/
│   │   ├── state.py
│   │   └── workflows/ (6 workflows, 18 nodes)
│   ├── customer_success/
│   │   ├── state.py
│   │   └── workflows/ (6 workflows, 18 nodes)
│   └── market_intel/
│       ├── state.py
│       └── workflows/ (4 workflows, 13 nodes)
├── shared/                             # Infrastructure (unchanged)
│   ├── models.py                       # + OperatorConfig, WorkflowConfig, NodeConfig
│   ├── config.py                       # + load_operator_configs()
│   ├── claude_client.py, hubspot_client.py, slack_client.py
│   ├── logger.py, tracing.py
├── temporal/
│   ├── worker.py, schedules.py
│   ├── activities/
│   │   ├── company_intel_activity.py
│   │   └── operator_activity.py        # generic: run_operator()
│   └── workflows/
│       ├── company_intel_workflow.py
│       └── nurture_workflow.py          # durable multi-day
└── config/
    ├── operators.yaml                   # 5 operators, 22 workflows, 80 nodes
    ├── agents.yaml                      # legacy (used for Temporal schedules)
    └── prompts/                         # 20 system prompts

smoke_e2e.py                            # e2e: Temporal → LangGraph → Claude API
```

---

## Remaining: T25-T26

| Task | Description | Requires |
|------|-------------|----------|
| T25 | Smoke test with real APIs | `.env` with API keys + `docker compose up` |
| T26 | Go live | Temporal Cloud or local Docker, real HubSpot/Slack |

---

*Last updated: 2026-02-16*
