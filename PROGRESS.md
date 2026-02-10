# OpenVibe Progress

> 新 session 开始先读这个文件, 然后按 Session Resume Protocol 走
> 每个重要阶段结束时更新

---

## Current State

**Phase:** V2 Design
**Status:** V2 thesis confirmed. 4 design docs drafted. Implementation plan not yet started.
**Why V2:** V1 treated the product as "Slack + AI" — too derivative, too narrow. V2 reframes: the first medium designed for human+agent collaboration.

---

## V2 Design Progress

### Completed (2026-02-09)

- [x] Mother thesis defined: "AI is becoming a participant in work. Human+agent collaboration needs a new medium."
- [x] Three-layer framework: Protocol (agents) / Interface (humans) / Space (shared)
- [x] `docs/v2/THESIS.md` — root document, everything derives from it
- [x] `docs/v2/DESIGN-SYNTHESIS.md` — thesis -> design decisions + MVP roadmap
- [x] `docs/v2/design/AGENT-MODEL.md` — SOUL structure, trust levels, memory, data model
- [x] `docs/v2/design/AGENT-IN-CONVERSATION.md` — invocation model, message types, progressive disclosure
- [x] `docs/v2/design/PERSISTENT-CONTEXT.md` — memory architecture, knowledge pipeline, context assembly
- [x] `docs/v2/design/FEEDBACK-LOOP.md` — feedback channels, persistence levels, metrics
- [x] `docs/v2/reference/V1-INSIGHT-AUDIT.md` — 8 must-carry, 7 blind spots, 10 reusable assets
- [x] Doc reorganization: v1/ and v2/ versioned directories

### Not Yet Written

- [ ] `docs/v2/design/TRUST-SYSTEM.md` — L1-L4 mechanical details
- [ ] `docs/v2/design/ORCHESTRATION.md` — Proposal -> Mission -> Steps
- [ ] `docs/v2/design/NOTIFICATION-MODEL.md` — Attention management for agent events

### Open Questions (before implementation)

1. Agent roster for dogfood: pre-configured @Vibe + @Coder, or "hire agent" flow?
2. Visual design direction: agent message styling needs mockup
3. V2 sprint plan: needs to account for V1 code reuse and new V2 features

---

## V1 Implementation (Reusable)

V1 Sprint 0-1 code is the **shared space substrate** for V2. Channels, messaging, auth all carry forward.

### Sprint 0: Infrastructure (Done 2026-02-08)
- Nx monorepo + Supabase + Next.js 15 + tRPC + Tailwind v4
- 12-table DB schema + migrations + seed data
- CI/CD (GitHub Actions) + Fly.io config

### Sprint 1: Auth + Channels + Messaging (Done 2026-02-08)
- Supabase Auth (SSR + Google OAuth)
- Workspace/channel/message CRUD via tRPC
- Real-time updates (Supabase Realtime)
- 4-zone Discord-like layout
- Known issue: auth cookie Secure flag over HTTP (fix: `fixCookieOptions()` in dev)

---

## V1 Research & Design (Archived)

All V1 docs moved to `docs/v1/`. Key validated assets preserved via V1-INSIGHT-AUDIT:

| Asset | Score/Status | V2 Role |
|-------|-------------|---------|
| Resolution Prompt v2 | 4.45/5 validated | Template for agent output |
| Progressive Disclosure | Confirmed | Standard for all agent messages |
| Risk-Based Action Classification | Confirmed | Maps to trust levels |
| Slack Pain Data (1,097 threads) | Confirmed | Problem validation |
| Context Assembly (4-layer) | Confirmed | Adapted for V2 SOUL + memory |

---

## Session Resume Protocol

1. Read `PROGRESS.md` (this file) — where we are
2. Read `docs/v2/THESIS.md` — the "why"
3. Read `docs/v2/DESIGN-SYNTHESIS.md` — the "what"
4. Important milestones -> pause for user confirmation

## Architecture

- **Frontend:** Next.js 15 + Tailwind v4 + shadcn/ui + Zustand + tRPC v11
- **Backend:** tRPC routers + Supabase (PostgreSQL + Realtime + Auth)
- **Agent:** Claude API (Sonnet 4.5 primary, Haiku for summaries)
- **Agents:** @Vibe (thinking partner), @Coder (code)

## Rules

- UI 方向不确定时 → 暂停等用户草图
- 重要阶段完成 → 暂停等用户确认
- 外发内容先确认

---

*Last updated: 2026-02-09*
