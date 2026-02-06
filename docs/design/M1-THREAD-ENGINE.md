> **SUPERSEDED**: This document is from the initial design phase. For implementation, refer to Phase 1.5 docs:
> - [`THREAD-UX-PROPOSAL.md`](../research/phase-1.5/THREAD-UX-PROPOSAL.md) — Fork/Resolve UX
> - [`BACKEND-MINIMUM-SCOPE.md`](../research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) — Data model

# M1: Thread Engine (Git-like Conversation Core)

> Status: Draft | Priority: High | Dependency: M4

## Overview

Thread Engine is the product's core differentiator — applying Git's version control concepts to conversations. It supports branching, merging, and version history.

## Core Concepts

### Data Model

```typescript
// Similar to a git commit
interface Message {
  id: string;              // unique id (like commit hash)
  threadId: string;        // owning thread
  parentId: string | null; // previous message (null = thread root)
  author: Author;          // human or agent
  content: Content;        // message content
  timestamp: number;
  metadata: {
    branchPoint?: boolean; // whether this is a branch point
    mergedFrom?: string[]; // merge sources
  };
}

interface Thread {
  id: string;
  channelId: string;
  rootMessageId: string;
  branches: Branch[];
  status: 'active' | 'merged' | 'archived';
}

interface Branch {
  id: string;
  name: string;           // e.g., "explore-option-a"
  headMessageId: string;  // current latest message
  baseMessageId: string;  // the message this branch was created from
  createdBy: Author;
  createdAt: number;
}

interface Author {
  type: 'human' | 'agent';
  id: string;
  name: string;
  avatar?: string;
}
```

### Git-like Operations

| Operation | Git Analogy | User Action |
|-----------|-------------|-------------|
| **Reply** | commit | Normal reply |
| **Branch** | git branch | Create a branch from a message to explore |
| **Switch** | git checkout | Switch to a different branch to view |
| **Merge** | git merge | Merge a branch discussion back to the main line |
| **Diff** | git diff | Compare discussions between two branches |
| **History** | git log | View complete conversation history |

## API Design

### Thread Operations

```typescript
// Create thread
POST /api/threads
{
  channelId: string;
  initialMessage: Content;
  author: Author;
}

// Get thread (including all branches)
GET /api/threads/:threadId
Response: {
  thread: Thread;
  messages: Message[];  // messages on the current branch
  branches: Branch[];
}

// Create branch
POST /api/threads/:threadId/branches
{
  name: string;
  baseMessageId: string;  // where to branch from
  author: Author;
}

// Switch branch
GET /api/threads/:threadId?branch=:branchId

// Merge branch
POST /api/threads/:threadId/merge
{
  sourceBranch: string;
  targetBranch: string;  // usually main
  mergeMessage?: string; // optional merge description
}
```

### Message Operations

```typescript
// Send message
POST /api/threads/:threadId/messages
{
  parentId: string;
  content: Content;
  author: Author;
  branchId?: string;  // defaults to main
}

// Get message history (for a branch)
GET /api/threads/:threadId/messages?branch=:branchId&limit=50

// Get branch comparison
GET /api/threads/:threadId/diff?from=:branchA&to=:branchB
```

## Content Types

```typescript
interface Content {
  type: 'text' | 'code' | 'file' | 'decision' | 'summary';
  body: string;

  // type-specific fields
  language?: string;      // for code
  fileName?: string;      // for file
  options?: string[];     // for decision
  resolved?: boolean;     // for decision
}
```

## Storage Design

### Option A: Postgres (Recommended for MVP)

```sql
CREATE TABLE threads (
  id UUID PRIMARY KEY,
  channel_id UUID NOT NULL,
  root_message_id UUID,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE branches (
  id UUID PRIMARY KEY,
  thread_id UUID REFERENCES threads(id),
  name TEXT NOT NULL,
  head_message_id UUID,
  base_message_id UUID,
  created_by JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE messages (
  id UUID PRIMARY KEY,
  thread_id UUID REFERENCES threads(id),
  branch_id UUID REFERENCES branches(id),
  parent_id UUID REFERENCES messages(id),
  author JSONB NOT NULL,
  content JSONB NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_messages_branch ON messages(branch_id);
CREATE INDEX idx_messages_parent ON messages(parent_id);
```

### Option B: Git-backed (Advanced)

Store conversations directly in git, where each message is a commit:
- Native branch/merge support
- Can be analyzed with git tools
- High complexity, not recommended for MVP

## Real-time Sync

Subscribe to message changes using Supabase Realtime:

```typescript
// Subscribe to thread updates
supabase
  .channel(`thread:${threadId}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'messages',
    filter: `thread_id=eq.${threadId}`
  }, (payload) => {
    // New message received
    addMessage(payload.new);
  })
  .subscribe();
```

## Edge Cases

### Merge Conflicts

Unlike code, conversations don't have true "conflicts". Merge strategies:
1. **Append**: Simply append discussions from both branches, marking their sources
2. **Summary**: AI generates a summary of both branch discussions as the merge commit
3. **Manual**: User selects which discussions to keep

### Too Many Branches

Limit each thread to a maximum of 10 active branches, encouraging timely merging or archiving.

## MVP Scope

**Phase 1 (Must have)**:
- [x] Basic thread CRUD
- [x] Single-branch message flow
- [ ] Create branches
- [ ] Switch branches to view

**Phase 2 (Important)**:
- [ ] Merge branches
- [ ] Branch comparison (diff view)
- [ ] Branch visualization (git graph style)

**Phase 3 (Nice to have)**:
- [ ] AI auto-summarize branches
- [ ] Branch templates (e.g., "Explore options", "Counterarguments")
- [ ] Branch voting/decisions

## Open Questions

1. **Branch naming**: Auto-generated vs user-specified?
2. **Message editing**: Allow it? How to handle history?
3. **Deletion**: Soft delete or hard delete?
4. **Branch visibility**: Private branches (visible only to the creator)?

---

*To be refined after Charles confirms*
