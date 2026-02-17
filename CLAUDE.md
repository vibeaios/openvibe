# OpenVibe

> The first workspace designed for human+agent collaboration.

## Current Focus: V4

**Read first:** `v4/docs/THESIS.md`
**Current project:** `v4/vibe-ai-adoption/`
**All docs:** `v4/docs/`

## Version History

### V4 (Current)
- **Focus:** Vibe AI Adoption — dogfooding with Marketing & Sales teams
- **Stack:** Python 3.13, Temporal + LangGraph + Anthropic SDK (no CrewAI)
- **Implementation:** 5 operators, 22 workflows, 80 nodes, 116 tests
- **Docs:** `v4/docs/` (THESIS, DESIGN, DESIGN-PRINCIPLES, ROADMAP, proposed/)
- **Project:** `v4/vibe-ai-adoption/` (read its `PROGRESS.md` for full status)

### V3 (Archived)
- Built the operator pattern. CrewAI removed. Docs scattered — consolidated into V4.
- Docs: `v3/docs/`, `v3/vibe-ai-adoption/docs/`

### V2 (Archived)
- Design principles: SOUL, progressive disclosure, feedback loop, trust levels, persistent context.
- Strategy: Partner-led GTM (superseded by dogfood-first).
- Docs: `v2/docs/`

### V1 (Archived)
- "AI Deep Dive" — too derivative, too narrow. Nx + Supabase + Next.js prototype.
- Validated assets: Resolution Prompt v2 (4.45/5), Progressive Disclosure, Context Assembly.
- Docs: `v1/docs/`, code: `v1/implementation/`

## Session Resume Protocol

1. Read `PROGRESS.md` — current state
2. Read `v4/docs/THESIS.md` — core thesis
3. Read `v4/vibe-ai-adoption/PROGRESS.md` — implementation status
4. Read `v4/docs/DESIGN.md` — architecture
5. Important milestones → pause for user confirmation

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
5. **Configuration over Code** — SOUL + config-driven operators, not hardcoded behavior
