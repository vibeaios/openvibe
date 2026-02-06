> **SUPERSEDED**: This document is from the initial design phase. For implementation, refer to:
> - [`FRONTEND-ARCHITECTURE.md`](../research/phase-1.5/FRONTEND-ARCHITECTURE.md) — Complete frontend design
> - [`THREAD-UX-PROPOSAL.md`](../research/phase-1.5/THREAD-UX-PROPOSAL.md) — UX patterns

# M2: Frontend (Real-time UI)

> Status: Draft | Priority: High | Dependency: M1, M5

## Overview

A Discord-like real-time chat UI with git-like thread interactions. Humans and AI agents collaborate in the same interface.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: TailwindCSS + shadcn/ui
- **State**: Zustand (lightweight)
- **Realtime**: Supabase Realtime
- **Icons**: Lucide

## Page Structure

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar          │  Main Content                       │
│  ┌─────────────┐  │  ┌───────────────────────────────┐  │
│  │ Channels    │  │  │ Channel Header                │  │
│  │ - #general  │  │  ├───────────────────────────────┤  │
│  │ - #project  │  │  │                               │  │
│  │ - #random   │  │  │  Thread List / Thread View    │  │
│  │             │  │  │                               │  │
│  ├─────────────┤  │  │                               │  │
│  │ Agents      │  │  │                               │  │
│  │ Agent-1     │  │  │                               │  │
│  │ Agent-2     │  │  ├───────────────────────────────┤  │
│  │             │  │  │ Message Input                 │  │
│  └─────────────┘  │  └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. ThreadView (Core)

```tsx
interface ThreadViewProps {
  threadId: string;
  currentBranch: string;
}

// Features:
// - Display message flow for the current branch
// - Branch switching tabs
// - Branch point markers (create new branches from here)
// - Merge entry point
```

**Branch UI**:
```
┌─────────────────────────────────────────────────┐
│ [main ▼] [explore-pricing] [+ New Branch]       │  ← Branch tabs
├─────────────────────────────────────────────────┤
│                                                 │
│  Charles: Let's discuss pricing strategy        │
│                                                 │
│  Agent-1: There are several directions to       │
│  consider...                                    │
│       ↳ [Branch from here]                      │  ← Shown on hover
│                                                 │
│  Charles: Option A sounds good                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2. BranchGraph (Differentiator)

```tsx
// Git graph style branch visualization
interface BranchGraphProps {
  threadId: string;
  branches: Branch[];
  onSelectBranch: (branchId: string) => void;
}

// ASCII example:
// ●──●──●──●──●  main
//       │
//       └──●──●  explore-pricing
//          │
//          └──●  sub-experiment
```

**Implementation reference**:
- react-git-graph
- Or draw with SVG

### 3. MessageBubble

```tsx
interface MessageBubbleProps {
  message: Message;
  isBranchPoint: boolean;
  onBranch: () => void;
  onReply: () => void;
}

// Distinguish human vs agent styles
// Agent messages show thinking process (collapsible)
// Supports markdown rendering
// Code highlighting (shiki)
```

### 4. MessageInput

```tsx
interface MessageInputProps {
  threadId: string;
  branchId: string;
  onSend: (content: Content) => void;
}

// Features:
// - Text input
// - @ mention agents
// - File upload
// - Code block shortcuts
```

### 5. AgentCard (Sidebar)

```tsx
interface AgentCardProps {
  agent: Agent;
  status: 'online' | 'busy' | 'offline';
  currentTask?: string;
}

// Displays:
// - Agent avatar/name
// - Current status
// - Task being processed
// - Click to DM or view details
```

## Key Interactions

### Branch Creation Flow

```
1. Hover over a message → "Branch from here" button appears
2. Click → Modal appears:
   ┌─────────────────────────────────┐
   │ Create Branch                   │
   ├─────────────────────────────────┤
   │ Branch name: [explore-option-b] │
   │                                 │
   │ Starting from:                  │
   │ "There are several directions   │
   │  to consider..."                │
   │                                 │
   │ [Cancel]           [Create]     │
   └─────────────────────────────────┘
3. Automatically switches to the new branch after creation
```

### Merge Flow

```
1. Click the "Merge" button on the branch tab
2. Merge preview appears:
   ┌─────────────────────────────────────┐
   │ Merge "explore-pricing" → main      │
   ├─────────────────────────────────────┤
   │ This branch has 5 messages          │
   │                                     │
   │ Merge strategy:                     │
   │ ○ Append all messages               │
   │ ● AI Summary (recommended)          │
   │ ○ Manual select                     │
   │                                     │
   │ [Cancel]               [Merge]      │
   └─────────────────────────────────────┘
3. Merge commit displayed after completion
```

### @ Mention Agent

```
Typing "@" triggers autocomplete:
┌───────────────────┐
│ @agent-1 (Coder)  │
│ @agent-2 (Writer) │
│ @all-agents       │
└───────────────────┘

After selection: "@agent-1 analyze this proposal for me"
→ System automatically routes to the corresponding agent
```

## State Management

```typescript
// Zustand store
interface ThreadStore {
  // Current thread state
  currentThreadId: string | null;
  currentBranchId: string;
  messages: Message[];
  branches: Branch[];

  // Actions
  setThread: (threadId: string) => void;
  switchBranch: (branchId: string) => void;
  addMessage: (message: Message) => void;
  createBranch: (name: string, baseMessageId: string) => void;
  mergeBranch: (sourceBranch: string, strategy: MergeStrategy) => void;
}

interface AgentStore {
  agents: Agent[];
  agentStatus: Record<string, AgentStatus>;

  updateStatus: (agentId: string, status: AgentStatus) => void;
}
```

## Responsive Design

| Breakpoint | Layout |
|------------|--------|
| Desktop (>1024px) | Sidebar + Main (as shown above) |
| Tablet (768-1024px) | Collapsible sidebar |
| Mobile (<768px) | Bottom nav + Full screen views |

## Accessibility

- Keyboard navigation (Tab, Enter, Escape)
- ARIA labels
- Color contrast (WCAG AA)
- Screen reader friendly

## Performance Optimization

- Message virtual scrolling (react-virtual)
- Image lazy loading
- Branch data loaded on demand
- Optimistic updates (display first, confirm later)

## MVP Scope

**Phase 1 (Must have)**:
- [ ] Basic layout (Sidebar + Main)
- [ ] Channel list
- [ ] Thread message flow
- [ ] Message input and send
- [ ] Real-time updates

**Phase 2 (Important)**:
- [ ] Branch tabs + switching
- [ ] Create branches
- [ ] Agent status display
- [ ] @ mention

**Phase 3 (Differentiator)**:
- [ ] Branch graph visualization
- [ ] Merge UI
- [ ] Diff view
- [ ] Mobile adaptation

## Design References

- Discord (basic layout)
- Linear (clean aesthetics)
- GitHub (branch visualization)
- Slack (threads)

## Open Questions

1. **Dark/Light mode**: Only dark for MVP?
2. **Message pagination**: Scroll-to-load vs click-to-load-more?
3. **Agent avatars**: Auto-generated vs user-uploaded?
4. **Notifications**: Browser notifications in MVP?

---

*To be refined after Charles confirms*
