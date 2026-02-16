# OpenVibe

> The first workspace designed for human+agent collaboration.

## Current Focus: V3

**Read first:** `v3/docs/THESIS.md`
**Current project:** `v3/vibe-ai-adoption/`

## Version History

### V3 (Current)
- **Focus:** Vibe AI Adoption - dogfooding with Marketing & Sales teams
- **Stack:** Python, Temporal + LangGraph + CrewAI, 20 agents, 98 tests
- **Docs:** `v3/docs/`
- **Project:** `v3/vibe-ai-adoption/` (read its `PROGRESS.md` for full status)
- **Design:** `v3/vibe-ai-adoption/docs/DESIGN.md` (3-layer architecture + 3 workflows)

### V2 (Archived)
- **Thesis:** AI is transitioning from tool to colleague. Human+agent collaboration needs a new medium.
- **Docs:** `v2/docs/`
- **Key files:** THESIS.md, DESIGN-SYNTHESIS.md, STRATEGY.md

### V1 (Archived)
- **Thesis:** "AI Deep Dive amplifies human cognition in team conversations"
- **Docs:** `v1/docs/`
- **Implementation:** `v1/implementation/` (Nx monorepo, Supabase, Next.js)
- **Why archived:** Too derivative (Slack replacement), too narrow (deep dive is a feature, not a product)

## Session Resume Protocol

1. Read `PROGRESS.md` — understand current state
2. Read `v3/docs/THESIS.md` — understand V3 direction
3. Read `v3/vibe-ai-adoption/PROGRESS.md` — project status
4. Each Sprint completed -> pause for user confirmation

## Constraints

- Only submit complete implementations (no partial work)
- Do not leave TODOs
- New features must have tests
- Two teammates should not edit the same file simultaneously

## Design Principles

1. **Agent in the conversation** — AI is a participant, not a sidebar tool
2. **Progressive Disclosure** — Headline / summary / full for all agent output
3. **Workspace gets smarter** — Context, memory, knowledge compound over time
4. **Feedback is the moat** — Agent shaped by team feedback > smarter model without context
5. **Configuration over Code** — SOUL + config-driven agents, not hardcoded behavior
