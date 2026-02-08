# OpenVibe

> **Updated 2026-02-08:** Terminology changed from Fork/Resolve to Deep Dive/Publish per PRODUCT-CORE-REFRAME.md

> A Deep Dive Thread product for Human + AI agent collaboration

## Vision

A team collaboration platform to replace Slack, with the core innovation being the **Deep Dive** conversation model:
- **Deep Dive** — Start an AI-assisted exploration from any message point
- **Publish** — AI generates a structured result, and findings flow back to the main thread
- **Discard** — Archive explorations that don't need to be published

The core problem it solves: Someone on the team asks a question, another person copies it to an AI to research, pastes the result back, the result is too long, someone else copies it to another AI to digest, and context is continuously lost.

## Status

```
Phase 1: Research ────────── ✅ Complete (R1-R7 + SYNTHESIS)
Phase 1.5: Design Deep Dive ─ ✅ Complete (Architecture, UX, BDD)
Phase 2: MVP Implementation ─ 🔄 Next (8 weeks)
Phase 3: Dogfood ──────────── Pending
```

**Current entry point:** [`docs/INTENT.md`](docs/INTENT.md) — Project goals and roadmap

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Next.js 14)                       │
│              Discord-like layout + Fork Sidebar              │
└─────────────────────────────┬───────────────────────────────┘
                              │ tRPC + Supabase Realtime
┌─────────────────────────────▼───────────────────────────────┐
│                      Backend (tRPC)                          │
│               ~30 procedures, 10 tables                      │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
┌───────────▼───────────┐         ┌───────────▼───────────┐
│   Agent Runtime       │         │   Supabase            │
│   Claude SDK + MCP    │         │   Postgres + Realtime │
│   @Vibe, @Coder       │         │   Auth + Storage      │
└───────────────────────┘         └───────────────────────┘
```

## Key Design Decisions (from Research)

| Decision | Rationale |
|----------|-----------|
| **Deep Dive/Publish** (not Branch/Merge) | Simpler mental model, AI as thinking partner |
| **AI Deep Dive Quality = Critical Risk** | The entire model depends on AI being a good thinking partner and generating good dive results |
| **2 agents for MVP** | @Vibe (general + deep dive partner), @Coder (dev tasks) |
| **~$640-940/month** | Dogfood infrastructure cost (20 users) |
| **8-week sprint plan** | BDD specs, feature-by-feature implementation |

## Documentation

### Core Docs
| Doc | Purpose |
|-----|---------|
| [`docs/INTENT.md`](docs/INTENT.md) | Current goals, phase roadmap |
| [`docs/PRODUCT-REASONING.md`](docs/PRODUCT-REASONING.md) | Product thinking derivation |
| [`docs/FRAMEWORK-DIAGRAM.md`](docs/FRAMEWORK-DIAGRAM.md) | Visual architecture |

### Phase 1 Research (R1-R7)
| Doc | Question |
|-----|----------|
| [`R1-THREAD-MODEL.md`](docs/research/R1-THREAD-MODEL.md) | Deep Dive/Publish vs Git-like branching |
| [`R2-GENERATIVE-UI.md`](docs/research/R2-GENERATIVE-UI.md) | Config-driven UI for verticals |
| [`R3-AGENT-LIFECYCLE.md`](docs/research/R3-AGENT-LIFECYCLE.md) | Long-running task management |
| [`R4-CLAUDE-TEAMS.md`](docs/research/R4-CLAUDE-TEAMS.md) | Claude Code SDK integration |
| [`R5-CLI-BLEND-RISKS.md`](docs/research/R5-CLI-BLEND-RISKS.md) | CLI vs API architecture |
| [`R6-PRIVACY-HYBRID.md`](docs/research/R6-PRIVACY-HYBRID.md) | Privacy + hybrid deployment |
| [`R7-CONTEXT-UNIFICATION.md`](docs/research/R7-CONTEXT-UNIFICATION.md) | Cross-runtime context |
| [`SYNTHESIS.md`](docs/research/SYNTHESIS.md) | **Phase 1 consolidated conclusions** |
| [`COMPETITIVE-LANDSCAPE.md`](docs/research/COMPETITIVE-LANDSCAPE.md) | Competitive analysis |

### Phase 1.5 Deep Dive
| Doc | Content |
|-----|---------|
| [`SYSTEM-ARCHITECTURE.md`](docs/research/phase-1.5/SYSTEM-ARCHITECTURE.md) | Full infrastructure (dogfood vs scale) |
| [`THREAD-UX-PROPOSAL.md`](docs/research/phase-1.5/THREAD-UX-PROPOSAL.md) | Deep Dive/Publish UX design |
| [`AGENT-DEFINITION-MODEL.md`](docs/research/phase-1.5/AGENT-DEFINITION-MODEL.md) | Agent configuration model |
| [`BDD-IMPLEMENTATION-PLAN.md`](docs/research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md) | **8-week sprint plan + Gherkin specs** |
| [`FRONTEND-ARCHITECTURE.md`](docs/research/phase-1.5/FRONTEND-ARCHITECTURE.md) | Next.js + Zustand + tRPC |
| [`BACKEND-MINIMUM-SCOPE.md`](docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) | 10-table schema, ~30 procedures |
| [`RUNTIME-ARCHITECTURE.md`](docs/research/phase-1.5/RUNTIME-ARCHITECTURE.md) | Per-user agent runtime |
| [`ADMIN-CONFIGURABLE-UI.md`](docs/research/phase-1.5/ADMIN-CONFIGURABLE-UI.md) | Config-driven UI |
| [`HANDOFF-CONTEXT-THESIS.md`](docs/research/phase-1.5/HANDOFF-CONTEXT-THESIS.md) | Context handoff: 6 sub-question analysis |

### Original Module Designs (to be updated post-research)
| Module | Description | Status |
|--------|-------------|--------|
| [M1: Thread Engine](docs/design/M1-THREAD-ENGINE.md) | Fork/Resolve conversation core | 🔄 Needs update |
| [M2: Frontend](docs/design/M2-FRONTEND.md) | Real-time UI | 🔄 Superseded by Phase 1.5 |
| [M3: Agent Runtime](docs/design/M3-AGENT-RUNTIME.md) | Agent runtime | 🔄 Needs update |
| [M4: Team Memory](docs/design/M4-TEAM-MEMORY.md) | Shared memory | 📝 Draft |
| [M5: Orchestration](docs/design/M5-ORCHESTRATION.md) | Routing + coordination | 📝 Draft |
| [M6: Auth](docs/design/M6-AUTH.md) | Access control | 📝 Draft |

## Tech Stack

- **Frontend**: Next.js 14 + TailwindCSS + shadcn/ui + Zustand
- **API**: tRPC
- **Realtime**: Supabase Realtime
- **Database**: PostgreSQL (Supabase) + pgvector
- **Agent Runtime**: Claude SDK + MCP
- **Infra**: Fly.io (app) + Supabase (managed)

## Next Steps (Phase 2)

1. **Setup monorepo** — Nx workspace structure
2. **Implement Foundation Epic** — Auth, workspace creation (Week 1-2)
3. **Thread + Messaging Epic** — Core chat functionality (Week 3-4)
4. **Deep Dive/Publish Epic** — The differentiator (Week 5-6)
5. **Agent Integration Epic** — @Vibe, @Coder (Week 7-8)

See [`BDD-IMPLEMENTATION-PLAN.md`](docs/research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md) for detailed Gherkin specs.

## Dogfood Context

- **First users**: Vibe team (20 people)
- **Replacing**: Slack
- **Latency requirements**: ~500ms is sufficient (forum-style, no need for extreme real-time performance)
- **Cost budget**: ~$1,000-2,500/month (including LLM)

---

*Created: 2026-02-06*
*Updated: 2026-02-07 (Phase 1.5 complete)*
