# OpenVibe

> The first workspace designed for human+agent collaboration.

## Current Focus: V5

**Read first:** `v5/docs/THESIS.md`
**Architecture:** `v5/docs/DESIGN.md`
**Current state:** `PROGRESS.md`

## Session Resume Protocol

1. Read `PROGRESS.md` — current state and phase
2. Read `v5/docs/THESIS.md` — core thesis
3. Read `v5/docs/DESIGN.md` — architecture
4. Important milestones → pause for user confirmation

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
5. **Configuration over Code** — SOUL + config-driven roles, not hardcoded behavior
