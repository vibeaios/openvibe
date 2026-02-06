# Phase 1 Research Synthesis

> THE input document for Phase 2 (Design MVP)
> Status: Complete | Researcher: integration-critic | Date: 2026-02-07

---

## Executive Summary

1. **The fork/resolve thread model (R1) is the right core differentiator**, but it is unproven with real users. The interaction model has been reframed from Git semantics (branch/merge/conflict) to simpler concepts (fork/resolve/abandon). AI-generated resolution summaries are the single most important technical capability to validate.

2. **No existing framework solves cross-runtime context unification (R7).** This is OpenVibe's strongest architectural opportunity. However, it is infrastructure work that the dogfood user (the Vibe team) will not directly appreciate. Defer deep investment to Phase 2-3; build minimal shared context for MVP.

3. **The cost model is viable.** ~$1,000-2,500/month for a 20-person team using AI agents daily. Token costs are falling 50-67% annually. The value proposition holds if agents save even 1 hour/person/day.

4. **The "one codebase, all industries" vision is 75% true.** Config-driven UI handles 75% of vertical differentiation. The remaining 25% requires custom component development per vertical. This is a go-to-market cost, not a technical blocker. For dogfood, verticals are irrelevant -- focus on the Vibe team's needs.

5. **Claude Code should be used as one agent runtime, not THE platform.** The recommended architecture (R4) is "wrap + extend" with a runtime-agnostic interface. This preserves flexibility while leveraging Claude Code's excellent coding capabilities.

---

## Key Findings Across All Research (Ranked by Impact)

### 1. Fork/Resolve Is Simpler and Better Than Branch/Merge (R1)

The original DESIGN-SPEC proposed full Git semantics (branch/merge/checkout/diff). R1's research -- drawing on Discourse's 15+ years of threading data, ChatGPT's branching feature, and analysis of GitChat/Forky/Threds.dev -- concludes this is overengineered. No product has succeeded with full Git-like conversation branching at multi-user scale.

The recommended model: **fork** (create a side conversation from any message), **resolve** (AI summarizes the fork's conclusion back to the parent thread), **abandon** (archive without summary). This is the minimum viable interaction that is differentiated without being confusing.

**Impact: CRITICAL.** This reframes the entire product. M1-THREAD-ENGINE.md needs rewriting.

### 2. AI Summary Quality Is the Load-Bearing Wall (R1, R3)

The fork/resolve flow depends entirely on AI generating good resolution summaries. If summaries are bad, the main thread is polluted with low-quality information, and the entire interaction model fails. This is the single highest-risk technical dependency.

**Impact: CRITICAL.** Must prototype and test summary quality with real Vibe team conversations before committing to full implementation. This should be the first thing built in Phase 3.

### 3. No Framework Solves Cross-Runtime Context (R7)

CrewAI, LangGraph, AutoGen, OpenAI SDK, Google ADK, Letta -- none of them handle context propagation across different runtimes (CLI + messaging + web). All assume single-runtime operation. OpenVibe's Context Unification Layer (extending M4 Memory with Supabase Realtime + MCP server + REST API) would be genuinely novel.

**Impact: HIGH long-term, LOW for dogfood.** The Vibe team's immediate need is a better Slack, not cross-runtime context. Build the architecture seams (provider interfaces) now, implement the full context bus later.

### 4. API-First Is the Right Production Architecture, CLI-Blend Is OK for Dogfood (R5)

Every successful platform (Backstage, Retool, Terraform Cloud, Pulumi) evolved from CLI-first to API-first. The CLI-blend approach (agents executing via Claude Code CLI with Web UI as facade) has an unacceptable risk matrix for production (fragile output parsing, no structured progress events, vendor-controlled update cadence). But it works for internal dogfood.

**Impact: HIGH.** Design the API contract (Task API from R5) in Phase 2 even if the dogfood uses CLI-blend. This prevents architectural debt.

### 5. Config-Driven UI Handles 75-80% of Vertical Differentiation (R2, R5)

The 4-layer config system from DESIGN-SPEC is sound. Config handles layout, terminology, agent roster, permissions, compliance flags, notification rules. Code is needed for novel component types, deep integrations, and vertical-specific UI widgets (~25% of differentiation).

For the core conversation UI, R2 found it is ~95% identical across medical/legal/construction verticals. The differences are metadata fields, compliance indicators, and terminology -- all configurable.

**Impact: MEDIUM.** Validates the "Configuration over Code" principle. Not relevant for dogfood (single-user Vibe team) but critical for future vertical expansion.

### 6. Claude Code Is a Tool, Not the Platform (R4)

Claude Code Agent Teams is excellent for single-machine developer tasks but lacks: cross-runtime coordination, persistent team memory, multi-model support, distributed agents, per-user cost tracking. The recommended integration: use Claude Code SDK as one runtime among several, behind a runtime-agnostic interface.

**Impact: HIGH.** Prevents over-coupling to Anthropic. The `AgentRuntime` interface defined in R4 should be a Phase 2 design artifact.

### 7. Risk-Based Action Classification Beats Confidence-Based Autonomy (R3)

LLMs are poorly calibrated at self-reporting confidence. Instead of "how confident are you?", classify actions by risk: AUTONOMOUS (read-only, drafts), APPROVE-THEN-ACT (external comms, code commits), ESCALATE (ambiguous, multi-stakeholder). This aligns with the existing OpenVibe preference of confirming all external communications before sending.

**Impact: MEDIUM.** Important for agent behavior design. Straightforward to implement as configuration.

### 8. AGPL-3.0 Is the Right License (R6)

For trust-sensitive industries (medical, legal), code auditability IS the product feature. AGPL protects against cloud competitors while being genuinely open source. Redis returned to AGPLv3 in 2025, validating the trend. Revenue comes from managed service, not feature gating.

**Impact: MEDIUM long-term.** Licensing decision can be deferred until closer to public release, but should be decided in Phase 2 to inform architecture (no proprietary dependencies).

### 9. Hybrid LLM Routing Solves the Privacy/Capability Tension (R6)

The fundamental tension: cloud LLMs have better capability but data leaves the boundary; local LLMs keep data private but are weaker. The hybrid router routes by data sensitivity classification (L0-L4). Sensitive data goes local, non-sensitive goes to cloud.

**Impact: LOW for dogfood (Vibe team uses cloud), HIGH for regulated verticals.**

### 10. Task Lifecycle State Machine Is Essential Infrastructure (R3)

Current design only covers simple request-response. Long-running agent tasks need: CREATED -> QUEUED -> RUNNING -> SUSPENDED -> COMPLETING -> COMPLETED, with BLOCKED and FAILED error paths. Checkpointing + structured handoffs enable tasks to span multiple sessions and runtimes.

**Impact: MEDIUM.** Needed for anything beyond simple Q&A, but the full state machine can be built incrementally. MVP needs: QUEUED, RUNNING, COMPLETED, FAILED.

---

## Contradictions Found

### Contradiction 1: R1's Fork Model vs R3's Task Lifecycle

**R1 says:** Agents should work in forks and generate resolution summaries. Forks are lightweight, temporary explorations.

**R3 says:** Agent tasks have a complex lifecycle (10 states) with checkpointing, suspension, and cross-session handoffs.

**The tension:** If a fork is "lightweight," does the agent working in it need the full task lifecycle? What happens when an agent is researching in a fork and its context window fills? Does the fork get "suspended"? Can a different agent resume in the same fork?

**Resolution:** Forks ARE tasks. A fork with an active agent is a task in RUNNING state. If the agent needs to pause, the task moves to SUSPENDED and the fork stays "active" in the UI. The fork/resolve UX is the user-facing layer; the task state machine is the system-facing layer. They must be designed together, not separately.

**Action for Phase 2:** Design fork lifecycle and task lifecycle as one integrated system, not two separate concerns.

### Contradiction 2: R5's API-First vs R4's Claude Code SDK

**R5 says:** API-first is the right production architecture. All agent capabilities should be exposed as APIs. CLI tools are one of many consumers.

**R4 says:** Use Claude Code SDK as primary agent runtime for coding tasks. Claude Code runs locally, processes locally, has local filesystem access.

**The tension:** If agents run via Claude Code SDK on a local machine, how does the Web UI get structured progress events? The CLI-blend risk matrix (R5) shows this is fragile. But the API-first approach requires building an agent runtime that replicates what Claude Code does.

**Resolution:** The R5 recommendation of "Hybrid -- API-First with CLI as Development Tool" is correct. For dogfood, accept the fragility of CLI-blend. Build the API contract (Task submission, progress SSE stream, cancellation, results) in Phase 2 design. In Phase 3-4, Claude Code writes results to Memory via the API, and the Web UI reads from Memory. The CLI is the execution engine; the API is the observation layer. They don't need to be the same thing for dogfood.

**Action for Phase 2:** Define the Task API contract. Accept that dogfood will have two paths: CLI-direct for execution, API for observation/state.

### Contradiction 3: R6's Privacy Model vs R7's Context Bus

**R6 says:** Data has sensitivity levels (L0-L4). Telegram is L0-L1 only. Local-only for L3+ data in regulated verticals. Trust boundaries are per-runtime.

**R7 says:** Memory should be a "context bus" that propagates context across all runtimes. All runtimes read/write to the same unified context layer.

**The tension:** If OpenClaw (Telegram) is L0-L1 only, but the context bus propagates context to all runtimes, sensitive context could leak to Telegram. The context bus doesn't have per-runtime filtering based on data classification.

**Resolution:** The context bus MUST implement classification-aware filtering. When OpenClaw queries the context bus, L2+ items should be excluded or redacted. The ContextItem schema from R7 needs a `classification` field that the resolver checks against the runtime's trust level before delivering.

**Action for Phase 2:** Add data classification to the ContextItem schema. Context resolvers must filter by runtime trust level. This is not optional -- it's a security requirement.

### Contradiction 4: R3's Cost Model vs Agent Teams Token Multiplier

**R3 says:** ~$1,000-2,500/month for a 20-person team. Agent Teams use a 5x token multiplier.

**R3 also says:** Token costs are falling 50-67% annually.

**The tension:** If the team uses Agent Teams heavily (which R4 recommends for complex tasks), the 5x multiplier could push costs to $5,000+/month. The "falling costs" projection assumes current pricing trends continue, which is not guaranteed.

**Resolution:** The cost model needs guardrails, not just projections. Implement per-task and per-user token budgets. Agent Teams should be used for genuinely complex tasks, not for everything. The auto-decision framework (R3) should factor in cost: simple tasks use single agents (Haiku), complex tasks use teams (Sonnet/Opus).

**Action for Phase 2:** Define token budget policies. Include cost-awareness in the orchestration layer.

---

## Gaps Identified

### Gap 1: No User Research on Fork/Resolve

Every researcher assumes the fork/resolve model is better than Slack threads. R1's thread-interaction-designer explicitly notes this is based on analysis of existing tools and forum research, not actual user testing. The Discourse research supports flat-first + occasional branching, but the specific fork/resolve interaction has never been tested with real users.

**Risk:** The entire product bet rests on an untested assumption.

**Recommendation:** Before building full fork implementation, build a minimal prototype (static HTML + a few interactions) and test with the Vibe team. Does anyone actually WANT to fork a conversation? Or do they just want better AI summaries on linear threads? If Tier 1 (smart linear threads) satisfies 90% of needs, the fork/resolve differentiator may be irrelevant.

### Gap 2: Notification Model Is Undefined

No researcher addressed notifications. When someone posts in a fork, who gets notified? All thread participants? Only fork participants? The notification model directly determines signal-to-noise ratio -- the exact problem that makes Slack painful.

**Risk:** If notifications are wrong, OpenVibe recreates Slack's noise problem.

**Recommendation:** Phase 2 must design the notification model. Proposed default: fork creators and @mentioned participants are notified of fork activity. Other thread participants are notified only when a fork is resolved (the summary appears in the main thread). This minimizes noise.

### Gap 3: Search Is Not Addressed

No researcher addressed how search works across threads, forks, and agent memory. Search is the second most important feature in a collaboration tool after messaging (Slack's search is one of its most-used features, despite being mediocre).

**Risk:** Without good search, accumulated memory is worthless.

**Recommendation:** Phase 2 must include search design. Minimum for dogfood: full-text search across messages and fork content. Phase 2+: semantic search powered by embeddings (M4 already plans this).

### Gap 4: Offline and Mobile Are Unaddressed

R5 flagged that construction sites often lack internet. R6 acknowledged edge/air-gapped deployment. But no researcher addressed how the conversation UI works offline or on mobile devices.

**Risk:** For dogfood, this doesn't matter (Vibe team has internet and uses desktops). For construction vertical (Phase 5+), this is critical.

**Recommendation:** Explicitly defer offline and mobile to post-dogfood. Note in Phase 2 design that the data model should not preclude offline support (e.g., use CRDTs or conflict-free append-only design for messages).

### Gap 5: Agent Component Catalog Has No Concrete Design

R2 proposes ~15 base components for agent responses (table, form, action_buttons, summary_card, etc.) but the exact props, interaction patterns, accessibility requirements, and rendering behavior are undefined.

**Risk:** Building the catalog during implementation without a design spec leads to inconsistent, inaccessible components.

**Recommendation:** Phase 2 must produce a component design spec for the 5-7 MVP components. Include props, states, accessibility requirements, and visual design.

### Gap 6: Data Model Is Still High-Level

The GAP-ANALYSIS already flagged this: no global ER diagram exists. R1 proposed changes to the thread/fork data model. R3 proposed a task state machine. R7 proposed context item schemas. These need to be unified into a single data model.

**Recommendation:** Phase 2 must produce a unified data model (DATA-MODEL.md) covering threads, forks, messages, tasks, context items, agent state, and user/team structure.

### Gap 7: Device System Is Irrelevant for Dogfood

DESIGN-SPEC dedicates significant attention to "Device as First-Class Entity" (Vibe Bot, Vibe Dot, Board). For the dogfood (replacing Slack), none of these devices are relevant. The Vibe team uses Slack for text communication, not hardware-mediated interactions.

**Recommendation:** Explicitly defer the entire Device System to post-dogfood. It adds complexity without value for the immediate goal.

---

## Revised Module Priority

The original design had 6 modules (M1-M6) with no clear priority order. Based on research, here is the revised priority:

### Dogfood MVP (Phase 3-4)

| Priority | Module | Scope | Notes |
|----------|--------|-------|-------|
| **P0** | Thread Engine (M1 revised) | Channels, linear threads, fork, resolve | Core interaction model. Rewrite M1 with fork/resolve semantics. |
| **P0** | Frontend (M2 revised) | Web UI for threads, forks, agent responses | Discord-like layout. Core components only. No admin console. |
| **P0** | Agent Runtime (M3 revised) | Claude Code SDK integration, basic agent invocation | Single-agent, @mention-triggered. No teams, no orchestration. |
| **P1** | Memory (M4 minimal) | Store threads, forks, messages, agent context | Supabase/Postgres. No zoom levels. No cross-runtime sync. |
| **P1** | Auth (M6 minimal) | User accounts, workspace, basic roles | Supabase Auth. No RBAC, no RLS beyond workspace isolation. |
| **P2** | Orchestration (M5 minimal) | Message routing to agents, basic task queue | Route @mentions, queue tasks, return results. No scheduling. |

### Phase 2 Design (Not Implementation)

| Module | Design Work | Implementation Phase |
|--------|-------------|---------------------|
| Task API contract | Define input/output/events/cancel/resume | Phase 3-4 |
| Context Unification API | Define REST + MCP server schema | Phase 4-5 |
| Provider interfaces | DataStore, SecretsProvider, LLMProvider | Phase 3 (interfaces only) |
| Agent Component Catalog | 5-7 MVP components design spec | Phase 3 |
| Plugin/Extension API | Backstage-inspired extension points | Phase 5+ |

### Explicitly Deferred

| Module | Why Deferred | Revisit When |
|--------|-------------|--------------|
| Device System | Irrelevant for dogfood | Post-dogfood, hardware integration needed |
| Config System (full 4-layer) | Dogfood uses one config | Pre-vertical expansion |
| Vertical Templates | No verticals in dogfood | Customer demand |
| Admin Console | YAML config during dogfood | Pre-vertical expansion |
| Cross-Runtime Context Bus | Not needed for single-runtime dogfood | Phase 4-5 |
| Hybrid LLM Routing | Dogfood uses cloud only | Phase 5+ (regulated verticals) |
| AGPL Licensing | Internal tool first | Pre-public release |
| Self-Hosted Deployment | SaaS first | Customer demand |
| Mobile UI | Desktop first | User demand |
| Offline Support | Internet assumed | Construction vertical |
| Zoom Levels (L1/L2/L3) | Nice to have, not essential | Scale (>50 users) |

---

## Recommended Phase 2 (Design MVP) Scope

### Must Have for Dogfood (Replace Slack for Vibe Team)

1. **Channels**: Create, join, list. Map Slack's #general, #engineering, #product, #random. This is table-stakes.

2. **Linear threads within channels**: Post a message, reply to it. Thread appears in sidebar or inline. Same mental model as Slack threads. Must work on day 1.

3. **Real-time message updates**: New messages appear without refresh. Supabase Realtime. ~500ms latency is fine (forum model, per INTENT.md).

4. **@mention agents**: Type @AgentName in a message, agent receives and responds in the thread. This is the basic AI augmentation that justifies switching from Slack.

5. **Fork from any message**: One-click to create a side thread from any message. Auto-named. The core differentiator.

6. **Resolve fork**: Click "Resolve", AI generates a 2-3 sentence summary posted to parent thread. Fork archived but accessible. THE killer feature.

7. **Fork sidebar**: View all active forks for a thread. One-line descriptions. Switch between main thread and forks by clicking.

8. **Message rendering**: Markdown, code blocks, basic formatting. Author distinction (human vs agent with different styling).

9. **User accounts + workspace**: Sign up, create workspace, invite team. Supabase Auth with email/password and Google OAuth.

10. **Basic search**: Full-text search across messages. Find things you've discussed.

### Should Have (Makes It Compelling vs. Just Functional)

1. **AI-generated thread summaries**: Auto-generate when threads exceed ~15-20 messages. On-demand via button. This is what Linear does and Slack AI does -- table stakes for AI-augmented collaboration.

2. **Agent-suggested forks**: Agent detects diverging discussion and suggests "This conversation has two topics. Fork into separate threads?" Requires agent to monitor thread content.

3. **Reactions/emoji**: Quick acknowledgment without a reply. Slack has this; absence would be noticed.

4. **File attachments**: Images, documents. Basic upload and display.

5. **Decision/action item extraction**: AI identifies "we decided X" and "Y needs to do Z" and surfaces them. Structured output from thread analysis.

6. **Multiple agent types**: At minimum: a general-purpose assistant, a code-focused agent, and a research agent. @Assistant, @Coder, @Researcher.

7. **Token usage dashboard**: Basic visibility into how many tokens the team is consuming. Not billing, just awareness.

### Will Not Have (For Now)

1. **Branch visualization (git graph)**: Explicitly rejected by R1. Forks are shown in a sidebar list, not a graph.
2. **Diff view between forks**: Rejected by R1. Unnecessary complexity.
3. **Structured thread types** (patient-encounter, case-thread): Phase 5+ vertical feature.
4. **Agent Teams / multi-agent coordination**: Single agents only for dogfood. Agent Teams is Phase 2-3.
5. **Cross-runtime context**: Build the interface, implement later.
6. **Admin console**: Config via YAML during dogfood.
7. **Vertical templates**: Single "vibe-internal" config.
8. **Self-hosted deployment**: Cloud-only via Supabase.
9. **Mobile UI**: Desktop web only.
10. **Notifications beyond in-app**: Use Slack/email bridge initially. Not building a notification system for dogfood.
11. **Device system**: No hardware integration.
12. **Plugin/extension API**: Not needed until vertical expansion.
13. **Private forks or fork-level permissions**: All forks visible to all channel members.
14. **Agent progressive autonomy**: Start with fixed risk-based classification.

---

## Technical Architecture Recommendations

### 1. Data Model: Fork Replaces Branch

```
Thread
  - id, channelId, rootMessageId, status (active/resolved/archived)

Fork (replaces Branch in M1)
  - id, threadId, parentMessageId (where fork starts)
  - description (auto or manual)
  - status: active | resolved | abandoned
  - resolution: string (AI summary, null until resolved)
  - resolvedAt: timestamp
  - createdBy: userId

Message
  - id, threadId, forkId (null = main thread)
  - parentId (reply chain)
  - authorId, authorType (human | agent)
  - content (markdown)
  - timestamp
  - metadata: { isResolution: boolean }

Task
  - id, threadId, forkId
  - status: queued | running | completed | failed
  - agentId, input, output
  - tokenUsage: { input, output }
  - startedAt, completedAt
```

### 2. Tech Stack (Confirmed by Research)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Frontend | Next.js + TailwindCSS + shadcn/ui | Already in M2. Standard, fast. |
| State management | Zustand | Already in M2. Simple, sufficient. |
| API | tRPC | Already in DESIGN-SPEC. Type-safe. |
| Database | Supabase (PostgreSQL + pgvector) | Already in DESIGN-SPEC. Realtime, auth, storage included. |
| Real-time | Supabase Realtime | Validated by R7. Sufficient for dogfood scale. |
| Auth | Supabase Auth | Already in M6. Email, OAuth. |
| Agent runtime | Claude Code SDK (headless) | R4 recommendation. Single-agent for MVP. |
| LLM primary | Claude Sonnet 4.5 | Cost-effective for most tasks. |
| LLM light | Claude Haiku 4.5 | Routing, classification, summaries. |
| LLM heavy | Claude Opus 4.5/4.6 | Complex reasoning when needed. |
| Monorepo | Nx | Already in DESIGN-SPEC. |

### 3. Architecture Layers

```
┌──────────────────────────────────────────────────┐
│  Web UI (Next.js)                                 │
│  - Channels, Threads, Forks, Messages             │
│  - Agent response rendering (component catalog)   │
│  - Fork sidebar, resolution flow                  │
└──────────────────┬───────────────────────────────┘
                   │ tRPC
┌──────────────────▼───────────────────────────────┐
│  API Layer                                        │
│  - Thread/Fork CRUD                               │
│  - Message handling                               │
│  - Agent invocation (via Task queue)              │
│  - Search                                         │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
┌────────▼─────────┐  ┌──────▼──────────────────┐
│  Supabase        │  │  Agent Runtime           │
│  - PostgreSQL    │  │  - Claude Code SDK       │
│  - Realtime      │  │  - Task queue (simple)   │
│  - Auth          │  │  - Result writer         │
│  - Storage       │  │                          │
└──────────────────┘  └─────────────────────────┘
```

### 4. Key Design Decisions Clarified by Research

| Decision | Before Research | After Research | Source |
|----------|----------------|----------------|--------|
| Thread model | Git semantics (branch/merge/diff) | Fork/Resolve (simplified) | R1 |
| Merge strategy | Three options (append/summary/manual) | Resolution only (AI summary) | R1 |
| UI approach | "Generative UI" (LLM generates components) | Config-driven + agent component catalog | R2, R5 |
| Agent runtime | OpenClaw containers | Claude Code SDK + OpenClaw API | R4 |
| Production architecture | Undefined | API-first hybrid (CLI for dogfood, API for production) | R5 |
| Privacy model | Pluggable storage only | Full provider pattern (DataStore + Secrets + LLM) with classification | R6 |
| Cross-runtime context | @state/ files | M4 Memory as context bus (future) | R7 |
| Agent autonomy | Undefined | Risk-based action classification | R3 |
| Open source | Undefined | AGPL-3.0 recommended | R6 |
| Task lifecycle | Request-response only | 10-state machine with checkpointing | R3 |

---

## Risks & Mitigations

### Risk 1: Fork/Resolve Is Not Actually Better Than Slack Threads + AI

**Probability: MEDIUM**

If users find forks confusing or unnecessary, and linear threads with AI summaries (Tier 1) satisfy all needs, then OpenVibe's core differentiator evaporates. It becomes "Slack + AI" which is not enough to justify switching.

**Mitigation:**
- Build Tier 1 (smart linear threads) FIRST. Make it genuinely better than Slack's AI features.
- Add fork/resolve as Tier 2. If the Vibe team never uses forks after 2 weeks of Tier 1, reconsider the product thesis.
- Track fork usage metrics obsessively during dogfood.
- Have a "Plan B" product thesis: "the AI-native team chat" focused on agent quality, not thread interaction innovation.

### Risk 2: AI Summary Quality Is Insufficient

**Probability: MEDIUM**

The resolution summaries that make fork/resolve work could be low-quality, miss key decisions, or inject hallucinated information into the main thread.

**Mitigation:**
- Prototype summary generation with real Vibe team Slack conversations BEFORE building the fork system.
- Include a "thumbs up/down" feedback mechanism on every resolution summary.
- Allow manual editing of resolution summaries before posting.
- Use Claude Sonnet 4.5 (not Haiku) for summaries -- quality matters more than cost here.
- Define a structured prompt that extracts: conclusion, key decisions, action items, dissenting views.

### Risk 3: Engineering Scope Exceeds Team Capacity

**Probability: HIGH**

The full vision (threads + forks + agents + memory + context bus + multi-runtime + vertical config + self-hosted + hybrid LLM) is 2-3 years of work for a large team. A small team attempting all of it will deliver none of it well.

**Mitigation:**
- The "Must Have" list above is deliberately minimal: channels, threads, forks, resolve, @mention agents, basic search, auth.
- Everything else is explicitly deferred.
- Target 4-6 weeks for Phase 3 (core implementation), then 2-4 weeks of dogfood iteration.
- One developer can build the MVP if scope is held. Two developers is ideal.
- Use Supabase for everything possible (auth, database, realtime, storage) to minimize infrastructure work.

### Risk 4: Anthropic Dependency

**Probability: MEDIUM impact, LOW probability of catastrophe**

OpenVibe depends on Claude API pricing, SDK stability, and feature availability. A significant pricing increase, breaking SDK change, or service outage directly impacts the product.

**Mitigation:**
- The AgentRuntime interface from R4 decouples business logic from Claude Code.
- For dogfood, Anthropic dependency is acceptable.
- For production, implement model routing (R3) to use Haiku for cheap tasks, Sonnet for medium, Opus for hard.
- Monitor Anthropic release notes. Pin SDK versions.
- If Anthropic pricing doubles, the cost model still works (~$2,000-5,000/month vs $1,000-2,500).

### Risk 5: Slack AI Becomes Good Enough

**Probability: MEDIUM**

Slack AI is GA and improving. Slackbot is now a context-aware agent. If Slack adds thread summaries that are as good as OpenVibe's, and agents that work in threads as well as OpenVibe's, the switching cost isn't justified.

**Mitigation:**
- Ship fast. The dogfood should be live within 2-3 months.
- Focus on what Slack CANNOT do: fork/resolve (structural limitation), agents working in parallel forks, cross-runtime context (Slack is one surface).
- If after dogfood Slack AI satisfies the Vibe team's needs, pivot the product thesis rather than competing head-on.

---

## Open Questions for Phase 2

1. **Fork depth limit**: Can you fork from a fork? R1 recommends max 1 level of nesting. Phase 2 should test this with the Vibe team and decide.

2. **Fork naming**: Is "fork" the right term for non-technical users? Alternatives: "side discussion," "tangent," "exploration." Should this be configurable per workspace (R2 suggests yes)?

3. **Notification model for forks**: Who gets notified when? This was a gap in R1-R7.

4. **Agent behavior in forks**: When an agent is @mentioned in a fork, does it have context from the parent thread? How much? The agent needs to know the conversation up to the fork point, plus the fork content.

5. **Resolution summary format**: Should it be structured (decision + action items + summary) or free-form text? Structured is more useful but harder to generate reliably.

6. **Invite and onboarding flow**: How does the Vibe team get into OpenVibe? Invite link? Email invitation? Self-signup? This is mundane but blocks dogfood.

7. **Slack migration tooling**: Should we import Slack message history? Or start fresh? Importing history would provide immediate memory value but is complex. Starting fresh is simpler but means the team has to maintain two systems during transition.

8. **Agent response latency tolerance**: R1 mentions "forum model, ~500ms is fine." But agent responses (which require LLM API calls) will take 2-10 seconds. Is that acceptable? Need explicit UX design for "agent is thinking" states.

9. **Cost allocation**: Should token costs be tracked per-user, per-agent, per-workspace, or all three? What's visible to whom?

10. **Data retention**: How long are messages kept? Forks? Resolved forks? Agent task logs? For dogfood, keep everything forever. But design the schema to support retention policies.

---

## Original Design Docs: What to Keep, Revise, Discard

### M1-THREAD-ENGINE.md

**Status: MAJOR REVISION NEEDED**

- **Keep:** Thread concept, channel concept, message data model (parentId chain), real-time updates via Supabase
- **Revise:** Replace "Branch" with "Fork" throughout. Replace "merge" with "resolve." Remove diff, checkout, branch visualization. Simplify to three operations: fork, resolve, abandon. Add fork lifecycle (active/resolved/abandoned) and resolution summary field.
- **Discard:** Git-backed storage (Option B), merge conflict semantics, branch naming conventions, cherry-pick, rebase analogs. The 10-branch limit should be 5-fork limit.
- **Rename to:** M1-THREAD-ENGINE-v2.md or just rewrite.

### M2-FRONTEND.md

**Status: MODERATE REVISION NEEDED**

- **Keep:** Discord-like layout, Next.js + TailwindCSS + shadcn/ui + Zustand, basic component structure
- **Revise:** Replace branch tabs with fork sidebar. Add agent component catalog rendering. Remove generative UI references. Add resolution flow UI. Add "agent is thinking" loading states.
- **Discard:** Branch merge flow mockups, branch visualization tab, anything related to explicit merge UI

### M3-AGENT-RUNTIME.md

**Status: MAJOR REVISION NEEDED**

- **Keep:** Agent type taxonomy (Personal/Role/Worker), basic agent states (idle/processing/error)
- **Revise:** Replace OpenClaw container architecture with Claude Code SDK integration for coding tasks. Add task lifecycle state machine from R3. Add structured handoff protocol. Add auto-decision framework (risk-based classification).
- **Discard:** Container-per-agent for MVP (too complex). OpenClaw containerization (replaced by API wrapper). The 300s timeout (tasks can be long-running with checkpointing).

### M4-TEAM-MEMORY.md

**Status: MINOR REVISION NEEDED**

- **Keep:** Memory hierarchy (Workspace/Space/Thread/Personal), document/vector/metadata stores, Supabase backend, API design
- **Revise:** Add context bus extensions from R7 (source_runtime, scope, urgency, relevance_tags fields). Add context item schema. Plan for MCP server interface (design only, implement later).
- **Discard:** Nothing -- M4 is the strongest module. But defer zoom levels, auto-summarization pipeline, and cross-runtime sync to post-dogfood.

### M5-ORCHESTRATION.md

**Status: MODERATE REVISION NEEDED**

- **Keep:** Message routing concept, @mention routing logic
- **Revise:** Add task queue with basic state tracking (queued/running/completed/failed). Add agent scheduling (simple round-robin for MVP). Add the Task API contract from R5 (input/output/events/cancel).
- **Discard:** Complex concurrent work manager, multi-agent coordination, priority-based scheduling (all post-dogfood).

### M6-AUTH.md

**Status: MINOR REVISION NEEDED**

- **Keep:** Supabase Auth, RBAC concept, RLS policies, API keys for agents
- **Revise:** Add data classification fields (L0-L4) to relevant tables. Add trust level per runtime (for future context bus filtering). Add provider interfaces (DataStore, SecretsProvider) as TypeScript interfaces only.
- **Discard:** Nothing, but defer: HIPAA-specific controls, SAML SSO, complex role hierarchies. Dogfood uses workspace-level isolation only.

### DESIGN-SPEC.md

**Status: SIGNIFICANT UPDATE NEEDED**

- **Keep:** Memory First philosophy, Configuration over Code, Layered Permissions, Supabase choice, Nx monorepo
- **Revise:** Thread Engine section (rewrite for fork/resolve). Agent Architecture section (add Claude Code SDK runtime, task lifecycle). Add Privacy/Deployment section (provider pattern from R6). Add Context Unification section (from R7). Update Device System to "deferred."
- **Discard:** Git-like operation mapping table (commit/branch/checkout/merge/diff/log). The analogy is now "fork/resolve" not "Git for conversations."

### CONFIG-SYSTEM.md

**Status: NO CHANGES FOR DOGFOOD**

The 4-layer config system is sound and validated by R2/R5. No changes needed. For dogfood, only Layer 1 (platform defaults) is active. The full system is Phase 5+.

### VERTICALS.md

**Status: DEFER ENTIRELY**

Not relevant for dogfood. The vertical analysis from R2 and R5 (75/25 config/code split) should be noted but not acted on until Phase 5+.

---

*Synthesis completed: 2026-02-07*
*Researcher: integration-critic*
*This document is the primary input for Phase 2 (Design MVP)*
