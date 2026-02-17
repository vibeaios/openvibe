# Memory Architecture Vision

> **Date:** 2026-02-17
> **Status:** Proposed (brainstorm output)
> **Context:** Exploring memory infrastructure for agentic workspace
> **Builds on:** Cognitive Architecture (proposed), SDK V1 (implemented)

---

## 1. The End Goal

A company running in an agentic way. Many humans and agents work together in a shared workspace. This requires:

1. **Workspace Memory** — shared org knowledge, always evolving, many contributors
2. **Agent Memory** — per-agent knowledge, generated from interaction, layered
3. **Human-Agent Information Flow** — permission-controlled, density-aware

---

## 2. Two-Tier Memory Architecture

```
┌─────────────────────────────────────────────────┐
│  Workspace Memory (team-level, always evolving)  │
│  Shared facts, org knowledge, constantly updated │
│  Every agent/human contributes and reads         │
└──────────────┬──────────────────┬───────────────┘
               │ FETCH            │ PUBLISH
               │ (pull relevant)  │ (push learnings)
               ▼                  ▲
┌──────────────────────────────────────────────────┐
│  Agent Memory (per-agent, per-session)            │
│  L1 raw logs → L2 episodes → L3 insights         │
│  Working context for current task                 │
└──────────────────────────────────────────────────┘
```

### Workspace Memory

Like a company's knowledge system:

| Real World | Workspace Memory |
|-----------|-----------------|
| Google Drive / Confluence | Structured org knowledge |
| CRM (HubSpot) | Entity-based facts (companies, deals, people) |
| Slack channels | Ephemeral conversation knowledge |
| Meeting notes | Episodes from multi-agent collaboration |

Not a flat database. More like an **entity-centric fact store**:

```
workspace/
├── entities/
│   ├── acme_corp/
│   │   ├── profile          # 200 employees, B2B SaaS
│   │   ├── deal_history     # scored 85, tier high
│   │   └── interactions     # 3 calls, 2 emails
│   ├── q1_pipeline/
│   │   ├── targets          # $2M target
│   │   └── current_state    # $1.2M actual
│   └── webinar_campaign/
│       ├── metrics          # 500 registrations, 40% show rate
│       └── insights         # "converts 2x vs cold"
├── insights/                # org-level patterns
└── access_policies/
    ├── cro.yaml             # clearance profile
    └── cmo.yaml
```

### Agent Memory

Each agent has a "working directory" at runtime:

```
agent_cro/
├── identity/
│   └── soul.md              # WHO I am (rarely changes)
├── insights/                # L3: patterns I've learned
│   ├── enterprise_deals.md
│   └── webinar_conversion.md
├── episodes/                # L2: my experiences
│   ├── 2026-02-17-acme-qualification.md
│   └── 2026-02-17-pipeline-review.md
├── working/                 # current task context
│   └── current_context.md
└── workspace_cache/         # fetched from workspace memory
    ├── acme_corp.md
    └── q1_targets.md
```

Benefits: human-inspectable, natural hierarchy, version-controllable, maps to SDK protocols.

---

## 3. Atomic Facts

The base unit of all knowledge:

```python
@dataclass
class Fact:
    id: str
    content: str              # "Acme Corp has 200 employees"
    source: str               # agent_id or "human"
    confidence: float         # 0.0-1.0

    # Access control (per-fact)
    classification: str       # "public" | "internal" | "confidential" | "restricted"
    domains: list[str]        # ["revenue", "customer"]

    # Entity grouping
    entity: str               # "acme_corp"
    attribute: str            # "employee_count"

    # Lifecycle
    supersedes: str | None    # replaces an older fact
    created_at: datetime
    updated_at: datetime
    tags: list[str]
```

### Zoom Levels

Zoom levels are **generated views**, not separate storage:

```
Zoom 0 (atomic):   "Acme Corp scored 85 in lead qualification"
Zoom 0 (atomic):   "Acme Corp has 200 employees"
Zoom 0 (atomic):   "Acme Corp uses Salesforce and HubSpot"
Zoom 1 (context):  "Acme Corp: 200-person B2B SaaS, uses Salesforce/HubSpot, scored 85 (high tier)"
Zoom 2 (summary):  "Acme Corp is a qualified high-tier enterprise prospect"
Zoom 3 (overview): "3 new high-tier leads this week"
```

Store atomic facts. Generate higher zooms by aggregating permitted facts per requester.

### Permission Filtering

```
CRO queries "Acme Corp":
  clearance: {revenue: confidential, customer: confidential}
  → sees all facts ✅

CMO queries "Acme Corp":
  clearance: {revenue: internal, customer: internal}
  → sees: employees, industry, tech stack ✅
  → blocked: lead score (confidential/revenue) ❌

CMO gets zoom 1: "Acme Corp: 200-person B2B SaaS, uses Salesforce/HubSpot"
  (score fact omitted from aggregation — different agents see different zoom of same entity)
```

---

## 4. Human-Agent Information Flow

When a human enters the workspace and interacts with agents:

### Permission (can I tell them?)

Based on clearance profile, automatic filtering. Infrastructure-level.

### Information Density (how much should I tell?)

Same fact, different contexts need different density:

```
CEO asks "How's Acme?"
→ High density: all atomic facts + context + recommendation

CMO asks "How's Acme?"
→ Medium density: only CMO-clearance facts, focused on marketing-relevant info

New intern asks "How's Acme?"
→ Low density: public facts only, summary level
```

Not just permission filtering — **context-aware summarization**. Agent understands what level of information the requester needs.

### Agent Cognition

The agent has judgment: "should I tell the human this?" Two dimensions:
1. **Permission**: Can they see it? (clearance-based, automatic)
2. **Relevance/Density**: Should I include this detail? (context-based, LLM-driven)

---

## 5. Sync Protocol

```
Agent starts working:
  1. FETCH: pull relevant workspace facts into workspace_cache/
  2. PROCESS: work, generate L1→L2→L3 locally
  3. PUBLISH: push learnings back to workspace

Workspace continuously evolving:
  - Other agents publishing
  - Humans updating
  - External data arriving (HubSpot, Slack)
```

Key questions:
- Real-time fetch vs batch fetch vs subscribe?
- Conflict resolution when facts contradict?
- Confidence adjustment when re-published?

---

## 6. SDK Infrastructure Layers

```
Layer 0: Storage
  FactStore protocol     — atomic facts (entity + attribute + value + metadata)
  AgentStore protocol    — agent-local memory (episodes, insights, working context)

Layer 1: Access Control
  ClearanceProfile       — per agent/human permission config
  AccessFilter           — requester + facts → filtered facts

Layer 2: Memory Lifecycle
  MemoryPyramid          — L1→L2→L3 processing (agent-local)
  FactExtractor          — extract atomic facts from LLM output
  Reflection             — L2→L3 insight generation

Layer 3: Context Assembly
  MemoryAssembler        — task + requester → memory snapshot
  ZoomSelector           — select appropriate detail level
  TokenBudgeter          — control context window usage

Layer 4: Sync
  WorkspaceSync          — agent ↔ workspace memory sync
  FactPublisher          — agent insights → workspace facts
  FactFetcher            — workspace facts → agent working context
```

---

## 7. Design Tensions

### Structured vs Flexible
- Structured: `Fact(entity="acme", attribute="employees", value=200)` — precise but rigid
- Flexible: `Fact(content="Acme has 200 employees")` — flexible but hard to query
- Likely need both: structured metadata + free-text content

### Real-time vs Batch
- Fetch from workspace every LLM call? (slow but fresh)
- Fetch once per session? (fast but stale)
- Subscribe to changes? (complex but optimal)

### Entity-centric vs Flat
- Entity grouping (acme_corp/ folder) — natural for CRM-like data
- Flat facts — simpler, more flexible, better for cross-entity insights
- Probably start flat, add entity grouping later

---

## 8. Implementation Roadmap

### SDK V2 (Foundation)
- Fact type with classification + domains
- FactStore protocol + InMemoryFactStore
- WorkspaceMemory (shared FactStore + access filtering)
- AgentMemory (L1-L2-L3 + workspace reference)
- ClearanceProfile + AccessFilter
- MemoryAssembler (basic: relevance + permission + budget)
- Auto-recording in decorators
- AuthorityConfig on Role

### SDK V3 (Intelligence)
- FactExtractor (LLM extracts atomic facts from output)
- Zoom-level generation (LLM summarization)
- Entity-centric organization
- Sophisticated MemoryAssembler (context-aware density)
- Real-time workspace subscriptions

### SDK V4 (Collaboration)
- Cross-agent memory queries
- Shared insights with visibility control
- Belief promotion pipeline (L3→L4)
- Knowledge graph relationships between facts
- Audit logging
- Human-agent information density negotiation

---

*Brainstorm output: 2026-02-17. To be refined into implementation design.*
