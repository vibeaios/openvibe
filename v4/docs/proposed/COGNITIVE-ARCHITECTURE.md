# Cognitive Architecture for AI Agents — Design Document

> **Date:** 2026-02-16
> **Status:** Proposed
> **Author:** Charles (APOS)
> **Depends on:** Operator pattern (implemented), Inter-Operator Comms (proposed), Operator SDK (proposed)

---

## 1. Problem

The current operator pattern provides **execution capability** — stateless workflows that process inputs and produce outputs. But production AI agents need more:

1. **Identity** — persistent persona, values, communication style
2. **Memory** — learn from experience, recall relevant knowledge
3. **Goals** — respond to human-world objectives (OKRs), prioritize autonomously
4. **Relationships** — report to humans, delegate to operators, collaborate with peers
5. **Collaboration** — work alongside humans and other agents in shared spaces
6. **Self-evolution** — continuously improve through reflection and learning

Operators are **hands**. This document designs the **brain**.

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  Cognitive Layer (this document)                          │
│  Identity, Memory, Goals, Relationships, Decision Engine  │
│  "WHO the agent is + WHAT it knows + WHAT it decides"     │
└──────────────────┬───────────────────────────────────────┘
                   │ drives
┌──────────────────▼───────────────────────────────────────┐
│  Operator Layer (existing)                                │
│  Workflows, Nodes, LLM calls                              │
│  "WHAT the agent does"                                    │
└──────────────────┬───────────────────────────────────────┘
                   │ executes on
┌──────────────────▼───────────────────────────────────────┐
│  Infrastructure Layer (existing)                          │
│  Temporal, LangGraph, NATS, Claude API                    │
│  "HOW it runs"                                            │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Agent Data Model

```python
@dataclass
class Agent:
    id: str
    identity: Identity
    memory: AgentMemory
    goals: GoalSystem
    relationships: OrgChart
    operators: list[str]        # operator IDs this agent can delegate to
    spaces: list[str]           # collaboration space IDs
    decision_engine: DecisionEngine
```

---

## 4. Identity Layer

Not just a system prompt. A structured, persistent state that is injected into every LLM call.

```yaml
agent:
  id: cro
  name: "Chief Revenue Officer"

  persona:
    values: ["data-driven", "aggressive but measured", "direct"]
    communication_style: "concise, metrics-first, challenges assumptions"
    decision_framework: "ROI > gut feel, always quantify"

  role:
    title: CRO
    domains: ["revenue", "sales", "pipeline", "deals"]

    authority:
      autonomous:
        - qualify_lead
        - trigger_nurture_sequence
        - adjust_lead_scoring_weights
        - generate_pipeline_report
        - send_daily_brief
        - prioritize_deals

      needs_approval:
        - commit_to_deal_terms
        - change_pricing
        - enter_new_market_segment
        - modify_team_assignments
        - change_quarterly_targets

      forbidden:
        - sign_contracts
        - make_hiring_decisions
        - access_competitor_systems
        - modify_own_authority
        - delete_own_memory_l4_l5

    impact_rules:
      high:
        - deal_value > 100000
        - affects_quarterly_target
        - involves_key_account
      medium:
        - deal_value > 20000
        - referral_lead
        - multi_stakeholder
      low:
        - routine_qualification
        - standard_nurture
        - scheduled_report

  context_window:
    always_include:
      - identity/persona.md
      - memory/working/current.md
      - goals/active_okrs.md
```

Every `call_claude()` is augmented with:

```python
system_prompt = f"""
{agent.identity.persona}

## Relevant Memories
{await agent.memory.recall(current_context)}

## Current Goals
{agent.goals.active_okrs}

## Your Task
{original_prompt}
"""
```

---

## 5. Memory Architecture

### 5.1 Memory Pyramid — 5 Levels

Each level is a compression/distillation of the level below.

```
                    ┌───────────┐
                    │ Identity  │  L5 — core persona, rarely changes
                    │           │       only human can modify
                    ├───────────┤
                    │ Beliefs   │  L4 — high-confidence knowledge
                    │           │       agent proposes, human approves
                   ┌┴───────────┴┐
                   │  Insights   │  L3 — patterns from episodes
                   │             │       agent writes freely
                  ┌┴─────────────┴┐
                  │   Episodes     │  L2 — structured event records
                  │                │       auto-created per workflow run
                 ┌┴────────────────┴┐
                 │    Raw Log        │  L1 — complete interaction history
                 │                   │       immutable, append-only
                 └───────────────────┘
```

### 5.2 Level Definitions

```python
# L1: Raw Log — complete lifecycle record
@dataclass
class RawLogEntry:
    id: str
    agent_id: str
    timestamp: str
    type: str                   # "llm_call" | "event_received" | "action_taken" | "message_sent"
    input: dict                 # full input
    output: dict                # full output
    metadata: dict              # model, tokens, cost, latency
    # IMMUTABLE — append-only, never deleted

# L2: Episode — meaningful events, structured from raw logs
@dataclass
class Episode:
    id: str
    agent_id: str
    timestamp: str
    action: str                 # "qualified_lead", "escalated_deal", "generated_report"
    trigger: str                # what caused this
    context_snapshot: dict      # goals, memories consulted at decision time
    outcome: dict               # what happened
    feedback: str | None        # human feedback
    raw_log_ids: list[str]      # trace back to L1
    tags: list[str]             # for querying
    classification: str         # access control (see Section 6)
    domains: list[str]          # information domains (see Section 6)

# L3: Insight — patterns discovered across episodes
@dataclass
class Insight:
    id: str
    agent_id: str
    content: str                # "Webinar leads convert 2x vs cold inbound"
    confidence: float           # 0.0 - 1.0
    evidence_count: int         # how many episodes support this
    source_episodes: list[str]  # L2 IDs
    created_at: str
    last_confirmed: str         # last time an episode confirmed this
    last_contradicted: str | None
    status: str                 # "active" | "weakening" | "retired"
    classification: str
    domains: list[str]

# L4: Belief — high-confidence knowledge that influences decisions
@dataclass
class Belief:
    id: str
    agent_id: str
    statement: str              # "Enterprise deals need VP sponsor to close"
    confidence: float           # must be > 0.8 to qualify as belief
    source_insights: list[str]  # L3 IDs
    influences: list[str]       # which decisions/prompts this affects
    created_at: str
    review_date: str            # beliefs need periodic review
    approved_by: str            # human who approved promotion to belief
    classification: str
    domains: list[str]

# L5: Identity — core persona, almost never changes
@dataclass
class IdentityState:
    agent_id: str
    persona: dict               # values, style, framework
    role: dict                  # title, authority, domains
    version: int                # changes tracked
    changed_by: str             # only human can change L5
    changed_at: str
```

### 5.3 Distillation Pipeline

```
L1 → L2: Real-time
  Every workflow completion → auto-create Episode (structure raw logs)

L2 → L3: Periodic (daily)
  Temporal cron → agent.reflect()
  "Analyze this week's episodes. What patterns appear?"
  → New Insights or update existing Insight confidence

L3 → L4: Threshold-triggered
  When Insight.confidence > 0.8 AND evidence_count > 10
  → Agent proposes promotion to Belief
  → Requires human approval

L4 → L5: Human-only
  Identity changes only by human decision
  Agent can propose: "Based on my experience, I think my role should expand..."
  Execution requires human approve
```

```python
class AgentMemory:
    raw_log: RawLogStore        # append-only log (Postgres or object storage)
    episodic: EpisodicStore     # Postgres — structured events
    semantic: SemanticStore     # pgvector — insights (vector-searchable)
    beliefs: BeliefStore        # Postgres — high-confidence knowledge
    working: WorkingMemory      # NATS KV / Redis — current context, volatile

    async def record_episode(self, event: Episode):
        """Every workflow run auto-records an episode."""
        await self.episodic.store(event)

    async def reflect(self):
        """Periodic: analyze recent episodes, extract patterns."""
        recent = await self.episodic.query(since=self.last_reflection)
        analysis = await call_claude(
            system=f"{self.agent.identity}\nYou are reflecting on your recent experiences.",
            user=f"Episodes:\n{recent}\n\nWhat patterns? What should you do differently?",
            model="sonnet",
        )
        new_insights = parse_insights(analysis)
        for insight in new_insights:
            existing = await self.semantic.find_similar(insight)
            if existing:
                existing.confidence += 0.1  # reinforced
                existing.evidence_count += 1
                existing.last_confirmed = now()
                await self.semantic.update(existing)
            else:
                await self.semantic.store(insight)

    async def recall(self, context: str) -> str:
        """Retrieve relevant memories for current task."""
        beliefs = await self.beliefs.search(context)
        insights = await self.semantic.search(context, top_k=5)
        episodes = await self.episodic.search_similar(context, limit=3)
        return format_memories(beliefs, insights, episodes)
```

### 5.4 Self-Evolution Boundaries

```
Agent CAN modify on its own:
  ✅ L1 Raw Log (write — append only)
  ✅ L2 Episodes (write)
  ✅ L3 Insights (write, update confidence)
  ✅ Working memory (current priorities, active context)
  ✅ Workflow execution strategy (which operator, what parameters)
  ✅ Confidence calibration (learn from outcomes)

Agent NEEDS human approval to modify:
  ⚠️ L4 Beliefs (propose, human approves)
  ⚠️ Authority boundaries (can request expansion)
  ⚠️ Reporting relationships (can suggest reorg)
  ⚠️ Operator prompts/configs (can propose adjustments)

Agent can NEVER modify:
  ❌ L5 Identity (only human)
  ❌ Own authority level (cannot self-promote)
  ❌ Permission matrix rules (system-level)
  ❌ Other agents' memory (isolation)
  ❌ Audit logs (immutable)
```

---

## 6. Memory Permission System

### 6.1 Two Dimensions: Domain + Classification

Information access is controlled by the intersection of **what category** and **how sensitive**.

**Classification levels (sensitivity):**

| Level | Name | Access |
|-------|------|--------|
| L0 | Public | Any agent/human in the organization |
| L1 | Internal | Organization members with relevant domain clearance |
| L2 | Confidential | Requires domain-specific clearance |
| L3 | Restricted | Named access only (explicit grant) |

**Information domains:**

| Domain | Examples |
|--------|---------|
| `finance` | Board decisions, funding, burn rate, financial projections |
| `revenue` | Pipeline data, deal terms, sales strategy, commission |
| `product` | Roadmap, architecture, technical debt, feature prioritization |
| `marketing` | Campaigns, content strategy, brand guidelines, market positioning |
| `people` | HR data, performance reviews, compensation, hiring |
| `customer` | PII, account details, support tickets, usage data |
| `strategy` | M&A discussions, competitive intelligence, market entry plans |

### 6.2 Memory Entry Access Tags

Every memory entry carries access control metadata:

```python
@dataclass
class MemoryEntry:
    id: str
    agent_id: str
    content: str
    level: int                  # L1-L5 (pyramid level)

    # Access control
    classification: str         # "public" | "internal" | "confidential" | "restricted"
    domains: list[str]          # ["finance", "revenue"]

    # Explicit overrides
    granted_to: list[str]       # specific agent/human IDs (always allowed)
    denied_to: list[str]        # specific agent/human IDs (always denied, overrides all)
```

### 6.3 Agent/Human Clearance Profile

Each agent and human has a clearance profile specifying their maximum access per domain:

```yaml
cro:
  clearance:
    revenue: confidential       # full access to pipeline, deals
    marketing: internal         # sees campaign results, not strategy details
    finance: internal           # knows budget, not board discussions
    product: internal           # knows roadmap for sales positioning
    customer: confidential      # needs customer data for deals
    strategy: confidential      # competitive intelligence
    people: none                # no access to HR data

cmo:
  clearance:
    revenue: internal           # knows pipeline overview, not deal terms
    marketing: confidential     # full access to all marketing data
    finance: none               # no access to financial data
    product: internal           # knows roadmap for messaging
    customer: internal          # customer personas, not PII
    strategy: confidential      # market positioning
    people: none                # no access to HR data

ceo:  # human
  clearance:
    revenue: restricted         # full access to everything
    marketing: restricted
    finance: restricted
    product: restricted
    customer: restricted
    strategy: restricted
    people: restricted
```

### 6.4 Access Decision Logic

```python
CLASSIFICATION_RANK = {
    "none": 0,
    "public": 1,
    "internal": 2,
    "confidential": 3,
    "restricted": 4,
}

class MemoryAccessControl:

    def can_access(self, accessor: str, memory: MemoryEntry) -> bool:
        # Rule 1: Explicit deny always wins
        if accessor in memory.denied_to:
            return False

        # Rule 2: Explicit grant always allows
        if accessor in memory.granted_to:
            return True

        # Rule 3: Public is always accessible
        if memory.classification == "public":
            return True

        # Rule 4: Check clearance against classification + domain
        accessor_clearance = self.get_clearance(accessor)

        for domain in memory.domains:
            domain_clearance = accessor_clearance.domains.get(domain, "none")
            if CLASSIFICATION_RANK[domain_clearance] >= CLASSIFICATION_RANK[memory.classification]:
                return True

        return False
```

### 6.5 Access Scenarios

```
Memory: "Board discussing bridge round at $5M pre-money"
  classification: restricted
  domains: [finance, strategy]

  CEO (finance: restricted)     → ✅ access granted
  CFO (finance: restricted)     → ✅ access granted
  CRO (finance: internal)       → ❌ blocked (needs confidential+)
  CMO (finance: none)           → ❌ blocked

Memory: "Acme deal at $150K, negotiating 20% discount"
  classification: confidential
  domains: [revenue, customer]

  CRO (revenue: confidential)   → ✅ access granted
  CEO (revenue: restricted)     → ✅ access granted
  CMO (revenue: internal)       → ❌ blocked (needs confidential)
  CS agent (customer: conf.)    → ✅ access granted (via customer domain)

Memory: "Q1 pipeline at $1.2M / $2M target"
  classification: internal
  domains: [revenue]

  CRO, CMO, CEO, all agents    → ✅ (internal meets internal clearance)
```

### 6.6 Cross-Agent Memory Query

When one agent queries another's memory, results are filtered by clearance:

```python
class CrossAgentMemoryQuery:

    async def query(self, requester: str, target_agent: str, query: str) -> list[MemoryEntry]:
        # Get all relevant memories from target agent
        all_memories = await self.agent_memory(target_agent).search(query)

        # Filter by requester's clearance
        accessible = [
            m for m in all_memories
            if self.acl.can_access(requester, m)
        ]

        # Redact partially accessible memories if needed
        return [self._maybe_redact(requester, m) for m in accessible]
```

### 6.7 Shared Memory Pool

Agents can explicitly share insights with controlled visibility:

```python
class SharedMemoryPool:

    async def share_insight(self, agent_id: str, insight: Insight, visibility: str):
        """
        visibility:
          "team"   — same reporting chain only
          "org"    — all agents in organization
          "space"  — specific collaboration space participants
        """
        shared = SharedInsight(
            source_agent=agent_id,
            content=insight.content,
            confidence=insight.confidence,
            visibility=visibility,
            classification=insight.classification,
            domains=insight.domains,
        )
        await self.store(shared)

    async def adopt_insight(self, agent_id: str, shared_id: str):
        """Agent incorporates shared insight into its own L3, at lower confidence."""
        shared = await self.get(shared_id)
        if not self.acl.can_access(agent_id, shared):
            raise PermissionError("Insufficient clearance")

        local = Insight(
            agent_id=agent_id,
            content=shared.content,
            confidence=shared.confidence * 0.7,  # lower until self-verified
            source_episodes=[],
        )
        await self.agent_memory(agent_id).semantic.store(local)
```

### 6.8 Audit Trail

```python
class MemoryAuditLog:
    """Immutable record of every memory access attempt."""

    async def log_access(self, accessor: str, memory_id: str, granted: bool, reason: str):
        await self.append(AuditEntry(
            timestamp=now(),
            accessor=accessor,
            memory_id=memory_id,
            granted=granted,
            reason=reason,
        ))

    async def log_share(self, sharer: str, memory_id: str, shared_with: str): ...
    async def log_belief_proposal(self, agent_id: str, belief: Belief): ...
    async def log_belief_approval(self, human_id: str, belief_id: str): ...
```

---

## 7. Decision Authority Framework

### 7.1 Four-Dimension Evaluation

Every incoming event is evaluated across four dimensions before the agent decides how to act:

```
Event arrives
    │
    ▼
1. DOMAIN — Is this within my domains?
    ├── No → Ignore or forward to correct agent
    ├── Partial → Collaborate with domain owner
    └── Yes ↓

2. AUTHORITY — Am I allowed to act on this?
    ├── Forbidden → Escalate immediately
    ├── Needs approval → Act + request approval
    └── Autonomous ↓

3. CONFIDENCE — How sure am I about the right action?
    (Assessed by consulting beliefs, insights, similar episodes)

4. IMPACT — How big is the consequence if wrong?
    (Assessed by impact_rules in identity config + goal relevance)
```

### 7.2 Action Matrix: Confidence x Impact

```
┌──────────────┬──────────────────┬──────────────────┬──────────────────┐
│              │ Low Impact       │ Medium Impact    │ High Impact      │
│              │ (routine)        │ (meaningful)     │ (strategic)      │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ High         │ ACT              │ ACT + REPORT     │ ACT + REPORT     │
│ Confidence   │ delegate to      │ delegate, notify │ delegate, notify │
│ (>0.7)       │ operator, log    │ manager after    │ manager before   │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Medium       │ ACT + LEARN      │ ACT + CONSULT    │ PROPOSE          │
│ Confidence   │ try it, observe  │ ask peer, then   │ present options  │
│ (0.4-0.7)    │ outcome          │ act              │ to manager       │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Low          │ EXPERIMENT       │ ESCALATE         │ ESCALATE         │
│ Confidence   │ small test,      │ ask manager for  │ immediately flag │
│ (<0.4)       │ learn from it    │ guidance         │ to manager       │
└──────────────┴──────────────────┴──────────────────┴──────────────────┘
```

### 7.3 Decision Engine Implementation

```python
class DecisionEngine:

    def __init__(self, agent: Agent):
        self.agent = agent

    async def evaluate(self, event: Event) -> Decision:
        # Step 1: Domain check
        domain = self._check_domain(event)
        if domain == "not_mine":
            return Decision(action="ignore")
        if domain == "partial":
            return Decision(action="forward", target=self._find_owner(event))

        # Step 2: Authority check
        authority = self._check_authority(event)
        if authority == "forbidden":
            return Decision(
                action="escalate",
                target=self.agent.relationships.reports_to,
                reason="outside authority bounds",
            )

        # Step 3: Confidence assessment
        confidence = await self._assess_confidence(event)

        # Step 4: Impact assessment
        impact = await self._assess_impact(event)

        # Step 5: Matrix lookup
        action = ACTION_MATRIX[confidence.level][impact.level]

        return Decision(
            action=action.type,
            confidence=confidence,
            impact=impact,
            delegation=self._choose_operator(event) if action.needs_delegation else None,
            notify=self._who_to_notify(action, authority),
            reasoning=self._explain_decision(event, confidence, impact, action),
        )

    async def _assess_confidence(self, event: Event) -> ConfidenceAssessment:
        """How confident am I about the right action?"""

        # Check beliefs (L4) — highest signal
        relevant_beliefs = await self.agent.memory.beliefs.search(event.context)

        # Check insights (L3)
        relevant_insights = await self.agent.memory.semantic.search(event.context, top_k=5)

        # Check similar episodes (L2) — what happened last time?
        similar_episodes = await self.agent.memory.episodic.search_similar(event.context, top_k=3)

        # LLM self-assessment (meta-cognition)
        assessment = await call_claude(
            system=f"{self.agent.identity.system_prompt}\nAssess your confidence.",
            user=f"Event: {event}\nBeliefs: {relevant_beliefs}\n"
                 f"Insights: {relevant_insights}\nSimilar episodes: {similar_episodes}\n"
                 f"How confident are you? Rate 0.0-1.0 and explain.",
            model="haiku",
        )

        return ConfidenceAssessment(
            score=assessment.parsed_score,
            level=_score_to_level(assessment.parsed_score),
            reasoning=assessment.content,
            memories_consulted=len(relevant_beliefs) + len(relevant_insights) + len(similar_episodes),
        )

    async def _assess_impact(self, event: Event) -> ImpactAssessment:
        """How big is the consequence if I'm wrong?"""

        # Rule-based (fast) — from identity.role.impact_rules
        for rule in self.agent.identity.role.impact_rules.get("high", []):
            if self._matches_rule(event, rule):
                return ImpactAssessment(level="high", reason=rule)

        for rule in self.agent.identity.role.impact_rules.get("medium", []):
            if self._matches_rule(event, rule):
                return ImpactAssessment(level="medium", reason=rule)

        # Check goal relevance
        goal_relevance = self._check_goal_relevance(event)
        if goal_relevance > 0.8:
            return ImpactAssessment(level="high", reason="directly impacts active OKR")

        return ImpactAssessment(level="low", reason="routine operation")

    def _check_domain(self, event: Event) -> str:
        my_domains = self.agent.identity.role.domains
        event_domain = event.metadata.get("domain", "unknown")
        if event_domain in my_domains:
            return "mine"
        if any(d in event.tags for d in my_domains):
            return "partial"
        return "not_mine"

    def _check_authority(self, event: Event) -> str:
        action_type = self._infer_action_type(event)
        auth = self.agent.identity.role.authority
        if action_type in auth.get("forbidden", []):
            return "forbidden"
        if action_type in auth.get("needs_approval", []):
            return "needs_approval"
        if action_type in auth.get("autonomous", []):
            return "autonomous"
        return "needs_approval"  # default: ask
```

---

## 8. Organizational Design

### 8.1 Three Layers of Agency

```
┌──────────────────────────────────────────────────────────┐
│  Decision Layer — C-level agents                          │
│  Set strategy, allocate resources, monitor, decide        │
│  DO NOT execute workflows directly                        │
│                                                           │
│  CEO (human)                                              │
│    ├── CRO (agent): revenue strategy, pipeline decisions  │
│    ├── CMO (agent): brand strategy, demand gen decisions   │
│    └── CTO (agent): product + tech decisions               │
├──────────────────────────────────────────────────────────┤
│  Execution Layer — Operators (shared resources)           │
│  Stateless workflow execution, no memory between runs     │
│  Operators are NOT owned by agents — they are shared      │
│                                                           │
│  Revenue Ops     ◄── CRO delegates                        │
│  Content Engine  ◄── CMO delegates (primary)              │
│                  ◄── CRO requests (via CMO)               │
│  Company Intel   ◄── CRO, CMO, CTO can all trigger       │
│  Market Intel    ◄── CMO delegates (primary)              │
│                  ◄── CRO reads insights                   │
│  Customer Success ◄── CRO delegates                       │
├──────────────────────────────────────────────────────────┤
│  Specialist Layer — Domain expert agents (future)         │
│  Deep domain knowledge, own memory, learn over time       │
│                                                           │
│  SEO Specialist  ◄── CMO delegates                        │
│  BDR Agent       ◄── CRO delegates                        │
│  Sales Engineer  ◄── CRO delegates                        │
│  Copywriter      ◄── CMO delegates                        │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Why Not One Super-Agent?

Putting all growth workflows under one agent (e.g., "Chief Growth Officer") has three problems:

**Context window explosion.** A single agent managing all growth must load pipeline data + content calendar + SEO metrics + brand guidelines + campaign performance into every decision. Split agents have focused memory — higher recall precision.

**Belief conflicts.** CRO belief: "Focus on enterprise, bigger deals." CMO belief: "Focus on mid-market, faster sales cycles, better for case studies." In one agent, these contradict. Split agents, both beliefs are correct for their domain. Productive tension resolves in collaboration spaces.

**Learning pollution.** Combined reflection mixes pipeline episodes with content episodes, diluting the learning signal. Separate agents learn deeply in their domain.

### 8.3 Operator Access Control

Operators are shared organizational resources, not owned by a single agent:

```python
OPERATOR_ACCESS = {
    "revenue_ops": {
        "primary": "cro",
        "can_trigger": ["cro"],
        "can_read_output": ["cro", "ceo", "cmo"],
    },
    "content_engine": {
        "primary": "cmo",
        "can_trigger": ["cmo"],
        "can_read_output": ["cmo", "cro", "ceo"],
        "can_request": ["cro"],  # CRO requests content via CMO
    },
    "company_intel": {
        "primary": None,  # shared utility
        "can_trigger": ["cro", "cmo", "cto"],
        "can_read_output": ["cro", "cmo", "cto", "ceo"],
    },
    "market_intel": {
        "primary": "cmo",
        "can_trigger": ["cmo"],
        "can_read_output": ["cmo", "cro", "ceo"],
    },
    "customer_success": {
        "primary": "cro",
        "can_trigger": ["cro"],
        "can_read_output": ["cro", "ceo"],
    },
}
```

### 8.4 Cross-Agent Requests

When CRO needs content, it doesn't directly trigger Content Engine. It requests CMO:

```
CRO: "I need a case study for enterprise fintech deal."
  → CRO.decision_engine: domain="marketing" → not mine → forward to CMO
  → CRO sends request to CMO (via NATS or shared space)

CMO receives request:
  → CMO.decision_engine: domain="marketing" → mine, autonomous
  → CMO delegates to Content Engine operator
  → CMO applies brand beliefs (voice, quality standards)
  → CMO shares output with CRO
```

Why not direct? Because CMO has content-specific beliefs and quality standards that CRO lacks. Content without brand filter is off-brand.

### 8.5 When to Create a New Agent vs Use an Operator Workflow

```
Needs its own AGENT:
  ✅ Needs independent memory + learning over time
  ✅ Needs autonomous decision authority
  ✅ Participates in collaboration spaces
  ✅ Domain knowledge deep enough to justify separate identity

An operator WORKFLOW is sufficient:
  ✅ Stateless execution (input → output, no memory between runs)
  ✅ Always triggered by another agent (no autonomous decisions)
  ✅ No need to interact with other agents
  ✅ Quality judged by triggering agent's beliefs
```

Example: SEO. Today it's a workflow in Content Engine (CMO triggers, reviews output). When SEO becomes complex enough to need its own memory (track ranking changes over months) and its own decisions (autonomously reprioritize keywords), it becomes a specialist agent reporting to CMO.

---

## 9. Goal System

### 9.1 Goal Hierarchy

```python
class GoalSystem:
    okrs: list[OKR]             # from human world (CEO sets)
    sub_goals: list[SubGoal]    # agent decomposes from OKRs
    reactive_goals: list        # triggered by events
    learning_goals: list        # self-improvement targets
```

### 9.2 OKR-Driven Behavior

```
CEO sets OKR: "Q1 pipeline $2M"
    ↓
CRO decomposes:
  - Weekly: qualify 50 leads → revenue_ops.lead_qualification
  - Weekly: 20 personalized outreach → revenue_ops.engagement
  - Daily: monitor pipeline health → revenue_ops.deal_support
  - Weekly: adjust strategy → self.reflect()
    ↓
CRO monitors:
  - Pipeline at 60% → escalate to CEO
  - Conversion dropping → adjust lead scoring weights
  - New segment performing well → request CMO for more content
```

### 9.3 Daily Prioritization

```python
async def prioritize_day(self):
    context = {
        "okrs": self.goals.okrs,
        "pipeline": await self.get_pipeline_state(),
        "recent_events": await self.memory.episodic.recent(limit=10),
        "calendar": await self.get_today_schedule(),
    }
    priorities = await call_claude(
        system=f"{self.identity}\nPrioritize your day.",
        user=f"Context:\n{context}\n\nTop 3 priorities for today?",
        model="sonnet",
    )
    return priorities
```

---

## 10. Cognitive Loop

The core execution cycle for every agent:

```
Perceive → Decide → Act → Observe → Reflect → Learn
```

```python
class CognitiveLoop:

    async def perceive(self, event: Event):
        """Process incoming event."""
        # Update working memory
        await self.agent.memory.working.update(event)

    async def decide(self, event: Event) -> Decision:
        """Determine response."""
        return await self.agent.decision_engine.evaluate(event)

    async def act(self, decision: Decision):
        """Execute decision."""
        if decision.action == "delegate":
            result = await self.agent.runtime.activate(
                decision.delegation.operator_id,
                decision.delegation.trigger_id,
                decision.delegation.input_data,
            )
        elif decision.action == "escalate":
            await self.notify(decision.notify_target, decision.reasoning)
        elif decision.action == "propose":
            await self.post_to_space(decision.space, decision.options)
        # ... other action types

    async def observe(self, action, result):
        """Record what happened."""
        episode = Episode(
            agent_id=self.agent.id,
            action=action.type,
            context_snapshot=self.agent.memory.working.snapshot(),
            outcome=result,
        )
        await self.agent.memory.record_episode(episode)

    async def reflect(self):
        """Periodic: analyze episodes, extract insights."""
        await self.agent.memory.reflect()

    async def learn(self):
        """Promote high-confidence insights to beliefs (with human approval)."""
        candidates = await self.agent.memory.semantic.find_promotion_candidates(
            min_confidence=0.8, min_evidence=10
        )
        for insight in candidates:
            await self.propose_belief(insight)  # queued for human review
```

### CRO's Typical Day

```
06:00  Temporal cron → perceive("daily_start")
       → decide() → prioritize day based on OKRs + pipeline state
       → act() → schedule day's workflows

07:00  NATS events: 12 new HubSpot leads
       → decide() × 12 → all within domain + authority + high confidence
       → act() → delegate to revenue_ops.lead_qualification × 12

09:00  Results: 3 sales, 5 nurture, 4 educate
       → observe() → record 12 episodes
       → act() → post to "Revenue War Room" space

10:00  Space message from CEO: "How's the Acme deal?"
       → perceive() → relevant (about a deal)
       → decide() → recall Acme memories + episodes
       → act() → respond with context + recommendation

14:00  NATS event: deal.risk_detected (Acme stalled 14 days)
       → decide() → domain=mine, authority=autonomous, confidence=high, impact=medium
       → act() → delegate to revenue_ops.deal_support + report to space

18:00  Temporal cron → reflect()
       → analyze 15 episodes
       → new insight: "Webinar leads convert 2x vs cold inbound"
       → store in semantic memory (L3)

Friday  Temporal cron → weekly_report()
        → compile metrics + insights + recommendations
        → post to CEO via Slack
        → update OKR progress
```

---

## 11. Collaboration Spaces

Shared environments where agents and humans interact as peers.

```python
@dataclass
class Space:
    id: str
    name: str                           # "Q1 Revenue War Room"
    participants: list[Participant]     # humans + agents
    shared_context: SharedContext       # documents, dashboards, live state
    message_history: list[Message]

    async def post(self, sender: str, content: str):
        msg = Message(sender=sender, content=content, timestamp=now())
        self.message_history.append(msg)

        # Notify all agent participants
        for p in self.participants:
            if p.type == "agent":
                await self.bus.publish(
                    f"spaces.{self.id}.message",
                    msg.to_dict(),
                )

    async def on_message(self, agent: Agent, message: Message):
        """Agent decides whether and how to respond."""
        should_respond = await agent.decision_engine.evaluate_space_message(message, self)
        if should_respond:
            response = await agent.generate_response(
                message,
                space_context=self.shared_context,
                memories=await agent.memory.recall(message.content),
            )
            await self.post(agent.id, response)
```

---

## 12. Storage Architecture

| Data | Store | Reason |
|------|-------|--------|
| L1 Raw Logs | Object storage (S3) or Postgres (partitioned) | Append-only, high volume, rarely queried |
| L2 Episodes | Postgres | Structured, indexed, queried by time/tags |
| L3 Insights | pgvector | Vector-searchable for semantic recall |
| L4 Beliefs | Postgres | Structured, versioned, audited |
| L5 Identity | YAML files (version controlled) | Human-editable, git-tracked |
| Working Memory | NATS KV or Redis | Fast, volatile, session-scoped |
| Shared Context | NATS KV | Cross-agent, real-time |
| Audit Log | Postgres (append-only) | Immutable, compliance |
| Access Policies | YAML files | Human-editable, version controlled |

---

## 13. Open Questions

| Question | Options | Leaning |
|----------|---------|---------|
| Reflection frequency | Hourly / daily / weekly | Daily for episodes, weekly for deep reflection |
| Belief review cadence | Monthly / quarterly | Quarterly (with human review) |
| Max agents in a space | Unlimited / capped | Cap at 5-7 (mirrors effective team size) |
| Cross-org agents | Support multi-company? | Not in V1, but design for it |
| Agent-to-agent trust | Flat / hierarchical | Hierarchical (manager trusts more than peer) |
| Memory retention | Keep forever / decay | Keep forever with relevance decay on recall |

---

## 14. Relationship to Other Design Docs

| Document | Layer | Status |
|----------|-------|--------|
| `OPERATOR-DESIGN.md` | Execution (operators, workflows, nodes) | Implemented |
| `INTER-OPERATOR-COMMS.md` | Infrastructure (NATS, event bus, KV) | Proposed |
| `OPERATOR-SDK-DESIGN.md` | Developer experience (decorators, API) | Proposed |
| **This document** | **Cognitive (identity, memory, decisions)** | **Proposed** |

Together they form the complete stack: cognitive agents → declarative SDK → operator execution → messaging infrastructure.

---

*Source of truth: This file (cognitive architecture) + `OPERATOR-DESIGN.md` (execution) + `INTER-OPERATOR-COMMS.md` (messaging) + `OPERATOR-SDK-DESIGN.md` (SDK/API)*
