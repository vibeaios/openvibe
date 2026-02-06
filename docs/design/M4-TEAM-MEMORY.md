> **SUPERSEDED**: This document is from the initial design phase. For implementation, refer to:
> - [`BACKEND-MINIMUM-SCOPE.md`](../research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) — Data model
> - [`R7-CONTEXT-UNIFICATION.md`](../research/R7-CONTEXT-UNIFICATION.md) — Context architecture

# M4: Team Memory Layer (Shared Memory)

> Status: Draft | Priority: Critical | Dependency: None (Foundation layer)

## Overview

Team Memory is the persistent knowledge layer shared by all agents and humans. It supports structured storage, semantic search, and access control. This is the foundation of the entire system.

## Core Requirements

1. **Shared context**: All participants can see the same background information
2. **Decision records**: Decisions made during discussions are persisted
3. **Knowledge accumulation**: Project knowledge grows over time
4. **Searchable**: Quickly find relevant information
5. **Access control**: Different roles see different content

## Architecture

```
┌───────────────────────────────────────────────────────┐
│                    Memory API                          │
│   (read, write, search, subscribe)                    │
└──────────────────────┬────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Document   │ │   Vector    │ │  Metadata   │
│   Store     │ │   Store     │ │   Store     │
│ (Postgres)  │ │ (pgvector)  │ │ (Postgres)  │
└─────────────┘ └─────────────┘ └─────────────┘
       │               │               │
       └───────────────┼───────────────┘
                       ▼
              ┌─────────────────┐
              │    Supabase     │
              │ (Managed Postgres) │
              └─────────────────┘
```

## Data Model

### Memory Item

```typescript
interface MemoryItem {
  id: string;
  teamId: string;

  // Content
  type: MemoryType;
  title: string;
  content: string;

  // Metadata
  path: string;           // e.g., "/projects/pricing/decisions"
  tags: string[];
  source: MemorySource;   // where it came from

  // Permissions
  visibility: 'team' | 'role' | 'private';
  allowedRoles?: string[];

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  expiresAt?: Date;       // optional expiration time

  // Vector (for semantic search)
  embedding?: number[];
}

type MemoryType =
  | 'context'     // background information
  | 'decision'    // decision record
  | 'document'    // document
  | 'note'        // note
  | 'reference'   // external reference
  | 'thread-summary';  // conversation summary

interface MemorySource {
  type: 'human' | 'agent' | 'import' | 'auto';
  authorId?: string;
  threadId?: string;      // if sourced from a thread
  messageId?: string;     // if sourced from a message
}
```

### Directory Structure (Logical)

```
/team-memory/
├── context/              # Team background
│   ├── overview.md
│   ├── goals.md
│   └── constraints.md
├── projects/             # Project-related
│   └── {project-id}/
│       ├── brief.md
│       ├── decisions/
│       └── notes/
├── decisions/            # Global decisions
│   ├── 2026-02-06-pricing.md
│   └── ...
├── docs/                 # Documentation
│   ├── guides/
│   └── references/
└── agents/               # Agent-related
    ├── capabilities.md
    └── history/
```

## Database Schema

```sql
-- Main table
CREATE TABLE memory_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL,

  -- Content
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,

  -- Metadata
  path TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  source JSONB NOT NULL,

  -- Permissions
  visibility TEXT DEFAULT 'team',
  allowed_roles TEXT[] DEFAULT '{}',

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,

  -- Vector (pgvector)
  embedding vector(1536)
);

-- Indexes
CREATE INDEX idx_memory_team ON memory_items(team_id);
CREATE INDEX idx_memory_path ON memory_items(path);
CREATE INDEX idx_memory_type ON memory_items(type);
CREATE INDEX idx_memory_tags ON memory_items USING GIN(tags);

-- Vector search index
CREATE INDEX idx_memory_embedding ON memory_items
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Full-text search
ALTER TABLE memory_items ADD COLUMN fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || content)) STORED;
CREATE INDEX idx_memory_fts ON memory_items USING GIN(fts);
```

## API Design

### Write

```typescript
// Create memory item
POST /api/memory
{
  type: "decision",
  title: "Chose Option A pricing strategy",
  content: "After discussion, we decided to adopt Option A...",
  path: "/projects/pricing/decisions",
  tags: ["pricing", "strategy"],
  source: {
    type: "agent",
    authorId: "agent-1",
    threadId: "thread-xxx",
    messageId: "msg-yyy"
  }
}

// Update
PUT /api/memory/:id
{ ... }

// Delete (soft delete)
DELETE /api/memory/:id
```

### Read

```typescript
// Read by path
GET /api/memory?path=/projects/pricing
Response: MemoryItem[]

// Read by ID
GET /api/memory/:id

// List directory
GET /api/memory/tree?path=/projects
Response: {
  items: MemoryItem[],
  subdirs: string[]
}
```

### Search

```typescript
// Semantic search
POST /api/memory/search
{
  query: "pricing strategy discussion",
  type?: "decision",     // optional filter
  path?: "/projects",    // optional scope
  limit: 10
}

Response: {
  results: [
    {
      item: MemoryItem,
      score: 0.92,        // similarity
      highlight: "..."    // matching snippet
    }
  ]
}

// Full-text search
GET /api/memory/search?q=pricing+strategy&type=decision
```

### Subscribe to Changes

```typescript
// WebSocket / Supabase Realtime
// Subscribe to changes under a specific path

supabase
  .channel('memory:projects/pricing')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'memory_items',
    filter: `path=like./projects/pricing%`
  }, (payload) => {
    // Handle changes
  })
  .subscribe();
```

## Memory Lifecycle

### Auto-creation

Automatically extract memory from conversations:

```typescript
// Trigger conditions
const triggers = {
  decision: /decided|chose|confirmed|agreed/i,
  action: /TODO|action item|need to do/i,
  reference: /reference|see also/i,
};

// Agent writes automatically when a decision is detected
if (isDecision(message)) {
  await createMemory({
    type: 'decision',
    title: extractTitle(message),
    content: message.content,
    source: { threadId, messageId }
  });
}
```

### Thread Summary

Automatically generate summaries after conversations end:

```typescript
// When a thread is merged or archived
async function summarizeThread(threadId: string) {
  const messages = await getThreadMessages(threadId);
  const summary = await llm.summarize(messages);

  await createMemory({
    type: 'thread-summary',
    title: `Thread: ${thread.title}`,
    content: summary,
    source: { type: 'auto', threadId }
  });
}
```

### Expiration Cleanup

```typescript
// Periodically clean up expired items
// Cron job: daily at 3am
DELETE FROM memory_items
WHERE expires_at IS NOT NULL
AND expires_at < NOW();
```

## Agent Access Patterns

### Read-only Shared

```typescript
// Load relevant memory when agent initializes
async function loadAgentContext(agentId: string, threadId: string) {
  const thread = await getThread(threadId);

  // 1. Load team context
  const teamContext = await searchMemory({
    path: '/context',
    limit: 5
  });

  // 2. Load relevant project memory
  const projectMemory = await searchMemory({
    query: thread.topic,
    limit: 10
  });

  // 3. Load recent decisions
  const recentDecisions = await searchMemory({
    type: 'decision',
    limit: 5,
    orderBy: 'created_at DESC'
  });

  return { teamContext, projectMemory, recentDecisions };
}
```

### Agent Write

Agents can write to memory, but must tag the source:

```typescript
// Agent writes items that need review
await createMemory({
  type: 'note',
  content: '...',
  source: { type: 'agent', authorId: 'agent-1' },
  visibility: 'team',
  metadata: { needsReview: true }  // Humans can review
});
```

## Filesystem Interface (Optional)

In addition to the API, memory can be mounted as a filesystem for agents to read directly:

```
/agent/team/              # mount point
├── context/
│   └── overview.md       # Auto-synced from DB
├── decisions/
└── docs/
```

Implementation: FUSE filesystem or periodic sync script

## Permission Model

```typescript
interface MemoryPermission {
  // Visibility
  visibility: 'team' | 'role' | 'private';

  // Role restrictions
  allowedRoles?: ('admin' | 'member' | 'agent')[];

  // Operation permissions
  operations: {
    read: boolean;
    write: boolean;
    delete: boolean;
  };
}

// Permission check
function canAccess(user: User, item: MemoryItem): boolean {
  if (item.visibility === 'team') return true;
  if (item.visibility === 'private') {
    return item.source.authorId === user.id;
  }
  if (item.visibility === 'role') {
    return item.allowedRoles.includes(user.role);
  }
  return false;
}
```

## MVP Scope

**Phase 1 (Must have)**:
- [ ] Basic CRUD API
- [ ] Postgres schema deployment (Supabase)
- [ ] Read by path
- [ ] Basic search (full-text)

**Phase 2 (Important)**:
- [ ] Embedding generation (OpenAI)
- [ ] Semantic search
- [ ] Realtime subscriptions
- [ ] Agent auto-write

**Phase 3 (Advanced)**:
- [ ] Filesystem mount
- [ ] Access control
- [ ] Auto-expiration
- [ ] Version history

## Technology Choice Rationale

**Why Supabase**:
- Managed Postgres, zero ops
- Built-in pgvector for vector search
- Realtime subscriptions out of the box
- Quick to get started, suitable for MVP

**Why not a pure filesystem**:
- Difficult to handle concurrent write conflicts
- Poor search performance
- Hard to implement access control
- Can still serve as a fallback / export format

## Open Questions

1. **Embedding model**: OpenAI ada-002 vs local model?
2. **Memory size limit**: Maximum characters per item?
3. **Version history**: Do we need to retain edit history?
4. **Export format**: Markdown? JSON? Both?

---

*To be refined after Charles confirms*
