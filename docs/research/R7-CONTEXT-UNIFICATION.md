# R7: Cross-Runtime Context Unification Research

> Status: Complete | Researcher: agent-lifecycle-researcher | Date: 2026-02-07

---

## Research Questions

1. How to design a unified context layer across OpenClaw (Telegram), Claude Code (CLI), and Web UI?
2. Can Memory serve as a "context bus" -- not just storage but active context propagation?
3. How to abstract MCP skill differences across runtimes? (Claude Code has Bash, OpenClaw doesn't)
4. What's the minimum shared context that makes cross-runtime experience coherent?
5. How do OpenAI Agents SDK, Google ADK, or A2A protocol handle cross-runtime context?
6. Practical proposal: what would a context unification API look like?

---

## Sources Consulted

### Internal Design Documents
- `docs/design/M3-AGENT-RUNTIME.md` -- Agent containers with memory mounts, team vs private memory split
- `docs/design/M4-TEAM-MEMORY.md` -- Memory API, document/vector/metadata stores, Supabase backend
- `docs/design/M5-ORCHESTRATION.md` -- Message routing, WebSocket gateway, agent scheduling
- `docs/architecture/DESIGN-SPEC.md` -- Memory-first philosophy, pluggable storage, 4-layer config
- `docs/design/GAP-ANALYSIS.md` -- R7 identified as "complete blind spot": OpenClaw MEMORY.md, Claude Code .session-memory, @state/ as file-level not context-level sharing

### External Research
- Google A2A protocol specification v0.3 (a2a-protocol.org)
- Google ADK session state and memory management (google.github.io/adk-docs)
- MCP specification November 2025 (modelcontextprotocol.io, 97M+ monthly SDK downloads)
- OpenAI Agents SDK handoff and context patterns (openai.github.io/openai-agents-python)
- Letta/MemGPT memory blocks and context engineering (docs.letta.com)
- Claude Code Tasks and Agent Teams context patterns (code.claude.com)
- LangGraph checkpointing for cross-session state (langchain.com/langgraph)

### Current Runtime Analysis
- OpenClaw: Telegram bot, uses MEMORY.md + daily logs, SOUL.md personality, markdown-based context
- Claude Code: CLI tool, uses .session-memory, CLAUDE.md, filesystem-based context, Tasks feature
- APOS @state/ folder: priorities.md, focus.yaml, sync.yaml -- file-level sharing between systems

---

## Current State Analysis: The Problem in Detail

### Three Runtimes, Three Contexts

```
OpenClaw (Telegram)              Claude Code (CLI)                Future Web UI
===================              ================                ==============
Context Store:                   Context Store:                   Context Store:
  @claw/maxos/MEMORY.md           @apos/memory/                    ??? (TBD)
  @claw/maxos/SOUL.md             .session-memory/
  @claw/maxos/logs/               CLAUDE.md
                                   ~/.claude/tasks/

Memory Model:                    Memory Model:                    Memory Model:
  Markdown files (read/write)      Session memory (ephemeral)       ??? (TBD)
  Append-only daily logs           Filesystem (persistent)
                                   Tasks (persistent, local)

Tool Access:                     Tool Access:                     Tool Access:
  MCP (limited set)                MCP + Bash + File ops            MCP (limited set)
  No filesystem access             Full filesystem access            API-based tools
  No code execution                Full code execution              Sandboxed execution
  Telegram API                     Terminal access                  Browser APIs

State Sharing:                   State Sharing:                   State Sharing:
  Reads/writes @state/             Reads/writes @state/             ??? (TBD)
  Via filesystem only              Via filesystem only
```

### What Gets Lost Between Runtimes

| Scenario | What's Lost |
|----------|------------|
| User asks OpenClaw a question, then continues in Claude Code | OpenClaw's conversation history, reasoning, and context are invisible to Claude Code |
| Claude Code agent discovers something during a coding task | OpenClaw doesn't know about it unless someone manually writes it to @state/ |
| User switches from CLI to web | All session context is lost, starts from scratch |
| Agent makes a decision in one runtime | Other runtimes don't know why or that it happened |
| A task is blocked in Claude Code | OpenClaw can't help the user follow up on it |

### Root Cause

The `@state/` folder provides **file-level sharing** but not **context-level sharing**:
- Files must be explicitly written and read
- No notification when something changes
- No semantic search across runtimes
- No structured context format
- No real-time propagation

This is like sharing a Google Drive folder and hoping everyone reads the right files at the right time. It works for static data but fails for dynamic context.

---

## Question 1: Unified Context Layer Design

### Options Explored

#### Option A: Shared Database (Extend M4 Team Memory)

**Description:** Extend the existing M4 Team Memory design (Supabase/Postgres) to serve as the unified context store. All runtimes read from and write to the same database.

**Architecture:**
```
OpenClaw ─────┐
              |     ┌───────────────────────────────────┐
              ├────>│        Unified Context Layer        │
              |     │                                     │
Claude Code ──┤     │  ┌─────────┐  ┌────────────────┐  │
              |     │  │ Context │  │  Notification   │  │
              ├────>│  │  Store  │  │    Service      │  │
              |     │  │ (M4 DB) │  │  (Realtime)     │  │
Web UI ───────┘     │  └─────────┘  └────────────────┘  │
                    │                                     │
                    │  ┌─────────┐  ┌────────────────┐  │
                    │  │ Vector  │  │    Context      │  │
                    │  │ Search  │  │   Resolution    │  │
                    │  │         │  │    Engine       │  │
                    │  └─────────┘  └────────────────┘  │
                    └───────────────────────────────────┘
```

**How each runtime connects:**
- **OpenClaw**: REST API calls to Context Layer (OpenClaw already uses HTTP for tool calls)
- **Claude Code**: MCP server that bridges to Context Layer (Claude Code uses MCP for tools)
- **Web UI**: Direct Supabase client connection (standard web pattern)

**Pros:**
- Extends existing M4 design -- not starting from scratch
- Single source of truth for all context
- Supabase Realtime provides change notification for free
- Vector search (pgvector) enables semantic context retrieval
- SQL for structured queries, vectors for semantic queries

**Cons:**
- Requires network connectivity from all runtimes
- Claude Code and OpenClaw need adapters (MCP server or REST client)
- Latency: every context read/write goes through network
- Offline capability limited

**Verdict: Adopt as primary approach.** This is the right architecture. M4 was designed for this; it just needs to be extended from "team memory" to "unified context layer."

#### Option B: File-Based Sync (Extend @state/)

**Description:** Enhance the current @state/ folder approach with structure, conventions, and file watching.

**Pros:**
- Simple, already partially works
- No new infrastructure needed
- Both OpenClaw and Claude Code can read/write files

**Cons:**
- No semantic search
- No real-time notification (file watching is fragile)
- Concurrent writes cause conflicts
- Doesn't work across machines (non-local runtimes)
- No permission model

**Verdict: Reject as primary.** Keep @state/ as a local cache/fallback, but it's insufficient for real context unification.

#### Option C: Event-Driven Bus (Pub/Sub)

**Description:** All runtimes publish context events to a central bus. Each runtime subscribes to relevant events.

**Pros:**
- Real-time propagation
- Loose coupling between runtimes
- Can filter by relevance

**Cons:**
- Events are ephemeral -- need a store anyway (back to Option A)
- Adds infrastructure (Redis/Kafka/NATS)
- Complex to get right for ordered, reliable delivery
- Overkill for ~20 user dogfood

**Verdict: Defer.** Supabase Realtime provides pub/sub-like capability on top of the database. Add dedicated event bus only if Supabase Realtime is insufficient at scale.

### Recommendation

**Option A (Shared Database via M4) with Supabase Realtime for notifications.** This gives database persistence + real-time propagation without additional infrastructure. The @state/ folder becomes a local cache/sync target, not the source of truth.

---

## Question 2: Memory as "Context Bus"

### The Concept

Instead of Memory being passive storage ("write data, read it later"), Memory becomes an active context propagation system:
- **Write**: Runtime writes context + signals that it's relevant to other runtimes
- **Propagate**: Context Layer notifies interested runtimes of new context
- **Resolve**: Each runtime pulls in the context it needs, formatted for its capabilities
- **React**: Agents in other runtimes can act on new context automatically

### Design

```
Context Bus = M4 Memory + Realtime Notifications + Context Resolution

Write Path:
  Runtime writes context item with metadata:
    - source_runtime: "claude-code"
    - scope: "task" | "thread" | "global"
    - relevance: ["coding", "project-x", "@user-charles"]
    - urgency: "background" | "attention" | "blocking"
    - ttl: 3600 (seconds, optional)

Propagation:
  Supabase Realtime broadcasts to all subscribed runtimes:
    - Filter by scope, relevance tags, urgency
    - Each runtime subscribes to relevant channels

Resolution:
  Each runtime's adapter transforms context for its capabilities:
    - Claude Code: Inject into conversation via /add-context or MCP tool
    - OpenClaw: Add to next message's system context
    - Web UI: Display in sidebar or inject into thread
```

### Implementation Layers

**Layer 1: Context Items (Data)**
```typescript
interface ContextItem {
  id: string;
  teamId: string;

  // Content
  type: 'discovery' | 'decision' | 'status' | 'request' | 'alert';
  title: string;
  content: string;
  summary: string;  // One-line for quick injection

  // Source
  sourceRuntime: 'openclaw' | 'claude-code' | 'web' | 'system';
  sourceAgentId?: string;
  sourceTaskId?: string;
  sourceThreadId?: string;

  // Routing
  scope: 'task' | 'thread' | 'space' | 'global';
  relevanceTags: string[];
  urgency: 'background' | 'attention' | 'blocking';

  // Lifecycle
  createdAt: Date;
  expiresAt?: Date;
  consumed: boolean;  // Has any runtime acted on this?

  // Vector for semantic matching
  embedding?: number[];
}
```

**Layer 2: Context Subscriptions (Routing)**
```typescript
interface ContextSubscription {
  runtimeId: string;
  runtimeType: 'openclaw' | 'claude-code' | 'web';

  // What to subscribe to
  scopes: string[];
  relevanceTags: string[];
  minUrgency: 'background' | 'attention' | 'blocking';

  // How to deliver
  deliveryMode: 'push' | 'pull';
  endpoint?: string;  // For push mode
}
```

**Layer 3: Context Resolution (Adaptation)**
```typescript
interface ContextResolver {
  // Transform context item for specific runtime
  resolve(item: ContextItem, targetRuntime: RuntimeType): ResolvedContext;
}

// Example: Claude Code resolver
class ClaudeCodeResolver implements ContextResolver {
  resolve(item: ContextItem, target: 'claude-code'): ResolvedContext {
    return {
      // Claude Code gets markdown format injected via MCP
      format: 'markdown',
      content: `## Context Update: ${item.title}\n${item.content}`,
      injection: 'mcp-tool',  // Inject via MCP read tool
    };
  }
}

// Example: OpenClaw resolver
class OpenClawResolver implements ContextResolver {
  resolve(item: ContextItem, target: 'openclaw'): ResolvedContext {
    return {
      // OpenClaw gets concise text for Telegram
      format: 'text',
      content: item.summary,
      injection: 'system-prompt-append',
    };
  }
}
```

### Assessment

Memory as a context bus is **architecturally sound** and aligns with the DESIGN-SPEC's "Memory First" philosophy. The key insight is that Memory's role expands from "persistent knowledge store" to "real-time context propagation layer." This is not a separate system -- it's M4 with three additions:

1. **Realtime subscriptions** (Supabase already provides this)
2. **Context resolution** (runtime-specific adapters, new component)
3. **Urgency/scope routing** (metadata on memory items, extension of existing schema)

**Verdict: Adopt.** This is the right mental model. Memory is not just a database -- it's the nervous system of the platform.

---

## Question 3: MCP Skill Abstraction Across Runtimes

### The Problem

```
Claude Code capabilities:        OpenClaw capabilities:
  - Bash (terminal execution)      - No Bash
  - Read/Write files               - Limited file access
  - Glob/Grep (file search)        - No file search
  - Git operations                 - No git
  - MCP tools                      - MCP tools (different set)
  - Web search/fetch               - Web search/fetch
  - Claude Code specific tools     - Telegram API
                                   - OpenClaw specific tools
```

When an agent in Claude Code writes "run `npm test`" as part of a task, and the task needs to be continued in OpenClaw, what happens to that step?

### Options Explored

#### Option A: Capability Intersection (Lowest Common Denominator)

**Description:** Only use capabilities available in ALL runtimes. Tasks that need runtime-specific tools are locked to that runtime.

**Pros:** Simple, predictable
**Cons:** Severely limits agent capability. Can't even search files from OpenClaw.

**Verdict: Reject.** Too restrictive. Throws away the value of specialized runtimes.

#### Option B: Capability Abstraction Layer

**Description:** Define abstract capabilities that each runtime implements differently (or declares it cannot).

**Capability Categories:**
```yaml
capabilities:
  code_execution:
    claude-code: native (Bash tool)
    openclaw: via-api (call a remote code execution service)
    web-ui: sandboxed (WebContainer or similar)

  file_operations:
    claude-code: native (Read/Write/Glob/Grep)
    openclaw: via-api (memory layer for reads, task queue for writes)
    web-ui: via-api (API calls to backend)

  communication:
    claude-code: via-mcp (Slack, email MCP servers)
    openclaw: native (Telegram API) + via-mcp (Slack, email)
    web-ui: via-api (backend handles)

  search:
    claude-code: native (Grep, Glob, web search)
    openclaw: via-mcp (web search only)
    web-ui: via-api (backend search)

  memory:
    claude-code: via-mcp (Context Layer MCP server)
    openclaw: via-api (Context Layer REST API)
    web-ui: native (Supabase client)
```

**How it works:**
1. Task defines what capabilities it needs (not HOW to execute them)
2. Orchestrator checks target runtime's capability matrix
3. If native: execute directly
4. If via-api: delegate to a service that has the capability
5. If unavailable: queue for a runtime that can handle it, or escalate

**Pros:**
- Each runtime uses its native strengths
- Tasks can still move between runtimes (with degradation)
- Clear contract for what each runtime provides
- New runtimes just need to declare their capabilities

**Cons:**
- "via-api" execution adds latency
- Some capabilities can't be meaningfully abstracted (e.g., interactive terminal)
- Capability matrix needs maintenance as runtimes evolve

**Verdict: Adopt.** This is the right architecture. It doesn't force uniformity but provides graceful degradation.

#### Option C: Remote Execution Proxy

**Description:** When a runtime needs a capability it doesn't have, it sends the request to a runtime that does.

**Example:** OpenClaw needs to run `npm test` -> sends request to Claude Code runtime -> gets result back.

**Pros:**
- Full capability access from any runtime
- No duplication of tools

**Cons:**
- Requires always-available "capability provider" runtimes
- Latency for remote execution
- Security implications (remote code execution)
- Complex failure handling

**Verdict: Partial adopt.** Use for specific cases (e.g., code execution from OpenClaw) but not as the general solution. Capability abstraction (Option B) is the primary approach.

### Recommended MCP Abstraction

**Shared MCP Server for Context Layer:**

Build a single MCP server that all runtimes can connect to, providing:
```
OpenVibe Context MCP Server
  Tools:
    - context_read(scope, query)     # Read context items
    - context_write(item)            # Write context item
    - context_search(query, filters) # Semantic search
    - task_status(taskId)            # Check task state
    - task_update(taskId, status)    # Update task state
    - memory_query(path, type)       # Query team memory
    - memory_write(item)             # Write to team memory

  Resources:
    - team-context://current         # Current team context
    - task://active                  # Active tasks
    - decisions://recent             # Recent decisions
```

This MCP server is the bridge. Claude Code connects to it like any other MCP server. OpenClaw connects to it. Web UI uses the underlying API directly. All share the same context.

**Runtime-specific capabilities remain local:**
- Claude Code keeps Bash, file ops, git (local tools)
- OpenClaw keeps Telegram API (local tool)
- Web UI keeps browser APIs (local tools)

**Cross-runtime capabilities go through the MCP server:**
- Context reading/writing
- Task management
- Memory access
- Team communication

---

## Question 4: Minimum Shared Context for Coherence

### What Makes Cross-Runtime Experience Feel "Connected"

The user should feel like they're talking to the same system regardless of which runtime they're using. This requires a minimum set of shared context.

### Minimum Viable Shared Context

```yaml
minimum_shared_context:
  # Layer 1: Identity (Who)
  user_identity:
    - user_id
    - user_name
    - current_role (CEO/personal/family)
    - preferences (communication style, language)
    - trust_level (per runtime)

  # Layer 2: State (What's happening now)
  active_state:
    - current_tasks (id, title, status, assigned_runtime)
    - blocked_items (what's waiting for human input)
    - recent_decisions (last 10, with reasoning)
    - current_focus (from @state/focus.yaml equivalent)

  # Layer 3: History (What happened recently)
  recent_context:
    - last_5_interactions (summary, not full transcript)
    - last_3_decisions (decision + reasoning)
    - active_thread_summaries (what's being discussed)

  # Layer 4: Knowledge (What we know)
  team_knowledge:
    - project_context (active projects, goals, constraints)
    - team_members (who does what)
    - key_decisions (important decisions with reasoning)
    - frequently_accessed_docs (pinned references)
```

### Token Budget Analysis

Each runtime needs to inject shared context into its conversation. How many tokens does this cost?

| Context Layer | Est. Tokens | Notes |
|--------------|-------------|-------|
| User identity + preferences | ~200 | Small, static |
| Active tasks (5 tasks) | ~500 | Title + status + brief |
| Blocked items | ~300 | What needs attention |
| Recent decisions (5) | ~750 | Decision + 1-line reasoning |
| Current focus | ~100 | Single paragraph |
| Last 5 interactions (summaries) | ~1,000 | ~200 tokens each |
| Active thread summaries (3) | ~600 | ~200 tokens each |
| Project context | ~500 | Active project briefs |
| **Total minimum context** | **~3,950** | **~4K tokens** |

At ~4K tokens, this is affordable to inject at every interaction across all runtimes. Even with Claude Haiku at $1/1M input tokens, this costs $0.004 per interaction -- negligible.

### Injection Strategy per Runtime

**Claude Code:**
- Inject via CLAUDE.md or MCP server `context_read()` tool at session start
- Auto-refresh via MCP when context changes (new task status, new decision)
- Full 4K context budget is fine (Claude Code has large context windows)

**OpenClaw:**
- Inject condensed version (~2K tokens) into system prompt
- Focus on: active tasks, blocked items, recent decisions
- Skip: full interaction history (OpenClaw has its own)
- Update on each user message (pull latest from Context Layer)

**Web UI:**
- Display context in sidebar (not injected into LLM context -- shown visually)
- LLM gets full 4K context for AI-assisted features
- Real-time updates via Supabase Realtime subscriptions

---

## Question 5: How Other Frameworks Handle Cross-Runtime Context

### OpenAI Agents SDK

**Approach:** Handoffs transfer full conversation history between agents.

**Context handling:**
- Sessions provide persistent memory within an agent loop
- Handoffs carry all prior messages to the receiving agent
- No cross-runtime concept -- all agents run in the same Python/TypeScript process

**Strengths:** Simple mental model (handoff = conversation transfer)
**Weaknesses:** Doesn't scale to different runtimes. Full history transfer is token-expensive.

**Relevance to OpenVibe:** The handoff concept is useful for within-runtime agent switches, but doesn't solve cross-runtime. OpenVibe needs structured handoffs (see R3), not conversation replay.

### Google ADK

**Approach:** Session state with scoped persistence using key prefixes.

**Context handling:**
- `user:` prefix -- state persists across all sessions for this user
- `app:` prefix -- state persists across all sessions for all users
- Session state updated via `EventActions.state_delta` -- changes are tracked and persisted
- Multiple `SessionService` backends: InMemory (dev), VertexAI (prod), DatabaseSession (custom)

**Strengths:**
- Clean state scoping model (user-level, app-level, session-level)
- State changes are event-sourced (trackable, replayable)
- Multiple persistence backends

**Weaknesses:**
- Designed for single-framework (ADK) agents, not cross-runtime
- State is key-value, not semantic (no vector search)
- Session services don't communicate across different ADK deployments

**Relevance to OpenVibe:** The state prefix pattern (`user:`, `app:`) is directly applicable. OpenVibe should adopt similar scoping:
- `user:{userId}:` -- user preferences, history
- `team:{teamId}:` -- team knowledge, decisions
- `task:{taskId}:` -- task-specific context
- `thread:{threadId}:` -- thread-specific context

### Google A2A Protocol

**Approach:** Standardized inter-agent communication over HTTPS with JSON-RPC.

**Context handling:**
- Agent Cards: JSON metadata documents describing agent identity, capabilities, skills
- Tasks: The unit of work exchanged between agents, with status tracking
- Artifacts: Results produced by agents (text, files, structured data)
- Support for sync, streaming, and async interaction modes

**Strengths:**
- Open standard with 150+ organizations supporting it
- Transport-agnostic (HTTPS + JSON-RPC, with gRPC support in v0.3)
- Agent discovery via Agent Cards (self-describing capabilities)
- Multi-mode: sync for quick queries, async for long-running tasks

**Weaknesses:**
- Designed for inter-organization agent communication, not intra-team context sharing
- No shared memory or persistent context between A2A interactions
- Each interaction is relatively independent (no accumulated context)
- Still young (v0.3, mid-2025)

**Relevance to OpenVibe:**
- Agent Card concept maps to OpenVibe's agent capability declarations
- A2A's task model (with status and artifacts) aligns with R3's task lifecycle
- The protocol is worth supporting for external agent integration (e.g., customer's agents talking to OpenVibe agents)
- But A2A alone doesn't solve the internal context unification problem -- it's a communication protocol, not a context layer

### Letta/MemGPT

**Approach:** Self-editing memory blocks that persist across all interactions.

**Context handling:**
- Memory blocks: structured, persistent, always-visible context sections
- Agents actively manage their own memory using tools
- Core memory (always in context) vs archival memory (retrieved on demand)
- Conversations API (Jan 2026): agents maintain shared memory across parallel experiences

**Strengths:**
- Most sophisticated context management in the ecosystem
- Memory blocks are the closest thing to a "context bus" concept
- Agents learn and evolve their context over time
- Production REST API for multi-client access

**Weaknesses:**
- Single-framework (Letta agents only)
- Complex to set up and tune
- Memory management overhead (every edit = tool call = tokens)
- No built-in cross-runtime abstraction

**Relevance to OpenVibe:** Letta's memory blocks are the best existing model for what OpenVibe's context unification should look like. Key patterns to adopt:
- Structured, labeled context sections (not just free-form text)
- Agents that actively maintain context (not just consume it)
- Always-visible core context + retrievable extended context
- Context engineering as a first-class discipline

### Comparative Assessment

| Aspect | OpenAI SDK | Google ADK | A2A Protocol | Letta |
|--------|-----------|------------|-------------|-------|
| Cross-runtime context | None | Scoped state | Agent Cards | Memory blocks |
| Persistent shared context | None | Session state | None | Conversations API |
| Real-time propagation | None | None | Async/streaming | None |
| Semantic search | None | None | None | Archival search |
| Context resolution per runtime | None | None | Agent capability matching | None |

**Key insight:** No existing framework solves cross-runtime context unification. They all assume agents run in a single framework/runtime. OpenVibe needs to build this capability, but can learn from their patterns.

---

## Question 6: Context Unification API Proposal

### Overview

The Context Unification API is an extension of M4 Team Memory that adds: real-time propagation, runtime-specific resolution, and structured shared context management.

### API Design

#### Core Endpoints

```typescript
// === Context Management ===

// Write context (any runtime can write)
POST /api/context
{
  type: 'discovery' | 'decision' | 'status' | 'request' | 'alert',
  title: string,
  content: string,
  summary: string,        // One-line summary for compact injection
  scope: 'task' | 'thread' | 'space' | 'global',
  relevanceTags: string[],
  urgency: 'background' | 'attention' | 'blocking',
  sourceRuntime: string,
  sourceTaskId?: string,
  sourceThreadId?: string,
  expiresAfterSeconds?: number
}

// Read context (filtered for runtime)
GET /api/context?scope={scope}&runtime={runtime}&limit={n}&since={timestamp}
Response: {
  items: ContextItem[],
  totalTokens: number  // Pre-computed token count for budget awareness
}

// Search context (semantic)
POST /api/context/search
{
  query: string,
  scope?: string,
  type?: string,
  limit: number
}
Response: {
  results: [
    {
      item: ContextItem,
      score: number,
      highlight: string
    }
  ]
}

// Get minimum shared context (formatted for specific runtime)
GET /api/context/shared?runtime={runtime}&tokenBudget={budget}
Response: {
  identity: { ... },
  activeTasks: [ ... ],
  recentDecisions: [ ... ],
  currentFocus: string,
  recentInteractionSummaries: [ ... ],
  totalTokens: number,
  formattedMarkdown: string  // Ready to inject into agent context
}
```

#### Real-Time Subscriptions

```typescript
// WebSocket / Supabase Realtime
// Subscribe to context changes

// Runtime subscribes to relevant context
supabase
  .channel(`context:${teamId}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'context_items',
    filter: `scope=in.(global,space) AND urgency=in.(attention,blocking)`
  }, (payload) => {
    const item = payload.new;
    const resolved = resolver.resolve(item, currentRuntime);
    injectContext(resolved);
  })
  .subscribe();
```

#### MCP Server Interface

```typescript
// OpenVibe Context MCP Server
// (All runtimes connect to this via MCP)

tools:
  openvibe_context_read:
    description: "Read current shared context for this team"
    parameters:
      scope: string  // 'task', 'thread', 'space', 'global'
      limit: number
    returns: ContextItem[]

  openvibe_context_write:
    description: "Write a context item (discovery, decision, status update)"
    parameters:
      type: string
      title: string
      content: string
      scope: string
      urgency: string

  openvibe_context_search:
    description: "Search context by semantic query"
    parameters:
      query: string
      limit: number
    returns: SearchResult[]

  openvibe_task_status:
    description: "Get or update task status"
    parameters:
      taskId: string
      newStatus?: string
    returns: TaskInfo

  openvibe_memory_query:
    description: "Query team memory"
    parameters:
      path: string
      type: string
    returns: MemoryItem[]
```

### Database Schema Extension (on top of M4)

```sql
-- Extend memory_items table for context bus functionality
ALTER TABLE memory_items ADD COLUMN IF NOT EXISTS
  source_runtime TEXT,
  scope TEXT DEFAULT 'global',
  urgency TEXT DEFAULT 'background',
  relevance_tags TEXT[] DEFAULT '{}',
  summary TEXT,
  consumed BOOLEAN DEFAULT FALSE,
  expires_at TIMESTAMPTZ;

-- Context subscriptions
CREATE TABLE context_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL,
  runtime_id TEXT NOT NULL,
  runtime_type TEXT NOT NULL,
  scopes TEXT[] DEFAULT '{}',
  relevance_tags TEXT[] DEFAULT '{}',
  min_urgency TEXT DEFAULT 'background',
  delivery_mode TEXT DEFAULT 'pull',  -- 'push' | 'pull'
  endpoint TEXT,  -- For push delivery
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast context retrieval
CREATE INDEX idx_context_scope_urgency
  ON memory_items(team_id, scope, urgency)
  WHERE source_runtime IS NOT NULL;

CREATE INDEX idx_context_runtime_tags
  ON memory_items USING GIN(relevance_tags)
  WHERE source_runtime IS NOT NULL;
```

### Runtime Adapter Implementations

**Claude Code Adapter:**
```
Connection: MCP server (openvibe-context MCP)
Context injection: On session start, call openvibe_context_read
Context writing: Agent calls openvibe_context_write during task execution
Updates: Periodic polling via MCP tool calls (no push in MCP yet)
Token budget: 4K tokens for shared context
```

**OpenClaw Adapter:**
```
Connection: REST API (Context Layer HTTP endpoints)
Context injection: Prepend to system prompt on each user message
Context writing: After each significant agent action, POST to /api/context
Updates: Poll on each message (sufficient for Telegram's interaction pattern)
Token budget: 2K tokens for condensed shared context
```

**Web UI Adapter:**
```
Connection: Supabase client (direct DB access + Realtime)
Context injection: Display in UI sidebar; inject into AI calls
Context writing: User actions trigger context writes
Updates: Real-time via Supabase Realtime subscriptions
Token budget: 4K tokens for AI features, unlimited for UI display
```

### Implementation Phases

**Phase 1 (MVP/Dogfood):**
- Deploy M4 schema with context extensions
- Build OpenVibe Context MCP server (basic read/write/search)
- Connect Claude Code via MCP
- Connect OpenClaw via REST API
- Shared context: user identity + active tasks + recent decisions
- Manual sync trigger (not real-time)

**Phase 2:**
- Add Supabase Realtime subscriptions
- Build context resolution engine (runtime-specific formatting)
- Add vector search for semantic context retrieval
- Automated context propagation (no manual trigger)
- Token budget management per runtime

**Phase 3:**
- Web UI adapter with real-time updates
- Agent-driven context management (agents write context as they work)
- Context analytics (what context is used, what's stale)
- A2A protocol support for external agent integration
- Advanced capability routing (remote execution proxy for cross-runtime tools)

---

## Recommendation

### Architecture Decision

Build a **Context Unification Layer** as an extension of M4 Team Memory, exposed via:
1. **REST API** for runtimes that use HTTP (OpenClaw, custom agents)
2. **MCP Server** for runtimes that use MCP (Claude Code, future MCP-compatible tools)
3. **Supabase Client** for runtimes that can connect directly (Web UI)
4. **Supabase Realtime** for push notifications to subscribed runtimes

### Why This Is Right

1. **Extends, doesn't replace**: M4 Team Memory is already designed for shared knowledge. Context unification adds routing, resolution, and real-time propagation -- it's an upgrade, not a rewrite.

2. **Memory First**: Aligns perfectly with DESIGN-SPEC.md's core philosophy. The context layer IS memory, just with active propagation.

3. **MCP as the bridge**: MCP is the one protocol that works across Claude Code, OpenClaw, and most modern AI frameworks. Using MCP as the connection protocol is future-proof (97M+ monthly SDK downloads, Linux Foundation governance).

4. **Incremental delivery**: Phase 1 (basic read/write via MCP + REST) is buildable in days, not weeks. Real-time and semantic search layer on later.

5. **Token-efficient**: ~4K tokens for full shared context per interaction is negligible cost-wise and well within all context windows.

### What NOT to Do

- Don't try to make all runtimes identical -- they have different strengths
- Don't replicate context in each runtime's native format (MEMORY.md, .session-memory) -- centralize
- Don't build a custom pub/sub system -- Supabase Realtime is sufficient
- Don't wait for A2A protocol maturity -- build on proven tech (REST + MCP) now

---

## Open Questions

1. **Conflict resolution**: When two runtimes write conflicting context simultaneously (e.g., two agents make different decisions about the same thing), who wins? Need a conflict resolution strategy (last-write-wins? human arbitration?).

2. **Context staleness**: How to detect and clean up stale context? TTL is one mechanism, but some context (decisions) should persist indefinitely while others (status updates) should expire.

3. **Privacy across runtimes**: If a user shares something privately in Claude Code, should it propagate to OpenClaw? Need per-item privacy controls that respect the runtime boundary.

4. **MCP server hosting**: Where does the OpenVibe Context MCP server run? Locally (alongside each runtime) or centrally (as a service)? Central is simpler but adds latency. Local requires synchronization.

5. **Offline handling**: What happens when a runtime can't reach the Context Layer? Cache locally and sync later? This is essentially @state/ as a fallback, which is what we have today.

6. **Context injection timing**: When exactly should shared context be injected into an agent's prompt? Every message? Only on session start? On demand? Different strategies have different cost/freshness tradeoffs.

---

## Rejected Approaches

### 1. File-Based Sync as Primary Context Layer (@state/ Enhancement)

**Why rejected:** Files don't support semantic search, real-time propagation, concurrent writes, or structured querying. They work for static configuration sharing but fail for dynamic context.

**Reconsider when:** Never as primary. Keep as fallback/cache for offline scenarios.

### 2. Separate Context Store per Runtime (Federated Model)

**Why rejected:** Each runtime maintaining its own context store with sync between them creates n^2 sync complexity. Three runtimes = 6 sync directions. Adding a fourth = 12. Centralized store with adapters is O(n).

**Reconsider when:** If runtimes need to operate completely independently for extended periods (e.g., air-gapped deployment). In that case, CRDTs or event sourcing with merge could work, but this is Phase 3+ complexity.

### 3. A2A Protocol as Internal Communication Layer

**Why rejected:** A2A is designed for inter-organization agent communication (agent at Company A talks to agent at Company B). It's too heavyweight for intra-team context sharing. The Agent Card discovery, HTTPS transport, and JSON-RPC framing add unnecessary complexity when the agents are all part of the same system.

**Reconsider when:** OpenVibe needs to support external agents (e.g., a customer's agent querying OpenVibe's agents). At that point, A2A is the right protocol for the external boundary, while the internal Context Layer remains the internal protocol.

### 4. Building Custom Real-Time Infrastructure (WebSocket Server, Redis Pub/Sub)

**Why rejected:** Supabase Realtime provides this out of the box on top of the Postgres database that M4 already uses. Adding Redis or a custom WebSocket server for 20 users during dogfood is unnecessary complexity.

**Reconsider when:** Scale exceeds Supabase Realtime's capacity (hundreds of concurrent subscriptions, sub-100ms latency requirements). At that point, dedicated infrastructure may be needed, but this is a scale problem, not an architecture problem.

### 5. Full Conversation History Sharing Between Runtimes

**Why rejected:** Sharing full conversation transcripts between OpenClaw and Claude Code would be enormously token-expensive and context-polluting. A 50-message OpenClaw conversation = ~25K tokens that Claude Code would have to process without clear relevance.

**Reconsider when:** Context windows become so large (10M+) that the token cost is negligible AND models become better at filtering irrelevant context. Possibly 2027+.

---

*Research completed: 2026-02-07*
*Researcher: agent-lifecycle-researcher*
