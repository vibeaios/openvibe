> **SUPERSEDED**: This document is from the initial design phase. For implementation, refer to:
> - [`SYSTEM-ARCHITECTURE.md`](../research/phase-1.5/SYSTEM-ARCHITECTURE.md) — Full architecture
> - [`BACKEND-MINIMUM-SCOPE.md`](../research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) — API design

# M5: Orchestration (Routing + Coordination)

> Status: Draft | Priority: High | Dependency: M1, M3, M4

## Overview

The Orchestration Layer is the central coordinator, responsible for:
- Message routing (who should handle this message)
- Agent scheduling (assigning tasks to the appropriate agent)
- Concurrency control (coordination when multiple agents collaborate)
- State synchronization (ensuring all participants see a consistent state)

## Architecture

```
                    ┌─────────────────┐
                    │    Frontend     │
                    └────────┬────────┘
                             │ WebSocket
                    ┌────────▼────────┐
                    │   API Gateway   │
                    │   (Next.js)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Orchestrator   │  ◄── Core
                    │                 │
                    │ ┌─────────────┐ │
                    │ │   Router    │ │
                    │ ├─────────────┤ │
                    │ │  Scheduler  │ │
                    │ ├─────────────┤ │
                    │ │   Queue     │ │
                    │ └─────────────┘ │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌─────────┐        ┌─────────┐        ┌─────────┐
    │ Agent 1 │        │ Agent 2 │        │ Agent N │
    └─────────┘        └─────────┘        └─────────┘
```

## Core Components

### 1. Message Router

Determines who should receive a message:

```typescript
interface RouteDecision {
  targets: Target[];
  priority: 'high' | 'normal' | 'low';
  requiresResponse: boolean;
}

interface Target {
  type: 'agent' | 'broadcast' | 'specific-agent';
  agentId?: string;
  agentType?: string;  // e.g., 'coder', 'researcher'
}

// Routing rules
function routeMessage(message: Message): RouteDecision {
  // 1. Explicit @ mention
  if (message.mentions.length > 0) {
    return {
      targets: message.mentions.map(m => ({
        type: 'specific-agent',
        agentId: m.id
      })),
      priority: 'high',
      requiresResponse: true
    };
  }

  // 2. Content-based auto-routing
  const intent = classifyIntent(message.content);

  if (intent === 'coding') {
    return {
      targets: [{ type: 'agent', agentType: 'coder' }],
      priority: 'normal',
      requiresResponse: true
    };
  }

  if (intent === 'research') {
    return {
      targets: [{ type: 'agent', agentType: 'researcher' }],
      priority: 'normal',
      requiresResponse: true
    };
  }

  // 3. Default: do not auto-respond unless auto-respond is configured
  return {
    targets: [],
    priority: 'low',
    requiresResponse: false
  };
}
```

### 2. Agent Scheduler

Selects the most suitable agent instance to execute a task:

```typescript
interface ScheduleResult {
  agentId: string;
  estimatedWait: number;  // estimated wait time (ms)
}

async function scheduleTask(
  task: Task,
  agentType: string
): Promise<ScheduleResult> {
  // 1. Get all available agents of this type
  const agents = await getAgentsByType(agentType);

  // 2. Filter healthy ones
  const healthy = agents.filter(a => a.status === 'healthy');

  // 3. Select the least busy
  const sorted = healthy.sort((a, b) =>
    a.currentLoad - b.currentLoad
  );

  const selected = sorted[0];

  // 4. If all are busy, add to queue
  if (selected.currentLoad >= 1.0) {
    await addToQueue(task, agentType);
    return {
      agentId: selected.id,
      estimatedWait: estimateQueueWait(agentType)
    };
  }

  return {
    agentId: selected.id,
    estimatedWait: 0
  };
}
```

### 3. Task Queue

Manages pending tasks:

```typescript
interface QueuedTask {
  id: string;
  task: Task;
  targetAgentType: string;
  priority: number;
  createdAt: Date;
  attempts: number;
  maxAttempts: 3;
}

// Redis queue (or simplified Postgres version)
class TaskQueue {
  async enqueue(task: Task, priority: number): Promise<void> {
    await redis.zadd(
      `queue:${task.agentType}`,
      priority * -1,  // Higher priority first
      JSON.stringify(task)
    );
  }

  async dequeue(agentType: string): Promise<Task | null> {
    const result = await redis.zpopmin(`queue:${agentType}`);
    return result ? JSON.parse(result) : null;
  }

  async getQueueLength(agentType: string): Promise<number> {
    return redis.zcard(`queue:${agentType}`);
  }
}
```

### 4. Concurrent Work Manager

Handles scenarios where multiple agents work simultaneously:

```typescript
interface WorkSession {
  id: string;
  threadId: string;
  activeAgents: string[];
  locks: Lock[];
}

interface Lock {
  resource: string;  // e.g., 'file:/src/app.ts'
  agentId: string;
  acquiredAt: Date;
  expiresAt: Date;
}

// Prevent conflicts
async function acquireLock(
  agentId: string,
  resource: string
): Promise<boolean> {
  const existing = await getLock(resource);

  if (existing && existing.agentId !== agentId) {
    // Already locked by another agent
    return false;
  }

  await setLock({
    resource,
    agentId,
    acquiredAt: new Date(),
    expiresAt: new Date(Date.now() + 60000)  // 1 min TTL
  });

  return true;
}
```

## Message Flow

### User Sends a Message

```
1. Frontend → API Gateway (WebSocket)
2. Gateway → Orchestrator.routeMessage()
3. Orchestrator determines routing:
   a. @ mention → Send to specified agent
   b. Needs AI → Select appropriate agent
   c. Human-only conversation → No action
4. If agent is needed:
   a. Scheduler.selectAgent()
   b. Send task to agent
   c. Wait for response (async)
5. Agent responds → Write to Thread → Broadcast to Frontend
```

### Agent Initiates a Message

```
1. Agent has output to send
2. Agent → Orchestrator.submitResponse()
3. Orchestrator:
   a. Validate agent permissions
   b. Write to Thread (M1)
   c. Update Memory (M4) if needed
   d. Broadcast to all Frontend clients
```

## API Design

### Internal API (Orchestrator <-> Agents)

```typescript
// Agent registration
POST /internal/agents/register
{
  agentId: string;
  agentType: string;
  capabilities: string[];
  endpoint: string;  // Agent's API address
}

// Agent heartbeat
POST /internal/agents/:agentId/heartbeat
{
  status: 'idle' | 'busy';
  currentTask?: string;
  load: number;  // 0-1
}

// Assign task
POST /internal/agents/:agentId/task
{
  taskId: string;
  threadId: string;
  message: Message;
  context: {
    recentMessages: Message[];
    memory: MemoryItem[];
  };
}

// Agent response
POST /internal/tasks/:taskId/response
{
  agentId: string;
  response: {
    content: string;
    type: ContentType;
    memoryUpdates?: MemoryUpdate[];
  };
}
```

### External API (Frontend <-> Gateway)

```typescript
// WebSocket events

// Send message
{
  event: 'message:send',
  data: {
    threadId: string;
    branchId: string;
    content: string;
    mentions: string[];
  }
}

// Receive new message
{
  event: 'message:new',
  data: {
    message: Message;
    isAgent: boolean;
  }
}

// Agent status change
{
  event: 'agent:status',
  data: {
    agentId: string;
    status: AgentStatus;
    task?: string;
  }
}

// Typing indicator
{
  event: 'typing:start' | 'typing:stop',
  data: {
    threadId: string;
    userId: string;  // or agentId
  }
}
```

## State Management

### Orchestrator State

```typescript
interface OrchestratorState {
  // Agent registry
  agents: Map<string, AgentInfo>;

  // Active sessions
  sessions: Map<string, WorkSession>;

  // Task queue status
  queues: Map<string, QueueStatus>;

  // Locks
  locks: Map<string, Lock>;
}

// Storage: Redis (fast) + Postgres (persistent)
```

## Failure Handling

### Agent Unresponsive

```typescript
async function handleAgentTimeout(taskId: string) {
  const task = await getTask(taskId);

  if (task.attempts < task.maxAttempts) {
    // Retry
    task.attempts++;
    await reschedule(task);
  } else {
    // Give up, notify user
    await notifyFailure(task.threadId,
      `Agent processing timed out. Please try again later.`
    );
  }
}
```

### Agent Crash

```typescript
// Heartbeat timeout detection
setInterval(async () => {
  const staleAgents = await findStaleAgents(
    HEARTBEAT_TIMEOUT // 30s
  );

  for (const agent of staleAgents) {
    // Mark as offline
    await updateAgentStatus(agent.id, 'offline');

    // Reassign its tasks
    const tasks = await getAgentTasks(agent.id);
    for (const task of tasks) {
      await reschedule(task);
    }
  }
}, 10000);
```

## Configuration

```yaml
orchestrator:
  # Routing
  routing:
    defaultAgentType: "general"
    autoRespond: false  # Whether agents auto-respond

  # Scheduling
  scheduling:
    maxConcurrentTasks: 10
    taskTimeout: 300  # seconds
    queueMaxSize: 100

  # Retry
  retry:
    maxAttempts: 3
    backoffMs: [1000, 5000, 15000]

  # Heartbeat
  heartbeat:
    intervalMs: 10000
    timeoutMs: 30000
```

## MVP Scope

**Phase 1 (Must have)**:
- [ ] Basic message routing (@ mention)
- [ ] Single agent scheduling
- [ ] Simple task queue (Postgres)
- [ ] WebSocket gateway

**Phase 2 (Important)**:
- [ ] Multi-agent scheduling
- [ ] Content-based auto-routing
- [ ] Agent health checks
- [ ] Failure retry

**Phase 3 (Advanced)**:
- [ ] Redis queue (performance)
- [ ] Concurrency lock mechanism
- [ ] Load balancing
- [ ] Monitoring dashboard

## Open Questions

1. **Routing strategy**: Pure rules vs LLM-based classification?
2. **Concurrency model**: How many agents per thread simultaneously?
3. **Priority**: VIP user priority?
4. **Cost control**: Token limits per task?

---

*To be refined after Charles confirms*
