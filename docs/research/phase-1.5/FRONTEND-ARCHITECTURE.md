# Phase 1.5: Frontend Engineering Architecture

> Status: Complete | Researcher: frontend-architect | Date: 2026-02-07

---

## Research Question

What is the concrete frontend engineering architecture for the OpenVibe MVP -- a thread-based human+AI collaboration platform with Discord-like layout, fork/resolve thread model, real-time message updates, and agent response rendering -- built with Next.js 14 App Router, TailwindCSS, shadcn/ui, Zustand, tRPC, and Supabase Realtime within an Nx monorepo?

---

## Sources Consulted

### Internal Design Documents
- `docs/research/R1-THREAD-MODEL.md` -- Fork/resolve model, three-tier adoption, prototype scenarios
- `docs/research/R2-GENERATIVE-UI.md` -- Config-driven UI + agent component catalog (7 MVP components)
- `docs/research/SYNTHESIS.md` -- Phase 1 integration, revised module priorities, tech stack confirmation
- `docs/research/phase-1.5/THREAD-UX-PROPOSAL.md` -- Focus Mode + Fork Sidebar + Progressive Disclosure, wireframes, notification model, 4 concrete interaction scenarios
- `docs/research/phase-1.5/RUNTIME-ARCHITECTURE.md` -- Per-user runtime, MVP simplification (per-request context hydration), SSE streaming, cost model
- `docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md` -- Complete data model (10 tables), ~30 tRPC procedures, Supabase Realtime event catalog, Vercel deployment
- `docs/research/phase-1.5/ADMIN-CONFIGURABLE-UI.md` -- Config schema, `useConfig()` hook, CSS custom properties for branding, 7 MVP agent components
- `docs/design/M2-FRONTEND.md` -- Original frontend layout, component sketches (to be superseded by this document)

### External Research
- [Zustand Slices Pattern](https://zustand.docs.pmnd.rs/guides/slices-pattern) -- Official slice composition for multiple stores
- [Zustand Architecture Patterns at Scale](https://brainhub.eu/library/zustand-architecture-patterns-at-scale) -- Custom hooks, selectors, devtools middleware patterns
- [Zustand with Next.js](https://zustand.docs.pmnd.rs/guides/nextjs) -- SSR-safe store creation, request-scoped stores
- [TanStack Virtual](https://tanstack.com/virtual/latest) -- Headless virtualizer for dynamic-height message lists
- [Reverse Infinite Scroll with TanStack Virtual](https://medium.com/@rmoghariya7/reverse-infinite-scroll-in-react-using-tanstack-virtual-11a1fea24042) -- Chat-style bottom-anchored scrolling pattern
- [Stream Chat VirtualizedMessageList](https://getstream.io/chat/docs/sdk/react/components/core-components/virtualized_list/) -- Production chat virtualization reference
- [Supabase Realtime Getting Started](https://supabase.com/docs/guides/realtime/getting_started) -- postgres_changes, broadcast, presence channels
- [Supabase Realtime Subscription Reliability](https://www.answeroverflow.com/m/1398819457035538635) -- Reconnection patterns and heartbeat monitoring
- [tRPC with Next.js App Router](https://brockherion.dev/blog/posts/how-to-use-trpc-with-nextjs-app-router/) -- Server-side caller pattern, React Query integration
- [Discord Clone Architecture (React)](https://github.com/Guilospanck/discord-clone) -- Clean architecture patterns for chat UIs
- [shadcn/ui Component Library](https://ui.shadcn.com) -- Copy-paste component patterns for TailwindCSS

---

## 1. App Structure

### 1.1 Next.js App Router Layout Hierarchy

The App Router uses nested layouts to establish the application shell. Each layout wraps its children and persists across route transitions within its segment, avoiding unnecessary re-renders.

```
app/
  layout.tsx                    # Root: HTML, body, fonts, global providers
  (auth)/
    layout.tsx                  # Auth shell: centered card layout
    login/page.tsx              # /login
    signup/page.tsx             # /signup
    callback/page.tsx           # /callback (OAuth redirect)
  (workspace)/
    layout.tsx                  # Workspace shell: sidebar + main area
    [workspaceId]/
      layout.tsx                # Workspace-specific: loads config, Realtime base
      channels/page.tsx         # /w/[id]/channels (channel list / default)
      channel/
        [channelId]/
          layout.tsx            # Channel-specific: subscribe to channel events
          page.tsx              # /w/[id]/channel/[cId] (thread list)
          thread/
            [threadId]/
              page.tsx          # /w/[id]/channel/[cId]/thread/[tId] (thread view)
      search/page.tsx           # /w/[id]/search
      settings/page.tsx         # /w/[id]/settings (admin only)
```

### 1.2 Route Structure

| Route | Purpose | Layout |
|-------|---------|--------|
| `/login`, `/signup` | Authentication | Auth shell (centered) |
| `/callback` | OAuth redirect handler | Auth shell |
| `/w/[workspaceId]` | Workspace root (redirects to default channel) | Workspace shell |
| `/w/[workspaceId]/channels` | Channel list / home | Workspace shell |
| `/w/[workspaceId]/channel/[channelId]` | Thread list for a channel | Workspace + Channel |
| `/w/[workspaceId]/channel/[channelId]/thread/[threadId]` | Thread view with messages + forks | Workspace + Channel + Thread |
| `/w/[workspaceId]/search` | Global search | Workspace shell |
| `/w/[workspaceId]/settings` | Admin workspace settings | Workspace shell |

**URL design rationale:** Short workspace prefix (`/w/`) keeps URLs manageable. Thread IDs in URLs enable deep-linking and browser history. Fork views are NOT separate routes -- they are state within the thread view (controlled by Zustand), because fork switching should be instant without route transitions.

### 1.3 Layout Components

The Discord-like layout has 4 zones:

```
+--+----------+----------------------------+----------------+
|  | Sidebar  |  Main Content Area          | Detail Panel   |
|  |          |                             | (conditional)  |
|S | Channel  |  Channel Header             |                |
|e | List     |  +-----------------------+  | Fork Info      |
|r |          |  | Thread/Fork Content   |  | OR             |
|v | Agent    |  |                       |  | Thread         |
|e | List     |  |                       |  | Details        |
|r |          |  +-----------------------+  |                |
|  |          |  | Compose Box           |  |                |
|L |          |  +-----------------------+  |                |
|i |          |                             |                |
|s |          |                             |                |
|t |          |                             |                |
+--+----------+----------------------------+----------------+
48px  240px        flex (min 480px)           320px (opt)
```

**Zone 1: Server List (48px)** -- Not used in MVP. In future: workspace switcher icons. For dogfood, workspace is implicit from the URL.

**Zone 2: Sidebar (240px)** -- Channel list, agent roster, fork sidebar (when viewing a thread). Sections are config-driven (`ui.sidebar.sections`). Collapsible on tablet.

**Zone 3: Main Content (flex)** -- Channel header, thread list or thread view, compose box. This is where focus mode operates: it shows EITHER the main thread OR a single fork, never both.

**Zone 4: Detail Panel (320px, conditional)** -- Shows fork info panel when viewing a fork, or thread metadata when useful. Hidden by default. Toggled by user action.

### 1.4 How the Discord-Like Layout Works

```
Workspace Shell (layout.tsx)
  +-- ServerList (Zone 1, future)
  +-- Sidebar (Zone 2)
  |     +-- WorkspaceName
  |     +-- SidebarSections (config-driven)
  |           +-- ChannelList
  |           +-- AgentRoster
  |           +-- ForkSidebar (when thread is active)
  +-- MainContent (Zone 3)
  |     +-- ChannelHeader
  |     +-- children (page content)
  |           +-- ThreadList (channel page)
  |           OR
  |           +-- ThreadView / ForkView (thread page)
  |     +-- ComposeBox
  +-- DetailPanel (Zone 4, conditional)
```

**Navigation flow:** Click channel in sidebar -> loads thread list in main area. Click thread -> loads thread view. Click fork in fork sidebar -> main area switches to fork view (focus mode). Click "Back to thread" -> returns to main thread.

---

## 2. Component Architecture

### 2.1 Component Hierarchy

Three levels of components:

```
Level 1: Shell Components (app-level, layout-bound)
  WorkspaceShell, Sidebar, MainContent, DetailPanel, ChannelHeader

Level 2: Feature Components (domain-specific, route-bound)
  ChannelList, ThreadList, ThreadView, ForkView, ForkSidebar,
  ComposeBox, SearchView, SettingsView

Level 3: Shared Components (reusable across features)
  MessageBubble, AgentResponseRenderer, AgentComponentCatalog,
  UserAvatar, TypingIndicator, LoadingState, EmptyState,
  ResolutionCard, ForkStatusBadge
```

### 2.2 Key Components

#### ChannelView (`ThreadList` when at channel level)

```typescript
interface ThreadListProps {
  channelId: string;
}

// Displays list of threads in a channel.
// Each thread shows: root message preview, author, timestamp,
// reply count, active fork count, last activity.
// Click navigates to /thread/[threadId].
// Subscribes to channel-level Realtime for new threads.
```

#### ThreadView

```typescript
interface ThreadViewProps {
  threadId: string;
}

// The core component. Displays messages in the main thread.
// Focus Mode: shows main thread OR a specific fork (never both).
// When a fork is selected in ForkSidebar, ThreadView swaps its
// content to ForkView. This is Zustand state, not a route change.
//
// Contains:
//   - ThreadHeader (title, status, breadcrumb for forks)
//   - MessageList (virtualized, with fork-point markers)
//   - ComposeBox (contextual: knows thread/fork)
// Subscribes to thread-level Realtime for messages, forks, tasks.
```

#### ForkView

```typescript
interface ForkViewProps {
  forkId: string;
  threadId: string;
}

// Same layout as ThreadView but:
//   - Shows breadcrumb: "Main Thread > Fork: [name]"
//   - Shows the forked-from message as context header
//   - Has "Back to thread" button
//   - Has "Resolve" button (triggers resolution flow)
//   - Messages are fork-scoped (fork_id filter)
```

#### ForkSidebar

```typescript
interface ForkSidebarProps {
  threadId: string;
}

// Appears in Zone 2 (sidebar) when viewing a thread.
// Two sections: "Active" forks and "Resolved" forks.
// Each entry shows:
//   - Fork description (auto-generated or manual)
//   - Participants (avatars)
//   - Message count
//   - Time since last activity
//   - Status badge (Active / Resolved / Abandoned)
// Click switches main content to ForkView (focus mode).
// Max 7 active forks displayed (from THREAD-UX-PROPOSAL).
```

#### MessageBubble

```typescript
interface MessageBubbleProps {
  message: Message;
  isForkPoint: boolean;      // Show fork indicator
  showActions: boolean;       // Hover actions visible
  isStreaming?: boolean;      // Agent response streaming
}

// Renders a single message. Differentiates:
//   - Human messages: standard styling, user avatar
//   - Agent messages: distinct background color, robot avatar,
//     progressive disclosure (headline/summary/full), component catalog rendering
//   - System messages: resolution summaries, fork creation notices
//
// Hover actions: Reply, React, Fork, Copy
// Fork-point messages show a branch indicator icon
```

#### AgentResponseRenderer

```typescript
interface AgentResponseRendererProps {
  content: string;           // Markdown text (always present)
  components?: AgentComponent[];  // Structured components from agent
  isStreaming?: boolean;
}

interface AgentComponent {
  type: 'text' | 'table' | 'action_buttons' | 'summary_card' |
        'confirmation' | 'progress' | 'form';
  props: Record<string, unknown>;
}

// Renders agent responses using the component catalog.
// Pipeline:
//   1. Check if response has structured components
//   2. For each component, verify it's in workspace's allowed list
//   3. If allowed, render the catalog component
//   4. If not allowed or unknown type, fall back to text rendering
//   5. Always render the text content as base layer
// Handles progressive disclosure: summary visible, full collapsed.
```

#### ComposeBox

```typescript
interface ComposeBoxProps {
  threadId: string;
  forkId?: string;           // null = main thread
}

// Message composition area.
// Features:
//   - Text input with markdown preview toggle
//   - @mention autocomplete (agents + users)
//   - File attachment button (Phase 2)
//   - Send button + Cmd/Ctrl+Enter shortcut
// @mention detection: on "@" keystroke, show dropdown of agents
// (from agentStore) and workspace members.
```

#### ResolutionCard

```typescript
interface ResolutionCardProps {
  fork: Fork;
  resolution: string;
  onViewFork: () => void;
}

// Rendered in the main thread when a fork is resolved.
// Shows:
//   - "Fork resolved: [name]" header
//   - Who resolved it + agent involved
//   - Resolution summary text (headline + points)
//   - "View full research (N messages)" link
// Click on link switches to ForkView in read-only mode.
```

### 2.3 Component Communication Patterns

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Props** | Parent-child, direct data flow | `MessageList` -> `MessageBubble` (message data) |
| **Zustand** | Cross-component state that persists across renders | Current thread/fork selection, UI state (panel visibility) |
| **React Context** | Scoped provider data needed by many descendants | `ConfigProvider` (workspace config), `RealtimeProvider` (subscription manager) |
| **tRPC + React Query** | Server state (data from API) | Thread data, message lists, agent configs |
| **Supabase Realtime** | Push-based server updates | New messages, fork status changes, task updates |
| **URL params** | Shareable navigation state | `workspaceId`, `channelId`, `threadId` |

**Rule of thumb:**
- If it comes from the server and is cacheable: tRPC query (React Query manages cache)
- If it is pushed from the server in real-time: Supabase Realtime -> update Zustand store
- If it is UI-only client state: Zustand
- If it is shared across many components in a subtree: React Context
- If it determines what page you see: URL

### 2.4 Config-Driven Component Rendering

The workspace config (from ADMIN-CONFIGURABLE-UI.md) affects rendering through two mechanisms:

**1. `useConfig()` hook** -- Components read config to determine visibility, labels, and layout:

```typescript
function Sidebar() {
  const config = useConfig();
  const t = useTerminology();

  const sections = config.ui.sidebar.sections
    .filter(s => s.visible)
    .sort((a, b) => a.order - b.order);

  return (
    <aside>
      {sections.map(section => (
        <SidebarSection key={section.id} label={section.label || t(section.id)}>
          {renderSection(section.id)}
        </SidebarSection>
      ))}
    </aside>
  );
}
```

**2. CSS custom properties** -- Branding config sets CSS variables on `<html>`:

```typescript
// In WorkspaceShell layout
function applyBranding(config: WorkspaceConfig) {
  const root = document.documentElement;
  root.style.setProperty('--primary', config.ui.branding.primaryColor);
  root.style.setProperty('--accent', config.ui.branding.accentColor || config.ui.branding.primaryColor);
}
```

For dogfood, the config is a static YAML loaded at startup. The component patterns are identical regardless of whether config comes from a file or a database.

---

## 3. State Management

### 3.1 Zustand Store Structure

Seven stores, organized by domain. Each store is a separate Zustand `create()` call (not one monolithic store), following the multiple-stores pattern recommended for independent domains.

```typescript
// stores/authStore.ts
interface AuthStore {
  user: User | null;
  workspace: Workspace | null;
  isLoading: boolean;

  setUser: (user: User) => void;
  setWorkspace: (workspace: Workspace) => void;
  logout: () => void;
}

// stores/channelStore.ts
interface ChannelStore {
  channels: Channel[];
  activeChannelId: string | null;

  setChannels: (channels: Channel[]) => void;
  setActiveChannel: (channelId: string) => void;
  addChannel: (channel: Channel) => void;
}

// stores/threadStore.ts
interface ThreadStore {
  // Thread list for current channel
  threads: Record<string, Thread[]>;   // channelId -> threads
  activeThreadId: string | null;

  setThreads: (channelId: string, threads: Thread[]) => void;
  setActiveThread: (threadId: string) => void;
  addThread: (channelId: string, thread: Thread) => void;
  updateThread: (threadId: string, updates: Partial<Thread>) => void;
}

// stores/messageStore.ts
interface MessageStore {
  // Messages keyed by context (thread main or fork)
  messages: Record<string, Message[]>; // "thread:{id}" or "fork:{id}" -> messages
  pendingMessages: Message[];          // Optimistic sends awaiting confirmation

  setMessages: (contextKey: string, messages: Message[]) => void;
  addMessage: (contextKey: string, message: Message) => void;
  updateMessage: (contextKey: string, messageId: string, updates: Partial<Message>) => void;
  addPendingMessage: (message: Message) => void;
  confirmPendingMessage: (tempId: string, realMessage: Message) => void;
  removePendingMessage: (tempId: string) => void;
}

// stores/forkStore.ts
interface ForkStore {
  forks: Record<string, Fork[]>;       // threadId -> forks
  activeForkId: string | null;         // Current fork in focus mode

  setForks: (threadId: string, forks: Fork[]) => void;
  setActiveFork: (forkId: string | null) => void;  // null = main thread
  addFork: (threadId: string, fork: Fork) => void;
  updateFork: (forkId: string, updates: Partial<Fork>) => void;
}

// stores/agentStore.ts
interface AgentStore {
  agents: AgentConfig[];                // Workspace agents
  activeTasks: Record<string, Task>;    // taskId -> task (running tasks)

  setAgents: (agents: AgentConfig[]) => void;
  setTask: (task: Task) => void;
  removeTask: (taskId: string) => void;
}

// stores/uiStore.ts
interface UIStore {
  sidebarCollapsed: boolean;
  detailPanelOpen: boolean;
  detailPanelContent: 'fork-info' | 'thread-details' | null;
  searchOpen: boolean;
  composeExpanded: boolean;
  resolutionModalOpen: boolean;
  resolutionModalForkId: string | null;

  toggleSidebar: () => void;
  toggleDetailPanel: (content?: 'fork-info' | 'thread-details') => void;
  openSearch: () => void;
  closeSearch: () => void;
  openResolutionModal: (forkId: string) => void;
  closeResolutionModal: () => void;
}
```

### 3.2 Store Interaction

Stores do NOT directly import each other. Cross-store coordination happens in two ways:

**1. Component-level composition:**
```typescript
function ThreadPage({ threadId }: { threadId: string }) {
  const setActiveThread = useThreadStore(s => s.setActiveThread);
  const setActiveFork = useForkStore(s => s.setActiveFork);

  useEffect(() => {
    setActiveThread(threadId);
    setActiveFork(null); // Reset fork focus when entering thread
  }, [threadId]);

  // ...
}
```

**2. Realtime event handlers:**
```typescript
// In useThreadSubscription hook
function handleNewMessage(message: Message) {
  const messageStore = useMessageStore.getState();
  const agentStore = useAgentStore.getState();

  messageStore.addMessage(contextKey, message);

  // If this is an agent response, update the associated task
  if (message.metadata?.taskId) {
    agentStore.removeTask(message.metadata.taskId);
  }
}
```

### 3.3 Server State vs Client State

| Data | Owner | Why |
|------|-------|-----|
| Messages, threads, forks, channels | **Server (tRPC + Supabase)** | Source of truth is the database. React Query caches locally. Realtime pushes updates. |
| Agent configs | **Server (tRPC)** | Configured by admin, rarely changes. Fetched once, cached. |
| Active thread/fork/channel selection | **Client (Zustand + URL)** | Navigation state. URL for shareable state, Zustand for transient focus state. |
| UI state (panel open/closed, search open) | **Client (Zustand)** | Purely UI. Not persisted. Lost on page reload (intentional). |
| Workspace config | **Server (tRPC) -> Client (Zustand)** | Fetched once on workspace load. Cached in `configStore`. Updated via Realtime when admin changes config. |
| Typing indicators | **Ephemeral (Supabase Broadcast)** | Not persisted anywhere. Fire-and-forget events. |
| Pending messages (optimistic) | **Client (Zustand)** | Exist only until server confirms. Shown with "sending" indicator. |

### 3.4 Optimistic Updates for Messages

When a user sends a message, it appears immediately without waiting for the server:

```typescript
async function sendMessage(content: string, threadId: string, forkId?: string) {
  const messageStore = useMessageStore.getState();
  const authStore = useAuthStore.getState();
  const contextKey = forkId ? `fork:${forkId}` : `thread:${threadId}`;

  // 1. Create optimistic message
  const tempId = `temp-${Date.now()}-${Math.random()}`;
  const optimisticMessage: Message = {
    id: tempId,
    thread_id: threadId,
    fork_id: forkId || null,
    author_id: authStore.user!.id,
    author_type: 'human',
    content,
    created_at: new Date().toISOString(),
    metadata: { _optimistic: true },
  };

  // 2. Add to store immediately (user sees it)
  messageStore.addPendingMessage(optimisticMessage);
  messageStore.addMessage(contextKey, optimisticMessage);

  try {
    // 3. Send to server via tRPC
    const realMessage = await trpc.message.send.mutate({
      threadId,
      forkId,
      content,
    });

    // 4. Replace optimistic with real message
    messageStore.confirmPendingMessage(tempId, realMessage);
  } catch (error) {
    // 5. On failure, mark as failed (show retry button)
    messageStore.updateMessage(contextKey, tempId, {
      metadata: { _optimistic: true, _failed: true },
    });
  }
}
```

**Deduplication:** When Supabase Realtime broadcasts the new message (because it was inserted into Postgres), the handler checks if the message already exists (by real ID after confirmation) to avoid duplicates.

---

## 4. Real-time Subscriptions

### 4.1 Supabase Realtime Subscription Architecture

Three types of Supabase Realtime channels are used:

| Type | Purpose | Trigger |
|------|---------|---------|
| **Postgres Changes** | New/updated messages, forks, tasks, threads | Database INSERT/UPDATE/DELETE |
| **Broadcast** | Typing indicators | Client-to-client ephemeral events |
| **Presence** | User online status (Phase 2) | Client connection state |

### 4.2 Subscription Lifecycle

Subscriptions are managed by custom hooks that tie into component lifecycle:

```typescript
// hooks/useThreadSubscription.ts
function useThreadSubscription(threadId: string | null) {
  const channelRef = useRef<RealtimeChannel | null>(null);
  const messageStore = useMessageStore();
  const forkStore = useForkStore();
  const agentStore = useAgentStore();

  useEffect(() => {
    if (!threadId) return;

    // Subscribe to thread-scoped events
    const channel = supabase
      .channel(`thread:${threadId}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'messages',
        filter: `thread_id=eq.${threadId}`,
      }, (payload) => {
        const message = payload.new as Message;
        const contextKey = message.fork_id
          ? `fork:${message.fork_id}`
          : `thread:${threadId}`;
        messageStore.addMessage(contextKey, message);
      })
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'forks',
        filter: `thread_id=eq.${threadId}`,
      }, (payload) => {
        if (payload.eventType === 'INSERT') {
          forkStore.addFork(threadId, payload.new as Fork);
        } else if (payload.eventType === 'UPDATE') {
          forkStore.updateFork(payload.new.id, payload.new as Fork);
        }
      })
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'tasks',
        filter: `thread_id=eq.${threadId}`,
      }, (payload) => {
        const task = payload.new as Task;
        if (task.status === 'running') {
          agentStore.setTask(task);
        } else if (task.status === 'completed' || task.status === 'failed') {
          agentStore.removeTask(task.id);
        }
      })
      .subscribe();

    channelRef.current = channel;

    return () => {
      supabase.removeChannel(channel);
    };
  }, [threadId]);
}
```

### 4.3 When to Subscribe / Unsubscribe

| Event | Action |
|-------|--------|
| User opens a channel | Subscribe to `channel:{channelId}` for thread list updates |
| User leaves a channel | Unsubscribe from `channel:{channelId}` |
| User opens a thread | Subscribe to `thread:{threadId}` for messages, forks, tasks |
| User leaves a thread | Unsubscribe from `thread:{threadId}` |
| User opens a fork | No new subscription needed -- fork messages come through the thread subscription (same `thread_id`) |
| User closes a fork | No unsubscribe needed -- stay on the thread subscription |
| User types in compose box | Send typing broadcast to `typing:{threadId}` |
| User stops typing (2s debounce) | Send stop-typing broadcast |

**Key insight:** Subscriptions are per-thread, not per-fork. All fork messages for a thread come through the same subscription (they all have the same `thread_id`). The frontend filters by `fork_id` to display the right messages in the right view.

### 4.4 Handling Specific Events

#### New Messages
```
Supabase postgres_changes (INSERT on messages)
  -> Check if message.fork_id matches current fork view
     -> If yes, append to visible message list
     -> If no (message in a different fork), update fork sidebar
        (increment message count, update "last activity")
  -> Check for deduplication against optimistic messages
  -> Auto-scroll to bottom if user was already at bottom
```

#### Message Edits
```
Supabase postgres_changes (UPDATE on messages)
  -> Find message in store by ID
  -> Update content, updated_at
  -> Show "edited" indicator on MessageBubble
```

#### Fork Creation
```
Supabase postgres_changes (INSERT on forks)
  -> Add fork to ForkSidebar
  -> Show subtle notification "New fork: [description]"
  -> Do NOT switch focus (user stays in current context)
```

#### Fork Resolution
```
Supabase postgres_changes (UPDATE on forks, status='resolved')
  -> Update fork status in sidebar (move to "Resolved" section)
  -> The resolution summary message arrives as a separate INSERT on messages
     with metadata.isResolution=true -- render as ResolutionCard in main thread
  -> If user was viewing this fork, show "Fork resolved" banner with
     "Return to thread" button
```

#### Agent Typing Indicators
```
Supabase postgres_changes (UPDATE on tasks, status='running')
  -> Show "[Agent Name] is thinking..." indicator in the relevant
     thread/fork message area
  -> Indicator persists until the agent's response message arrives
     (INSERT on messages with author_type='agent')
  -> No separate typing broadcast needed -- task status is sufficient
```

### 4.5 Reconnection Strategy

Supabase Realtime handles reconnection automatically with exponential backoff (1s, 2s, 5s, 10s). The frontend adds a reliability layer:

```typescript
// hooks/useRealtimeHealth.ts
function useRealtimeHealth() {
  const [status, setStatus] = useState<'connected' | 'reconnecting' | 'disconnected'>('connected');

  useEffect(() => {
    // Monitor Supabase Realtime connection state
    const subscription = supabase.realtime.onOpen(() => setStatus('connected'));
    const closeSubscription = supabase.realtime.onClose(() => setStatus('reconnecting'));

    // If disconnected for > 30 seconds, show banner
    let timeout: NodeJS.Timeout;
    if (status === 'reconnecting') {
      timeout = setTimeout(() => setStatus('disconnected'), 30_000);
    }

    return () => clearTimeout(timeout);
  }, [status]);

  // On reconnect: refetch active thread data via tRPC to catch
  // any messages missed during disconnection
  useEffect(() => {
    if (status === 'connected') {
      const threadId = useThreadStore.getState().activeThreadId;
      if (threadId) {
        // Refetch thread data to fill any gaps
        trpc.thread.get.fetch({ threadId });
      }
    }
  }, [status]);

  return status;
}
```

**UI treatment:**
- Connected: no indicator
- Reconnecting (< 30s): subtle yellow dot in header
- Disconnected (> 30s): banner: "Connection lost. Reconnecting..." with manual retry button

**Gap recovery:** On reconnect, the client fetches the latest thread data via tRPC. This catches any messages that arrived during the disconnection window. Supabase Realtime does not guarantee delivery of missed events during disconnect, so the tRPC refetch is essential.

---

## 5. Agent Response Rendering

### 5.1 The Agent Component Catalog

7 MVP components, as defined in ADMIN-CONFIGURABLE-UI.md:

| Component | Purpose | Always Available |
|-----------|---------|-----------------|
| `TextMessage` | Markdown-formatted text with code blocks | Yes (cannot be disabled) |
| `SummaryCard` | Key-value summary of an entity or fork resolution | No (admin-configurable) |
| `ActionButtons` | Row of clickable action buttons | No (admin-configurable) |
| `CodeBlock` | Syntax-highlighted code with copy button | Yes (part of TextMessage) |
| `DataTable` | Sortable, filterable data table | No (admin-configurable) |
| `LoadingIndicator` | Agent "thinking" state with progress | Yes (cannot be disabled) |
| `ErrorMessage` | Agent failure with retry option | Yes (cannot be disabled) |

Additional components from the catalog:
- `Confirmation` -- yes/no decision point (always available)
- `Progress` -- multi-step task progress (always available)
- `Form` -- structured input collection (admin-configurable)

### 5.2 Component Selection Pipeline

Agent responses come in two forms:

**Form A: Plain text** (most common for conversational responses)
```json
{
  "content": "Here is my analysis of the pricing models...",
  "author_type": "agent"
}
```
Rendered as `TextMessage` with markdown parsing.

**Form B: Structured response** (when agent produces rich output)
```json
{
  "content": "Here are the competitor pricing models:",
  "metadata": {
    "components": [
      {
        "type": "table",
        "props": {
          "headers": [{"key": "name", "label": "Competitor"}, ...],
          "rows": [{"name": "Slack", "price": "$8.75/user"}, ...]
        }
      },
      {
        "type": "action_buttons",
        "props": {
          "buttons": [
            {"label": "Detailed analysis", "action": "expand"},
            {"label": "Export CSV", "action": "export"}
          ]
        }
      }
    ]
  }
}
```

**Rendering pipeline:**

```typescript
function AgentResponseRenderer({ message }: { message: Message }) {
  const config = useConfig();
  const allowedComponents = config.ui.agentComponents.allowed;
  const components = message.metadata?.components as AgentComponent[] | undefined;

  return (
    <div className="agent-response">
      {/* Always render text content */}
      <TextMessage content={message.content} />

      {/* Render structured components if present */}
      {components?.map((component, i) => {
        // Check if component type is allowed in this workspace
        if (!allowedComponents.includes(component.type)) {
          return null; // Fall back to text rendering above
        }

        return (
          <AgentCatalogComponent
            key={i}
            type={component.type}
            props={component.props}
          />
        );
      })}
    </div>
  );
}

function AgentCatalogComponent({ type, props }: { type: string; props: any }) {
  const componentMap: Record<string, React.ComponentType<any>> = {
    table: DataTable,
    action_buttons: ActionButtons,
    summary_card: SummaryCard,
    confirmation: Confirmation,
    progress: Progress,
    form: AgentForm,
  };

  const Component = componentMap[type];
  if (!Component) return null;

  return <Component {...props} />;
}
```

### 5.3 Streaming Responses

Agent responses stream token-by-token from the Claude API. The frontend handles this via Server-Sent Events (SSE):

```typescript
// hooks/useAgentStream.ts
function useAgentStream(taskId: string | null) {
  const [streamContent, setStreamContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    const eventSource = new EventSource(`/api/agent/stream/${taskId}`);
    setIsStreaming(true);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'token') {
        setStreamContent(prev => prev + data.text);
      } else if (data.type === 'done') {
        setIsStreaming(false);
        eventSource.close();
        // The complete message will arrive via Supabase Realtime
        // (agent inserts the full message into the messages table)
      } else if (data.type === 'error') {
        setIsStreaming(false);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };

    return () => eventSource.close();
  }, [taskId]);

  return { streamContent, isStreaming };
}
```

**Rendering a streaming message:**

```typescript
function StreamingAgentMessage({ taskId, agentConfig }: Props) {
  const { streamContent, isStreaming } = useAgentStream(taskId);

  if (isStreaming || streamContent) {
    return (
      <MessageBubble
        message={{
          author_type: 'agent',
          author_id: agentConfig.id,
          content: streamContent,
        }}
        isStreaming={isStreaming}
      />
    );
  }

  return <AgentThinkingIndicator agent={agentConfig} />;
}
```

**Flow:**
1. User sends `@Agent message`
2. Server creates task (status: queued -> running)
3. Supabase Realtime broadcasts task status change
4. Frontend shows `AgentThinkingIndicator`
5. Frontend opens SSE connection to `/api/agent/stream/{taskId}`
6. Tokens stream in, rendering progressively
7. When complete, SSE closes. Full message arrives via Realtime (normal INSERT).
8. Frontend switches from streaming view to normal MessageBubble.

**MVP simplification:** If SSE streaming adds too much complexity for initial implementation, the alternative is "insert empty message -> update as tokens arrive." The agent task processor inserts a message immediately (with partial content), then updates it repeatedly as tokens stream. Supabase Realtime broadcasts each UPDATE. This is simpler but creates more Realtime traffic. Evaluate during implementation.

---

## 6. Fork/Branch UX Implementation

### 6.1 Fork Sidebar Component

The fork sidebar replaces the agent roster section in the sidebar when a thread is active:

```
+-- Sidebar --+
| Channels    |
| #general    |
| #engineering|
| ...         |
+-------------+
| FORKS (3)   |  <- Section header with count
|             |
| > Pricing   |  <- Active fork entry
|   Research   |
|   Charles +  |
|   @Researcher|
|   8 msgs 5m  |
|   [Active]   |
|             |
| > Alt API   |  <- Active fork entry
|   Design    |
|   Dev + CTO  |
|   3 msgs 1m  |
|   [Active]   |
|             |
| RESOLVED (1)|  <- Resolved section
|             |
| > Auth Flow |  <- Resolved fork (dimmed)
|   [Resolved] |
+-------------+
```

**Implementation:**

```typescript
function ForkSidebar({ threadId }: { threadId: string }) {
  const forks = useForkStore(s => s.forks[threadId] || []);
  const activeForkId = useForkStore(s => s.activeForkId);
  const setActiveFork = useForkStore(s => s.setActiveFork);

  const activeForks = forks.filter(f => f.status === 'active');
  const resolvedForks = forks.filter(f => f.status === 'resolved');

  return (
    <SidebarSection label={`Forks (${activeForks.length})`}>
      {activeForks.map(fork => (
        <ForkSidebarEntry
          key={fork.id}
          fork={fork}
          isActive={fork.id === activeForkId}
          onClick={() => setActiveFork(fork.id)}
        />
      ))}

      {resolvedForks.length > 0 && (
        <SidebarSection label={`Resolved (${resolvedForks.length})`} collapsible defaultCollapsed>
          {resolvedForks.map(fork => (
            <ForkSidebarEntry
              key={fork.id}
              fork={fork}
              isActive={fork.id === activeForkId}
              onClick={() => setActiveFork(fork.id)}
              dimmed
            />
          ))}
        </SidebarSection>
      )}
    </SidebarSection>
  );
}
```

### 6.2 Fork Creation Flow

```
1. User hovers message -> "Fork" action appears in hover menu
2. User clicks "Fork"
3. Modal opens:
   +-----------------------------------------+
   | Create Fork                         [X] |
   +-----------------------------------------+
   | Starting from:                          |
   | "We need to implement rate limiting..." |
   |                                         |
   | Description (optional):                 |
   | [Auto: Rate limiting research       ]   |
   |                                         |
   | [Cancel]              [Create Fork]     |
   +-----------------------------------------+
4. On submit:
   - API call: fork.create({ threadId, parentMessageId, description })
   - Optimistic: add fork to ForkSidebar immediately
   - Switch focus to new fork (setActiveFork)
   - Fork view shows the parent message as context header
   - Compose box is ready for the user's first message in the fork
```

**Auto-description:** The fork description is auto-generated from the parent message content (first ~60 characters, cleaned up). User can edit before creating.

### 6.3 Resolution Flow

```
1. User clicks "Resolve" button in ForkView header
2. API call: fork.resolve({ forkId })
3. Server creates a 'fork_resolution' task
4. AI generates summary (headline + key points + recommendation)
5. Resolution modal opens with editable summary:
   +-----------------------------------------+
   | Resolve Fork: Rate Limiting Research [X] |
   +-----------------------------------------+
   |                                          |
   | AI-generated summary:                    |
   | (edit before posting to thread)           |
   |                                          |
   | Headline:                                |
   | [Use Cloudflare Token Bucket for rate ]  |
   | [limiting                             ]  |
   |                                          |
   | Summary:                                 |
   | [- Token Bucket via Cloudflare simplest] |
   | [- Handles 1000 req/s, ~$0.05/10K req ] |
   | [- No code changes -- config only     ] |
   |                                          |
   | This will post to the main thread.       |
   |                                          |
   | [Cancel]           [Post to Thread]      |
   +-----------------------------------------+
6. On confirm:
   - Resolution message inserted into main thread (fork_id = null)
   - Fork status updated to 'resolved'
   - Fork sidebar entry moves to "Resolved" section
   - Focus switches back to main thread
   - ResolutionCard renders in the main thread
```

### 6.4 Visual Distinction

| Element | Main Thread | Fork |
|---------|-------------|------|
| Background | Default | Subtle tinted background (e.g., `bg-slate-50/50`) |
| Breadcrumb | "#{channel} > {thread title}" | "#{channel} > {thread} > Fork: {name}" |
| Header action | None | "Resolve" and "Abandon" buttons |
| Context header | None | Shows the forked-from message in a quoted block |
| Sidebar state | Fork sidebar shows all forks | Current fork is highlighted |
| Compose placeholder | "Message #{channel}" | "Message in fork: {name}" |
| Message border | None | Subtle left border accent color |

### 6.5 Navigation Between Forks

Focus mode: the main content area shows ONE context at a time. Switching is done via the fork sidebar:

- Click fork in sidebar -> main area transitions to ForkView
- Click "Back to thread" in fork header -> main area transitions to ThreadView
- Click different fork in sidebar -> main area switches forks
- Fork resolution -> auto-switch back to main thread

Transition: instant swap (no animation in MVP). The URL does NOT change when switching forks -- this is client-side state only (`forkStore.activeForkId`). This keeps navigation fast and avoids unnecessary route changes.

---

## 7. Performance Considerations

### 7.1 Message Virtualization

For threads with hundreds of messages, rendering all DOM nodes is expensive. Use TanStack Virtual for windowed rendering:

```typescript
function VirtualizedMessageList({ messages }: { messages: Message[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated message height
    overscan: 10,           // Render 10 extra items above/below viewport
    // Reverse scroll: newest messages at bottom
    getItemKey: (index) => messages[index].id,
  });

  return (
    <div ref={parentRef} className="h-full overflow-y-auto">
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            ref={virtualizer.measureElement}
            data-index={virtualItem.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <MessageBubble message={messages[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

**When to virtualize:** Only when message count exceeds 50. Below that, native rendering is fine. The virtualizer adds complexity (scroll position management, dynamic heights, scroll-to-bottom behavior) that is not worth it for short threads.

**Scroll-to-bottom behavior:** When a new message arrives and the user is already at the bottom (within 100px), auto-scroll to the new message. If the user has scrolled up (reading history), show a "New messages" pill button that scrolls to bottom on click.

### 7.2 Image/Media Lazy Loading

```typescript
// Use Next.js Image component with lazy loading (default behavior)
<Image
  src={message.metadata?.imageUrl}
  alt="Uploaded image"
  width={400}
  height={300}
  loading="lazy"
  placeholder="blur"
  blurDataURL={message.metadata?.imagePlaceholder}
/>
```

Images and file previews use `loading="lazy"` (browser-native). Intersection Observer is not needed -- the virtualizer already handles which items are in view.

### 7.3 Bundle Splitting Strategy

Next.js App Router provides automatic code splitting per route segment. Additional manual splits:

| Bundle | Content | Loading Strategy |
|--------|---------|------------------|
| Core | Shell, sidebar, channel list, message rendering | Eager (initial load) |
| Thread | ThreadView, MessageList, ComposeBox | Route-based split (loaded on thread navigation) |
| Fork | ForkView, ForkSidebar, ResolutionModal | Route-based split (loaded on thread navigation) |
| Agent Components | DataTable, ActionButtons, Form, SummaryCard | Dynamic import (loaded when first agent response uses them) |
| Search | SearchView, search result rendering | Dynamic import (loaded when search opened) |
| Admin | SettingsView, config forms | Dynamic import (loaded only for admin users) |
| Markdown | Markdown parser + syntax highlighter (shiki) | Dynamic import (loaded on first message render) |

```typescript
// Agent component catalog: dynamic imports
const AgentComponentMap: Record<string, React.LazyExoticComponent<any>> = {
  table: lazy(() => import('@/components/agent/DataTable')),
  action_buttons: lazy(() => import('@/components/agent/ActionButtons')),
  summary_card: lazy(() => import('@/components/agent/SummaryCard')),
  form: lazy(() => import('@/components/agent/AgentForm')),
  confirmation: lazy(() => import('@/components/agent/Confirmation')),
  progress: lazy(() => import('@/components/agent/ProgressIndicator')),
};
```

### 7.4 Initial Load Performance Target

**Target: < 3 seconds for workspace view (channel list visible).**

Budget breakdown:
| Phase | Target | Strategy |
|-------|--------|----------|
| HTML delivery | < 200ms | Vercel edge, SSR for shell |
| JS parse + execute | < 500ms | Core bundle < 150KB gzipped |
| Auth check | < 300ms | Supabase session check (local token) |
| Workspace data fetch | < 500ms | Channels + user profile via tRPC (parallel) |
| First paint (shell) | < 1000ms | SSR renders sidebar + loading skeleton |
| Full interactive | < 2500ms | Channel list populated, subscriptions active |

**Strategies:**
- Server-side render the workspace shell (sidebar skeleton, header)
- Parallel data fetches: channels, user profile, workspace config
- Defer agent roster fetch until sidebar section is visible
- No blocking waterfall: auth -> workspace -> channels all resolve independently
- Prefetch thread data on channel hover (tRPC prefetch)

---

## 8. Folder Structure

### 8.1 Nx Monorepo Layout

```
openvibe/
  apps/
    web/                           # Next.js application
      app/                         # App Router (routes + layouts)
        (auth)/
          login/page.tsx
          signup/page.tsx
          callback/page.tsx
          layout.tsx
        (workspace)/
          [workspaceId]/
            channel/
              [channelId]/
                thread/
                  [threadId]/
                    page.tsx       # Thread view page
                page.tsx           # Channel view (thread list)
                layout.tsx
            channels/page.tsx
            search/page.tsx
            settings/page.tsx
            layout.tsx             # Workspace layout (sidebar + main)
          layout.tsx               # Auth guard layout
        layout.tsx                 # Root layout (HTML, providers)
        page.tsx                   # Landing / redirect

      components/                  # Feature components
        shell/                     # App shell components
          WorkspaceShell.tsx
          Sidebar.tsx
          MainContent.tsx
          DetailPanel.tsx
          ChannelHeader.tsx
        channel/                   # Channel feature
          ChannelList.tsx
          ChannelItem.tsx
        thread/                    # Thread feature
          ThreadList.tsx
          ThreadListItem.tsx
          ThreadView.tsx
          MessageList.tsx
          VirtualizedMessageList.tsx
        fork/                      # Fork feature
          ForkView.tsx
          ForkSidebar.tsx
          ForkSidebarEntry.tsx
          ForkCreationModal.tsx
          ResolutionModal.tsx
          ResolutionCard.tsx
        message/                   # Message components
          MessageBubble.tsx
          MessageActions.tsx
          ComposeBox.tsx
          MentionAutocomplete.tsx
          TypingIndicator.tsx
        agent/                     # Agent response rendering
          AgentResponseRenderer.tsx
          AgentThinkingIndicator.tsx
          catalog/                 # Agent component catalog
            DataTable.tsx
            ActionButtons.tsx
            SummaryCard.tsx
            Confirmation.tsx
            ProgressIndicator.tsx
            AgentForm.tsx
            CodeBlock.tsx
            ErrorMessage.tsx
        search/                    # Search feature
          SearchView.tsx
          SearchResult.tsx
        settings/                  # Admin settings
          SettingsView.tsx
          AgentConfigForm.tsx
          BrandingForm.tsx

      lib/                         # Utilities, hooks, stores
        stores/                    # Zustand stores
          authStore.ts
          channelStore.ts
          threadStore.ts
          messageStore.ts
          forkStore.ts
          agentStore.ts
          uiStore.ts
          configStore.ts
        hooks/                     # Custom React hooks
          useThreadSubscription.ts
          useChannelSubscription.ts
          useTypingIndicator.ts
          useAgentStream.ts
          useRealtimeHealth.ts
          useConfig.ts
          useTerminology.ts
          useOptimisticMessage.ts
          useVirtualizedScroll.ts
        trpc/                      # tRPC client setup
          client.ts                # tRPC React client
          server.ts                # tRPC server-side caller
          routers/                 # Router type imports
        supabase/                  # Supabase client setup
          client.ts                # Browser client
          server.ts                # Server client
          middleware.ts            # Auth middleware
        utils/                     # Pure utility functions
          markdown.ts              # Markdown parsing
          mentions.ts              # @mention parsing
          dates.ts                 # Date formatting
          cn.ts                    # Class name utility (shadcn pattern)

      providers/                   # React context providers
        ConfigProvider.tsx
        RealtimeProvider.tsx
        TRPCProvider.tsx

      public/                      # Static assets
        assets/

      next.config.js
      tailwind.config.ts
      tsconfig.json

  packages/
    ui/                            # Shared shadcn/ui components
      src/
        components/
          button.tsx
          input.tsx
          dialog.tsx
          dropdown-menu.tsx
          avatar.tsx
          badge.tsx
          card.tsx
          skeleton.tsx
          tooltip.tsx
          scroll-area.tsx
          separator.tsx
          sheet.tsx                 # Mobile sidebar
          command.tsx              # Command palette (search)
          textarea.tsx
        lib/
          utils.ts
      package.json
      tsconfig.json

    types/                         # Shared TypeScript types
      src/
        models/
          user.ts
          workspace.ts
          channel.ts
          thread.ts
          fork.ts
          message.ts
          task.ts
          agent.ts
        api/                       # tRPC router types
          router.ts
        config/
          workspace-config.ts      # Config schema types
          agent-component.ts       # Agent component types
      package.json
      tsconfig.json

    config/                        # Default config files
      src/
        defaults.yaml              # Platform defaults
        vibe-internal.yaml         # Dogfood workspace config
      package.json

  nx.json
  package.json
  tsconfig.base.json
```

### 8.2 Key Conventions

**File naming:** PascalCase for React components, camelCase for hooks/utils/stores. One component per file. Co-locate tests next to source files (`ThreadView.tsx` + `ThreadView.test.tsx`).

**Import paths:** Use Nx path aliases:
- `@openvibe/ui` -> `packages/ui/src`
- `@openvibe/types` -> `packages/types/src`
- `@/components` -> `apps/web/components`
- `@/lib` -> `apps/web/lib`
- `@/providers` -> `apps/web/providers`

**Component organization:** Feature folders group all components related to a domain. Shared UI primitives (button, input, dialog) live in `packages/ui`. Feature-specific components (MessageBubble, ForkSidebar) live in `apps/web/components/{feature}/`.

---

## 9. MVP vs Full Vision

### 9.1 MVP Pages/Views (Dogfood Minimum)

| View | Route | Status |
|------|-------|--------|
| Login / Signup | `/login`, `/signup` | **Must Have** |
| OAuth Callback | `/callback` | **Must Have** |
| Channel List | `/w/[id]/channels` | **Must Have** |
| Channel View (Thread List) | `/w/[id]/channel/[cId]` | **Must Have** |
| Thread View (Messages + Forks) | `/w/[id]/channel/[cId]/thread/[tId]` | **Must Have** |
| Fork View (within Thread View) | Client-side state, no separate route | **Must Have** |
| Search | `/w/[id]/search` | **Must Have** |
| Admin Settings | `/w/[id]/settings` | **Should Have** (simple form for agent config) |

### 9.2 MVP Feature Scope

**Must Have (Weeks 1-4):**
- [x] Discord-like shell: sidebar + main content area
- [x] Channel list in sidebar
- [x] Thread list in channel view
- [x] Thread view with message list
- [x] Message composition with @mention autocomplete (agents)
- [x] Real-time message updates via Supabase Realtime
- [x] Fork creation from any message
- [x] Fork sidebar showing active/resolved forks
- [x] Focus mode: switch between main thread and forks
- [x] Fork resolution flow (AI summary -> edit -> post to thread)
- [x] Agent response rendering (markdown + code blocks)
- [x] Agent "thinking" indicator
- [x] Human vs agent message styling distinction
- [x] Optimistic message sending
- [x] Full-text search across messages
- [x] Config-driven branding (CSS custom properties)
- [x] Config-driven terminology (`useTerminology()` hook)

**Should Have (Weeks 5-6):**
- [ ] Agent response streaming (SSE token-by-token)
- [ ] Agent component catalog (DataTable, SummaryCard, ActionButtons)
- [ ] Progressive disclosure on agent responses (expand/collapse)
- [ ] Message virtualization for long threads
- [ ] Peek mode for forks (read-only preview in sidebar)
- [ ] ResolutionCard component for resolved fork summaries
- [ ] Keyboard shortcuts (Cmd+K search, Cmd+Enter send, Esc close panels)

### 9.3 Explicitly Deferred

| Feature | Why Deferred | Effort to Add Later |
|---------|-------------|---------------------|
| Dark mode | Cosmetic, not blocking | 2-3 days (CSS variables) |
| Reactions/emoji | Nice-to-have | 1-2 days |
| File attachments | Use existing tools for now | 3-5 days |
| Mobile responsive layout | Desktop-first per SYNTHESIS | 1-2 weeks |
| Animations/transitions | Fork switching, message appear | 1-2 days |
| Accessibility polish (WCAG AA) | Required before public launch | 1-2 weeks |
| i18n | English only for dogfood | 2+ weeks |
| Offline support | Internet assumed for Vibe team | Multi-week |
| User presence (online/offline) | Not critical for forum model | 2-3 days |
| Unread message tracking | Scroll to bottom + search is enough | 3-5 days |
| Notification system | Use existing Slack during transition | 1-2 weeks |
| Thread titles (auto-generated) | First message preview is sufficient | 1 day |
| Message edit history | Low value for dogfood | 2-3 days |
| Visual layout builder (admin) | YAML config is sufficient for dogfood | Multi-week |
| Canvas/spatial view | Rejected by THREAD-UX-PROPOSAL | Would not build |
| Branch visualization (git graph) | Rejected by R1 | Would not build |

---

## Open Questions

1. **SSE vs Realtime for agent streaming.** The document proposes SSE for token streaming and Supabase Realtime for final message delivery. An alternative is to use Supabase Realtime for everything: insert partial message, update with each chunk. This is simpler but creates heavy UPDATE traffic. Needs benchmarking during implementation.

2. **Virtualization library.** TanStack Virtual is recommended for its headless approach and dynamic height support. But the chat-specific patterns (reverse scroll, scroll-to-bottom anchoring, prepend loading) are not well-documented. If implementation proves difficult, fall back to a simpler approach: paginate messages (load last 50, "Load more" button for history) without virtualization. This is sufficient for most threads.

3. **Fork state in URL.** The current proposal keeps fork selection in Zustand only (not URL). This means deep-linking to a specific fork is not possible, and browser back/forward does not navigate between forks. If users find this frustrating during dogfood, add `?fork=[forkId]` as a URL search parameter.

4. **Markdown rendering library.** Options: `react-markdown` (popular, React-native), `marked` + `DOMPurify` (fast, requires sanitization), `@mdx-js/mdx` (overkill). Recommendation: `react-markdown` with `rehype-highlight` for syntax highlighting and `remark-gfm` for GitHub-flavored markdown (tables, strikethrough). Add `shiki` for code block syntax highlighting if `rehype-highlight` quality is insufficient.

5. **Config refresh during session.** When the admin changes workspace config (e.g., adds an agent), how quickly should active users see the change? Current proposal: Supabase Realtime broadcasts config change, clients refetch config via tRPC, Zustand store updates, components re-render. Latency: < 2s. Is this acceptable or should config be pushed directly in the Realtime payload?

6. **Compose box position.** The wireframes in THREAD-UX-PROPOSAL show the compose box at the bottom of the main content area, which is standard. But when the thread is very long, the compose box might be below the fold if the user has scrolled up. Options: (a) fixed at bottom of viewport, (b) fixed at bottom of thread container, (c) floating. Recommendation: (b) fixed at bottom of thread container, same as Discord/Slack.

7. **Initial data loading strategy.** When user navigates to a thread for the first time, what data is fetched? Options: (a) fetch all messages at once (simple, works for threads < 200 messages), (b) fetch last 50 + paginate backwards (standard chat pattern). Recommendation: (a) for MVP (most threads will be < 100 messages during dogfood). Add pagination when thread sizes demand it.

---

## Rejected Approaches

### 1. Server Components for Message Rendering

**What:** Use React Server Components (RSC) for rendering message lists, with streaming SSR.

**Why rejected:** Messages update in real-time via Supabase Realtime. Server Components cannot receive push updates -- they render once on the server. The message list must be a Client Component to subscribe to Realtime events and update the DOM on new messages. Server Components are used for the layout shell (sidebar structure, headers) where data changes infrequently.

**Reconsider if:** Next.js adds server-push support for RSC, or if Partial Prerendering (PPR) matures enough to handle the initial message list as a static shell with dynamic client holes.

### 2. Redux / Redux Toolkit for State Management

**What:** Use Redux with RTK Query for state management and data fetching.

**Why rejected:** SYNTHESIS confirmed Zustand as the tech choice. Zustand is simpler, has less boilerplate, and is sufficient for the state complexity of this application. RTK Query overlaps with React Query (which tRPC provides). Adding Redux would mean two state management patterns.

**Reconsider if:** State interactions become extremely complex (10+ stores with heavy cross-store dependencies). Zustand can handle this with the slices pattern, but if it becomes unmanageable, Redux's explicit action flow may help debug.

### 3. Socket.IO for Real-time

**What:** Deploy a Socket.IO server for real-time communication instead of using Supabase Realtime.

**Why rejected:** Supabase Realtime is already in the stack (free with Supabase), provides postgres_changes (database-driven events), and requires no additional infrastructure. Socket.IO would need a separate server process, custom event routing, and reconnection logic that Supabase handles.

**Reconsider if:** Supabase Realtime proves unreliable at scale (> 200 concurrent connections), or if custom event patterns (not tied to database changes) become a primary need.

### 4. Tab-Based Fork Navigation (M2 Original Design)

**What:** Forks displayed as tabs at the top of the thread view, similar to browser tabs.

**Why rejected:** THREAD-UX-PROPOSAL and R1 both reject tabs. Tabs don't scale beyond 5-7 items, provide no status information, and don't show the relationship between forks and their parent messages. The sidebar + focus mode pattern is strictly superior.

**Reconsider if:** User testing reveals the sidebar is too "hidden" and users miss active forks. Then consider a hybrid: 2-3 most recent forks as inline quick-switch buttons above the message list, with the full sidebar for all forks.

### 5. Full-Page Route Transitions for Forks

**What:** Each fork is a separate URL route (`/thread/[threadId]/fork/[forkId]`).

**Why rejected:** Fork switching should be instant. Route transitions (even with Next.js client-side navigation) involve layout recalculation, data fetching, and potential loading states. Keeping fork selection as client-side Zustand state allows instant swap of the message list content without any route-level effects.

**Reconsider if:** Deep-linking to forks becomes essential (e.g., someone shares a fork URL in Slack). Then add `?fork=[forkId]` as a URL search parameter that initializes the Zustand fork state on page load, without making it a full route segment.

### 6. CSS-in-JS (styled-components, Emotion, Stitches)

**What:** Use a CSS-in-JS library for component styling.

**Why rejected:** TailwindCSS + shadcn/ui is the confirmed tech stack. CSS-in-JS adds runtime overhead (style computation, injection) that TailwindCSS avoids entirely. The ADMIN-CONFIGURABLE-UI research specifically recommends CSS custom properties over CSS-in-JS for branding -- zero runtime cost.

**Reconsider if:** Never. This is a settled decision reinforced by multiple research documents.

### 7. GraphQL (Apollo Client) for Data Layer

**What:** Use GraphQL with Apollo Client instead of tRPC for the API layer.

**Why rejected:** BACKEND-MINIMUM-SCOPE confirms tRPC. With a single frontend client, GraphQL's query flexibility is unnecessary overhead. tRPC provides end-to-end type safety with zero schema definition, which is faster to develop and maintain for a single-client application.

**Reconsider if:** Multiple clients (mobile app, third-party integrations) need different data shapes. At that point, GraphQL's query flexibility justifies the schema overhead.

---

*Research completed: 2026-02-07*
*Researcher: frontend-architect (Phase 1.5)*
*Dependencies: Builds on THREAD-UX-PROPOSAL (fork UX), BACKEND-MINIMUM-SCOPE (tRPC API, Realtime events, data model), ADMIN-CONFIGURABLE-UI (config schema, component catalog), RUNTIME-ARCHITECTURE (streaming, session model). Feeds directly into Phase 3 implementation.*
