# Design Gap Analysis

> **RESOLVED**: Phase 1 (R1-R7) and Phase 1.5 are complete. This document is retained as historical reference.
>
> Current status: **Phase 2 - Implementation**
> Entry document: [`docs/INTENT.md`](../INTENT.md)

---

## Phase 1 Research Results

| Issue | Conclusion | Detailed Document |
|-------|------------|-------------------|
| **R1: Thread Model** | Fork/Resolve replaces Branch/Merge | [`R1-THREAD-MODEL.md`](../research/R1-THREAD-MODEL.md) |
| **R2: Generative UI** | Config-driven handles 75-80% | [`R2-GENERATIVE-UI.md`](../research/R2-GENERATIVE-UI.md) |
| **R3: Agent Lifecycle** | Risk-based action classification | [`R3-AGENT-LIFECYCLE.md`](../research/R3-AGENT-LIFECYCLE.md) |
| **R4: Claude Teams** | Wrap + extend pattern | [`R4-CLAUDE-TEAMS.md`](../research/R4-CLAUDE-TEAMS.md) |
| **R5: CLI Blend** | API-first for production | [`R5-CLI-BLEND-RISKS.md`](../research/R5-CLI-BLEND-RISKS.md) |
| **R6: Privacy/Hybrid** | Hybrid router by classification | [`R6-PRIVACY-HYBRID.md`](../research/R6-PRIVACY-HYBRID.md) |
| **R7: Context Unification** | Memory as context bus (long-term) | [`R7-CONTEXT-UNIFICATION.md`](../research/R7-CONTEXT-UNIFICATION.md) |

Combined conclusions: [`SYNTHESIS.md`](../research/SYNTHESIS.md)

---

## Phase 1.5 Design Results

| Document | Content |
|----------|---------|
| [`BDD-IMPLEMENTATION-PLAN.md`](../research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md) | 8-week Sprint + Gherkin specs |
| [`BACKEND-MINIMUM-SCOPE.md`](../research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) | 10 tables, ~30 tRPC procedures |
| [`FRONTEND-ARCHITECTURE.md`](../research/phase-1.5/FRONTEND-ARCHITECTURE.md) | Next.js + Zustand structure |
| [`THREAD-UX-PROPOSAL.md`](../research/phase-1.5/THREAD-UX-PROPOSAL.md) | Fork/Resolve UX design |
| [`AGENT-DEFINITION-MODEL.md`](../research/phase-1.5/AGENT-DEFINITION-MODEL.md) | Agent config model |
| [`SYSTEM-ARCHITECTURE.md`](../research/phase-1.5/SYSTEM-ARCHITECTURE.md) | Infrastructure diagrams |
| [`RUNTIME-ARCHITECTURE.md`](../research/phase-1.5/RUNTIME-ARCHITECTURE.md) | Per-user agent runtime |
| [`ADMIN-CONFIGURABLE-UI.md`](../research/phase-1.5/ADMIN-CONFIGURABLE-UI.md) | Config-driven UI |
| [`HANDOFF-CONTEXT-THESIS.md`](../research/phase-1.5/HANDOFF-CONTEXT-THESIS.md) | Context handoff 6 sub-questions |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Fork/Resolve** not Branch/Merge | Simple; no one has successfully used Git semantics for conversations |
| **AI Summary Quality = Critical Risk** | The entire model depends on the quality of resolution summaries |
| **2 agents for MVP** | @Vibe + @Coder, sufficient for start |
| **Single-process dogfood** | 20 people don't need distributed systems |
| **Focus Mode** | One context at a time to avoid confusion |

---

## Original Gaps (Historical Reference)

The following issues were identified before Phase 1 and have since been resolved through research:

### ~~R1: Git-like Thread Model~~ Done
- Conclusion: Fork/Resolve replaces Branch/Merge
- Merge conflict in conversations = divergence points requiring human decision
- See [`R1-THREAD-MODEL.md`](../research/R1-THREAD-MODEL.md)

### ~~R2: Generative UI~~ Done
- Conclusion: Config-driven handles 75-80%, remainder needs per-vertical components
- 7 MVP components defined in [`ADMIN-CONFIGURABLE-UI.md`](../research/phase-1.5/ADMIN-CONFIGURABLE-UI.md)

### ~~R3: Agent Lifecycle~~ Done
- Conclusion: Risk-based classification (AUTONOMOUS/APPROVE/ESCALATE)
- Task state machine: QUEUED → RUNNING → COMPLETED/FAILED
- MVP only needs 4 states, full 10 states for Phase 3+

### ~~R4: Claude Code Integration~~ Done
- Conclusion: Wrap + extend, not build on top of
- AgentRuntime interface abstraction, supports multiple runtimes

### ~~R5: CLI Blend Risk~~ Done
- Conclusion: Dogfood accepts CLI-blend, Production needs API-first
- Task API contract designed in Phase 2

### ~~R6: Privacy/Hybrid~~ Done
- Conclusion: Data classification L0-L4, hybrid router by sensitivity
- Dogfood uses cloud, regulated verticals use hybrid

### ~~R7: Context Unification~~ Done
- Conclusion: No existing framework solves this; it's a long-term opportunity
- MVP: ~4K tokens minimum shared context
- Long-term: Memory as context bus

---

*Updated: 2026-02-07*
*Status: Phase 1 + 1.5 Complete, gaps resolved*
