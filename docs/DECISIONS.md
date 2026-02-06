# OpenVibe - Decision Log

> Records important technical and product decisions

---

## Template

```markdown
## [YYYY-MM-DD] - [Decision Title]

**Context**: Why this decision was needed

**Options Considered**:
1. Option A - pros/cons
2. Option B - pros/cons
3. Option C - pros/cons

**Decision**: Final choice

**Rationale**: Why this was chosen

**Consequences**:
- Positive impact
- Negative impact
- Things to watch out for

**Status**: Proposed / Accepted / Deprecated / Superseded by [link]
```

---

## Decisions

### 2026-02-06 - Memory First Architecture

**Context**: Need to determine where the system's core value lies

**Options Considered**:
1. Thread Engine as core - Git-like is the differentiator
2. Agent Runtime as core - AI capabilities are the selling point
3. Memory System as core - Cumulative assets are most important

**Decision**: Memory First

**Rationale**:
- LLMs are a commodity, can be swapped anytime
- Channels (Slack/Discord) are a commodity
- Only Memory is a cumulative asset that becomes more valuable with use
- 90% of long-term value is in Memory

**Consequences**:
- Memory API design requires the most effort
- Other modules are built around Memory
- Memory schema evolution must be considered early

**Status**: Accepted

---

### 2026-02-06 - Supabase as Backend

**Context**: Need to select the backend tech stack for Phase 1

**Options Considered**:
1. Self-hosted Postgres
2. Supabase (Managed Postgres + Realtime + Auth)
3. PlanetScale + Upstash

**Decision**: Supabase

**Rationale**:
- Native Postgres + pgvector support
- Built-in Realtime subscriptions
- Built-in Auth (though not used in Phase 1)
- Fast development speed, can migrate later

**Consequences**:
- Dependency on Supabase SDK and conventions
- Need to learn Supabase RLS (Row Level Security)
- May need to migrate to self-hosted in the future

**Status**: Accepted

---

*Add new decisions above this line*
