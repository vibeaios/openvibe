# OpenVibe Design Principles

> Extracted from V2 design documents. These are structural requirements, not features.
> They define how agents behave, how humans interact, and how value compounds.
> Last updated: 2026-02-16

---

## Three Core Properties

If any fails, the product fails.

1. **Agent is in the conversation** — Not sidebar, not separate tab. @mention = invocation.
2. **Workspace gets smarter over time** — Day 1: OK. Day 30: remembers corrections. Day 90: knows team context.
3. **Agent output is worth reading** — If mediocre, product has no reason to exist.

---

## Agent Identity: SOUL

SOUL defines WHO the agent is. Config, not code. Queryable, versionable, inspectable.

```yaml
soul:
  identity:
    name, role, description, avatar
  philosophy:
    principles: ["Be concise", "Show reasoning", "Say when uncertain"]
    values: ["Clarity > comprehensiveness", "Usefulness > impressiveness"]
  capabilities:
    domains: ["product strategy", "data analysis"]
    tools: [granted tools]
    limitations: [explicit constraints]
  behavior:
    response_style: structured | conversational | minimal
    progressive_disclosure: true
    max_output_tokens: 2000
  constraints:
    trust_level: L1|L2|L3|L4
    allowed_channels: [list]
    escalation_rules: [rules]
```

---

## Trust Levels

Agents earn autonomy through performance, not by default.

| Level | Can Do | Promotion Signal |
|-------|--------|-----------------|
| **L1 Observer** | Respond to @mention, read assigned channels | — |
| **L2 Advisor** | + Suggest actions in messages | Acceptance >80% over 30 days |
| **L3 Operator** | + Proactive triggers, execute approved patterns | Zero escalation failures |
| **L4 Autonomous** | + Execute most actions, access private data | Consistent track record |

**Demotion**: Acceptance <50%, multiple negative feedback, trust violations.

---

## Progressive Disclosure

**Mandatory** for any agent output >1000 chars.

| Layer | Content | Target |
|-------|---------|--------|
| Headline | ~100 chars, one-line summary | Readable in 2 seconds |
| Key Points | 3-5 bullets | Readable in 10 seconds |
| Full Content | Expandable markdown | Click to expand |

Standards:
- Scannable at a glance (<10 seconds)
- Confidence hedging when uncertain ("Based on limited data...")
- Reasoning available via "Why?" expansion, not in main output

---

## Feedback Loop

### Three Persistence Levels

```
Level 1: IMMEDIATE
  Correction in thread → agent uses it in same thread
  Gone when conversation ends

Level 2: EPISODIC
  Feedback → stored in agent memory
  Last 5 unresolved injected into every invocation
  Agent "remembers" across conversations
  90-180 day TTL (explicit feedback = permanent)

Level 3: STRUCTURAL
  Pattern recognized → written to SOUL
  Agent always behaves this way
  Permanent until explicitly changed
  Requires human approval
```

### Feedback Taxonomy

| Type | Gesture | Time | Auto-Episode? |
|------|---------|------|---------------|
| Approve | Thumbs up | 1s | Yes |
| Reject | Thumbs down | 1s | Yes + optional correction |
| Correct | Reply with fix | 15s | Yes |
| Instruct | "Always/Never" rule | 30s | Yes + SOUL write |

**Key rules:**
- 3-second rule: most common feedback must be <3s
- Behavioral signals (ignores, rewrites) → admin dashboard, NOT auto-feedback
- No "Was this useful?" on routine output — only after high-effort tasks
- ≥3 feedback items from ≥2 users in 30 days → surface pattern to admin

---

## Memory Architecture

| Type | Scope | Retrieval | Lifespan |
|------|-------|-----------|----------|
| **Working** | Per-invocation | Fresh each time | Single call |
| **Episodic** | Per-agent | Last 5 unresolved feedback | 90-180 days |
| **Semantic** | Workspace-shared | Vector embeddings | Has expiry |

### Knowledge Pipeline

```
Conversation → Deep Dive → Publish → Pin to Knowledge → Future Context
```

Each cycle, the workspace gets smarter. This is the flywheel.

---

## Context Assembly

Priority stack for building agent context:

| Priority | Content | Tokens |
|----------|---------|--------|
| P0 | SOUL (identity, principles, constraints) | Always included |
| P1 | Current task context (thread messages) | 2K-8K |
| P2 | Active feedback (episodic, unresolved) | 300-500 |
| P3 | Relevant knowledge entries | 500-2K |
| P4 | Channel/workspace config | 100-200 |
| P5 | Recent results (headlines only) | 500-1K |
| P6 | Older episodic memory | Remainder |

---

## Invocation Modes

| Mode | When | Trust Required |
|------|------|----------------|
| **Reactive** | @mention in message | L1+ |
| **Proactive** | SOUL trigger fires (scheduled, metric alert) | L3+ |
| **System** | Platform event (PR, deploy, threshold) | L2+ |
| **Multi-agent** | Human requests collaboration | L3+ |

**Anti-pattern**: Agents NEVER respond to other agents' messages in public channels. Agent-to-agent coordination = orchestration layer only.

---

## Long-Running Tasks

```
User @mentions complex request
  → Agent estimates: <30s (quick) or >30s (mission)?
  → If mission → post plan + progress bar
  → Each step → live progress update
  → User can [Cancel] or [Redirect] mid-task
  → Final output replaces progress message
```

---

## Quality Metrics

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| **Acceptance Rate** | % output used as-is | Primary quality signal |
| **Correction Rate** | How often needs fixing | Lower = better |
| **Repeat Correction** | Same fix 2+ times | Alert if >20% |
| **Learning Incorporation** | Does it use feedback? | Learning velocity |
| **Engagement Trend** | Is proactive work valued? | 4-week rolling |

**Visible improvement**: One line up (acceptance), one line down (corrections). Glanceable in 3 seconds.

---

## Design Tensions Resolved

| Tension | Decision | Why |
|---------|----------|-----|
| Proactive noise | Budget + SOUL quality + feedback loop | Can't judge quality; feedback calibrates |
| Context overflow | Priority stack + task-type budgets | Every token counts |
| Feedback automation | Explicit only; behavioral → dashboard | Misinterpretation risk > benefit |
| Multi-agent in channel | Orchestration layer, not messages | Prevents loops + noise |
| Knowledge quality | Human-created from dives, not auto-extracted | "Let's try X" ≠ decision |
| Agent scaling | Config (SOUL) not code | Portable, queryable |
| Trust expansion | Earned via metrics | L1→L4 based on track record |

---

## Summary

Six principles that make the architecture coherent:

1. **Message as medium** — Everything surfaces as a message. No hidden state.
2. **Context as product** — Deliberately created, prioritized, budgeted.
3. **Feedback as compound interest** — Immediate → episodic → structural. Human decides escalation.
4. **Identity as substrate** — SOUL enables portability and trust.
5. **Trust as autonomy** — Levels gate actions. Agents earn expansion.
6. **The flywheel** — Conversation → structure → knowledge → smarter conversations.
