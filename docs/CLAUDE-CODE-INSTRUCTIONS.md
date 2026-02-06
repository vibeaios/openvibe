# OpenVibe - Claude Code Instructions

> Reference in Claude Code: `Read docs/CLAUDE-CODE-INSTRUCTIONS.md`

---

## Project Overview

**OpenVibe** = A Fork/Resolve Thread product for Human + AI agent collaboration

Core differentiator: The **Fork/Resolve** model solves the context fragmentation problem in team AI collaboration

```
┌─────────────────────────────────────────────────────┐
│            Web UI (Next.js 14)                       │
│         Discord-like + Fork Sidebar                  │
└─────────────────────┬───────────────────────────────┘
                      │ tRPC + Supabase Realtime
┌─────────────────────▼───────────────────────────────┐
│              Backend (~30 tRPC procedures)           │
└─────────────────────┬───────────────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   [@Vibe]        [@Coder]       [Humans]
       │              │
       └──────┬───────┘
              ▼
        [Supabase]
   (Postgres + Realtime)
```

---

## Required Reading

### Phase 2 Implementation (Current)

| Document | Content | Priority |
|----------|---------|----------|
| [`docs/INTENT.md`](INTENT.md) | Current goals + Sprint plan | **Every session** |
| [`docs/research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md`](research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md) | Gherkin specs + 8-week plan | **Must read** |
| [`docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md`](research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) | 10 tables, ~30 procedures | **Must read** |
| [`docs/research/phase-1.5/FRONTEND-ARCHITECTURE.md`](research/phase-1.5/FRONTEND-ARCHITECTURE.md) | Next.js + Zustand | **Must read** |
| [`docs/research/phase-1.5/THREAD-UX-PROPOSAL.md`](research/phase-1.5/THREAD-UX-PROPOSAL.md) | Fork/Resolve UX | **Must read** |

### Background Understanding

| Document | Content |
|----------|---------|
| [`docs/research/SYNTHESIS.md`](research/SYNTHESIS.md) | Phase 1 research synthesis |
| [`docs/PRODUCT-REASONING.md`](PRODUCT-REASONING.md) | Product reasoning derivation |
| [`docs/research/phase-1.5/SYSTEM-ARCHITECTURE.md`](research/phase-1.5/SYSTEM-ARCHITECTURE.md) | Complete architecture diagrams |

### Historical Reference (Superseded)

`docs/design/M1-M6` -- Initial designs, updated in Phase 1.5

---

## Current Phase: Phase 2 - Implementation (8 Weeks)

### Sprint Overview

| Week | Epic | Key Deliverables |
|------|------|------------------|
| 1-2 | Foundation | Auth, Workspace, Channel CRUD |
| 3-4 | Thread + Messaging | Realtime messages, streaming |
| 5-6 | **Fork/Resolve** | Core differentiator, AI summary |
| 7-8 | Agent Integration | @Vibe, @Coder |

### Critical Risk

**AI Summary Quality = Load-bearing wall**

Week 5-6's Fork Resolve is the validation point. Poor summary quality = product doesn't work.

---

## Tech Stack

| Layer | Tech | Notes |
|-------|------|-------|
| Frontend | Next.js 14 + shadcn/ui + Zustand | App Router |
| API | tRPC | Type-safe |
| Realtime | Supabase Realtime | postgres_changes |
| Database | PostgreSQL + pgvector | Supabase hosted |
| Agent | Claude SDK | Sonnet 4.5 |
| Infra | Fly.io + Supabase | Single machine for dogfood |

---

## Monorepo Structure (Nx)

```
apps/
  web/                 # Next.js frontend
  api/                 # tRPC API (if separated)

packages/
  db/                  # Prisma/Drizzle schema
  ui/                  # Shared components
  config/              # Config types
  agent/               # Agent runtime

docs/                  # All documentation
  INTENT.md            # Current goals
  research/            # Phase 1 + 1.5 research
  design/              # Original M1-M6 (superseded)
```

---

## Implementation Priorities

### Week 1-2: Foundation

```gherkin
Feature: User Signup
Feature: User Login
Feature: Workspace Creation
Feature: Channel CRUD
```

Files to create:
- `apps/web/` - Next.js app
- `packages/db/` - Schema
- Supabase setup

### Week 3-4: Thread + Messaging

```gherkin
Feature: Thread Creation
Feature: Send Message
Feature: Real-time Updates
Feature: Agent Response Streaming
```

### Week 5-6: Fork/Resolve (CRITICAL)

```gherkin
Feature: Fork Creation
Feature: Fork Sidebar
Feature: Focus Mode
Feature: Fork Resolution with AI Summary  # ← Critical validation
Feature: Fork Abandonment
```

### Week 7-8: Agent Integration

```gherkin
Feature: @Vibe Agent
Feature: @Coder Agent
Feature: Task Progress
```

---

## Key Patterns

### State Management (Zustand)

```typescript
// Separate stores per domain
const useChannelStore = create(...)
const useThreadStore = create(...)
const useForkStore = create(...)
const useUIStore = create(...)
```

### Realtime Subscriptions

```typescript
supabase
  .channel(`channel:${channelId}`)
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'messages'
  }, handleMessage)
```

### Agent Invocation

```typescript
// Agent = config record, not process
const agent = await db.agentConfigs.findBySlug('vibe');
const response = await claude.complete({
  system: agent.systemPrompt,
  messages: threadHistory,
  stream: true
});
```

---

## Constraints

1. **Dogfood scope only** -- 20 users, single Fly.io machine
2. **No premature optimization** -- Scaling is a Phase 3+ concern
3. **Fork/Resolve first** -- This is the differentiator; everything else can be simplified
4. **Test with Gherkin** -- BDD specs are defined; test with Playwright

---

## Success Metrics

| Checkpoint | Criteria |
|------------|----------|
| Week 2 | Auth + Workspace + Channel working |
| Week 4 | Realtime messaging + streaming |
| Week 6 | **Fork/Resolve with AI summary** |
| Week 8 | Agents working, ready for dogfood |

---

*Updated: 2026-02-07*
*Phase: 2 - Implementation*
