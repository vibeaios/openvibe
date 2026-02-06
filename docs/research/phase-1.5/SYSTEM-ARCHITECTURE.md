# Phase 1.5: System Architecture

> Status: Complete | Researcher: system-architect | Date: 2026-02-07

---

## Research Questions

1. **Backend Infrastructure** -- What does the production infrastructure look like concretely? Dogfood vs scale. Service choices. Agent runtime connectivity. WebSocket architecture. Background job processing.
2. **Data Structure and Storage Design** -- Is the 10-table schema the right decomposition? Storage strategy. Data flow. Lifecycle. Hot/cold separation. Backup. Context/memory layer.
3. **System Decoupling** -- Where are the seams? Clear interfaces between subsystems. Swappable parts. Event-driven vs direct coupling. Plugin points. Parallel dev support. Module boundaries.
4. **System Decomposition** -- What are the major subsystems? Core interfaces. Data ownership. Dependencies. Communication patterns.

## Sources Consulted

### Internal
- `docs/INTENT.md` -- Phase roadmap, dogfood context, 7 research questions
- `docs/research/SYNTHESIS.md` -- Phase 1 research synthesis, revised priorities
- `docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md` -- 10-table schema, ~30 tRPC procedures, agent pipeline
- `docs/research/phase-1.5/RUNTIME-ARCHITECTURE.md` -- Per-user runtime model, session lifecycle, cost model
- `docs/research/phase-1.5/THREAD-UX-PROPOSAL.md` -- Fork/resolve UX patterns
- `docs/research/phase-1.5/ADMIN-CONFIGURABLE-UI.md` -- Config-driven UI, component catalog
- `docs/architecture/DESIGN-SPEC.md` -- Design philosophy, Supabase choice, config system, auth model
- `docs/design/M1-M6` -- All module designs

### External
- Next.js + tRPC monorepo patterns (create.t3.gg, nx.dev, turborepo docs)
- Supabase event-driven architecture guides (supabase.com/docs, bootstrapped.app)
- Nx monorepo package structure and clean architecture (nx.dev/blog, khlafawi.medium.com)
- Platform comparison: Fly.io vs Railway vs Vercel for long-running processes (docs.railway.com, jasonsy.dev, northflank.com)
- Event-driven architecture patterns for TypeScript backends (freecodecamp.org, confluent.io, stackoverflow.blog)
- Supabase Realtime architecture (medium.com/@ansh91627)

---

## Question 1: Backend Infrastructure

### 1.1 Full Infrastructure Diagram -- Dogfood (20 Users)

```
                         ┌──────────────────────────────────────────┐
                         │            INTERNET                       │
                         └───────────────────┬──────────────────────┘
                                             │
                                             │ HTTPS
                                             │
                    ┌────────────────────────▼────────────────────────┐
                    │               Fly.io (Single Region)             │
                    │                                                   │
                    │  ┌──────────────────────────────────────────┐    │
                    │  │         Next.js Application                │    │
                    │  │         (single Machine, 1GB RAM)         │    │
                    │  │                                            │    │
                    │  │  ┌────────────────┐  ┌─────────────────┐ │    │
                    │  │  │  Web UI (SSR)  │  │  tRPC API       │ │    │
                    │  │  │  Static assets │  │  ~30 procedures │ │    │
                    │  │  │  CDN-cached    │  │                 │ │    │
                    │  │  └────────────────┘  └────────┬────────┘ │    │
                    │  │                                │          │    │
                    │  │  ┌─────────────────────────────▼────────┐ │    │
                    │  │  │  Agent Task Processor                 │ │    │
                    │  │  │  (in-process, async)                  │ │    │
                    │  │  │  - @mention handler                   │ │    │
                    │  │  │  - Fork resolution handler            │ │    │
                    │  │  │  - Streaming response collector       │ │    │
                    │  │  └────────────┬──────────────────────────┘ │    │
                    │  └───────────────┼──────────────────────────┘    │
                    └──────────────────┼──────────────────────────────┘
                                       │
                      ┌────────────────┼────────────────────┐
                      │                │                    │
                      ▼                ▼                    ▼
           ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
           │   Supabase       │  │  Anthropic   │  │  Fly.io CDN  │
           │   (managed)      │  │  API         │  │  (static)    │
           │                  │  │              │  │              │
           │  ┌─────────────┐ │  │  Claude      │  │  JS/CSS/img  │
           │  │ PostgreSQL  │ │  │  Sonnet 4.5  │  │              │
           │  │ + pgvector  │ │  │  Haiku 4.5   │  └──────────────┘
           │  │ + tsvector  │ │  │  Opus 4.6    │
           │  └─────────────┘ │  └──────────────┘
           │  ┌─────────────┐ │
           │  │ Realtime    │ │
           │  │ (WebSocket) │ │
           │  └─────────────┘ │
           │  ┌─────────────┐ │
           │  │ Auth        │ │
           │  │ (OAuth/JWT) │ │
           │  └─────────────┘ │
           │  ┌─────────────┐ │
           │  │ Storage     │ │
           │  │ (files)     │ │
           │  └─────────────┘ │
           └──────────────────┘
```

**Dogfood minimal infra:**

| Component | Service | Spec | Monthly Cost |
|-----------|---------|------|-------------|
| Application server | Fly.io Machine | shared-cpu-2x, 1GB RAM | ~$15 |
| Database | Supabase Pro | 8GB DB, 250GB bandwidth | $25 |
| LLM API | Anthropic | Sonnet/Haiku/Opus | ~$600-900 |
| DNS + SSL | Fly.io (included) | Automatic | $0 |
| CDN | Fly.io edge (included) | Static assets | $0 |
| **Total** | | | **~$640-940/month** |

No Redis. No separate worker. No message queue. No Kubernetes. The Next.js server handles everything in a single process.

### 1.2 Full Infrastructure Diagram -- Scale (200+ Users)

```
                         ┌──────────────────────────────────────────┐
                         │            INTERNET                       │
                         └───────────────────┬──────────────────────┘
                                             │
                                     ┌───────▼───────┐
                                     │  Cloudflare   │
                                     │  (CDN + WAF)  │
                                     └───────┬───────┘
                                             │
                    ┌────────────────────────▼────────────────────────┐
                    │               Fly.io (Multi-Region)              │
                    │                                                   │
                    │  ┌─────────────────────────────────────────────┐ │
                    │  │            Load Balancer (Fly Proxy)         │ │
                    │  └───────────┬──────────────┬─────────────────┘ │
                    │              │              │                    │
                    │   ┌──────────▼───┐  ┌──────▼──────────┐        │
                    │   │  Web Servers │  │  Web Servers    │        │
                    │   │  (3x 2GB)   │  │  (Region B)     │        │
                    │   │  Next.js    │  │  Next.js        │        │
                    │   │  + tRPC API │  │  + tRPC API     │        │
                    │   └──────┬──────┘  └──────┬──────────┘        │
                    │          │                 │                    │
                    │   ┌──────▼─────────────────▼──────────────┐    │
                    │   │         Agent Workers                  │    │
                    │   │  (5-10x 1GB Machines, auto-suspend)   │    │
                    │   │  - Task processor (long-running)      │    │
                    │   │  - Claude Code SDK (coding tasks)     │    │
                    │   │  - MCP tool execution                 │    │
                    │   └──────────┬─────────────────────────────┘    │
                    └──────────────┼──────────────────────────────────┘
                                   │
                 ┌─────────────────┼──────────────────┐
                 │                 │                   │
                 ▼                 ▼                   ▼
      ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
      │  Supabase        │  │  Anthropic   │  │  Upstash Redis   │
      │  (or self-hosted │  │  API         │  │  (queue + cache) │
      │   PostgreSQL)    │  │  (enterprise │  │                  │
      │                  │  │   pricing)   │  │  - Task queue    │
      │  Primary + Read  │  └──────────────┘  │  - Rate limiting │
      │  Replica         │                    │  - Session cache │
      └──────────────────┘                    └──────────────────┘
```

**What changes at 200+ users:**

| Change | Why | When |
|--------|-----|------|
| Multiple web servers (3+) | Handle concurrent requests | >50 concurrent users |
| Separate agent worker pool | Isolate agent CPU/memory from web serving | Agent tasks >5% of server load |
| Redis task queue (Upstash/BullMQ) | Reliable task distribution, priority queues | >100 agent tasks/hour |
| Read replica database | Offload read-heavy queries (thread lists, search) | DB CPU >60% |
| CDN (Cloudflare) | Global static asset distribution, DDoS protection | Multi-region users |
| WAF | Rate limiting, bot protection | Public-facing |
| Multi-region deployment | Latency for non-US users | International users |
| Self-hosted PostgreSQL | Full control, custom extensions, cost optimization | Supabase costs >$300/mo |

### 1.3 Why Fly.io (Not Vercel, Railway, or Self-Hosted)

| Factor | Fly.io | Vercel | Railway | Self-Hosted (VPS) |
|--------|--------|--------|---------|-------------------|
| **Long-running processes** | Native. No timeout. | 60-800s function limit | Native. No timeout. | Native. |
| **WebSocket support** | Native | No first-class support | Native | Native |
| **Auto-suspend/resume** | Yes (Firecracker) | N/A (serverless) | No | No |
| **Agent worker isolation** | Separate Machines | Separate functions (limited) | Separate services | Manual |
| **Global distribution** | 30+ regions | Edge network | Limited regions | Manual |
| **Cost (dogfood)** | ~$15/mo | ~$20/mo (Pro) | ~$10-15/mo | ~$10-20/mo |
| **Ops complexity** | Low (Dockerfile) | Very low | Low | High |
| **Migrate away** | Standard Docker | Vendor lock-in (build system) | Standard Docker | Already free |

**Decision: Fly.io for the application server.**

Rationale:
- Agent tasks need long-running processes (10-120s Claude API calls). Vercel's serverless functions have hard timeouts.
- Supabase Realtime uses WebSocket connections that the app server needs to proxy or pass through. Vercel has limited WebSocket support.
- Fly.io's auto-suspend Machines are the natural path to per-user runtime sessions (Option D from RUNTIME-ARCHITECTURE.md) when the time comes.
- Standard Docker deployment means zero vendor lock-in. Can move to Railway, Render, or any container host.

**Vercel is rejected for the application server** but could serve static assets or a marketing site. The core problem: Vercel functions cannot hold open connections for agent streaming responses that take 10-30s while simultaneously serving other requests. Vercel's Fluid Compute (Pro/Enterprise) partially addresses this but still has timeout ceilings and lacks persistent process support.

**Railway is a strong alternative** if Fly.io proves operationally complex. Railway's UX is simpler, pricing is comparable, and it supports long-running processes. The tradeoff: no auto-suspend (machines run 24/7), and no multi-region by default.

### 1.4 Agent Runtime Connection Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Next.js Application Server                     │
│                                                                    │
│  HTTP Request ──> tRPC Router ──> message.send mutation            │
│                                      │                             │
│                                      ▼                             │
│                            ┌─────────────────────┐                 │
│                            │  @mention detected?  │                 │
│                            └────────┬────────────┘                 │
│                                     │ yes                          │
│                                     ▼                              │
│                     ┌──────────────────────────────┐               │
│                     │  AgentTaskQueue.enqueue()     │               │
│                     │  (write to tasks table)       │               │
│                     └──────────────┬───────────────┘               │
│                                    │                               │
│              ┌─────────────────────▼──────────────────────┐        │
│              │          AgentTaskProcessor                  │        │
│              │  (in-process for dogfood,                   │        │
│              │   separate worker pool at scale)            │        │
│              │                                             │        │
│              │  1. Load agent config (system prompt, model)│        │
│              │  2. Build context (thread history + user)   │        │
│              │  3. Select runtime:                         │        │
│              │     ├─ DirectAnthropicRuntime (default)     │        │
│              │     ├─ ClaudeCodeRuntime (coding tasks)     │        │
│              │     └─ OpenClawRuntime (future)             │        │
│              │  4. Execute (streaming)                     │        │
│              │  5. Write response message to DB            │        │
│              │  6. Update task status                      │        │
│              └─────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ Supabase Realtime
                              │ (postgres_changes)
                              ▼
                    ┌─────────────────────┐
                    │  All connected       │
                    │  clients receive     │
                    │  new message via     │
                    │  WebSocket           │
                    └─────────────────────┘
```

The agent runtime connects to the rest of the system through three integration points:

1. **Input: Task table.** When a task is created (`status='queued'`), the processor picks it up. For dogfood, this is an in-process async function. At scale, workers poll the tasks table (or a Redis queue).

2. **Output: Messages table.** The agent writes its response as a new message row. Supabase Realtime automatically broadcasts to all thread subscribers. The agent never directly pushes to WebSockets.

3. **Status: Task table updates.** Task status changes (`queued` -> `running` -> `completed`) are broadcast via Supabase Realtime, driving the "agent is thinking" UI indicator.

This means the agent runtime is **database-mediated** -- it has no direct connection to the web server or clients. This is intentional: it means the agent runtime can run anywhere (same process, separate machine, different cloud) without changing the client or API code.

### 1.5 WebSocket Architecture

```
Browser                          Fly.io                          Supabase
  │                                │                                │
  │── WSS connect ────────────────>│                                │
  │                                │── WSS connect ────────────────>│
  │                                │<── Connection established ─────│
  │<── Connection established ─────│                                │
  │                                │                                │
  │── Subscribe thread:abc ───────>│                                │
  │                                │── Subscribe postgres_changes ─>│
  │                                │   table=messages               │
  │                                │   filter=thread_id=abc         │
  │                                │<── Subscribed ─────────────────│
  │<── Subscribed ─────────────────│                                │
  │                                │                                │
  │                     [Agent writes message to DB]                │
  │                                │                                │
  │                                │<── postgres_changes event ─────│
  │                                │   {new: {id, content, ...}}   │
  │<── message.created event ──────│                                │
  │                                │                                │
  │── Send typing indicator ──────>│                                │
  │                                │── Broadcast to thread:abc ────>│
  │                                │<── (relayed to other clients) ─│
  │                                │                                │
```

**Architecture decisions:**

1. **Supabase Realtime is the WebSocket layer.** No custom WebSocket server. The browser connects directly to Supabase Realtime (via the Supabase JS client). The Fly.io app server does NOT proxy WebSocket connections -- the client connects to Supabase independently.

2. **Per-thread subscriptions.** The client subscribes to `postgres_changes` for the thread(s) it's viewing. When the user switches threads, unsubscribe old, subscribe new. At 20 users viewing ~3 threads each = ~60 concurrent subscriptions. Supabase Pro handles this trivially.

3. **Typing indicators use Supabase Broadcast.** Ephemeral, no DB write. The `typing:${threadId}` channel carries typing events. Agents send typing indicators when their task status changes to `running`.

4. **No SSE for agent streaming in MVP.** The BACKEND-MINIMUM-SCOPE document collects the full agent response before inserting the message. This means no token-by-token streaming to the client. The "agent is thinking" indicator covers the waiting period. Post-MVP, add streaming by: inserting a placeholder message immediately, then updating it via Supabase Realtime as tokens arrive.

### 1.6 Background Job Processing

**Dogfood (simple):**
```typescript
// In the tRPC mutation handler
async function handleAgentMention(message, agentConfig, threadContext) {
  const task = await createTask(/* ... */);

  // Fire and forget -- runs in the same Node.js process
  processAgentTask(task.id).catch(err => {
    markTaskFailed(task.id, err);
  });

  return { taskId: task.id };
}
```

No queue. No worker. No Redis. The Node.js event loop handles concurrency. At 20 users with ~50 agent tasks/day, this is sufficient.

**Startup recovery:**
```typescript
// On server start, recover interrupted tasks
async function recoverTasks() {
  const stale = await db.tasks.findMany({
    where: {
      status: { in: ['queued', 'running'] },
      started_at: { lt: fiveMinutesAgo() }
    }
  });
  for (const task of stale) {
    await db.tasks.update(task.id, { status: 'queued', retry_count: task.retry_count + 1 });
    processAgentTask(task.id).catch(markFailed);
  }
}
```

**At scale (200+ users):**

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│  Web Servers (3x)       │     │  Agent Workers (5-10x)       │
│                         │     │                              │
│  tRPC mutations write   │────>│  Poll task queue             │
│  to Redis queue         │     │  (Redis/BullMQ)              │
│  (or tasks table)       │     │                              │
│                         │     │  Process tasks:              │
│  Serve UI, handle       │     │  - Claude API calls          │
│  reads, auth            │     │  - Claude Code SDK sessions  │
│                         │     │  - MCP tool execution        │
└─────────────────────────┘     │                              │
                                │  Write results to DB         │
                                │  (Supabase Realtime          │
                                │   handles broadcast)         │
                                └──────────────────────────────┘
```

The transition from in-process to separate workers requires changing ONE thing: where `processAgentTask` runs. The interface (task in, message out) stays identical. The database-mediated architecture means no API changes.

---

## Question 2: Data Structure and Storage Design

### 2.1 Schema Assessment

The 10-table schema from BACKEND-MINIMUM-SCOPE is **almost right** but needs two adjustments for the system architecture:

**Current tables (keep as-is):**
1. `workspaces` -- Multi-tenant boundary
2. `users` -- User identity
3. `workspace_members` -- Membership + roles
4. `channels` -- Container for threads
5. `threads` -- Container for messages + forks
6. `forks` -- Side conversations with resolution
7. `messages` -- The core data unit
8. `tasks` -- Agent task queue and tracking
9. `agent_configs` -- Agent definitions
10. `ui_configs` -- Admin UI configuration
11. `api_keys` -- Agent/external auth
12. `context_items` -- Future context bus

**Add: `reactions` table (deferred but schema-ready)**

The backend-architect correctly said "dogfood can start without reactions." But the messages table's `metadata` JSONB is not the right place for reactions because they need to be queryable and countable per-message. Add the table when needed:

```sql
-- Add in week 5+ if team requests it
CREATE TABLE reactions (
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  emoji TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (message_id, user_id, emoji)
);
```

**Add: `attachments` table (deferred but schema-ready)**

File attachments were listed as "Should Have" in SYNTHESIS. When adding:

```sql
CREATE TABLE attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size BIGINT NOT NULL,
  storage_path TEXT NOT NULL, -- Supabase Storage path
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Verdict: The 10-table decomposition is correct for MVP.** It maps cleanly to the domain model (workspace -> channels -> threads -> forks -> messages, with tasks as the agent work queue). No table is unnecessary, and no critical entity is missing.

### 2.2 Storage Strategy

```
┌────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYERS                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL (Supabase) -- SOURCE OF TRUTH                     │  │
│  │                                                               │  │
│  │  ALL structured data:                                         │  │
│  │  - Users, workspaces, channels, threads, forks, messages     │  │
│  │  - Tasks, agent configs, UI configs, API keys                │  │
│  │  - Context items (with pgvector embeddings, deferred)        │  │
│  │  - Full-text search indexes (tsvector + GIN)                 │  │
│  │                                                               │  │
│  │  WHY: Single source of truth. Supabase Realtime requires     │  │
│  │  data in Postgres to broadcast changes. RLS for security.    │  │
│  │  pgvector for future semantic search. No data in two places. │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Supabase Storage (S3-compatible) -- BINARY FILES             │  │
│  │                                                               │  │
│  │  - User avatars                                               │  │
│  │  - File attachments (images, documents, PDFs)                │  │
│  │  - Agent-generated artifacts (when applicable)               │  │
│  │                                                               │  │
│  │  WHY: Binary files don't belong in Postgres. Supabase        │  │
│  │  Storage integrates with Auth for access control.            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Redis (Upstash) -- EPHEMERAL/OPERATIONAL STATE               │  │
│  │  ** NOT NEEDED FOR DOGFOOD. Add at scale. **                  │  │
│  │                                                               │  │
│  │  When to add:                                                 │  │
│  │  - Task queue for agent workers (BullMQ)  [>100 tasks/hr]   │  │
│  │  - Rate limiting counters                 [>50 users]        │  │
│  │  - Session cache (user context hydration) [latency problem]  │  │
│  │  - Pub/Sub for cross-process events       [multi-server]     │  │
│  │                                                               │  │
│  │  WHY NOT for dogfood: Postgres tasks table + Supabase        │  │
│  │  Realtime covers all needs. Adding Redis adds an infra       │  │
│  │  dependency with no benefit at 20 users.                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow: Message Lifecycle

```
USER SENDS MESSAGE
        │
        ▼
┌───────────────────────┐
│ 1. API: message.send  │  tRPC mutation
│    Validate input     │
│    Check permissions  │
│    (RLS enforced)     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 2. STORE: INSERT INTO │  PostgreSQL
│    messages (...)      │
│    RETURNING *         │
│                        │
│    tsvector auto-      │
│    generated (STORED)  │
└───────────┬───────────┘
            │
     ┌──────┴───────────────────────┐
     │                              │
     ▼                              ▼
┌────────────────┐   ┌──────────────────────────┐
│ 3a. BROADCAST  │   │ 3b. AGENT DETECTION      │
│                │   │                          │
│ Supabase       │   │ Parse @mentions          │
│ Realtime fires │   │ If agent mentioned:      │
│ postgres_change│   │   Create task row        │
│ INSERT event   │   │   Fire processAgentTask  │
│                │   │                          │
│ All thread     │   │ Agent processes async:   │
│ subscribers    │   │   Build context          │
│ receive msg    │   │   Call Claude API        │
│                │   │   Insert response msg    │
│ Latency: ~200ms│   │   (triggers 3a again)    │
└────────────────┘   └──────────────────────────┘
            │
            ▼
┌───────────────────────┐
│ 4. INDEX: Already     │
│    indexed!           │
│                        │
│    tsvector column is │
│    GENERATED ALWAYS   │
│    AS (to_tsvector()) │
│    STORED -- updated  │
│    on INSERT/UPDATE   │
│                        │
│    GIN index on fts   │
│    column enables     │
│    instant full-text  │
│    search             │
└───────────────────────┘
            │
            ▼
┌───────────────────────┐
│ 5. SEARCHABLE         │
│                        │
│ search.messages tRPC  │
│ query uses:           │
│   fts @@ plainto_     │
│   tsquery('english',  │
│   $query)             │
│                        │
│ Results ranked by     │
│ ts_rank, with         │
│ ts_headline for       │
│ highlights            │
└───────────────────────┘
```

Key insight: **there is no separate indexing step.** PostgreSQL's generated tsvector column means every INSERT automatically updates the full-text search index. This eliminates the need for a separate search indexing pipeline, a message queue for search updates, or an external search engine. For 20 users generating a few thousand messages/week, this is performant and simple.

### 2.4 Data Lifecycle

| Phase | Trigger | What Happens | Storage Impact |
|-------|---------|--------------|---------------|
| **Creation** | User sends message / agent responds | INSERT into messages, tasks | Row in Postgres |
| **Update** | User edits message | UPDATE messages SET content, updated_at | Same row, tsvector regenerated |
| **Fork resolution** | User clicks "Resolve" | Fork status -> 'resolved', resolution text set, summary message inserted in parent thread | Fork row updated, new message row |
| **Fork abandonment** | User clicks "Abandon" | Fork status -> 'abandoned' | Fork row updated, messages preserved |
| **Thread archival** | Manual or auto after inactivity | Thread status -> 'archived' | No data deleted, status flag only |
| **Message deletion** | User or admin deletes | DELETE from messages (CASCADE to related) | Row removed, frees space |
| **Task completion** | Agent finishes | Task status -> 'completed', output/token_usage stored | Task row updated |
| **Task cleanup** | Periodic (daily cron) | Delete completed tasks older than 90 days? | Rows removed |

**For dogfood: keep everything forever.** Supabase free tier has 500MB, Pro has 8GB. At ~2KB per message, 8GB holds ~4 million messages. The Vibe team won't generate that in a year. Retention policies are a Phase 5+ concern.

### 2.5 Hot Data vs Cold Data

For dogfood, there is no meaningful hot/cold distinction. All data fits in Postgres memory. At scale:

| Data | Access Pattern | Storage | At Scale |
|------|---------------|---------|----------|
| **Hot: Recent messages** | Read constantly (thread views) | Postgres primary | Keep in buffer pool; consider Redis cache |
| **Hot: Active tasks** | Polled every few seconds | Postgres (indexed by status) | Move to Redis queue |
| **Hot: User sessions** | Every request | Supabase Auth JWT | Consider Redis session cache |
| **Warm: Thread list** | Read on channel open | Postgres (indexed by channel) | Read replica |
| **Warm: Search index** | On-demand searches | Postgres GIN index | Consider Elasticsearch at >1M messages |
| **Cold: Old threads** | Rarely accessed | Postgres | Archive to cheaper storage; load on demand |
| **Cold: Completed tasks** | Debugging/analytics only | Postgres | Delete after 90 days or archive |
| **Cold: Context items** | Future feature | Postgres + pgvector | Separate table, separate index |

### 2.6 Backup and Recovery (Dogfood)

| What | Strategy | RPO | RTO |
|------|----------|-----|-----|
| Database | Supabase automated daily backups (Pro plan) | 24 hours | ~30 minutes |
| Point-in-time recovery | Supabase Pro includes PITR (7-day window) | Minutes | ~15 minutes |
| File storage | Supabase Storage (S3-backed, durable) | N/A (durable) | N/A |
| Application code | Git (GitHub) | 0 (every commit) | `git clone && fly deploy` (~5 min) |
| Agent configs | In database (backed up with DB) | Same as DB | Same as DB |
| Environment variables | Fly.io secrets + Supabase dashboard | Manual | Re-enter from secure store |

**Recovery procedure (dogfood, total disaster):**
1. Supabase restores database from backup (~15 min)
2. `fly deploy` from latest git commit (~5 min)
3. Re-set environment variables if needed (~5 min)
4. Total RTO: ~25 minutes

### 2.7 Context/Memory Layer (R7) in Storage Design

The `context_items` table from BACKEND-MINIMUM-SCOPE is the storage layer for R7's context unification vision. Here is how it fits:

```
┌──────────────────────────────────────────────────────────────┐
│  ACTIVE DATA (messages, threads, forks, tasks)                │
│  = The live conversation and work happening now               │
│  = What users interact with directly                          │
│                                                               │
│           │ (extraction)                                      │
│           ▼                                                   │
│                                                               │
│  CONTEXT ITEMS (context_items table)                          │
│  = Distilled knowledge from conversations                    │
│  = Decisions, discoveries, status updates                    │
│  = Scoped (task/thread/channel/global)                       │
│  = Tagged for relevance                                       │
│  = Source-tracked (web/claude-code/openclaw)                  │
│  = Embeddable (vector column, deferred)                      │
│                                                               │
│           │ (injection into agent context)                    │
│           ▼                                                   │
│                                                               │
│  AGENT INVOCATION                                             │
│  = System prompt + user context + thread history              │
│    + relevant context_items (filtered by scope, tags)        │
│  = ~4K tokens of shared context per R7 recommendation        │
└──────────────────────────────────────────────────────────────┘
```

**For dogfood:** The context_items table exists but is empty. Agents get context from thread messages directly. No cross-runtime context.

**Post-dogfood:** Context items are populated by:
- Fork resolution summaries (automatically when forks are resolved)
- Agent-extracted decisions and action items
- Manual "pin" by users (mark a message as important context)
- OpenClaw observations (when integrated)

The key architectural decision: **context items are separate from messages.** Messages are the raw conversation. Context items are the distilled, structured knowledge extracted from conversations. They live in different tables because they have different lifecycles, access patterns, and query needs (tsvector for messages, vector similarity for context items).

---

## Question 3: System Decoupling

### 3.1 System Boundaries and Seams

```
┌──────────────────────────────────────────────────────────────────────┐
│                         OPENVIBE SYSTEM                                │
│                                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Thread     │  │   Agent     │  │    Auth &    │  │   Config   │  │
│  │   Engine     │  │   Runtime   │  │   Identity   │  │   System   │  │
│  │             │  │             │  │              │  │            │  │
│  │  channels   │  │  invocation │  │  users       │  │  workspace │  │
│  │  threads    │  │  task mgmt  │  │  workspaces  │  │  ui config │  │
│  │  forks      │  │  LLM calls  │  │  members     │  │  agent cfg │  │
│  │  messages   │  │  runtimes   │  │  sessions    │  │            │  │
│  │  resolution │  │             │  │  permissions │  │            │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                │                │                 │         │
│         └────────────────┼────────────────┼─────────────────┘         │
│                          │                │                            │
│                    ┌─────▼────────────────▼───────┐                   │
│                    │        Shared Services         │                   │
│                    │                                │                   │
│                    │  ┌────────────┐ ┌───────────┐ │                   │
│                    │  │ Real-time  │ │  Search   │ │                   │
│                    │  │ Layer      │ │           │ │                   │
│                    │  └────────────┘ └───────────┘ │                   │
│                    │  ┌────────────┐ ┌───────────┐ │                   │
│                    │  │ Storage    │ │  Context  │ │                   │
│                    │  │ (DB/Files) │ │  Memory   │ │                   │
│                    │  └────────────┘ └───────────┘ │                   │
│                    └────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

**The seams (where subsystems connect):**

| Seam | Between | Interface | Coupling Type |
|------|---------|-----------|--------------|
| A | Thread Engine <-> Agent Runtime | Task table (task created when @mention detected) | **Async, database-mediated** |
| B | Thread Engine <-> Real-time | Supabase Realtime publication (automatic on INSERT/UPDATE) | **Event-driven, implicit** |
| C | Agent Runtime <-> LLM Provider | `AgentRuntime` interface (see 3.2) | **Sync call, swappable** |
| D | All <-> Auth | RLS policies + JWT validation middleware | **Cross-cutting, enforced at DB level** |
| E | All <-> Storage | Supabase client (postgres + storage) | **Direct coupling, but behind client abstraction** |
| F | Config <-> Thread Engine/Frontend | `ui_configs` table reads | **Async, config-driven** |
| G | Thread Engine <-> Search | Generated tsvector column + GIN index | **Implicit, no explicit coupling** |

### 3.2 Swappable Components

The architecture has three kinds of components by swappability:

**Easily swappable (behind clear interfaces):**

```typescript
// LLM Provider -- swap Claude for OpenAI, local model, etc.
interface LLMProvider {
  generateResponse(params: {
    model: string;
    systemPrompt: string;
    messages: ConversationMessage[];
    maxTokens: number;
    stream?: boolean;
  }): AsyncGenerator<string> | Promise<string>;

  generateEmbedding(text: string): Promise<number[]>;
}

// Agent Runtime -- swap direct API for Claude Code SDK, OpenClaw, etc.
interface AgentRuntime {
  execute(task: AgentTask): Promise<AgentResult>;
  cancel(taskId: string): Promise<void>;
  getStatus(taskId: string): Promise<TaskStatus>;
}

// Implementation selection:
function getRuntime(task: AgentTask): AgentRuntime {
  if (task.taskType === 'code_execution') return new ClaudeCodeRuntime();
  if (task.taskType === 'message_response') return new DirectAnthropicRuntime();
  return new DirectAnthropicRuntime(); // default
}
```

**Moderately swappable (requires migration but no architecture change):**

| Component | Current | Swap To | Migration Effort |
|-----------|---------|---------|-----------------|
| Database | Supabase Postgres | Self-hosted Postgres | Schema + data dump/restore. Lose Realtime (need alternative). |
| Auth | Supabase Auth | Auth0, Clerk, self-hosted | Change JWT validation, OAuth config. Users need to re-auth. |
| File storage | Supabase Storage | S3, Cloudflare R2 | Change upload/download URLs. Migrate existing files. |
| Hosting | Fly.io | Railway, Render, VPS | Dockerfile is standard. Change deploy config. |

**Hard to swap (deeply integrated):**

| Component | Why Hard | Mitigation |
|-----------|----------|------------|
| Supabase Realtime | WebSocket subscriptions baked into frontend. No clean abstraction layer. | If swapping Supabase for self-hosted Postgres, need to add a custom Realtime layer (e.g., Socket.IO, Ably). Significant work. |
| PostgreSQL | tsvector, pgvector, RLS, generated columns are Postgres-specific | Don't try to swap. PostgreSQL is the right choice long-term. |
| tRPC | Router types are used across the entire frontend. | Type-safe API is the point. Swapping to REST/GraphQL means rewriting all API calls. |

**Recommendation: Invest in swappability only where it matters.** The LLM provider and agent runtime MUST be swappable (Anthropic dependency risk per SYNTHESIS.md Risk 4). The database and real-time layer should NOT try to be swappable -- PostgreSQL and Supabase Realtime are good choices that don't need abstraction.

### 3.3 Event-Driven vs Direct Coupling

| Interaction | Pattern | Why |
|-------------|---------|-----|
| User sends message -> other users see it | **Event-driven** (Supabase Realtime) | Fire-and-forget. No direct connection between sender and receivers. |
| User sends message -> agent receives task | **Event-driven** (task table insert -> processor picks up) | Decouples message handling from agent execution. Agent can be slow. |
| Agent completes task -> user sees response | **Event-driven** (message INSERT -> Realtime broadcast) | Agent writes to DB, Realtime delivers. No direct push. |
| User requests thread list | **Direct call** (tRPC query -> Postgres) | Synchronous read. No reason for indirection. |
| Admin updates agent config | **Direct call** (tRPC mutation -> Postgres) | Immediate effect needed. No event pipeline required. |
| User searches messages | **Direct call** (tRPC query -> Postgres tsvector) | Synchronous read. |
| Fork resolution | **Event chain** (resolve mutation -> create summary task -> agent processes -> insert resolution message -> Realtime broadcast) | Multi-step async. Each step is independent. |
| Typing indicator | **Event-driven** (Supabase Broadcast) | Ephemeral, no persistence needed. |

**Rule of thumb:**
- **Reads = direct calls.** The user wants data now.
- **Writes that trigger side effects = event-driven.** The write succeeds immediately; consequences happen async.
- **User-to-user communication = event-driven.** Via Realtime subscriptions.
- **Admin operations = direct calls.** Immediate feedback required.

### 3.4 Plugin/Extension Points (Future)

For dogfood, there are no plugins. But the architecture has natural extension points:

```
┌────────────────────────────────────────────────────────────────┐
│  EXTENSION POINTS (design seams, not implemented for dogfood)   │
│                                                                 │
│  1. Agent Runtime Registry                                      │
│     register(name, runtime: AgentRuntime)                      │
│     → Add new agent execution backends                          │
│     → e.g., OpenAI Assistants, local Ollama, custom API        │
│                                                                 │
│  2. Message Processing Pipeline                                 │
│     addHook('message.created', handler)                        │
│     → Run custom logic when messages are created               │
│     → e.g., compliance filtering, auto-translation             │
│                                                                 │
│  3. Agent Component Catalog                                     │
│     registerComponent(name, component: React.FC)               │
│     → Add new rich response types for agents                   │
│     → e.g., chart, form, approval-button                       │
│                                                                 │
│  4. Config Layer Providers                                      │
│     registerConfigProvider(layer, provider)                     │
│     → Add custom config sources                                │
│     → e.g., LaunchDarkly for feature flags                     │
│                                                                 │
│  5. Context Resolvers                                           │
│     registerContextResolver(runtime, resolver)                  │
│     → Add context sources for agent invocations                │
│     → e.g., Jira context, GitHub context                       │
└────────────────────────────────────────────────────────────────┘
```

### 3.5 Parallel Development Support

**How 2-3 developers work without stepping on each other:**

```
Developer A: "Thread Engine + Frontend"
  Owns: thread-engine package, web app UI components
  Files: packages/thread-engine/*, apps/web/app/(threads)/*
  DB tables: channels, threads, forks, messages

Developer B: "Agent System + Backend"
  Owns: agent-runtime package, API integration
  Files: packages/agent-runtime/*, apps/web/app/api/*
  DB tables: tasks, agent_configs

Developer C: "Auth + Config + Search"
  Owns: auth package, config package, search
  Files: packages/auth/*, packages/config/*, search routes
  DB tables: workspaces, users, workspace_members, ui_configs, api_keys
```

**Shared contracts (the "handshake" between developers):**

```typescript
// packages/core/src/types/index.ts
// This file is the contract. Changes require all devs to agree.

export interface Message {
  id: string;
  threadId: string;
  forkId: string | null;
  parentId: string | null;
  authorId: string;
  authorType: 'human' | 'agent' | 'system';
  content: string;
  metadata: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

export interface AgentTask {
  id: string;
  workspaceId: string;
  threadId: string;
  forkId: string | null;
  triggerMessageId: string;
  agentConfigId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  taskType: 'message_response' | 'fork_resolution' | 'thread_summary';
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  tokenUsage: { inputTokens: number; outputTokens: number; model: string } | null;
  createdAt: Date;
  startedAt: Date | null;
  completedAt: Date | null;
}

// ... all shared types
```

**Modules that can be developed independently:**

| Module | Can develop in isolation? | Hard dependencies |
|--------|--------------------------|-------------------|
| `packages/core` | Yes (types only, no runtime) | None |
| `packages/thread-engine` | Mostly (needs core types + DB) | `core` |
| `packages/agent-runtime` | Yes (can mock DB, mock Claude API) | `core` |
| `packages/auth` | Yes (Supabase Auth is independent) | `core` |
| `packages/config` | Yes (simple CRUD on ui_configs) | `core`, `auth` |
| `apps/web` (UI) | Partially (needs API, but can mock tRPC) | All packages (but via tRPC types) |

**Integration points (where devs must coordinate):**

1. **tRPC router types.** All routers merge into one `appRouter`. Each dev owns their routers, but the merge point requires coordination.
2. **Database migrations.** One migration folder. Devs must not create conflicting migrations. Use numbered prefix convention: `001_auth.sql`, `002_channels.sql`, etc.
3. **Supabase Realtime subscriptions.** Frontend subscribes to specific tables. If Dev A changes the messages table schema, Dev B's frontend subscriptions may break.
4. **Shared UI components.** Button, Input, Card, etc. in a shared `packages/ui` library. Changes affect everyone.

### 3.6 Monorepo Structure

```
openvibe/
├── package.json                    # Root workspace config
├── nx.json                         # Nx configuration
├── tsconfig.base.json              # Shared TypeScript config
│
├── packages/
│   ├── core/                       # Shared types, interfaces, utilities
│   │   ├── src/
│   │   │   ├── types/
│   │   │   │   ├── message.ts      # Message, Thread, Fork, Channel types
│   │   │   │   ├── agent.ts        # AgentConfig, AgentTask, AgentResult
│   │   │   │   ├── user.ts         # User, Workspace, WorkspaceMember
│   │   │   │   ├── config.ts       # UIConfig, ConfigKey
│   │   │   │   └── index.ts        # Re-exports
│   │   │   ├── interfaces/
│   │   │   │   ├── llm-provider.ts # LLMProvider interface
│   │   │   │   ├── agent-runtime.ts# AgentRuntime interface
│   │   │   │   ├── data-store.ts   # DataStore interface (future swappability)
│   │   │   │   └── index.ts
│   │   │   ├── utils/
│   │   │   │   ├── mentions.ts     # @mention parsing
│   │   │   │   ├── markdown.ts     # Markdown utilities
│   │   │   │   └── validation.ts   # Zod schemas for shared validation
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── thread-engine/              # Thread, fork, message logic
│   │   ├── src/
│   │   │   ├── routers/
│   │   │   │   ├── channel.ts      # channel.* tRPC router
│   │   │   │   ├── thread.ts       # thread.* tRPC router
│   │   │   │   ├── fork.ts         # fork.* tRPC router
│   │   │   │   ├── message.ts      # message.* tRPC router
│   │   │   │   └── search.ts       # search.* tRPC router
│   │   │   ├── services/
│   │   │   │   ├── thread-service.ts
│   │   │   │   ├── fork-service.ts
│   │   │   │   ├── message-service.ts
│   │   │   │   └── search-service.ts
│   │   │   └── index.ts            # Exports merged thread router
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── agent-runtime/              # Agent invocation, task management
│   │   ├── src/
│   │   │   ├── routers/
│   │   │   │   ├── agent.ts        # agent.* tRPC router
│   │   │   │   └── task.ts         # task.* tRPC router
│   │   │   ├── runtimes/
│   │   │   │   ├── direct-anthropic.ts  # DirectAnthropicRuntime
│   │   │   │   ├── claude-code.ts       # ClaudeCodeRuntime (future)
│   │   │   │   └── index.ts            # Runtime registry
│   │   │   ├── services/
│   │   │   │   ├── task-processor.ts    # processAgentTask
│   │   │   │   ├── task-queue.ts        # enqueue, dequeue, recover
│   │   │   │   ├── context-builder.ts   # Build agent context from thread
│   │   │   │   └── resolution-service.ts # Fork resolution logic
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── auth/                       # Authentication, permissions
│   │   ├── src/
│   │   │   ├── routers/
│   │   │   │   ├── auth.ts         # auth.* tRPC router
│   │   │   │   └── workspace.ts    # workspace.* tRPC router
│   │   │   ├── services/
│   │   │   │   ├── auth-service.ts
│   │   │   │   └── workspace-service.ts
│   │   │   ├── middleware/
│   │   │   │   ├── auth-middleware.ts    # JWT validation
│   │   │   │   └── role-middleware.ts    # Admin check
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── config/                     # Admin config system
│   │   ├── src/
│   │   │   ├── routers/
│   │   │   │   └── config.ts       # config.* tRPC router
│   │   │   ├── services/
│   │   │   │   └── config-service.ts
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── db/                         # Database client, migrations, seed
│   │   ├── src/
│   │   │   ├── client.ts           # Supabase client (anon + service role)
│   │   │   ├── types.ts            # Generated database types
│   │   │   └── index.ts
│   │   ├── migrations/
│   │   │   ├── 001_initial_schema.sql
│   │   │   ├── 002_rls_policies.sql
│   │   │   ├── 003_realtime_publication.sql
│   │   │   └── 004_seed_data.sql
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── ui/                         # Shared UI components
│       ├── src/
│       │   ├── components/
│       │   │   ├── button.tsx
│       │   │   ├── input.tsx
│       │   │   ├── card.tsx
│       │   │   ├── avatar.tsx
│       │   │   └── ... (shadcn/ui wrappers)
│       │   └── index.ts
│       ├── package.json
│       └── tsconfig.json
│
├── apps/
│   └── web/                        # Next.js application
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx            # Landing/redirect
│       │   ├── auth/
│       │   │   ├── login/page.tsx
│       │   │   └── callback/route.ts
│       │   ├── (workspace)/        # Authenticated workspace routes
│       │   │   ├── layout.tsx      # Workspace shell (sidebar + header)
│       │   │   ├── [channelSlug]/
│       │   │   │   ├── page.tsx    # Channel view (thread list)
│       │   │   │   └── [threadId]/
│       │   │   │       └── page.tsx # Thread view (messages + forks)
│       │   │   ├── search/page.tsx
│       │   │   └── admin/page.tsx  # Simple admin config
│       │   └── api/
│       │       └── trpc/[trpc]/route.ts  # tRPC HTTP handler
│       ├── lib/
│       │   ├── trpc/
│       │   │   ├── client.ts       # tRPC React client
│       │   │   ├── server.ts       # tRPC server setup (merges all routers)
│       │   │   └── context.ts      # tRPC context (auth, db)
│       │   ├── supabase/
│       │   │   ├── client.ts       # Browser Supabase client
│       │   │   ├── server.ts       # Server Supabase client
│       │   │   └── realtime.ts     # Realtime subscription helpers
│       │   └── hooks/
│       │       ├── use-messages.ts  # Subscribe to thread messages
│       │       ├── use-threads.ts   # Subscribe to channel threads
│       │       └── use-typing.ts    # Typing indicator
│       ├── components/
│       │   ├── thread/
│       │   │   ├── thread-view.tsx
│       │   │   ├── message-list.tsx
│       │   │   ├── message-input.tsx
│       │   │   └── agent-response.tsx
│       │   ├── fork/
│       │   │   ├── fork-sidebar.tsx
│       │   │   ├── fork-view.tsx
│       │   │   └── resolve-dialog.tsx
│       │   ├── channel/
│       │   │   ├── channel-sidebar.tsx
│       │   │   └── thread-list.tsx
│       │   └── layout/
│       │       ├── workspace-shell.tsx
│       │       └── navigation.tsx
│       ├── package.json
│       ├── next.config.ts
│       └── tsconfig.json
│
├── supabase/                       # Supabase local dev config
│   └── config.toml
│
└── .github/
    └── workflows/
        └── deploy.yml              # CI: lint + typecheck + build + deploy
```

**Why this structure:**

1. **`packages/core` has no runtime dependencies.** It's types and interfaces only. Every other package depends on it, but it depends on nothing. This is the stable foundation.

2. **`packages/db` centralizes database access.** No other package imports Supabase directly. This means swapping Supabase for another Postgres client changes one package, not everything.

3. **`packages/thread-engine` and `packages/agent-runtime` are the two major business logic packages.** They can be developed and tested independently. thread-engine doesn't know how agents work; it just creates task rows. agent-runtime doesn't know about forks; it just processes tasks.

4. **`apps/web` is an assembly point.** It imports from all packages and wires them together. The tRPC server merges all routers. The frontend uses hooks that subscribe to Realtime. The app has no business logic of its own -- only UI and routing.

5. **No `apps/api` -- the API is inside `apps/web`.** Next.js App Router API routes (`app/api/trpc/[trpc]/route.ts`) serve the tRPC API. No separate server deployment. For dogfood, this is simpler. If the API needs to be separated later (for a separate agent worker service), the tRPC router definitions live in packages, not in the app, so the extraction is clean.

---

## Question 4: System Decomposition

### 4.1 Subsystem Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐           │
│   │  1. Thread   │   │  2. Agent    │   │  3. Auth &   │           │
│   │     Engine   │   │     Runtime  │   │     Identity │           │
│   │              │   │              │   │              │           │
│   │  THE PRODUCT │   │  THE AI      │   │  THE TRUST   │           │
│   │  (what users │   │  (what makes │   │  BOUNDARY    │           │
│   │   interact   │   │   it smart)  │   │              │           │
│   │   with)      │   │              │   │              │           │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘           │
│          │                  │                   │                    │
│   ┌──────▼──────┐   ┌──────▼───────┐   ┌──────▼───────┐           │
│   │  4. Config  │   │  5. Real-    │   │  6. Search   │           │
│   │     System  │   │     time     │   │              │           │
│   │              │   │     Layer    │   │              │           │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘           │
│          │                  │                   │                    │
│          └──────────────────┼───────────────────┘                   │
│                             │                                       │
│                      ┌──────▼───────┐                               │
│                      │  7. Storage  │                               │
│                      │     Layer    │                               │
│                      └──────────────┘                               │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Subsystem 1: Thread Engine

**Purpose:** Manages the entire conversation lifecycle -- channels, threads, forks, messages, and resolution. This is what users interact with. It IS the product.

**Core interfaces:**

```typescript
// Channel operations
interface ChannelService {
  list(workspaceId: string): Promise<Channel[]>;
  create(workspaceId: string, input: CreateChannelInput): Promise<Channel>;
  get(channelId: string): Promise<Channel & { recentThreads: Thread[] }>;
  update(channelId: string, input: UpdateChannelInput): Promise<Channel>;
  delete(channelId: string): Promise<void>;
}

// Thread operations
interface ThreadService {
  list(channelId: string, cursor?: string, limit?: number): Promise<PaginatedResult<Thread>>;
  get(threadId: string): Promise<Thread & { messages: Message[]; forks: Fork[] }>;
  create(channelId: string, content: string, authorId: string): Promise<{ thread: Thread; message: Message }>;
  updateStatus(threadId: string, status: ThreadStatus): Promise<Thread>;
}

// Fork operations
interface ForkService {
  list(threadId: string): Promise<Fork[]>;
  get(forkId: string): Promise<Fork & { messages: Message[] }>;
  create(threadId: string, parentMessageId: string, createdBy: string, description?: string): Promise<Fork>;
  resolve(forkId: string): Promise<Fork>;  // Triggers AI summary task
  abandon(forkId: string): Promise<Fork>;
}

// Message operations
interface MessageService {
  list(threadId: string, forkId?: string, cursor?: string, limit?: number): Promise<PaginatedResult<Message>>;
  send(input: SendMessageInput): Promise<Message>;  // Detects @mentions, triggers agent tasks
  update(messageId: string, content: string, authorId: string): Promise<Message>;
  delete(messageId: string, authorId: string): Promise<void>;
}

// Types
type ThreadStatus = 'active' | 'resolved' | 'archived';
type ForkStatus = 'active' | 'resolved' | 'abandoned';
type AuthorType = 'human' | 'agent' | 'system';

interface SendMessageInput {
  threadId: string;
  forkId?: string;
  parentId?: string;
  content: string;
  authorId: string;
  authorType: AuthorType;
  mentions?: string[];  // Agent slugs extracted from content
}
```

**Data owned:** `channels`, `threads`, `forks`, `messages`

**Dependencies:**
- `auth` -- permission checks (is user a workspace member?)
- `agent-runtime` -- creates tasks when @mentions detected (but does NOT wait for agent response)
- `storage` -- reads/writes to Postgres via db package

**Communication pattern:**
- **Sync calls** for all CRUD operations
- **Async event** when message.send detects @mention -> writes task row (agent-runtime picks it up independently)
- **Implicit event** when rows are inserted -> Supabase Realtime broadcasts to subscribers

**Key design decisions:**
- The thread engine does NOT call the agent runtime directly. It writes a task row. This is the critical decoupling point.
- Fork resolution is initiated by the thread engine (fork.resolve) but executed by the agent runtime (summary generation). The thread engine creates the task; the agent runtime processes it and writes the resolution message.
- Messages have no thread-level cursor/offset tracking. Pagination uses `created_at` cursor. No unread tracking for dogfood.

### 4.3 Subsystem 2: Agent Runtime

**Purpose:** Executes AI tasks -- responding to @mentions, generating fork resolutions, summarizing threads. This is what makes OpenVibe "AI-native" rather than just another chat app.

**Core interfaces:**

```typescript
// The runtime interface -- implementations can be swapped
interface AgentRuntime {
  execute(task: AgentTask, context: AgentContext): Promise<AgentResult>;
  cancel(taskId: string): Promise<void>;
}

// Context provided to the agent
interface AgentContext {
  systemPrompt: string;
  conversationHistory: ConversationMessage[];  // Thread/fork messages
  userContext?: string;                        // Who is the requesting user
  sharedContext?: ContextItem[];               // Relevant context items (future)
  tools?: ToolDefinition[];                    // Available MCP tools (future)
}

// Result from agent execution
interface AgentResult {
  content: string;
  tokenUsage: { inputTokens: number; outputTokens: number; model: string };
  metadata?: Record<string, unknown>;
}

// Task queue interface
interface TaskQueue {
  enqueue(task: CreateTaskInput): Promise<AgentTask>;
  dequeue(): Promise<AgentTask | null>;      // For worker-based processing
  markRunning(taskId: string): Promise<void>;
  markCompleted(taskId: string, result: AgentResult): Promise<void>;
  markFailed(taskId: string, error: string): Promise<void>;
  recoverStale(maxAge: Duration): Promise<AgentTask[]>;
}

// Task processor (orchestrates the full pipeline)
interface TaskProcessor {
  process(taskId: string): Promise<void>;
  // Internally:
  // 1. Load task from DB
  // 2. Load agent config
  // 3. Build context (thread history + user context)
  // 4. Select runtime (direct API, Claude Code SDK, etc.)
  // 5. Execute
  // 6. Write response message to DB
  // 7. Update task status
}

// Context builder -- assembles the prompt
interface ContextBuilder {
  buildForMessageResponse(task: AgentTask, agentConfig: AgentConfig): Promise<AgentContext>;
  buildForForkResolution(task: AgentTask, fork: Fork, messages: Message[]): Promise<AgentContext>;
  buildForThreadSummary(task: AgentTask, thread: Thread, messages: Message[]): Promise<AgentContext>;
}

// Concrete implementations
class DirectAnthropicRuntime implements AgentRuntime {
  // Calls Anthropic Messages API directly
  // Used for: conversational responses, summaries, research
}

class ClaudeCodeRuntime implements AgentRuntime {
  // Wraps Claude Code SDK for coding tasks
  // Used for: code generation, file operations (future)
}
```

**Data owned:** `tasks`, `agent_configs`

**Dependencies:**
- `core` -- shared types
- `db` -- database access for tasks, agent configs, and reading thread context
- External: Anthropic API (direct dependency, behind `LLMProvider` interface)

**Communication pattern:**
- **Async, database-mediated.** The agent runtime polls for (or is notified of) `status='queued'` tasks. It never receives direct function calls from the thread engine.
- **Writes results to shared database.** Agent writes response messages to the `messages` table. Supabase Realtime handles delivery to clients.
- **Task status updates are observable.** Frontend subscribes to `tasks` table changes for "agent is thinking" UI.

**Key design decisions:**
- The agent runtime is intentionally NOT a microservice for dogfood. It runs in the same process. But the interface is designed so it CAN be extracted to a separate service (poll tasks table, process, write results) with zero API changes.
- The `ContextBuilder` is where prompt engineering lives. It decides how many messages to include (last 50 for dogfood), what system prompt to use, and what context items to inject.
- Model routing (Haiku for simple, Sonnet for complex, Opus for hard) is a property of the `AgentConfig`, not the runtime. The admin configures which model each agent uses.

### 4.4 Subsystem 3: Auth & Identity

**Purpose:** Manages who can do what. Users, workspaces, membership, sessions, and permission enforcement.

**Core interfaces:**

```typescript
// Auth service
interface AuthService {
  getSession(): Promise<UserSession | null>;
  signOut(): Promise<void>;
}

// Workspace service
interface WorkspaceService {
  get(workspaceId: string): Promise<Workspace>;
  update(workspaceId: string, input: UpdateWorkspaceInput): Promise<Workspace>;
  listMembers(workspaceId: string): Promise<WorkspaceMember[]>;
  invite(workspaceId: string, email: string, role: 'admin' | 'member'): Promise<void>;
  removeMember(workspaceId: string, userId: string): Promise<void>;
  updateMemberRole(workspaceId: string, userId: string, role: 'admin' | 'member'): Promise<void>;
}

// Permission checking (implemented as tRPC middleware)
interface PermissionMiddleware {
  requireAuth(): TRPCMiddleware;        // Must be logged in
  requireWorkspace(): TRPCMiddleware;    // Must be a workspace member
  requireAdmin(): TRPCMiddleware;        // Must be workspace admin
  requireAuthor(messageId: string): TRPCMiddleware;  // Must be message author
}

// User session (available in tRPC context)
interface UserSession {
  userId: string;
  email: string;
  workspaceId: string;
  role: 'admin' | 'member';
}
```

**Data owned:** `users`, `workspaces`, `workspace_members`, `api_keys`

**Dependencies:**
- External: Supabase Auth (handles OAuth, JWT, session management)
- `db` -- database access

**Communication pattern:**
- **Cross-cutting middleware.** Auth is not called explicitly by other subsystems. It's enforced via:
  1. tRPC middleware (checks JWT, loads user session into context)
  2. RLS policies (Postgres enforces workspace isolation at the database level)
- **Direct calls** for workspace management operations

**Key design decisions:**
- Auth is a middleware concern, not a service that other subsystems call. This means changing auth (e.g., swapping Supabase Auth for Auth0) doesn't require changes in thread-engine or agent-runtime -- only the middleware layer changes.
- RLS is the last line of defense. Even if the application code has a bug that skips permission checks, the database rejects unauthorized access. Defense in depth.
- Agent authentication is separate from user authentication. Agents use the service role key (bypasses RLS). This is acceptable because agents only write through the controlled `TaskProcessor` code path.

### 4.5 Subsystem 4: Config System

**Purpose:** Admin controls for workspace-level configuration -- agent roster, UI layout, feature toggles. The mechanism by which one codebase serves different use cases.

**Core interfaces:**

```typescript
// Config service
interface ConfigService {
  get(workspaceId: string, key: ConfigKey): Promise<ConfigValue>;
  list(workspaceId: string): Promise<UIConfig[]>;
  set(workspaceId: string, key: ConfigKey, value: ConfigValue): Promise<UIConfig>;
}

// Config keys (typed, not arbitrary strings)
type ConfigKey =
  | 'sidebar_layout'      // Which sidebar sections are visible
  | 'theme'               // Light/dark/custom
  | 'agent_roster_order'  // Order of agents in sidebar
  | 'fork_terminology'    // "Fork" vs "Side Discussion" vs "Tangent"
  | 'max_forks_per_thread'// Default: 5
  | 'default_agent'       // Which agent handles fork resolution
  | 'features';           // Feature flags

type ConfigValue = Record<string, unknown>;  // JSONB
```

**Data owned:** `ui_configs`

**Dependencies:**
- `auth` -- admin-only mutations
- `db` -- database access

**Communication pattern:**
- **Direct calls.** Frontend reads config on load. Admin writes config via tRPC mutation.
- No event-driven behavior. Config changes take effect on next page load (or can be made reactive via Supabase Realtime subscription on ui_configs, but not needed for dogfood).

**Key design decisions:**
- Config is simple key-value for dogfood. The 4-layer inheritance system (Platform -> Template -> Workspace -> User) from DESIGN-SPEC is sound but not implemented until vertical expansion. For dogfood, there is one workspace with one layer of config.
- Agent configs (`agent_configs` table) are technically part of the config system but owned by the agent-runtime subsystem. The config system owns only `ui_configs`.

### 4.6 Subsystem 5: Real-time Layer

**Purpose:** Delivers live updates to connected clients. New messages appear without refresh. Agent status updates show "thinking" indicators.

**Core interfaces:**

```typescript
// Client-side subscription hooks
interface RealtimeHooks {
  useThreadMessages(threadId: string): {
    messages: Message[];
    isLoading: boolean;
  };

  useThreadForks(threadId: string): {
    forks: Fork[];
  };

  useTaskStatus(threadId: string): {
    activeTasks: AgentTask[];
  };

  useTypingIndicator(threadId: string): {
    typingUsers: { userId: string; isAgent: boolean }[];
    sendTyping: () => void;
  };
}

// Event types (what Supabase Realtime broadcasts)
type RealtimeEvent =
  | { type: 'message.created'; payload: Message }
  | { type: 'message.updated'; payload: Message }
  | { type: 'message.deleted'; payload: { messageId: string } }
  | { type: 'fork.created'; payload: Fork }
  | { type: 'fork.resolved'; payload: Fork }
  | { type: 'fork.abandoned'; payload: Fork }
  | { type: 'task.status_changed'; payload: { taskId: string; status: string; agentId: string } }
  | { type: 'thread.updated'; payload: Thread }
  | { type: 'typing'; payload: { userId: string; threadId: string; forkId?: string; isAgent: boolean } };
```

**Data owned:** None. The real-time layer doesn't own data. It broadcasts changes from tables owned by other subsystems.

**Dependencies:**
- External: Supabase Realtime (the transport layer)
- Implicitly depends on `messages`, `forks`, `tasks`, `threads` tables being in the Supabase Realtime publication

**Communication pattern:**
- **Entirely event-driven.** No subsystem explicitly calls the real-time layer. Supabase Realtime automatically broadcasts when rows change in published tables.
- **Client-side only.** The server never sends messages through the real-time layer. It writes to the database, and Realtime handles distribution.

**Key design decisions:**
- The real-time layer is NOT a custom service. It's Supabase's built-in feature. We subscribe to database changes, not to custom events. This means any INSERT/UPDATE/DELETE that the application performs is automatically broadcast. Zero custom code for the transport layer.
- Typing indicators are the one exception: they use Supabase Broadcast (ephemeral pub/sub) rather than database changes, because typing events should not be persisted.
- Per-thread subscriptions, not per-workspace. This limits bandwidth and processing on the client.

### 4.7 Subsystem 6: Search

**Purpose:** Find messages by content across all channels and threads the user has access to.

**Core interfaces:**

```typescript
interface SearchService {
  searchMessages(input: {
    workspaceId: string;
    query: string;
    channelId?: string;  // Optional: restrict to one channel
    limit?: number;       // Default: 20
  }): Promise<SearchResult>;
}

interface SearchResult {
  messages: Array<{
    id: string;
    threadId: string;
    forkId: string | null;
    content: string;
    highlight: string;   // Content with <mark> tags around matches
    authorId: string;
    authorType: AuthorType;
    createdAt: Date;
    rank: number;
  }>;
  query: string;
}
```

**Data owned:** The `fts` generated column on `messages` and `context_items` tables, plus GIN indexes. No separate table.

**Dependencies:**
- `db` -- Postgres tsvector queries
- `auth` -- RLS ensures users only search messages in their workspace

**Communication pattern:**
- **Direct call.** Synchronous query, synchronous response.

**Key design decisions:**
- No separate search engine. PostgreSQL tsvector + GIN is sufficient for millions of messages. Elasticsearch/Typesense/Meilisearch would add infrastructure for zero benefit at dogfood scale.
- The tsvector column is `GENERATED ALWAYS AS ... STORED`, meaning it updates automatically on INSERT and UPDATE. No indexing pipeline. No eventual consistency lag.
- Future semantic search (vector similarity on embeddings) will use `context_items.embedding` column with pgvector. This is a separate query path, not a replacement for full-text search.

### 4.8 Subsystem 7: Storage Layer

**Purpose:** Abstracts database and file storage access. Centralizes Supabase client configuration. Provides a migration framework.

**Core interfaces:**

```typescript
// Database client factory
interface DatabaseClient {
  // Supabase client for authenticated user operations (RLS-enforced)
  userClient(accessToken: string): SupabaseClient;

  // Supabase client for server-side operations (bypasses RLS)
  serviceClient(): SupabaseClient;
}

// Migration runner
interface MigrationRunner {
  run(): Promise<void>;         // Apply pending migrations
  rollback(): Promise<void>;    // Revert last migration
  status(): Promise<MigrationStatus[]>;
}

// File storage
interface FileStorage {
  upload(bucket: string, path: string, file: Blob): Promise<{ url: string }>;
  download(bucket: string, path: string): Promise<Blob>;
  delete(bucket: string, path: string): Promise<void>;
  getPublicUrl(bucket: string, path: string): string;
}
```

**Data owned:** All tables (as the underlying store), but data semantics are owned by the subsystems above.

**Dependencies:**
- External: Supabase (Postgres, Storage, Realtime, Auth)

**Communication pattern:**
- **Direct calls** from all other subsystems. Every subsystem reads/writes through the storage layer.

**Key design decisions:**
- The `packages/db` package is the ONLY package that imports `@supabase/supabase-js`. All other packages access the database through this package. This is the key to future swappability: if Supabase is replaced with a direct Postgres client (e.g., Drizzle ORM), only `packages/db` changes.
- Migrations are SQL files, not ORM migrations. Raw SQL gives full control over Postgres features (generated columns, RLS policies, publications). An ORM would abstract away the features that make this architecture work.
- Two Supabase clients: `userClient` (with user's JWT, RLS-enforced) for read operations; `serviceClient` (service role key, bypasses RLS) for agent writes and admin operations. The choice is explicit per operation.

### 4.9 Subsystem Dependency Matrix

```
                    Thread  Agent   Auth   Config  Real-   Search  Storage
                    Engine  Runtime        System  time
Thread Engine        --     ASYNC    MW     READ    IMPL    --      RW
Agent Runtime       WRITE    --      --     READ    IMPL    --      RW
Auth & Identity      --      --      --      --      --      --     RW
Config System        --      --      MW      --      --      --     RW
Real-time Layer      --      --      --      --      --      --     READ
Search               --      --      MW      --      --      --     READ
Storage Layer        --      --      --      --      --      --      --

Legend:
  ASYNC  = Async, database-mediated (writes task row, doesn't call directly)
  MW     = Middleware (auth checked automatically, not explicit call)
  READ   = Reads data owned by that subsystem
  WRITE  = Writes data into that subsystem's tables
  IMPL   = Implicit (Supabase Realtime triggers automatically on DB changes)
  RW     = Read/Write to storage
  --     = No dependency
```

**Key observations:**
1. **Thread Engine and Agent Runtime are decoupled.** Thread Engine writes task rows (ASYNC). Agent Runtime reads and processes them. They never call each other directly.
2. **Auth is cross-cutting.** It's middleware, not a service call. Changing auth doesn't require changes in any other subsystem's business logic.
3. **Real-time Layer has no incoming dependencies.** No subsystem explicitly invokes it. It's purely reactive (triggered by database changes).
4. **Storage Layer has no outgoing dependencies.** It depends on nothing. Everything depends on it.
5. **Config System is leaf-level.** Only auth depends on it (for admin checks). Thread Engine and Agent Runtime read configs but don't depend on the config subsystem's logic.

### 4.10 Communication Patterns Summary

```
┌──────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION MAP                               │
│                                                                    │
│  SYNCHRONOUS (tRPC procedure calls):                               │
│    User ──> Thread Engine (channel/thread/fork/message CRUD)      │
│    User ──> Auth (session, workspace management)                  │
│    User ──> Config (get/set config)                               │
│    User ──> Search (search queries)                               │
│    User ──> Agent Runtime (list agents, get task status)          │
│                                                                    │
│  ASYNC DATABASE-MEDIATED:                                          │
│    Thread Engine ──[task row]──> Agent Runtime                    │
│    Agent Runtime ──[message row]──> Thread Engine (response)      │
│    Agent Runtime ──[task status]──> All Subscribers (via RT)      │
│                                                                    │
│  EVENT-DRIVEN (Supabase Realtime):                                 │
│    messages table ──[INSERT]──> Client WebSocket subscribers      │
│    forks table ──[UPDATE]──> Client WebSocket subscribers         │
│    tasks table ──[UPDATE]──> Client WebSocket subscribers         │
│    threads table ──[UPDATE]──> Client WebSocket subscribers       │
│                                                                    │
│  EPHEMERAL (Supabase Broadcast):                                   │
│    User ──[typing event]──> Other users in same thread            │
│    Agent ──[typing event]──> All users in same thread             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Recommendation Summary

### For Dogfood (20 Users)

1. **Single Fly.io Machine** running Next.js (API + frontend + agent processor). No separate services.
2. **Supabase Pro** for database, auth, real-time, and storage. One managed dependency.
3. **Direct Anthropic API** calls for agent tasks. In-process, fire-and-forget. No queue.
4. **Monorepo** with `packages/` (core, thread-engine, agent-runtime, auth, config, db, ui) and `apps/web`.
5. **Supabase Realtime** for all live updates. No custom WebSocket server.
6. **PostgreSQL tsvector** for search. No external search engine.
7. **No Redis, no CDN, no separate workers, no Kubernetes.**

Total infrastructure cost: **~$640-940/month** (dominated by LLM API costs).

### For Scale (200+ Users)

1. **Separate agent worker pool** (Fly.io Machines, auto-suspend)
2. **Redis** for task queue (BullMQ) and rate limiting (Upstash)
3. **Multiple web server instances** behind Fly.io's load balancer
4. **Read replica** for database
5. **Cloudflare CDN + WAF** for static assets and security
6. **Per-user runtime sessions** (Option D from RUNTIME-ARCHITECTURE.md)

The architecture supports this scale-up because:
- Agent processing is database-mediated (extracting it to workers = moving one function)
- All real-time is through Supabase Realtime (no custom WebSocket state to migrate)
- The monorepo structure means packages can be deployed independently when needed

---

## Open Questions

1. **Vercel for frontend only?** If the team prefers Vercel's DX for the Next.js frontend, a split architecture (Vercel for SSR + static, Fly.io for API + agents) is possible but adds complexity. Recommendation: start with everything on Fly.io, reconsider if deployment ergonomics become a problem.

2. **When to add Redis?** The threshold is subjective. Watch for: agent task processing delays (tasks sitting in `queued` for >5s regularly), web server CPU spikes during agent processing, or need for rate limiting. For 20 users, this won't happen.

3. **Database ORM timing.** Raw SQL + Supabase client is fine for 10 tables. At 20+ tables or when 3+ developers are writing queries, an ORM (Drizzle recommended) reduces bugs and improves DX. Recommendation: add Drizzle in Phase 4 when the schema stabilizes.

4. **Monorepo tooling: Nx vs Turborepo.** DESIGN-SPEC chose Nx. Turborepo is simpler and sufficient for this project size. Nx's code generation and dependency graph visualization are powerful but add learning curve. Either works. Recommendation: use Turborepo for simplicity; switch to Nx only if code generation or advanced caching is needed.

5. **Agent response streaming.** The current design inserts the complete response after the agent finishes. Streaming tokens to the UI (insert placeholder, update as tokens arrive) provides better UX but adds: message UPDATE subscriptions, partial content state management, and "replace placeholder with final" logic. Recommendation: implement streaming in Phase 4 after the core loop works.

---

## Rejected Approaches

### 1. Vercel-Only Deployment

**Why rejected:** Vercel serverless functions have hard timeouts (60-800s depending on plan). Agent tasks involve streaming 10-30s Claude API calls. While Vercel's Fluid Compute extends timeouts, the platform fundamentally doesn't support long-running processes or persistent WebSocket connections from the app server. For a product where AI agent responses are the core feature, the agent processing must be reliable and unconstrained by serverless timeout limits.

**Reconsider when:** Vercel launches persistent compute with no timeout limits and native WebSocket support. Or if agent tasks can be guaranteed to complete in <60s.

### 2. Microservices from Day 1

**Why rejected:** Splitting into thread-service, agent-service, auth-service, and search-service adds: 4 deployments, inter-service communication (HTTP or gRPC), distributed tracing, service discovery, and per-service monitoring. For 20 users and 2-3 developers, this is pure overhead. The monorepo + package structure provides the same logical separation without operational complexity.

**Reconsider when:** The team exceeds 5 developers, or specific subsystems need independent scaling (e.g., agent workers processing 1000+ tasks/hour while the web server handles 500+ concurrent users).

### 3. Event Sourcing

**Why rejected:** Event sourcing (storing every change as an immutable event, projecting current state) is powerful for audit trails and temporal queries but adds: event store, projections, eventual consistency, replay logic, and debugging complexity. Messages in OpenVibe are append-mostly. The simple INSERT + Supabase Realtime pattern provides the same real-time delivery without event sourcing overhead.

**Reconsider when:** Regulatory requirements demand immutable audit trails of every message edit and deletion, or when offline-first CRDT-based sync is needed.

### 4. GraphQL API

**Why rejected:** GraphQL adds schema definition, resolver implementation, codegen tooling, and a runtime (Apollo/URQL). For a single-client application (Next.js web app), tRPC provides the same end-to-end type safety with zero schema overhead. GraphQL's strengths (multiple clients with different data needs, deep nested queries) are irrelevant when there's one frontend.

**Reconsider when:** A mobile app or third-party API consumers need to query the data with different shape requirements.

### 5. Separate apps/api and apps/web

**Why rejected:** Running the API as a separate deployment from the web app adds: inter-process communication latency, CORS configuration, separate deployment pipelines, and environment duplication. With Next.js App Router, the tRPC API runs inside the same application. Server Components can even call tRPC procedures without HTTP. For dogfood, the simplicity of one deployable outweighs any separation benefits.

**Reconsider when:** The API needs to serve non-web clients (mobile app, CLI tool, external integrations), or the agent worker needs to be a separate process with its own scaling characteristics (at 200+ users).

---

*Research completed: 2026-02-07*
*Researcher: system-architect*
