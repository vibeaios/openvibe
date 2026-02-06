# Per-User Runtime Architecture

> Status: Complete | Researcher: runtime-architect | Date: 2026-02-07

---

## Research Question

What does "each user has their own runtime environment" mean technically, and how should OpenVibe implement per-user runtimes that enable AI-augmented collaboration for the dogfood MVP (20-person Vibe team)?

The founder's vision: **each person who comes in should have their own runtime environment (like OpenClaw)**, within a thread-based UI, where they can interact with AI agents. OpenClaw is a Telegram bot that serves as a 24/7 AI assistant with personality, memory, and tool access (via MCP).

---

## Sources Consulted

### Internal Design Documents
- `docs/INTENT.md` -- Phase roadmap, dogfood context, 7 research questions
- `docs/research/R3-AGENT-LIFECYCLE.md` -- Task state machine, context overflow strategies, cost model (~$1,000-2,500/month for 20 users), framework comparison
- `docs/research/R4-CLAUDE-TEAMS.md` -- Claude Code SDK capabilities, "wrap + extend" recommendation, AgentRuntime interface
- `docs/research/R5-CLI-BLEND-RISKS.md` -- API-first hybrid architecture, CLI-blend acceptable for dogfood
- `docs/research/R7-CONTEXT-UNIFICATION.md` -- Context bus design, MCP server for cross-runtime, ~4K token minimum shared context
- `docs/research/SYNTHESIS.md` -- Fork/resolve model, revised module priorities, tech stack confirmation
- `docs/design/M3-AGENT-RUNTIME.md` -- Original container-per-agent design (OpenClaw-based)
- `docs/design/M5-ORCHESTRATION.md` -- Message routing, agent scheduling, task queue
- `docs/architecture/DESIGN-SPEC.md` -- Memory-first philosophy, agent types, 4-layer config

### External Research
- OpenAI Assistants API architecture (platform.openai.com) -- stateful threads, per-user session management, deprecation in favor of Responses API by August 2026
- Vercel AI SDK 5/6 agent runtime patterns (ai-sdk.dev, vercel.com) -- agentic loop control, SSE streaming, Fluid Compute for long-running processes
- Restate durable agents with Vercel AI SDK (restate.dev) -- Virtual Objects for stateful sessions, crash recovery, human-in-the-loop
- Claude Code SDK headless mode and Agent SDK (code.claude.com, platform.claude.com) -- programmatic agent control, secure deployment in sandboxed containers, gVisor/Firecracker isolation
- AWS Bedrock AgentCore Runtime (aws.amazon.com) -- per-session microVM isolation, 8-hour session persistence, 15-minute idle timeout, memory sanitization on termination
- Fly.io Machines suspend/resume (fly.io) -- Firecracker snapshots for VM state preservation, autosuspend/resume on request, billing only for storage when suspended (~$0.15/GB/month)
- Serverless vs persistent agent runtime comparison (thenewstack.io, blaxel.ai) -- agents spend 30-70% of time in I/O wait, persistent runtimes vs externalized state tradeoffs

---

## 1. Per-User Runtime Model

### What "Each User Has Their Own Runtime" Means

The OpenClaw reference point is instructive. OpenClaw is:
- A single persistent process (Node.js)
- Connected to a specific user (Charles) via Telegram
- Has personality (SOUL.md), memory (MEMORY.md), and daily logs
- Has tool access via MCP servers
- Maintains conversational continuity across sessions
- Available 24/7

"Each user has their own runtime" means each Vibe team member gets an AI environment that:
1. **Knows them** -- preferences, communication style, role, history
2. **Remembers** -- past conversations, decisions, context across sessions
3. **Has tools** -- MCP servers for Slack, Gmail, Calendar, company tools
4. **Has personality** -- consistent interaction style, not a generic chatbot
5. **Is available** -- responds when needed, not just during active sessions

This is NOT the same as "each user has their own server process." The experience of having a personal runtime can be achieved through multiple architectural approaches.

### Options Explored

#### Option A: Dedicated Process Per User (Always-On)

**Description:** Each user gets a dedicated long-running process (like OpenClaw). The process maintains persistent state in memory, has tool connections open, and is ready to respond immediately.

**Architecture:**
```
User 1 ──> [Process 1: Node.js + Claude SDK + MCP servers]
User 2 ──> [Process 2: Node.js + Claude SDK + MCP servers]
...
User 20 ──> [Process 20: Node.js + Claude SDK + MCP servers]
```

**Pros:**
- Lowest latency -- no cold start, instant response
- Simplest mental model -- true 1:1 mapping
- State is always in memory -- no serialization/deserialization
- MCP server connections stay open
- Most faithful to the OpenClaw model

**Cons:**
- 20 processes running 24/7, most idle 95% of the time
- Each process uses ~50-200MB RAM (Node.js + loaded context)
- 20 processes = 1-4GB RAM minimum, even when everyone is sleeping
- MCP connections consume resources even when idle
- Process crashes require full restart + state recovery
- Scaling: at 200 users = 200 processes = significant server cost

**Cost estimate (Fly.io):**
- 20 x shared-cpu-1x (256MB) = 20 x ~$1.94/month = ~$39/month
- But for meaningful agent work, need 512MB-1GB per process: 20 x ~$3.90-7.50/month = ~$78-150/month
- Plus LLM API costs (~$1,000-2,500/month from R3)

**Verdict: Reject for MVP.** Wasteful for 20 users, catastrophic at scale. The OpenClaw model works for 1 user, not 20.

#### Option B: Shared Process Pool (On-Demand)

**Description:** A pool of worker processes handles requests. When a user sends a message, a worker loads that user's context, processes the request, then returns to the pool. No dedicated process per user.

**Architecture:**
```
                    ┌──────────────────────────┐
All Users ────────> │     Request Router        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     Worker Pool (N=3-5)   │
                    │  ┌─────────┐             │
                    │  │Worker 1 │ <-- loads    │
                    │  │         │     user ctx │
                    │  └─────────┘             │
                    │  ┌─────────┐             │
                    │  │Worker 2 │             │
                    │  └─────────┘             │
                    │  ┌─────────┐             │
                    │  │Worker 3 │             │
                    │  └─────────┘             │
                    └──────────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Shared State Store       │
                    │  (Supabase / Redis)       │
                    │  - User profiles          │
                    │  - Conversation history   │
                    │  - MCP configs            │
                    └──────────────────────────┘
```

**Pros:**
- Resource efficient -- 3-5 workers handle 20 users
- Workers scale based on actual demand, not user count
- No idle resource waste
- Worker crash only affects one in-flight request
- Scales linearly: 200 users might need 15-25 workers

**Cons:**
- Cold context load on every request (~100-500ms to hydrate user state)
- MCP server connections must be established per request or pooled
- No persistent in-memory state -- everything goes through the store
- More complex request routing
- User "feels" slower on first message of a session

**Cost estimate (Fly.io):**
- 5 workers x shared-cpu-1x (512MB) = 5 x ~$3.90/month = ~$20/month
- Redis (state cache): ~$5-10/month
- Supabase: free tier or ~$25/month
- Total infra: ~$50-55/month

**Verdict: Strong candidate for MVP.** Resource-efficient, scales well, and the cold-start penalty is negligible for a "forum model" (~500ms latency tolerance per INTENT.md).

#### Option C: Serverless Functions (Stateless)

**Description:** Each user request triggers a serverless function. The function loads context from a database, calls the LLM, writes results, and terminates. No persistent processes at all.

**Architecture:**
```
User Message ──> [Serverless Function]
                    │
                    ├── Load user context from DB
                    ├── Call Claude API
                    ├── Write response to DB
                    └── Terminate
```

**Pros:**
- Zero idle cost -- pay only for execution time
- Infinite scaling -- cloud provider handles it
- No process management
- Simplest operations

**Cons:**
- Cold start on every invocation (~500-2000ms)
- No persistent MCP connections (must establish per call)
- Timeout limits (Vercel: 60-800s depending on plan, Lambda: 15 min)
- Agent tasks that span multiple LLM calls are awkward
- No streaming support (or complex SSE workarounds)
- Cannot hold state between tool calls within a single agent turn

**Cost estimate (Vercel):**
- Pro plan: $20/month base
- Function execution: ~$0.18 per 100GB-hours
- Estimated for 20 users: ~$30-60/month

**Verdict: Reject for agent workloads.** Serverless functions cannot maintain the stateful agent loop that Claude SDK requires. An agent turn involves multiple LLM calls, tool executions, and decisions -- this needs a persistent process for at least the duration of the turn. Serverless works for simple request-response but not for agentic behavior.

#### Option D: Hybrid -- On-Demand Persistent Sessions (Recommended)

**Description:** Combine the best of B and C. When a user becomes active, spin up a persistent session that lives for the duration of their activity. The session loads user context, establishes MCP connections, and handles all that user's requests. When the user goes idle, the session suspends (state saved) or terminates (state written to DB). On next activity, resume or create a new session.

**Architecture:**
```
                    ┌──────────────────────────────────┐
                    │         Session Manager           │
                    │                                   │
                    │  Manages lifecycle:               │
                    │  - Create on first message        │
                    │  - Keep alive during activity     │
                    │  - Suspend after idle timeout     │
                    │  - Destroy after extended idle    │
                    └──────────────┬───────────────────┘
                                   │
          ┌────────────────────────┼──────────────────────┐
          ▼                        ▼                      ▼
   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
   │ User Session  │      │ User Session  │      │   (idle --   │
   │   (active)    │      │   (active)    │      │  no session) │
   │               │      │               │      └──────────────┘
   │ - User ctx    │      │ - User ctx    │
   │ - MCP conns   │      │ - MCP conns   │
   │ - Conv state  │      │ - Conv state  │
   │ - Agent loop  │      │ - Agent loop  │
   └──────────────┘      └──────────────┘

   State Store (Supabase):
   - User profiles, preferences
   - Conversation history (all threads)
   - Agent configs, tool configs
   - Session checkpoints (for resume)
```

**How it maps to AWS AgentCore's model:**
AWS Bedrock AgentCore (GA 2025) uses exactly this pattern: per-session microVMs with isolated CPU/memory/filesystem. Sessions persist for up to 8 hours, with 15-minute idle timeout. Each session gets complete state isolation. OpenVibe doesn't need microVM isolation (internal dogfood), but the lifecycle model is right.

**How it maps to Fly.io's suspend/resume:**
Fly.io Machines can be auto-suspended when idle (Firecracker snapshot of full VM state). Resume takes ~200ms. Cost while suspended: storage only (~$0.15/GB/month). This means a user's runtime can be "always available" conceptually while only consuming resources when active.

**Pros:**
- Fast response for active users (session already warm)
- Efficient resource use (idle users cost nothing or near-nothing)
- MCP connections maintained during active session
- Stateful agent loop works naturally within a session
- Scales well: concurrent active users determine resource needs, not total user count
- Session state can be checkpointed for resume (aligns with R3 checkpointing)

**Cons:**
- Session management complexity (create, keep-alive, suspend, destroy)
- First message after idle has cold-start penalty (~1-3s for session creation + context load)
- Need to decide: suspend (preserve full state) vs terminate (reconstruct from DB)
- MCP connection re-establishment on resume adds latency

**Cost estimate (Fly.io with auto-suspend):**
- Assume 5-8 concurrent active users during business hours
- 8 x shared-cpu-1x (512MB) = 8 x ~$3.90/month = ~$31/month
- Suspended machines: 12 x 512MB storage = ~$0.90/month
- Supabase: $25/month
- Total infra: ~$57/month

**Verdict: Recommended for MVP.** This is the right balance of user experience, resource efficiency, and engineering complexity. The key insight: "each user has their own runtime" doesn't mean "each user has a 24/7 process" -- it means each user has a personal, stateful experience that feels continuous, backed by on-demand persistent sessions.

### Relationship to Claude Code SDK

R4 recommends "wrap + extend" -- use Claude Code SDK as one agent runtime behind a runtime-agnostic interface. The per-user session is NOT the Claude Code SDK instance. Instead:

```
Per-User Session
├── User context (identity, preferences, history)
├── MCP connections (tools available to this user)
├── Conversation state (active threads, current focus)
└── Agent invocation layer
    ├── Claude Code SDK (for coding tasks)
    ├── Direct Claude API (for conversational tasks)
    └── Other runtimes (future)
```

The user session manages WHO the user is and WHAT tools they have. The agent runtime (Claude SDK, direct API) handles HOW to process a specific request. This separation is critical -- it means swapping the underlying LLM or agent framework doesn't require rebuilding the session system.

### Relationship Between User Runtime and Threads

A user participates in multiple threads simultaneously. The user's runtime is NOT thread-scoped -- it spans all threads the user is in.

```
User Runtime (Charles)
├── Active in #general thread-1
├── Active in #engineering thread-5 (with fork-2 active)
├── Active in #product thread-12
└── Agent interactions happen within specific threads
    but user identity/tools/preferences are runtime-level
```

When Charles @mentions an agent in thread-5, the user runtime:
1. Provides user context (who is Charles, what can he access)
2. Provides thread context (what's been discussed in thread-5)
3. Routes to the appropriate agent runtime (Claude SDK for coding, direct API for Q&A)
4. Receives the response and routes it back to thread-5

---

## 2. Runtime Lifecycle

### Session States

```
                    ┌──────────┐
                    │   NONE   │  (no session exists)
                    └─────┬────┘
                          │
                    (user sends message)
                          │
                    ┌─────▼────┐
             ┌─────│ CREATING │
             │     └─────┬────┘
             │           │
             │     (context loaded, MCP connected)
             │           │
             │     ┌─────▼────┐
             │     │  ACTIVE  │◄───────────────┐
             │     └─────┬────┘                │
             │           │                     │
             │     ┌─────┴──────┐              │
             │     │            │              │
             │  (idle 5min)  (user message)    │
             │     │            │              │
             │     │            └──────────────┘
             │     │
             │     ▼
             │  ┌──────────┐
             │  │ IDLE     │  (warm, reduced priority)
             │  └─────┬────┘
             │        │
             │  ┌─────┴──────┐
             │  │            │
             │  │  (idle 15min)  (user message)
             │  │            │         │
             │  │            │    ┌────▼─────┐
             │  │            └───>│  ACTIVE  │
             │  │                 └──────────┘
             │  │
             │  ▼
             │  ┌───────────┐
             │  │ SUSPENDED │  (state checkpointed, process stopped)
             │  └─────┬─────┘
             │        │
             │  ┌─────┴──────┐
             │  │            │
             │  │  (24h)   (user message)
             │  │            │         │
             │  │            │    ┌────▼─────┐
             │  │            └───>│ RESUMING │───> ACTIVE
             │  │                 └──────────┘
             │  │
             │  ▼
             │  ┌─────────────┐
             └──│ TERMINATED  │  (state persisted to DB, session destroyed)
                └─────────────┘
```

### When Is a Runtime Created?

**Trigger: First message in a session period.**

Not on login (wasteful -- user might just browse), not always-on (wasteful for 20 users). When a user sends their first message (or @mentions an agent, or triggers an AI feature), the session manager:

1. Checks for a suspended session -> RESUME (fast, ~200ms on Fly.io)
2. Checks for recent session state in DB -> RECREATE (medium, ~1-3s)
3. No recent state -> CREATE fresh (medium, ~1-3s)

The UI shows the channel/thread list immediately on login (read from Supabase directly). The runtime only activates when AI interaction is needed.

### When Is It Destroyed?

**Tiered timeout:**

| State Transition | Trigger | What Happens |
|-----------------|---------|--------------|
| ACTIVE -> IDLE | 5 min no user interaction | Reduce process priority, keep MCP connections |
| IDLE -> ACTIVE | User sends message | Instant resume (already running) |
| IDLE -> SUSPENDED | 15 min no interaction | Checkpoint state, suspend process (Fly.io) or save to DB |
| SUSPENDED -> ACTIVE | User sends message | Resume from checkpoint (~200ms) or recreate (~1-3s) |
| SUSPENDED -> TERMINATED | 24 hours suspended | Write final state to DB, destroy session |
| Any -> TERMINATED | Explicit user logout | Write state to DB, destroy session |

### Multiple Concurrent Conversations

A user can be in 3 threads simultaneously. The user runtime handles all of them:

```
User Session (Charles) -- single process
│
├── Thread-handler: #general/thread-1
│   └── Agent invocation in progress (Claude API call)
│
├── Thread-handler: #engineering/thread-5
│   └── Waiting for user input
│
└── Thread-handler: #product/thread-12
    └── Fork-2 active, agent working on research task
```

**Implementation:** The user session process handles requests asynchronously. Multiple agent calls can be in-flight simultaneously (they're async HTTP calls to Claude API). The session process is an event loop (Node.js), not a blocking thread-per-request model.

**Concurrency within a session:**
- Reading threads: Unlimited (read from Supabase directly, bypass runtime)
- Agent invocations: Max 3 concurrent per user (configurable, prevents runaway costs)
- Tool executions: Managed by the agent loop, not the session

### Context Window Management

When a user's runtime accumulates too much context across multiple threads:

1. **Per-thread context is independent.** Thread-1's context doesn't pollute thread-5's context. Each agent invocation gets: system prompt + user context (~2K tokens) + thread history (variable) + shared context (~4K tokens from R7).

2. **Thread context overflow:** Apply R3's layered strategy:
   - Recent messages: verbatim (last 20-30 messages)
   - Older messages: compressed summaries
   - Very old: only accessible via memory search

3. **User context is compact:** The user's runtime context (identity, preferences, active tasks, recent decisions) is ~4K tokens (R7 estimate). This is injected into every agent call and is affordable.

4. **No user-level context accumulation problem.** The user runtime is a session manager, not an LLM conversation. LLM conversations happen per-thread. The runtime's own state (which threads are active, what tools are connected) is structured data, not LLM context.

### Session Persistence

**Can a user close browser and come back to the same state? Yes.**

All durable state lives in Supabase:
- Messages, threads, forks -- persisted on write (real-time via Supabase)
- User preferences -- persisted to user profile
- Agent task state -- persisted per task (R3 task state machine)
- Conversation continuity -- thread history is in DB, not in runtime memory

The runtime is ephemeral. The state is persistent. When the user returns:
1. UI loads from Supabase (channels, threads, messages) -- instant
2. Runtime created on first AI interaction -- 1-3s
3. Runtime loads user context from DB -- seamless

The user perceives continuous experience because the UI and data are always available. The runtime is invisible infrastructure.

---

## 3. Agent Runtime vs User Runtime

### Two Distinct Abstractions

| Dimension | User Runtime | Agent Runtime |
|-----------|-------------|---------------|
| **Identity** | A human user (Charles, Sarah) | An AI agent (Coder, Researcher) |
| **Purpose** | Manage user session, tools, preferences | Execute AI tasks, generate responses |
| **Lifecycle** | Tied to user activity (login -> idle -> logout) | Tied to task lifecycle (created -> running -> completed) |
| **Multiplicity** | One per active user | One per active task (could be many per user) |
| **State** | User profile, active threads, MCP configs | Task context, conversation history, tool state |
| **Persistence** | Supabase (user profile, thread participation) | Supabase (task state) + checkpoints (long tasks) |
| **Cost** | Session infrastructure (process, memory) | LLM API tokens (the expensive part) |

### They Are NOT the Same Abstraction

The user runtime is a **session** -- it exists to provide context and tools for a human's interactions. It doesn't do AI work itself.

The agent runtime is an **executor** -- it exists to run a specific AI task (respond to a message, research a topic, write code).

```
User Runtime (Charles)
│
│  "Hey @Coder, fix the auth bug"
│  │
│  ├── Creates Task: fix-auth-bug
│  │   └── Agent Runtime (Coder instance)
│  │       ├── Loads task context
│  │       ├── Calls Claude API (multiple turns)
│  │       ├── Executes tools (read files, write code)
│  │       ├── Writes result to thread
│  │       └── Terminates
│  │
│  "Also @Researcher, find best practices for JWT"
│  │
│  └── Creates Task: jwt-research
│      └── Agent Runtime (Researcher instance)
│          ├── Loads task context
│          ├── Calls Claude API
│          ├── Executes tools (web search)
│          ├── Writes result to thread
│          └── Terminates
```

### What Happens When a User @mentions an Agent

Step-by-step at the runtime level:

1. **User sends message** with `@Coder fix the auth bug` in thread-5
2. **User runtime** receives the message (or the API server receives it directly)
3. **Orchestrator** (M5) identifies the @mention and routes to the Coder agent type
4. **Task created** in database: `{ id: task-123, threadId: thread-5, agentType: 'coder', status: 'queued', input: 'fix the auth bug' }`
5. **Agent Runtime Manager** picks up the task:
   - Selects execution strategy: Claude Code SDK for coding tasks
   - Prepares context: thread history + user permissions + relevant memory
   - Spawns an agent execution (Claude API call or Claude Code SDK session)
6. **Agent executes**: Multiple LLM turns, tool calls, code edits
7. **Agent writes result** to thread-5 (via API, stored in Supabase)
8. **Supabase Realtime** broadcasts the new message to all thread-5 participants
9. **User's UI** receives the message and displays it
10. **Task updated**: `{ status: 'completed', tokensUsed: 1500 }`
11. **Agent runtime terminates** (or returns to pool)

The user runtime is involved in steps 2-3 (providing user context and routing). Steps 5-10 are the agent runtime's domain. The user runtime doesn't wait for the agent -- it's async.

### Can a User's Runtime Invoke an Agent's Runtime?

Yes, but not directly. The invocation goes through the orchestration layer:

```
User Runtime ──> Orchestrator ──> Agent Runtime Manager ──> Agent Runtime
                     │
                     └── Why the indirection?
                         - Permission checks
                         - Rate limiting
                         - Cost tracking
                         - Agent selection/scheduling
                         - Token budget enforcement
```

The user runtime never directly spawns an agent process. The orchestrator is the gatekeeper. This is essential for:
- **Cost control:** Orchestrator enforces per-user token budgets
- **Security:** Orchestrator validates the user has permission to invoke that agent
- **Scheduling:** Orchestrator handles queue and load balancing
- **Observability:** All invocations go through one point, making monitoring straightforward

---

## 4. Cost Model

### Compute Cost (Infrastructure)

#### Option D Hybrid Model -- 20 Users

| Resource | Specification | Monthly Cost |
|----------|--------------|-------------|
| API Server (Next.js) | 1x shared-cpu-2x (1GB) on Fly.io | ~$15 |
| Session Workers | 5-8x shared-cpu-1x (512MB) auto-suspend | ~$20-31 |
| Agent Execution Workers | 3-5x shared-cpu-2x (1GB) on-demand | ~$15-25 |
| Supabase | Pro plan (8GB DB, 250GB bandwidth) | $25 |
| Redis (session state cache) | Upstash (pay-per-use) | ~$5-10 |
| **Total Infrastructure** | | **~$80-106/month** |

Suspended machines (idle users): ~$0.15/GB/month = negligible.

#### Comparison: Always-On vs On-Demand vs Hybrid

| Architecture | 20 Users | 50 Users | 200 Users | 1000 Users |
|-------------|----------|----------|-----------|------------|
| Always-On (Option A) | $150/mo | $375/mo | $1,500/mo | $7,500/mo |
| On-Demand Pool (Option B) | $55/mo | $80/mo | $200/mo | $600/mo |
| Serverless (Option C) | $40/mo | $60/mo | $150/mo | $400/mo |
| **Hybrid (Option D)** | **$90/mo** | **$120/mo** | **$300/mo** | **$900/mo** |

Hybrid is slightly more expensive than pure pool at small scale, but the better UX (warm sessions) justifies the ~$35/month difference.

### LLM Cost (The Dominant Cost)

From R3's analysis, adapted for per-user runtime model:

| Category | Daily Tokens | Monthly Cost (Sonnet-heavy) |
|----------|-------------|---------------------------|
| Conversational (thread messages) | ~4.3M | ~$520 |
| Agent task execution | ~2.4M | ~$290 |
| Agent teams (rare in MVP) | ~0.8M | ~$100 |
| Memory operations (embeddings) | ~0.7M | ~$10 |
| **Total** | **~8.2M/day** | **~$920/month** |

**Per-user LLM cost:** ~$920 / 20 users = **~$46/user/month**

This is the real cost. Infrastructure is noise (~$5/user/month). LLM tokens are 90% of the bill.

### Cost Optimization Levers

| Lever | Savings | Complexity | When to Apply |
|-------|---------|------------|---------------|
| **Model routing** (Haiku for simple, Sonnet for complex) | 30-50% | Low | Day 1 |
| **Prompt caching** (system prompts, user context) | 10-20% | Low | Day 1 |
| **Per-user token budgets** (soft limit + alert) | Variable | Medium | Week 2 |
| **Response caching** (identical queries) | 5-10% | Medium | Month 2 |
| **Batch API** (non-urgent background tasks) | 50% on batched | Medium | Month 2 |
| **Session context compression** (aggressive summarization) | 15-25% | Medium | Month 3 |

**Day 1 optimizations** (model routing + prompt caching) can reduce LLM costs to **~$550-650/month** for 20 users.

### Total Cost Summary

| Component | Monthly Cost (20 users) |
|-----------|------------------------|
| Infrastructure (Fly.io + Supabase + Redis) | ~$90 |
| LLM API (with Day 1 optimizations) | ~$600 |
| **Total** | **~$690/month** |
| **Per user** | **~$35/user/month** |

For comparison: Slack Pro = $8.75/user/month (no AI agents). OpenVibe at $35/user/month includes AI agents that save each person 1+ hours/day -- compelling value.

---

## 5. Infrastructure

### Recommended Stack

```
┌──────────────────────────────────────────────────────────────┐
│                        Client Layer                           │
│  Next.js Web App (Vercel or Fly.io)                          │
│  - Static assets on CDN                                      │
│  - SSR for initial load                                      │
│  - WebSocket/SSE for real-time                               │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ tRPC + WebSocket
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                      API Server                               │
│  Next.js API routes (Fly.io)                                 │
│  - tRPC endpoints                                            │
│  - WebSocket gateway (Supabase Realtime passthrough)         │
│  - Session manager (create/destroy sessions)                 │
│  - Task orchestrator (route to agent runtimes)               │
└──────────┬───────────────────────┬───────────────────────────┘
           │                       │
           ▼                       ▼
┌─────────────────┐    ┌──────────────────────────────────────┐
│  Supabase       │    │  Session Workers (Fly.io Machines)   │
│  - PostgreSQL   │    │                                      │
│  - pgvector     │    │  Per-user sessions (on-demand):      │
│  - Realtime     │    │  - User context loaded               │
│  - Auth         │    │  - MCP connections established        │
│  - Storage      │    │  - Agent invocations dispatched       │
│                 │    │  - Auto-suspend on idle               │
│  Source of      │    │                                      │
│  truth for      │    │  Agent execution:                     │
│  all state      │    │  - Claude API calls                   │
│                 │    │  - Claude Code SDK (for coding)       │
│                 │    │  - Tool execution                     │
└─────────────────┘    └──────────────────────────────────────┘
           │
           ▼
┌─────────────────┐
│  Upstash Redis  │
│  - Session cache│
│  - Rate limits  │
│  - Task queue   │
└─────────────────┘
```

### Where Do Runtimes Run?

| Component | Where | Why |
|-----------|-------|-----|
| Web UI | Vercel (or Fly.io edge) | CDN, fast global access |
| API Server | Fly.io (single region for dogfood) | Persistent processes, WebSocket support |
| Session Workers | Fly.io Machines (same region) | Auto-suspend/resume, Firecracker isolation |
| Database | Supabase (hosted) | Managed, Realtime included, pgvector |
| Redis | Upstash (serverless) | Pay-per-use, global |
| Claude API | Anthropic (cloud) | No self-hosting option |

**Why Fly.io for workers (not Vercel):**
- Vercel serverless functions have timeouts (60-800s)
- Agent tasks can take 2-30+ seconds (multiple LLM turns)
- Fly.io Machines have no timeout, support auto-suspend/resume
- Fly.io supports WebSocket natively (Vercel has limitations)

**Why not Docker/Kubernetes:**
- Overkill for 20-user dogfood
- K8s operational overhead is enormous
- Fly.io gives container-like isolation without K8s complexity
- Can migrate to K8s at 200+ users if needed

### Real-Time Communication

```
Browser ──── WebSocket ────> API Server
                                │
                                ├── Supabase Realtime (messages, presence)
                                │   - New messages broadcast to thread participants
                                │   - User online/offline status
                                │   - Agent "thinking" indicators
                                │
                                └── SSE Stream (agent responses)
                                    - Progressive response from Claude API
                                    - Streamed token-by-token to UI
                                    - Backpressure handling
```

**Message flow:**
1. User sends message -> API server writes to Supabase
2. Supabase Realtime broadcasts to all thread participants
3. If agent invocation needed -> API server dispatches to agent worker
4. Agent worker streams response -> SSE to requesting user
5. Final response written to Supabase -> broadcast to all participants

**Latency budget:**
- User sends message: ~50ms (write to Supabase)
- Broadcast to other users: ~200ms (Supabase Realtime)
- Agent starts responding: ~1-3s (context load + first LLM token)
- Agent completes response: ~3-15s depending on complexity

This is within the "forum model, ~500ms" tolerance (from INTENT.md) for message delivery. Agent response latency (1-15s) is separate and expected.

### Scaling Projections

| Scale | Active Users | Infrastructure | LLM Cost | Total |
|-------|-------------|---------------|----------|-------|
| **Dogfood (20)** | 5-8 concurrent | $90/mo | $600/mo | **$690/mo** |
| **Small team (50)** | 12-20 concurrent | $120/mo | $1,500/mo | **$1,620/mo** |
| **Medium (200)** | 40-80 concurrent | $300/mo | $6,000/mo | **$6,300/mo** |
| **Large (1000)** | 150-300 concurrent | $900/mo | $30,000/mo | **$30,900/mo** |

At 200+ users:
- Move from Fly.io Machines to dedicated instances or K8s
- Add regional deployment for latency
- Implement aggressive model routing (80% Haiku, 15% Sonnet, 5% Opus)
- Consider Anthropic enterprise pricing (volume discounts)

At 1000+ users:
- The cost model shifts: LLM costs dominate
- Infrastructure is <3% of total cost
- Need per-user billing tier strategy
- Consider local/hybrid LLM routing (R6 recommendation)

---

## 6. MVP Minimum (Phase 3 Implementation)

### What "Minimum" Means

For dogfood, we need the Vibe team to feel like they have a personal AI environment. We do NOT need the full session management system. We can simplify aggressively.

### MVP Architecture (Dogfood Minimum)

```
┌──────────────────────────────────────────────────┐
│  Next.js App (Fly.io)                            │
│                                                   │
│  - Web UI (channels, threads, forks)             │
│  - API routes (tRPC)                              │
│  - Agent invocation endpoint                      │
│  - SSE streaming for agent responses              │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  "User Runtime" (simplified)                 │ │
│  │                                              │ │
│  │  = User row in Supabase + preferences       │ │
│  │  + Per-request context hydration            │ │
│  │  + No persistent session process            │ │
│  │                                              │ │
│  │  On each agent invocation:                  │ │
│  │  1. Load user profile from DB               │ │
│  │  2. Load thread context from DB             │ │
│  │  3. Build prompt (system + user + thread)   │ │
│  │  4. Call Claude API (streaming)             │ │
│  │  5. Write response to DB                    │ │
│  │  6. Broadcast via Supabase Realtime         │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │     Supabase        │
            │  - Auth             │
            │  - PostgreSQL       │
            │  - Realtime         │
            │  - Storage          │
            └─────────────────────┘
```

### What's Simplified for MVP

| Full Vision | MVP Simplification | Why OK |
|------------|-------------------|--------|
| Persistent session process per user | Per-request context hydration | 20 users, forum latency -- no one notices 500ms extra |
| MCP server connections per user | Shared MCP connections at app level | All Vibe team members have same tool access |
| Auto-suspend/resume sessions | No sessions to suspend | Stateless per request |
| Session Manager service | None | No sessions to manage |
| Per-user token budgets | Team-level monitoring (dashboard) | Trust the team, monitor spending |
| Claude Code SDK for coding | Direct Claude API calls | Simpler. Code execution not needed for dogfood threads |
| Agent type routing (Coder/Researcher) | Single general-purpose agent | One agent handles everything. Add specialization later |
| Task state machine (10 states) | Simple: queued -> running -> completed/failed | No long-running tasks in MVP |

### MVP Implementation Plan

**Week 1-2: Foundation**
- Supabase project setup (auth, DB schema, Realtime)
- Next.js app with basic routing
- User auth (email + Google OAuth)
- Channel CRUD + message posting

**Week 3-4: Thread Engine**
- Thread creation and display
- Fork from any message
- Resolve fork (AI summary)
- Fork sidebar

**Week 5-6: Agent Integration**
- @mention detection
- Agent invocation via Claude API
- SSE streaming for responses
- Per-request user context hydration (the "simplified user runtime")
- Model routing (Haiku for simple, Sonnet for complex)

**Week 7-8: Polish + Dogfood Launch**
- Basic search
- Agent "thinking" indicators
- Error handling
- Invite flow for Vibe team
- Token usage tracking (team-level)

### What Gets Added Post-MVP

| Phase | Addition | Trigger |
|-------|----------|---------|
| Phase 3.5 | Persistent user sessions (Option D) | If context hydration latency annoys users |
| Phase 4 | MCP tool integration (Calendar, Gmail) | Team requests tool access |
| Phase 4 | Multiple agent types | Team wants specialized agents |
| Phase 4 | Task state machine | Need for long-running agent tasks |
| Phase 4-5 | Claude Code SDK integration | Need for code execution in threads |
| Phase 5 | Cross-runtime context (R7) | OpenClaw integration needed |
| Phase 5+ | Per-user token budgets | Multi-team deployment |

### Concrete Recommendation

**For Phase 3 (MVP dogfood), use Option B (shared process pool) implemented as the simplest possible version: the Next.js API server IS the "pool." No separate worker processes. Agent invocations are async handlers within the API server.**

This means:
- **One deployable** (Next.js app on Fly.io)
- **One database** (Supabase)
- **One LLM provider** (Claude API direct)
- **Zero separate services** (no Redis, no worker processes, no session manager)

The "per-user runtime" in MVP is a function call:

```typescript
async function getUserRuntime(userId: string) {
  const user = await db.users.findById(userId);
  const preferences = await db.preferences.findByUser(userId);
  const recentContext = await db.context.getRecent(userId, { limit: 5 });

  return {
    systemPrompt: buildSystemPrompt(user, preferences),
    tools: getAvailableTools(user.role),
    context: recentContext,
  };
}
```

This is intentionally boring. The magic is in the thread model (fork/resolve), not in the runtime architecture. For 20 users on a forum-latency product, boring is correct.

**When to upgrade from boring to Option D (hybrid persistent sessions):**
- More than 50 users
- Users complain about latency
- Need per-user MCP connections (different users, different tools)
- Need long-running agent tasks with checkpointing
- Cross-runtime integration (OpenClaw, Claude Code CLI)

---

## Open Questions

### 1. MCP Connection Sharing vs Per-User

For dogfood, all Vibe team members likely have the same MCP tools (Slack, Calendar, Gmail). But some tools need per-user authentication (Gmail reads MY inbox, not yours). When does per-user MCP become necessary?

**Proposed answer:** MVP uses shared MCP connections with user-token passthrough (the MCP call includes the user's OAuth token). This avoids per-user MCP server instances while still providing per-user data access.

### 2. Agent Execution Isolation

When two users @mention an agent simultaneously, the agent handles both in the same process. Is isolation needed? Can Agent A's execution leak into Agent B's response?

**Proposed answer:** Not a risk for MVP. Each agent invocation is a separate Claude API call with separate context. There's no shared state between invocations. Isolation matters when agents execute code (sandboxing) -- defer to when Claude Code SDK is integrated.

### 3. Session State: What Exactly Gets Persisted?

When we evolve to Option D (persistent sessions), what state lives in the session vs in the database?

**Proposed answer:**
- **Always in DB:** Messages, threads, forks, user profiles, task state, team memory
- **In session (ephemeral, reconstructable):** Compiled system prompt, MCP connection handles, in-flight agent state, local cache of recent thread context
- **In session checkpoint (for suspend/resume):** Above + open WebSocket connections, partial agent responses

The key principle: anything that would be lost if the session dies should also be in the DB. The session is an optimization (warm cache), not a source of truth.

### 4. How Does OpenClaw Become a "User Runtime"?

The founder's reference to OpenClaw suggests each user should have an OpenClaw-like experience. Currently OpenClaw runs as a single Telegram bot for one user. How does this translate?

**Proposed answer:** OpenClaw's value is: personality + memory + tools + availability. In OpenVibe, this is:
- **Personality:** Per-user or per-workspace agent configuration (system prompt with personality)
- **Memory:** Shared team memory (M4) + personal memory per user
- **Tools:** MCP servers accessible through the platform
- **Availability:** On-demand sessions that feel always-on

The user doesn't get "their own OpenClaw instance." They get the OpenClaw experience through the platform, without needing a separate bot process.

### 5. Agent Runtime Warm Pool

For frequently used agent types (general assistant), should we maintain a warm pool of pre-initialized Claude API sessions? This would reduce first-response latency.

**Proposed answer:** Not for MVP. Claude API calls don't benefit from "warm pools" -- each call is independent. The latency is in the LLM inference, not session setup. Warm pools matter for Claude Code SDK sessions (which have startup overhead). Defer to Phase 4.

---

## Rejected Approaches

### 1. Dedicated VM Per User (AWS AgentCore Style)

**What:** Each user gets their own microVM (like AWS Bedrock AgentCore's per-session isolation).

**Why rejected:** AgentCore's microVM isolation is designed for multi-tenant enterprise security (preventing cross-user data leaks). OpenVibe dogfood is a single team with shared data. The isolation overhead (VM boot, resource allocation) adds latency and cost without benefit. Additionally, microVM provisioning at ~$0.025/session is expensive when multiplied by frequent user activity.

**Reconsider when:** Multi-tenant deployment with regulatory isolation requirements (HIPAA, SOC2). At that point, per-user containers (not VMs) with namespace isolation may be appropriate.

### 2. WebSocket-Per-User Dedicated Connection to Agent

**What:** Each user maintains a persistent WebSocket to "their" agent process, enabling streaming, real-time tool updates, and bidirectional communication.

**Why rejected:** WebSocket connections are cheap, but dedicated agent processes behind them are not. The WebSocket should connect to the API server (for real-time message delivery via Supabase Realtime), not to a dedicated agent process. Agent responses can stream via SSE through the API server.

**Reconsider when:** Need for real-time collaborative editing within agent interactions (e.g., user and agent co-editing a document). Not relevant for forum-model conversations.

### 3. Claude Code CLI as User Runtime

**What:** Each user's runtime IS a Claude Code CLI session running on the server, with the web UI as a facade.

**Why rejected:** R5 thoroughly analyzed this. The risk matrix is unacceptable: fragile output parsing, no structured progress events, uncontrolled update cadence, OS-specific behavior. Claude Code CLI is designed for interactive developer use, not as a server-side runtime for 20 concurrent users.

**Reconsider when:** Anthropic releases a first-class Claude Code Server product with structured APIs, persistent sessions, and multi-tenant support. The Agent SDK (TypeScript/Python) is the right integration point, not the CLI.

### 4. Local-First Architecture (Runtimes on User's Machine)

**What:** The user's machine runs their own agent runtime (like how OpenClaw runs on a server that Charles controls). Each user installs a local daemon.

**Why rejected:** The Vibe team needs a "just open the browser" experience, not "install software on your laptop." Local runtimes create: version skew, connectivity requirements, hardware dependency, and support burden. Additionally, local runtimes can't access shared team context without a synchronization protocol.

**Reconsider when:** Privacy requirements demand that LLM calls happen locally (regulated verticals with local model routing, per R6). At that point, a local agent companion (like Ollama) could supplement cloud runtimes.

### 5. Always-On Agent Pool (Pre-allocated, Waiting)

**What:** Pre-allocate 5 agent instances (Coder, Researcher, Writer, General x2) that are always running, waiting for tasks. Any user's request gets routed to the appropriate idle agent.

**Why rejected:** Conflates agent types with agent instances. You don't need 5 processes waiting. You need the ability to invoke any agent type on demand. An "agent" in OpenVibe is a configuration (system prompt + tools + personality), not a process. The process is the execution environment; the configuration is the agent identity.

**Reconsider when:** Agent warm-up has significant latency (e.g., loading large codebases into context for Claude Code SDK). At that point, pre-warming specific agent contexts could reduce response time.

---

*Research completed: 2026-02-07*
*Researcher: runtime-architect*
