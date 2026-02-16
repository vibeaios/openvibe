# OpenVibe Progress

> 新 session 开始先读这个文件, 然后按 Session Resume Protocol 走
> 每个重要阶段结束时更新

---

## Current State

**Phase:** V3 - Vibe AI Adoption
**Status:** 20 AI agents built (Temporal + LangGraph + CrewAI). 98/98 tests passing. 3 design workflows complete.
**Next:** T25-T26 (smoke test with real API keys + go live). Then iterate on agent output quality.
**Project dir:** `v3/vibe-ai-adoption/` — read its `PROGRESS.md` for details

**Previous work:**
- V2: Strategy validation (see `v2/docs/validation/`)
- V1: Implementation archived (see `v1/implementation/`)

---

## V2 Strategy (2026-02-10)

### Key Decisions from 10-Agent Analysis

- **Web first, board second.** All 10 agents independently reached same conclusion.
- **$149/month/board.** 90-day free trial on all 40K boards at GA.
- **Consulting firms first.** Then tech, then financial services.
- **"Agent-first" language doesn't sell.** Lead with: "Your meetings keep working after everyone leaves the room."
- **Microsoft = 12-18 month window.** Move fast.
- **The durable moat = shared context layer** (SOUL + memory + knowledge + feedback), not the UI.
- **Agent output quality is THE existential risk.** Default passive. Earn trust.

### 6-Month Build Sequence

```
Sprint 2 (Week 1-4):   @mention agents + progressive disclosure + SOUL
Sprint 3 (Week 5-8):   Feedback + deep dives + publish flow
Sprint 4 (Week 9-12):  Episodic memory + long tasks + Slack bridge (read)
Sprint 5 (Week 13-16): Board MVP + trust levels + admin panel
Sprint 6 (Week 17-20): Proactive agents + knowledge base + meeting summary
Sprint 7 (Week 21-24): Multi-agent + mobile web + Slack write-back + search
```

### GTM Sequence

```
Month 1-2:  Alpha (10 customers, free)
Month 3-5:  Beta (100-200 boards, $149/mo, 90-day free)
Month 6:    GA (firmware push to all 40K boards)
Month 7-12: Growth (web-only sign-up + industry agent packs)
```

Full strategy: `v2/docs/STRATEGY.md`

---

## V2 Design Progress

### Completed (2026-02-09)

- [x] Mother thesis defined: "AI is becoming a participant in work. Human+agent collaboration needs a new medium."
- [x] Three-layer framework: Protocol (agents) / Interface (humans) / Space (shared)
- [x] `v2/docs/THESIS.md` — root document, everything derives from it
- [x] `v2/docs/DESIGN-SYNTHESIS.md` — thesis -> design decisions + MVP roadmap
- [x] `v2/docs/design/AGENT-MODEL.md` — SOUL structure, trust levels, memory, data model
- [x] `v2/docs/design/AGENT-IN-CONVERSATION.md` — invocation model, message types, progressive disclosure
- [x] `v2/docs/design/PERSISTENT-CONTEXT.md` — memory architecture, knowledge pipeline, context assembly
- [x] `v2/docs/design/FEEDBACK-LOOP.md` — feedback channels, persistence levels, metrics
- [x] `v2/docs/reference/V1-INSIGHT-AUDIT.md` — 8 must-carry, 7 blind spots, 10 reusable assets
- [x] Doc reorganization: v1/ and v2/ versioned directories

### Completed (2026-02-10 AM)

- [x] `v2/docs/STRATEGY.md` — 10-agent cross-analysis: market, competitive, GTM, pricing, build sequence, KPIs
- [x] THESIS.md updated with Q1 2026 market evidence
- [x] Competitive landscape mapped (Cowork, Frontier, Copilot, Slack AI)
- [x] Kill signals and KPIs defined for Month 3 and Month 6

### Completed (2026-02-10 PM)

- [x] **Brand Architecture: Three-Layer Strategy**
  - Layer 1: vibeorg.com (Movement, "Vibe your organization")
  - Layer 2: open-vibe.org (Open source, technical)
  - Layer 3: vibe.us (Commercial product)
- [x] **Domains acquired**: vibeorg.com ($5000), open-vibe.org, vibeorging.com
- [x] **Top-level docs refined (2026-02-10 Evening)**
  - THESIS.md: 275 → 203 lines (sharper positioning, 2 differentiation pillars)
  - STRATEGY.md: 550 → 257 lines (removed execution details, kept strategic decisions)
  - BRAND-ARCHITECTURE.md: 266 → 433 lines (vibeorg.com = category creation, build sequence defined)
  - Positioning: "Vibe your organization" (headline) + "The workspace where humans and agents work as a team" (subline)
  - Differentiation: 2 pillars (Open Infrastructure + Partner Ecosystem)
- [x] **GitHub org planned**: `openvibeorg` (available, ready to create)
- [x] **Vision tagline**: "Vibe your organization"
- [x] **Narrative strategy**: Lead with positive vision (not competition)
- [x] **GTM folder created**: `v2/docs/go-to-market/` with:
  - BRAND-ARCHITECTURE.md (3-layer strategy, messaging)
  - GITHUB-ORG-SETUP.md (org structure, repos, READMEs)
  - NARRATIVE-OPTIONS.md (5 storytelling approaches)
  - STRATEGIC-ANALYSIS.md (8-agent competitive analysis)
  - QUICK-REFERENCE.md (one-page summary)
- [x] THESIS.md updated with Vision section

### Not Yet Written

- [ ] `v2/docs/design/TRUST-SYSTEM.md` — L1-L4 mechanical details
- [ ] `v2/docs/design/ORCHESTRATION.md` — Proposal -> Mission -> Steps
- [ ] `v2/docs/design/NOTIFICATION-MODEL.md` — Attention management for agent events

### Open Questions (before Sprint 2)

1. ~~Agent roster for dogfood~~ → Decided: pre-configured @Vibe + @Coder
2. Visual design direction: agent message styling needs mockup
3. ~~V2 sprint plan~~ → Defined in STRATEGY.md (7 sprints, 24 weeks)

---

## V1 Implementation (Reusable)

V1 Sprint 0-1 code is the **shared space substrate** for V2. ~70% carries forward.

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

All V1 docs moved to `v1/docs/`. Key validated assets preserved via V1-INSIGHT-AUDIT:

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
2. Read `v3/docs/THESIS.md` — V3 direction
3. Read `v3/vibe-ai-adoption/PROGRESS.md` — project status (98 tests, 20 agents)
4. Read `v3/vibe-ai-adoption/docs/DESIGN.md` — 3-layer architecture + 3 workflows
5. Important milestones -> pause for user confirmation

For V2 context (archived): `v2/docs/THESIS.md`, `v2/docs/STRATEGY.md`

## Architecture

- **Frontend:** Next.js 15 + Tailwind v4 + shadcn/ui + Zustand + tRPC v11
- **Backend:** tRPC routers + Supabase (PostgreSQL + Realtime + Auth)
- **Agent:** Claude API (Sonnet 4.5 primary, Haiku for summaries)
- **Agents:** @Vibe (thinking partner), @Coder (code)
- **Structure:** Monolith (packages/core + apps/web + apps/board at Sprint 5)

## Rules

- UI 方向不确定时 → 暂停等用户草图
- 重要阶段完成 → 暂停等用户确认
- 外发内容先确认

---

*Last updated: 2026-02-10*
