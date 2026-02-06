# R3: Agent Lifecycle Research

> Status: Complete | Researcher: agent-lifecycle-researcher | Date: 2026-02-07

---

## Research Questions

1. When an agent's context window fills up mid-task, what strategies exist?
2. How should context handoff work between agent sessions?
3. Auto-decision framework: when should an agent act autonomously vs ask a human?
4. Task lifecycle state machine: what states, transitions, and recovery paths?
5. Realistic LLM cost estimate for a ~20 person team using agents daily?
6. How do existing frameworks (CrewAI, LangGraph, AutoGen) solve these problems?

---

## Sources Consulted

### Internal Design Documents
- `docs/design/M3-AGENT-RUNTIME.md` -- OpenClaw containerized agent architecture, lifecycle states (idle/processing/thinking/executing/cooldown/error/offline), API design
- `docs/design/M4-TEAM-MEMORY.md` -- Memory API, data model, lifecycle management, auto-creation triggers
- `docs/design/M5-ORCHESTRATION.md` -- Message routing, agent scheduling, task queue, concurrent work manager
- `docs/architecture/DESIGN-SPEC.md` -- Memory-first philosophy, agent types (Personal/Role/Worker), container isolation, 4-layer config
- `docs/design/GAP-ANALYSIS.md` -- Identified gaps: agent long-running tasks only cover request-response, no context handoff protocol, no auto-decision framework, no task lifecycle state machine

### External Research
- CrewAI docs and architecture (crewai.com, docs.crewai.com, AWS Prescriptive Guidance)
- AutoGen/AG2 multi-agent patterns (microsoft/autogen, ag2ai/ag2)
- LangGraph 1.0 stateful workflows and checkpointing (langchain.com, October 2025 release)
- OpenAI Agents SDK handoff patterns (openai.github.io/openai-agents-python)
- Google ADK lifecycle management (google.github.io/adk-docs, v1.0.0 stable)
- Letta/MemGPT memory architecture (letta.com, docs.letta.com)
- Claude Code Tasks and Agent Teams (code.claude.com/docs, January 2026 release)
- Context window management strategies (JetBrains Research Dec 2025, arxiv.org/pdf/2511.22729)
- LLM API pricing comparisons (platform.claude.com/docs, pricepertoken.com, multiple pricing guides)
- Agent auto-decision frameworks (Databricks, multiple 2025 guides on autonomy levels)

---

## Question 1: Context Window Overflow Strategies

### Problem Statement

Current M3 design assumes simple request-response: message in, response out, ~300s timeout. Real agent tasks (code refactoring, research, multi-step analysis) can consume 50K-200K+ tokens of context. When context fills, the agent either crashes, degrades in quality ("context rot"), or loses track of the task.

### Options Explored

#### Option A: Summarization (Progressive Compression)

**Description:** As context fills, older conversation segments are compressed into summaries. Recent exchanges remain verbatim while older content becomes increasingly compressed.

**How it works:**
- Monitor context usage (e.g., at 70% capacity, trigger summarization)
- LLM generates structured summaries: CONTEXT, ACTIONS, OUTCOMES, NEXT STEPS
- Achieves 4-10x token reduction per compression cycle
- Can be applied hierarchically: recent = full, medium = summaries, old = meta-summaries

**Pros:**
- Simple to implement, no external infrastructure needed
- Works within a single session -- no session restart required
- Proven approach used by Claude Code's `/compact` command
- Preserves reasoning continuity (the agent stays "in the loop")

**Cons:**
- Lossy -- details are permanently discarded during summarization
- Summarization itself costs tokens (meta-overhead)
- Quality degrades over very long tasks as summaries compound
- The agent makes its own compression decisions, which can be wrong

**Real-world evidence:** Claude Code uses this as its primary strategy via `/compact`. JetBrains Research (Dec 2025) found that "observation masking" (compressing tool outputs while preserving action/reasoning history) is more effective than blanket summarization for coding agents.

**Verdict: Adopt as baseline.** Every agent needs this capability. It's table stakes, not differentiating.

#### Option B: Checkpointing (State Persistence)

**Description:** Persist agent state to external storage at defined points. If context fills or the agent fails, resume from the last checkpoint with fresh context.

**How it works:**
- At each "super-step" (meaningful unit of work), serialize: task state, decisions made, files modified, current plan, remaining work
- Store checkpoint in database or filesystem
- On resume: load checkpoint into fresh context as a structured prompt
- LangGraph's implementation: `MemorySaver` (dev), `PostgresSaver` (prod)

**Pros:**
- Enables infinite-length tasks (theoretically)
- Clean recovery from failures, crashes, timeouts
- Each resumed session gets a fresh, uncontaminated context
- Natural fit with Claude Code's Tasks feature (disk-persisted task DAGs)

**Cons:**
- Session discontinuity -- the agent loses "feel" for the work across checkpoints
- Checkpoint design is task-specific: a coding checkpoint differs from a research checkpoint
- Requires careful design of what to serialize (too little = lost context, too much = wasted tokens)
- Cold-start overhead on each resume

**Real-world evidence:** LangGraph 1.0 (Oct 2025) built checkpointing as a first-class feature. Claude Code Tasks (Jan 2026) uses filesystem-based task persistence that survives `/clear` and session restarts. Both treat checkpointing as essential for production agents.

**Verdict: Adopt as primary strategy for long-running tasks.** This is the right architecture for OpenVibe's agent runtime, where tasks routinely span multiple sessions.

#### Option C: Hierarchical Agents (Decomposition)

**Description:** Break complex tasks into subtasks, each handled by a child agent with its own context window. A parent agent coordinates.

**How it works:**
- Parent agent analyzes task, creates subtask plan
- Each subtask is dispatched to a child agent with minimal, focused context
- Child agents return results (summaries, artifacts, status)
- Parent synthesizes results and coordinates next steps
- Claude Code Agent Teams uses this pattern: lead + teammates

**Pros:**
- Each child agent gets clean context -- no accumulation problem
- Natural parallelism: multiple subtasks can run concurrently
- Matches Claude Code's existing Team Agent pattern
- Scales well: can nest hierarchies for very complex tasks

**Cons:**
- Coordination overhead: parent must manage n children, each with their own failures
- Inter-agent context sharing is lossy (child doesn't know what sibling discovered)
- N agents = N x token cost minimum
- Adds latency from coordination round-trips
- Parent agent itself can hit context limits if managing many children

**Real-world evidence:** CrewAI's hierarchical process uses a "manager agent" for delegation and validation. Claude Code Agent Teams spawns independent teammates with separate context windows (~40% utilization vs 80-90% single-agent). OpenAI Agents SDK uses handoffs to transfer between specialized agents.

**Verdict: Adopt for complex multi-step tasks.** But the parent/coordinator itself needs checkpointing (Option B) to avoid the same problem at the orchestration level.

#### Option D: Sliding Window with Memory Pointers

**Description:** Keep only recent N turns in context. Replace older content with pointers to external memory that can be retrieved on demand.

**How it works:**
- Fixed window of recent conversation (5-7 turns)
- Older turns stored in external memory (Letta/MemGPT style)
- Agent uses retrieval tools to pull back specific older context when needed
- "Memory blocks" maintain always-visible structured state (Letta's approach)

**Pros:**
- Predictable token usage -- never overflows
- Agent actively manages what's in context
- Good for conversational agents with long histories

**Cons:**
- Retrieval quality depends on the agent knowing what to retrieve
- Adds tool-call overhead for every memory access
- Doesn't help with single large tasks (e.g., analyzing a 100K-line codebase)
- Complex implementation: needs vector store, retrieval pipeline, memory management tools

**Real-world evidence:** Letta/MemGPT pioneered this as the "LLM OS" approach. Their V1 architecture (2025-2026) treats context as RAM and archival storage as disk, with the LLM managing memory movement. Production-proven but complex.

**Verdict: Defer.** This is the right long-term architecture for OpenVibe's conversational threads, but too complex for MVP. The Team Memory (M4) Supabase-based approach is a simpler starting point.

### Recommendation for OpenVibe

**Layered strategy:**

1. **All agents**: Progressive summarization as baseline (like `/compact`)
2. **Long-running tasks**: Checkpointing to filesystem/database, integrated with Task state machine
3. **Complex multi-step work**: Hierarchical decomposition via Agent Teams
4. **Future (post-MVP)**: Sliding window + memory pointers for conversational context, aligned with M4 Memory evolution

The key insight: these are not mutually exclusive. Production systems combine all four. Claude Code already does: `/compact` (summarization) + Tasks (checkpointing) + Agent Teams (hierarchical).

---

## Question 2: Context Handoff Between Agent Sessions

### Problem Statement

Current design has no protocol for passing context between sessions. Each agent session starts from scratch. When a task spans multiple sessions (common for long work), context is lost.

### Options Explored

#### Option A: Structured Handoff Documents

**Description:** At session end, generate a structured handoff document containing everything the next session needs.

**Protocol:**
```
HANDOFF DOCUMENT
================
Task: {task_id}
Status: {in_progress | blocked | complete}
Checkpoint: {checkpoint_id}

## What Was Done
- {completed steps with outcomes}

## Current State
- {files modified, decisions made, open questions}

## What Remains
- {remaining steps in priority order}

## Key Context
- {critical decisions, constraints, discovered information}

## Artifacts
- {files, code, documents produced}
```

**Pros:**
- Human-readable, auditable
- Works across different agent types and runtimes
- Natural fit with OpenVibe's file-based approach (@state/ folder pattern)
- Claude Code's Tasks already use a similar disk-based pattern

**Cons:**
- Handoff quality depends on the outgoing agent's summarization ability
- No guarantee the incoming agent interprets it correctly
- Manual effort to design handoff templates per task type

**Verdict: Adopt.** This is Claude Code's approach (Tasks write to `~/.claude/tasks`) and it works well in practice.

#### Option B: Conversation Replay

**Description:** Replay key portions of the previous session's conversation to the new session.

**Pros:**
- Preserves nuance and reasoning that summaries might lose
- Simple implementation (just feed previous messages)

**Cons:**
- Expensive in tokens -- defeats the purpose of context management
- Replay can confuse the agent (thinking it already did the work)
- Doesn't scale: 3 session handoffs = 3x replay

**Verdict: Reject.** Token-inefficient and confusing. Only use for short continuations.

#### Option C: Shared Memory Bus (Database-Backed)

**Description:** Both outgoing and incoming sessions read/write to a shared memory store. Context is the union of what's in the store.

**How it works:**
- Agent writes key findings, decisions, state to Team Memory (M4) during execution
- On session start, agent queries Memory for task-relevant context
- Memory API provides: recent decisions, project context, task state
- Implemented via M4's existing `loadAgentContext()` pattern

**Pros:**
- Continuous accumulation -- no handoff event needed
- Multiple agents can access the same context simultaneously
- Aligns with M4 Team Memory design
- Supports cross-runtime sharing (OpenClaw, Claude Code, Web)

**Cons:**
- Requires disciplined memory writing during execution (agents often forget)
- Retrieval quality depends on memory organization and search
- No guaranteed ordering -- agent might miss critical context that wasn't written

**Verdict: Adopt as complement to structured handoffs.** The combination works best: structured handoffs for task-specific state, shared memory for accumulated knowledge.

### Recommended Handoff Protocol for OpenVibe

```
Session End:
1. Agent writes structured handoff doc to task storage
2. Agent writes key discoveries/decisions to Team Memory
3. Task state machine transitions to 'suspended' or 'complete'

Session Start:
1. Load task handoff doc (what to do, what was done)
2. Query Team Memory for relevant context (decisions, project info)
3. Resume from checkpoint state
4. Validate: agent confirms understanding before proceeding
```

This mirrors Claude Code's Tasks + Memory pattern, but makes it explicit and cross-runtime compatible.

---

## Question 3: Auto-Decision Framework

### Problem Statement

Current M5 Orchestration has no framework for deciding when an agent should act autonomously vs. escalate to a human. The design assumes either "agent responds" or "doesn't respond" with no middle ground.

### Options Explored

#### Option A: Confidence-Based Thresholds

**Description:** Agent self-reports confidence. Below threshold = escalate.

**Rules:**
- High confidence (>0.8): Act autonomously
- Medium confidence (0.5-0.8): Act but flag for review
- Low confidence (<0.5): Escalate to human

**Pros:** Simple to implement, intuitive
**Cons:** LLMs are notoriously bad at calibrating confidence. Self-reported confidence is unreliable.

**Verdict: Reject as primary mechanism.** Can be used as supplementary signal but not the gate.

#### Option B: Action Classification (Risk-Based)

**Description:** Classify actions by risk/reversibility. Gate by category, not confidence.

**Action Categories:**
```
AUTONOMOUS (no approval needed):
- Read-only operations (search, analyze, summarize)
- Draft generation (documents, messages -- not sent)
- Code suggestions (not committed)
- Internal memory writes
- Status updates

APPROVE-THEN-ACT (human confirms):
- External communications (Slack, email)
- Code commits / PRs
- Data modifications
- Spending decisions
- Anything affecting other humans

ESCALATE (human decides):
- Ambiguous requirements
- Conflicting instructions
- Out-of-scope requests
- Safety/compliance-sensitive actions
- Multi-stakeholder decisions
```

**Pros:**
- Deterministic -- same action always gets same treatment
- Auditable -- clear rules for what agents can do
- Aligns with enterprise compliance needs
- Matches the existing OpenVibe preference: "all external communications must be confirmed before sending"

**Cons:**
- Rigid -- doesn't account for context (same action might be safe in one context, dangerous in another)
- Requires comprehensive action classification upfront
- Agents may find creative workarounds

**Verdict: Adopt as primary mechanism.** This is the right default. Start conservative (most things need approval), relax over time as trust builds.

#### Option C: Progressive Autonomy (Trust Levels)

**Description:** Agents earn more autonomy over time based on track record. Similar to DESIGN-SPEC's 4-layer config: platform defaults -> workspace config -> user preferences.

**Trust Levels:**
```
Level 0 (New Agent): Everything needs approval
Level 1 (Established): Read-only + drafts autonomous
Level 2 (Trusted): + commits, + memory writes autonomous
Level 3 (Senior): + external comms with post-hoc review
Level 4 (Autonomous): Full autonomy, async audit
```

**Advancement criteria:**
- Time in service
- Success rate (tasks completed without human correction)
- Error rate (mistakes caught by humans)
- Domain-specific performance metrics

**Pros:**
- Natural progression that mirrors how human employees gain trust
- Configurable per workspace (medical clinic = slower progression)
- Encourages agent improvement
- Aligns with vertical adaptation (HIPAA = stricter levels)

**Cons:**
- Complex to implement tracking and progression
- Hard to define "success" objectively for all task types
- Risk of premature trust if metrics are gamed

**Verdict: Adopt as evolution path.** MVP starts with Option B (action classification), then adds progressive autonomy as agents prove themselves.

### Recommended Auto-Decision Framework

```
Decision Flow:
1. Agent determines intended action
2. Classify action by risk category (Option B)
3. Check agent's trust level (Option C) for borderline cases
4. If autonomous: execute, log for audit
5. If approve-then-act: present to human with context, wait for approval
6. If escalate: present situation, options, and recommendation to human

Override Rules:
- Workspace admin can override any level (lock actions to always-approve)
- Industry templates can enforce minimum approval levels (HIPAA = Level 0-1 max for PHI access)
- User can temporarily grant elevated autonomy for specific tasks
```

---

## Question 4: Task Lifecycle State Machine

### Problem Statement

Current M3 has basic agent states (idle/processing/thinking/executing/cooldown/error/offline) but no task-level state machine. Tasks need independent lifecycle management -- an agent can go offline while a task is suspended.

### Recommended State Machine

```
                    +-----------+
                    |  CREATED  |
                    +-----+-----+
                          |
                    (agent assigned)
                          |
                    +-----v-----+
                    |  QUEUED   |
                    +-----+-----+
                          |
                    (agent picks up)
                          |
                    +-----v-----+
              +---->| RUNNING   |<----+
              |     +-----+-----+     |
              |           |           |
              |     +-----+-----+    (resume)
              |     |           |     |
              |  (blocked)   (complete)
              |     |           |
              | +---v---+  +---v------+
              | |BLOCKED|  |COMPLETING|
              | +---+---+  +---+------+
              |     |           |
              | (unblocked)  (verified)
              |     |           |
              +-----+     +----v----+
                           |COMPLETED|
                           +---------+

        Error from any state:
              +--------+
              | FAILED |
              +---+----+
                  |
            (retry or abandon)
                  |
            +-----v-----+
            | RETRYING  |---> QUEUED
            +-----------+
                  or
            +-----v------+
            | ABANDONED  |
            +------------+

        Timeout from RUNNING:
              +-----------+
              | SUSPENDED |---(resume)---> RUNNING
              +-----------+
```

**States:**

| State | Description | Entry Condition | Exit Conditions |
|-------|-------------|-----------------|-----------------|
| CREATED | Task defined, not yet queued | Task creation | Agent assigned -> QUEUED |
| QUEUED | Waiting for agent availability | Agent assigned | Agent picks up -> RUNNING |
| RUNNING | Agent actively working | Agent starts work | Complete, blocked, timeout, error |
| BLOCKED | Waiting on external input | Agent declares blocker | Blocker resolved -> RUNNING |
| SUSPENDED | Paused (context full, timeout) | Context overflow, timeout | Resume triggered -> RUNNING |
| COMPLETING | Work done, verification pending | Agent declares complete | Verification passed -> COMPLETED |
| COMPLETED | Successfully finished | Verification passed | Terminal |
| FAILED | Error occurred | Unrecoverable error | Retry -> RETRYING, or ABANDONED |
| RETRYING | Preparing to retry | Retry triggered | -> QUEUED |
| ABANDONED | Permanently stopped | Max retries exceeded, or human decision | Terminal |

**Key Transitions:**

- `RUNNING -> SUSPENDED`: Agent's context window fills. Checkpoint is written. Task can be resumed by same or different agent.
- `SUSPENDED -> RUNNING`: New session loads checkpoint and continues.
- `RUNNING -> BLOCKED`: Agent needs human input, external API result, or another task to complete first.
- `BLOCKED -> RUNNING`: Blocker resolved (human responds, dependency completes).
- `FAILED -> RETRYING -> QUEUED`: Automatic retry with backoff. Max 3 retries (configurable).

**Integration with Claude Code Tasks:**

Claude Code Tasks (Jan 2026) already implement a DAG-based task model with status tracking and dependency blocking. OpenVibe's state machine should align with this rather than compete. The key extension is: Claude Code Tasks are local to one machine. OpenVibe's task state needs to be cross-runtime (visible from Web UI, CLI, and OpenClaw).

---

## Question 5: LLM Cost Estimation (~20 Person Team)

### Assumptions

- **Team size**: 20 humans
- **Active agents**: ~5 specialized agents + personal agents per human
- **Usage pattern**: Business hours (8h/day), 5 days/week
- **Primary model**: Claude Sonnet 4.5 ($3 input / $15 output per 1M tokens)
- **Heavy model**: Claude Opus 4.5 ($5 input / $25 output per 1M tokens) for complex tasks
- **Light model**: Claude Haiku 4.5 ($1 input / $5 output per 1M tokens) for routing, classification

### Daily Token Consumption Model

#### Conversational Interactions (Thread Messages)

| Activity | Per Interaction | Daily Per User | Daily Team |
|----------|----------------|----------------|------------|
| Simple Q&A | ~2K input + ~1K output | 20 interactions | 400 interactions |
| Complex discussion | ~10K input + ~5K output | 5 interactions | 100 interactions |
| Agent-to-agent (in threads) | ~5K input + ~3K output | 10 per thread | 200 interactions |

Daily thread tokens:
- Simple: 400 x 3K = 1.2M tokens
- Complex: 100 x 15K = 1.5M tokens
- Agent-to-agent: 200 x 8K = 1.6M tokens
- **Subtotal: ~4.3M tokens/day**

#### Agent Task Execution

| Task Type | Tokens Per Task | Daily Count | Daily Total |
|-----------|-----------------|-------------|-------------|
| Code review | ~50K (context + output) | 10 | 500K |
| Research task | ~100K (multi-step) | 5 | 500K |
| Document draft | ~30K | 15 | 450K |
| Summarization | ~20K | 20 | 400K |
| Orchestration overhead | ~5K per routing decision | 50 | 250K |
| Context summarization/compact | ~10K per event | 30 | 300K |

**Subtotal: ~2.4M tokens/day**

#### Agent Teams (Hierarchical Decomposition)

When using Claude Code Agent Teams or similar:
- 5-agent team = 5x token multiplier on coordinated tasks
- Assume 3-5 coordinated tasks per day
- Per coordinated task: ~200K tokens (lead + 4 teammates)

**Subtotal: ~800K tokens/day**

#### Memory Operations

- Embedding generation: ~500K tokens/day (for memory indexing)
- Memory retrieval context: ~200K tokens/day

**Subtotal: ~700K tokens/day**

### Daily Total: ~8.2M tokens

### Cost Breakdown

| Model | Token Share | Daily Tokens | Daily Cost |
|-------|------------|-------------|------------|
| Sonnet 4.5 (primary) | 60% | 4.9M | ~$29 |
| Haiku 4.5 (routing/classification) | 25% | 2.1M | ~$6 |
| Opus 4.5 (complex tasks) | 10% | 0.8M | ~$12 |
| Embedding (ada-002 or equivalent) | 5% | 0.4M | ~$0.10 |

**Daily cost: ~$47/day**
**Monthly cost (22 working days): ~$1,034/month**
**Annual cost: ~$12,400/year**

### Cost Scenarios

| Scenario | Monthly Cost | Notes |
|----------|-------------|-------|
| Conservative (light usage) | ~$500 | Mostly Q&A, few complex tasks |
| Moderate (above estimate) | ~$1,000 | Regular agent usage, some teams |
| Heavy (power users + agent teams) | ~$2,500 | Frequent multi-agent coordination |
| Peak (complex projects) | ~$5,000+ | Multiple concurrent agent teams, heavy research |

### Cost Optimization Levers

1. **Prompt caching** (90% savings on cached tokens): System prompts, common context -> saves ~$200/month
2. **Batch API** (50% discount): Non-urgent tasks processed async -> saves ~$150/month
3. **Model routing**: Use Haiku for simple tasks, Sonnet for medium, Opus only when needed
4. **Summarization**: Aggressive context compression reduces repeat token costs
5. **Caching agent responses**: Don't re-run identical queries

### Key Insight

At $1,000-2,500/month for a 20-person team, this is comparable to existing SaaS tools (Slack: ~$15/user/month = $300/month, but Slack doesn't include AI agents). The value proposition is clear if agents save even 1 hour/person/day.

**Risk factor:** Token costs are falling ~50-67% per year (Claude 4.5 series is 67% cheaper than Claude 4.1). By the time OpenVibe reaches production dogfood, costs will likely be lower.

---

## Question 6: Framework Comparison

### CrewAI

**Architecture:** Role-based agents organized into "Crews" with task delegation. Two modes: sequential (waterfall) and hierarchical (manager agent delegates).

**Strengths:**
- Simple mental model: define agents with roles, goals, backstory
- Hierarchical mode has a built-in "manager agent" that handles delegation and validation
- Memory system (short-term, long-term, entity memory) with optional RAG
- Growing ecosystem: Enterprise offering (Oct 2024), Crews Marketplace (2025)

**Weaknesses:**
- Memory is agent-local, not shared team memory with semantic search
- No native checkpointing -- tasks must complete in one session
- Context window management is rudimentary (no progressive summarization)
- Tightly coupled to Python -- no multi-runtime support

**Relevance to OpenVibe:**
- Role-based agent definitions are a good pattern to adopt
- Hierarchical delegation pattern maps to OpenVibe's orchestration needs
- Memory system is insufficient for OpenVibe's cross-runtime requirements
- No task lifecycle state machine -- tasks either complete or fail

### LangGraph

**Architecture:** Stateful, graph-based agent workflows. Nodes are processing steps, edges are transitions. State is explicit and reducer-driven.

**Strengths:**
- First-class checkpointing with multiple backends (Memory, SQLite, Postgres)
- Human-in-the-loop as a graph node (clean abstraction)
- State replay, time-travel debugging, resumption after failure
- LangGraph 1.0 (Oct 2025) is production-ready
- Best-in-class state management

**Weaknesses:**
- Complex abstractions (graph theory) for what could be simpler workflows
- Tightly coupled to LangChain ecosystem
- Python/JS only, no cross-runtime protocol
- Primarily designed for single-agent workflows, multi-agent is bolted on

**Relevance to OpenVibe:**
- Checkpointing architecture is the gold standard -- OpenVibe should adopt the pattern
- State management via reducers is over-engineered for MVP but right long-term
- Human-in-the-loop as a graph node is a clean model to study
- Doesn't solve cross-runtime context or agent-to-agent communication

### AutoGen / AG2

**Architecture:** Multi-agent conversation framework. Agents converse with each other to accomplish tasks. Two forks: AG2 (community, stable) and Microsoft AutoGen 0.4 (rewrite).

**Strengths:**
- Native multi-agent conversation -- agents talk to each other naturally
- Flexible topology: pairs, groups, hierarchies, sequential
- Code execution sandboxing built-in
- AG2 has "Magentic-One" -- a team of generalist agents

**Weaknesses:**
- Fork confusion: AG2 vs AutoGen 0.4 are diverging architecturally
- No built-in checkpointing or state persistence
- Memory management is conversation history only -- no structured memory
- Python-only for the serious features

**Relevance to OpenVibe:**
- Multi-agent conversation model aligns well with OpenVibe's thread-based design
- Agent-to-agent communication in conversations is the closest to OpenVibe's vision
- Lack of persistence and memory makes it unsuitable as-is
- The fork situation is a cautionary tale: don't depend on a single vendor's framework

### OpenAI Agents SDK

**Architecture:** Lightweight framework for multi-agent workflows with handoffs, guardrails, and tracing. Provider-agnostic despite the name.

**Strengths:**
- Clean handoff mechanism: agents transfer control with full conversation history
- Guardrails (input/output validation) as first-class concept
- Tracing built in (OpenTelemetry compatible)
- Simple, minimal API -- easy to understand and extend

**Weaknesses:**
- No checkpointing or state persistence (conversations are ephemeral)
- Handoffs pass full conversation history (expensive, doesn't scale)
- No shared memory or knowledge base
- Relatively new, less battle-tested than LangGraph

**Relevance to OpenVibe:**
- Handoff pattern is relevant but needs modification (structured handoffs instead of full history replay)
- Guardrails concept maps to OpenVibe's auto-decision framework
- Tracing architecture is worth studying
- Too lightweight for OpenVibe's needs -- would need extensive extension

### Google ADK

**Architecture:** Full-lifecycle agent framework with built-in state management, session persistence, evaluation tools, and deployment to Vertex AI.

**Strengths:**
- Comprehensive lifecycle: develop, test, evaluate, deploy, monitor
- Session state with magic prefixes (`user:`, `app:`) for scoped persistence
- Native A2A protocol support for inter-agent communication
- Multiple deployment backends (local, Cloud Run, Vertex AI Agent Engine)
- TypeScript SDK available (Jan 2026)

**Weaknesses:**
- Deeply tied to Google Cloud ecosystem (Vertex AI Agent Engine)
- A2A protocol is still young (v0.3, Jun 2025)
- State management is session-scoped, not task-scoped
- Less community adoption than LangGraph or CrewAI

**Relevance to OpenVibe:**
- Session state management pattern is directly applicable
- A2A protocol is worth watching but too immature to build on
- Evaluation framework is valuable for testing agents
- Google Cloud lock-in is a concern for OpenVibe's multi-deployment goals

### Letta (MemGPT)

**Architecture:** "LLM OS" -- treats context window as RAM, external storage as disk. Agents self-manage memory using tools.

**Strengths:**
- Most sophisticated memory management of any framework
- Agents actively edit their own in-context memory
- Memory blocks: structured, persistent, always-visible context sections
- Production-ready: REST API, database backends, SDKs
- Conversations API (Jan 2026) for shared memory across agents

**Weaknesses:**
- Complex to set up and operate
- Memory management overhead (every memory operation = tool call = tokens)
- Primarily single-agent focused (multi-agent is emerging)
- Smaller community than LangGraph or CrewAI

**Relevance to OpenVibe:**
- Memory block concept is directly applicable to Team Memory design
- Self-editing memory is the right long-term vision
- "LLM OS" philosophy aligns with OpenVibe's Memory-first approach
- Too complex for MVP but should inform M4 evolution

### Comparative Summary

| Capability | CrewAI | LangGraph | AutoGen/AG2 | OpenAI SDK | Google ADK | Letta |
|-----------|--------|-----------|-------------|------------|------------|-------|
| Context overflow handling | Weak | Strong (checkpoint) | Weak | None | Medium | Strong (memory mgmt) |
| Session handoff | None | Strong (checkpoint) | None | Handoff tool | Session state | Memory blocks |
| Multi-agent | Strong | Medium | Strong | Strong (handoffs) | Medium (A2A) | Emerging |
| Memory / persistence | Basic | Checkpoint-based | None | None | Session state | Strong |
| Cross-runtime | No | No | No | No | Partial (A2A) | No |
| Task lifecycle | Basic | Graph-based | None | None | Medium | None |
| Human-in-the-loop | Basic | Strong | Basic | Guardrails | Basic | Basic |
| Production readiness | Medium | High | Medium | Medium | High | Medium |

### Key Takeaway

**No single framework solves OpenVibe's needs.** The closest combination would be:
- LangGraph's checkpointing + state management
- CrewAI's role-based agent definitions
- Letta's memory management philosophy
- OpenAI SDK's handoff + guardrails patterns
- Google ADK's session state scoping
- A2A protocol for inter-agent communication standards

OpenVibe needs to build its own agent lifecycle layer, but should steal the best ideas from each framework rather than adopting any one wholesale.

---

## Open Questions

1. **Checkpoint format standardization**: Should OpenVibe define a standard checkpoint format that all agent types (OpenClaw, Claude Code, custom) can produce and consume? Or let each runtime define its own?

2. **Context window size assumptions**: Current estimates assume ~200K token windows (Claude Sonnet 4.5). As windows grow to 1M+ (Claude Opus 4.6), does the overflow problem diminish enough to defer solving it?

3. **Agent Teams cost viability**: 5x token multiplier for coordinated tasks may make heavy team usage prohibitively expensive for smaller customers. Need pricing tier analysis.

4. **Trust level calibration**: How to objectively measure "agent success rate" for progressive autonomy? Need to define measurable quality metrics per task type.

5. **Cross-framework agent lifecycle**: If a task starts in Claude Code (via CLI) and needs to continue in OpenClaw (via Telegram), what's the handoff mechanism? This is partially answered in R7 but needs concrete protocol design.

6. **Claude Code Tasks alignment**: Claude Code Tasks (Jan 2026) add filesystem-based task persistence. Should OpenVibe's task state machine wrap Claude Code Tasks, or be an independent system that works alongside them?

---

## Rejected Approaches

### 1. Full Conversation Replay for Handoffs

**Why rejected:** Token-prohibitive. A 100-turn conversation at ~5K tokens/turn = 500K tokens just for replay. This defeats the purpose of managing context.

**Reconsider when:** Context windows become so large (10M+ tokens) and cheap enough that replay becomes viable. Possibly 2027+.

### 2. Adopting a Single Framework (CrewAI/LangGraph/etc.)

**Why rejected:** No framework solves the cross-runtime problem. All are Python-only or single-runtime. OpenVibe's core challenge is bridging OpenClaw, Claude Code, and Web -- none of these frameworks address that.

**Reconsider when:** A framework adds genuine cross-runtime support and A2A protocol adoption becomes mainstream.

### 3. Agent Self-Reported Confidence as Primary Decision Gate

**Why rejected:** LLMs are poorly calibrated on confidence. Research consistently shows they express high confidence even when wrong. Action classification (risk-based) is more reliable.

**Reconsider when:** LLM calibration significantly improves, possibly with specialized fine-tuning for confidence estimation.

### 4. Pure Event-Driven Architecture (No Task State Machine)

**Why rejected:** Events alone don't capture the full task lifecycle. You need to answer "what's the current status of task X?" which requires state, not just events.

**Reconsider when:** Never -- state machines are the right abstraction for task lifecycle. Events complement them (event sourcing for audit), but don't replace them.

### 5. Letta/MemGPT-Style Memory Self-Management for MVP

**Why rejected:** Too complex for MVP. Requires agents to learn memory management tools, adds token overhead for every memory operation, and needs sophisticated prompting. Simpler checkpoint + structured handoff approach gives 80% of the benefit at 20% of the complexity.

**Reconsider when:** Post-MVP, when the memory system is mature enough to support agent-driven memory management. Likely Phase 3+.

---

*Research completed: 2026-02-07*
*Researcher: agent-lifecycle-researcher*
