# OpenVibe Implementation Progress

> **Updated 2026-02-08:** Terminology changed from Fork/Resolve to Deep Dive/Publish per PRODUCT-CORE-REFRAME.md

> 新 session 开始先读这个文件 + docs/INTENT.md
> 每个 Sprint 结束时更新

---

## Current State

**Phase:** 2 - Implementation
**Sprint:** 1 (Testing)
**Status:** Sprint 1 code complete. Auth cookie fix applied (HTTP/Secure flag issue). User needs to clear cookies + re-login to test.

---

## Completed Phases

### Phase 1: Research (2026-02-07)
- 7 core research questions (R1-R7) answered
- Competitive landscape mapped
- Phase 1 Synthesis produced
- Docs: `docs/research/R1-R7*.md`, `SYNTHESIS.md`, `COMPETITIVE-LANDSCAPE.md`

### Phase 1.5: MVP Design (2026-02-07)
- 10 design docs produced
- MVP Design Synthesis = THE blueprint
- Docs: `docs/research/phase-1.5/*.md`
- Key doc: `docs/research/phase-1.5/MVP-DESIGN-SYNTHESIS.md`

---

## Sprint Plan

### Sprint 0: Infrastructure (2-3 days)
- [x] Nx monorepo init
- [x] Supabase project setup + Google OAuth (user configured)
- [x] DB migrations (12 tables) — 4 SQL files written
- [x] CI/CD (GitHub Actions)
- [x] Fly.io config (fly.toml + Dockerfile)
- [x] Base packages structure (core, db, ui, thread-engine, agent-runtime, auth, config)
- [x] Core types + interfaces + utils (12 TypeScript files)
- [x] tRPC router stubs (7 routers: workspace, channel, message, thread, dive, agent, search)
- [x] Next.js 15 app with App Router + Tailwind v4 + tRPC client
- [x] Build passes (`pnpm build` + `pnpm typecheck`)

### Sprint 1: Auth + Channels + Messaging (Week 1-2)
- [x] Supabase Auth (SSR middleware + Google OAuth + login page + callback)
- [x] Workspace auto-creation + workspace store (Zustand)
- [x] Channel CRUD (list, getBySlug, create via tRPC + real Supabase queries)
- [x] Message posting + display (message list, composer, message item)
- [x] Real-time updates (Supabase Realtime postgres_changes subscription)
- [x] Basic layout (4-zone Discord-like: sidebar, header, main, thread panel)
- [x] All tRPC routers wired to real Supabase queries (workspace, channel, message)

### Sprint 2: Threads + Agents (Week 3-4)
- [ ] Thread replies + Thread panel
- [ ] @mention detection
- [ ] Agent config (YAML → DB seed)
- [ ] Agent invocation pipeline (@mention → task → Claude API → response)
- [ ] "Thinking" indicator
- [ ] Agent response styling

### Sprint 3: Deep Dives + Publish (Week 5-6)
- [ ] Deep dive creation from any message
- [ ] Active Dives sidebar
- [ ] Working in dives (messages within dive)
- [ ] Publish flow (AI summary → main thread)
- [ ] Discard dive
- [ ] Focus Mode navigation
- [ ] Progressive disclosure (headline/summary/full)

### Sprint 4: Search + Config + Polish (Week 7-8)
- [ ] Full-text search (PostgreSQL tsvector)
- [ ] Search UI (Cmd+K)
- [ ] YAML config loading
- [ ] Config-driven UI rendering
- [ ] Bug fixes + polish
- [ ] Dogfood launch prep

---

## Architecture Quick Reference

- **Frontend:** Next.js 15 + Tailwind v4 + shadcn/ui + Zustand + tRPC v11
- **Backend:** tRPC routers, Supabase (PostgreSQL + Realtime + Auth)
- **Agent:** Claude API (Sonnet 4.5 primary, Haiku for summaries)
- **Infra:** Fly.io (app) + Supabase Pro (DB/auth/realtime)
- **Monorepo:** Nx
- **Agents:** @Vibe (general + deep dive partner), @Coder (code)

## Key Design Docs (read order for new session)

1. `PROGRESS.md` (this file) — where we are
2. `docs/research/phase-1.5/MVP-DESIGN-SYNTHESIS.md` — THE blueprint
3. `docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md` — data model + API
4. `docs/research/phase-1.5/FRONTEND-ARCHITECTURE.md` — component structure
5. `docs/research/phase-1.5/SYSTEM-ARCHITECTURE.md` — subsystem decomposition
6. `docs/research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md` — sprint details

## Agent Team Structure

```
backend-agent  → packages/db, packages/core, tRPC routers, agent runtime
frontend-agent → apps/web, packages/ui
test-agent     → *.test.ts, e2e/
```

## Rules

- UI 方向不确定时 → 暂停等用户草图
- 每个 Sprint 完成 → 暂停等用户确认
- 外发内容先确认
- 字体考虑: Geist Pixel

---

## Sprint Log

### Sprint 0
- Started: 2026-02-07
- Completed: 2026-02-08
- Notes:
  - Monorepo: Nx 20 + pnpm 10 + TypeScript 5.9
  - 8 packages + 1 app scaffolded
  - Core types: Message, Agent, User, Config, WorkspaceConfig
  - Core interfaces: LLMProvider, AgentRuntime
  - Core utils: mention parsing, validation
  - DB: 4 migration files (12 tables, RLS, realtime pub, seed data)
  - tRPC: 7 router stubs with typed input schemas (zod)
  - Next.js: App Router, standalone output, Tailwind v4 CSS-first config
  - CI: GitHub Actions (typecheck + build)
  - Deploy: Dockerfile (multi-stage) + fly.toml (sjc region)
  - Remaining: Supabase project creation (needs user account), actual Fly.io deploy

### Sprint 1
- Started: 2026-02-08
- Completed: 2026-02-08
- Notes:
  - Auth: Supabase SSR (browser + server + middleware clients), Google OAuth, route protection
  - Layout: 4-zone Discord-like (sidebar, header, main content, thread panel stub)
  - Data: workspace/channel/message tRPC routers wired to real Supabase queries
  - Sidebar: real channel list from DB, active channel highlight
  - Messages: list with author info, auto-scroll, cursor pagination
  - Composer: textarea with Enter-to-send, Shift+Enter for newline, auto-resize
  - Realtime: Supabase postgres_changes subscription on messages table, auto-refetch
  - Stores: workspace store (Zustand), thread store (Zustand)
  - Workspace init: auto-creates "Vibe" workspace on first visit

---

*Last updated: 2026-02-08*
