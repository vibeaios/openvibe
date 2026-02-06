# OpenVibe - Current Intent

> This file defines the current working objectives. Read this at the start of every session.

---

## Roadmap

```
Phase 1: Research ──────── ✅ Complete (R1-R7 + SYNTHESIS)
Phase 1.5: Design Deep Dive ✅ Complete (Architecture, UX, BDD)
Phase 2: Implementation ─── 🔄 NOW (8 weeks)
Phase 3: Dogfood ────────── Pending
Phase 4+: ───────────────── TBD based on dogfood
```

| Phase | Input | Output | Status |
|-------|------|------|--------|
| **1. Research** | Existing design docs + external research | R1-R7 + SYNTHESIS.md | ✅ Done |
| **1.5. Design** | SYNTHESIS.md | Architecture, UX, BDD specs | ✅ Done |
| **2. Implementation** | Phase 1.5 docs | A runnable dogfood product | 🔄 Next |
| **3. Dogfood** | Runnable product | Real feedback + iteration direction | Pending |

---

## Current Goal

**Phase 2: Implementation (8 Weeks)**

Build the dogfood MVP based on Phase 1.5 designs.

### Sprint Plan

| Week | Epic | Key Deliverables |
|------|------|------------------|
| 1-2 | Foundation | Auth, Workspace, Channel CRUD |
| 3-4 | Thread + Messaging | Realtime messages, streaming |
| 5-6 | **Fork/Resolve** | Core differentiator, AI summary |
| 7-8 | Agent Integration | @Vibe, @Coder |

Detailed Gherkin specs: [`docs/research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md`](research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md)

### Critical Risk

**AI Summary Quality = Load-bearing wall**

The Fork/Resolve model depends on AI generating good resolution summaries. Weeks 5-6 are the validation point.

---

## Key Documents

### Phase 1.5 Design Docs (Implementation Reference)

| Doc | Purpose | Priority |
|-----|---------|----------|
| [`BDD-IMPLEMENTATION-PLAN.md`](research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md) | Sprint plan + Gherkin specs | **Must read** |
| [`BACKEND-MINIMUM-SCOPE.md`](research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) | 10 tables, ~30 tRPC procedures | **Must read** |
| [`FRONTEND-ARCHITECTURE.md`](research/phase-1.5/FRONTEND-ARCHITECTURE.md) | Next.js + Zustand structure | **Must read** |
| [`THREAD-UX-PROPOSAL.md`](research/phase-1.5/THREAD-UX-PROPOSAL.md) | Fork/Resolve UX design | **Must read** |
| [`AGENT-DEFINITION-MODEL.md`](research/phase-1.5/AGENT-DEFINITION-MODEL.md) | Agent config model | Week 7-8 |
| [`SYSTEM-ARCHITECTURE.md`](research/phase-1.5/SYSTEM-ARCHITECTURE.md) | Infrastructure diagrams | Reference |

### Phase 1 Research (Background Understanding)

| Doc | Purpose |
|-----|---------|
| [`SYNTHESIS.md`](research/SYNTHESIS.md) | Phase 1 comprehensive conclusions |
| [`R1-THREAD-MODEL.md`](research/R1-THREAD-MODEL.md) | Fork/Resolve derivation |
| [`R3-AGENT-LIFECYCLE.md`](research/R3-AGENT-LIFECYCLE.md) | Task lifecycle |
| [`R7-CONTEXT-UNIFICATION.md`](research/R7-CONTEXT-UNIFICATION.md) | Cross-runtime context (long-term) |

### Original Designs (Superseded by Phase 1.5)

`docs/design/M1-M6` -- Retained as historical reference; actual implementation follows Phase 1.5.

---

## Dogfood Context

- **First user**: Vibe team (20 people)
- **Replaces**: Slack
- **Latency requirement**: ~500ms is sufficient (forum mode)
- **Cost budget**: ~$640-940/month (infra) + ~$600-900/month (LLM)

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 + shadcn/ui + Zustand |
| API | tRPC |
| Realtime | Supabase Realtime |
| Database | PostgreSQL (Supabase) + pgvector |
| Agent | Claude SDK + MCP |
| Infra | Fly.io + Supabase |

---

## Success Criteria

### Week 2 Checkpoint
- [ ] Auth working (signup/login/OAuth)
- [ ] Workspace + Channel CRUD
- [ ] Basic UI shell (Discord-like layout)

### Week 4 Checkpoint
- [ ] Realtime messaging
- [ ] Thread creation and listing
- [ ] Agent response streaming

### Week 6 Checkpoint (Critical)
- [ ] Fork creation from any message
- [ ] **Fork resolve with AI summary** -- Core validation
- [ ] Focus mode switching

### Week 8 Checkpoint
- [ ] @Vibe agent working
- [ ] @Coder agent working
- [ ] Ready for internal dogfood

---

*Updated: 2026-02-07*
*Status: Phase 2 - Implementation*
