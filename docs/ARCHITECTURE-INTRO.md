# Vibe AI Workspace - Architecture Introduction

> From product requirements to system design derivation
>
> **Current Status**: Phase 2 - Implementation
> **Concrete Specs**: [`SYSTEM-ARCHITECTURE.md`](research/phase-1.5/SYSTEM-ARCHITECTURE.md) | [`BACKEND-MINIMUM-SCOPE.md`](research/phase-1.5/BACKEND-MINIMUM-SCOPE.md)

---

## Table of Contents

1. [Core Product Requirements](#1-core-product-requirements)
2. [Design Constraints Driven by Requirements](#2-design-constraints-driven-by-requirements)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Layer 1: Capture Layer](#4-layer-1-capture-layer)
5. [Layer 2: API Layer](#5-layer-2-api-layer)
6. [Layer 3: Coordination Layer](#6-layer-3-coordination-layer)
7. [Layer 4: Core Services](#7-layer-4-core-services)
8. [Layer 5: Memory Layer](#8-layer-5-memory-layer)
9. [Layer 6: Foundation Services](#9-layer-6-foundation-services)
10. [Data Flows](#10-data-flows)

---

## 1. Core Product Requirements

### 1.1 What Problem We're Solving

**Core question: How do Humans + Agents collaborate together?**

This is not "adding AI to existing tools," but redesigning how collaboration works.

### 1.2 Product Requirements List

| ID | Requirement | Description | Priority |
|----|------|------|--------|
| **R1** | Human-Agent same space | Humans and AI Agents collaborate in the same conversation space | P0 |
| **R2** | Organizational memory | All conversations and decisions automatically distill into a searchable knowledge base | P0 |
| **R3** | Multi-source capture | Support hardware (Bot/Dot) and software (Slack/Web) multi-entry | P0 |
| **R4** | Conversation branching | Threads support exploratory branches with mergeable conclusions | P0 |
| **R5** | Industry-configurable | Same system adapts to different industries (medical/construction/SaaS) | P0 |
| **R6** | Layered permissions | Different roles see different levels of detail | P1 |
| **R7** | Real-time collaboration | Multiple people interact simultaneously in a Thread | P1 |
| **R8** | Extensible Agents | New Agent types can be defined | P1 |
| **R9** | External integrations | Connect to EHR/CRM/PM and other external systems | P1 |
| **R10** | Device management | Hardware devices can be registered, monitored, and managed | P2 |

---

## 2. Design Constraints Driven by Requirements

Each core requirement creates constraints on the system design:

### R1: Human-Agent Same Space -> Unified Message Model

```
Requirement: Humans and Agents interact in the same conversation

Constraints:
  - Message must support author being either human or Agent
  - Agent replies and human replies live in the same Feed
  - Agent needs to read conversation context

Design decision:
  - Unified Message structure
  - Author can be { type: "human" | "agent", id: string }
  - Feed is Thread's core component
```

### R2: Organizational Memory -> Independent Memory System

```
Requirement: Conversations automatically distill into a searchable knowledge base

Constraints:
  - Need persistent storage
  - Need semantic search (not just keywords)
  - Need permission control (not everyone can see everything)
  - Need hierarchical structure (Workspace -> Space -> Thread)

Design decision:
  - Memory is an independent core layer, not a secondary feature
  - Use vector database for semantic search
  - Memory Items have zoom levels
  - Memory has hierarchically inherited permissions
```

### R3: Multi-Source Capture -> Capture Layer Abstraction

```
Requirement: Support hardware and software multi-entry

Constraints:
  - Need to uniformly process different input formats (audio, text, images)
  - Need async processing (audio transcription takes time)
  - Need to decouple from device management

Design decision:
  - Independent Capture Layer to abstract entry points
  - Unified Processing Pipeline
  - Device Service manages devices but doesn't process data
```

### R4: Conversation Branching -> Git-like Thread Engine

```
Requirement: Threads support exploratory branches

Constraints:
  - Messages need parent-child relationships (not just linear timeline)
  - Need to support creating branches from any message
  - Need to support merging branches

Design decision:
  - Thread has Branch concept
  - Message has parentId
  - Support Branch/Merge operations
  - Git-like data model
```

### R5: Industry-Configurable -> 4-Layer Configuration System

```
Requirement: Same system adapts to different industries

Constraints:
  - Different industries have different Agents
  - Different industries have different workflows
  - Some configurations need to be locked (compliance)
  - Admin and User have different permissions

Design decision:
  - 4-layer config: Platform -> Template -> Workspace -> User
  - Configuration supports inheritance, override, and locking
  - Industry Template includes Agents + Skills + Workflows
```

### R6: Layered Permissions -> Zoom Levels

```
Requirement: Different roles see different levels of detail

Constraints:
  - Same data needs multiple views
  - Permissions must be tied to roles
  - Filtering should be automatic during retrieval

Design decision:
  - Memory Item stores multiple zoom levels (L1/L2/L3)
  - User role determines which level they can see
  - Zoom level filtering is automatically applied during retrieval
```

### R7: Real-time Collaboration -> Realtime Infrastructure

```
Requirement: Multiple people interact simultaneously in a Thread

Constraints:
  - Messages need real-time sync
  - Need to show who's online, who's typing
  - Agent responses also need real-time push

Design decision:
  - WebSocket connections
  - Supabase Realtime or similar technology
  - Presence (online status) system
```

### R8: Extensible Agents -> Separated Agent Definition

```
Requirement: New Agent types can be defined

Constraints:
  - Agent definitions need to be flexible
  - Agent capabilities need to be configurable
  - Agents need to run in isolation

Design decision:
  - Agent defined via SOUL.md (similar to OpenClaw)
  - Agent capabilities configured through Skills
  - Agents run in containers
```

---

## 3. System Architecture Overview

Based on the above requirements and constraints, the system is divided into 6 layers:

```
+---------------------------------------------------------------------------+
|                     Layer 1: CAPTURE                                       |
|            Multi-entry data capture (R3)                                   |
+---------------------------------------------------------------------------+
|                     Layer 2: API                                           |
|            Unified gateway, authentication, routing                        |
+---------------------------------------------------------------------------+
|                     Layer 3: COORDINATION                                  |
|            Message routing, Agent scheduling (R1)                          |
+---------------------------------------------------------------------------+
|                     Layer 4: CORE SERVICES                                 |
|            Thread (R4) | Agent (R1, R8) | Device (R10)                     |
+---------------------------------------------------------------------------+
|                     Layer 5: MEMORY                                        |
|            Core data layer (R2, R6)                                        |
+---------------------------------------------------------------------------+
|                     Layer 6: FOUNDATION                                    |
|            Config (R5) | IAM (R6) | Integration (R9)                      |
+---------------------------------------------------------------------------+
```

**Why this layering:**

| Layer | Responsibility | Maps to Requirement |
|------|------|----------|
| Capture | Isolate data entry complexity | R3 Multi-source |
| API | Unified entry, security boundary | Foundation for all requirements |
| Coordination | Human-Agent routing | R1 Same-space collaboration |
| Core Services | Core business logic | R4, R7, R10 |
| Memory | Data core, highest priority | R2, R6 |
| Foundation | Supporting services | R5, R6, R9 |

---

## 4. Layer 1: Capture Layer

### 4.1 Responsibility

```
Receive data from different sources, standardize it, and pass it to the system.
```

### 4.2 Why This Layer Is Needed

```
Problem: Diverse data sources
  - Vibe Bot: Audio streams (WebSocket/MQTT)
  - Vibe Dot: Audio + text (API)
  - Slack: Webhook events
  - Web UI: HTTP/WebSocket
  - API: Direct calls

Without Capture Layer:
  - Each entry point connects directly to Core Services
  - Protocol handling logic is scattered
  - New entry points require changes in multiple places

With Capture Layer:
  - Unified data format enters the system
  - New entry points only need a new Adapter
  - Protocol complexity is isolated
```

### 4.3 Components

```
+---------------------------------------------------------------------------+
|                     CAPTURE LAYER                                          |
|                                                                            |
|  +-------------+  +-------------+  +-------------+                        |
|  | Bot Adapter |  | Dot Adapter |  |Slack Adapter|                        |
|  |             |  |             |  |             |                        |
|  | - Audio     |  | - Audio/    |  | - Webhook   |                        |
|  |   stream    |  |   text      |  | - Event     |                        |
|  | - Status    |  | - Sync      |  |   transform |                        |
|  |   report    |  |             |  |             |                        |
|  +------+------+  +------+------+  +------+------+                        |
|         |                |                |                                |
|         +----------------+----------------+                                |
|                          |                                                 |
|                          v                                                 |
|              +-----------------------+                                     |
|              |   Unified Ingest API  |                                     |
|              |                       |                                     |
|              | - Standardize message |                                     |
|              |   format              |                                     |
|              | - Attach metadata     |                                     |
|              | - Route to next layer |                                     |
|              +-----------------------+                                     |
+---------------------------------------------------------------------------+
```

### 4.4 Data Standardization

Different sources -> unified format:

```typescript
// Unified inbound message format
interface IngestMessage {
  // Source
  source: {
    type: "bot" | "dot" | "slack" | "web" | "api";
    deviceId?: string;
    channelRef?: string;
  };

  // Content
  payload: {
    type: "text" | "audio" | "file" | "event";
    content: string | Buffer;
    mimeType?: string;
  };

  // Target
  target: {
    workspaceId: string;
    spaceId?: string;
    threadId?: string;  // If known
  };

  // Metadata
  metadata: {
    timestamp: Date;
    author?: Author;
    correlationId: string;
  };
}
```

---

## 5. Layer 2: API Layer

### 5.1 Responsibility

```
Unified API gateway handling authentication, routing, and rate limiting.
```

### 5.2 Why This Layer Is Needed

```
Problem: Need a unified security boundary

Without API Layer:
  - Each service handles authentication separately
  - No unified rate limiting
  - Logs are scattered

With API Layer:
  - Authenticate once, trust everywhere
  - Unified rate limiting strategy
  - Centralized access logs
```

### 5.3 Components

```
+---------------------------------------------------------------------------+
|                       API LAYER                                            |
|                                                                            |
|  +---------------------------------------------------------------+       |
|  |                    API Gateway                                  |       |
|  |                                                                 |       |
|  |  +-----------+ +-----------+ +-----------+                      |       |
|  |  |   Auth    | |  Router   | |Rate Limit |                      |       |
|  |  |           | |           | |           |                      |       |
|  |  |- JWT      | |- Path     | |- Per user |                      |       |
|  |  |  validate | |  mapping  | |- Per IP   |                      |       |
|  |  |- API Key  | |- Version  | |- Per API  |                      |       |
|  |  |- Device   | |  mgmt     | |           |                      |       |
|  |  |  Token    | |           | |           |                      |       |
|  |  +-----------+ +-----------+ +-----------+                      |       |
|  |                                                                 |       |
|  |  +-----------+ +-----------+                                    |       |
|  |  | Validator | |  Logger   |                                    |       |
|  |  |           | |           |                                    |       |
|  |  |- Schema   | |- Access   |                                    |       |
|  |  |- Sanitize | |- Audit    |                                    |       |
|  |  +-----------+ +-----------+                                    |       |
|  +---------------------------------------------------------------+       |
|                                                                            |
|  +---------------------------------------------------------------+       |
|  |                 WebSocket Gateway                               |       |
|  |                                                                 |       |
|  |  - Long-lived connection management                             |       |
|  |  - Real-time message push                                       |       |
|  |  - Presence (online status)                                     |       |
|  +---------------------------------------------------------------+       |
+---------------------------------------------------------------------------+
```

### 5.4 Authentication Methods

| Caller | Auth Method | Token Format |
|--------|----------|-----------|
| Web user | JWT | `Bearer eyJ...` |
| API client | API Key | `Bearer vibe_xxx` |
| Device | Device Token | `Bearer vibe_dev_xxx` |
| Internal service | Service Token | `Internal xxx` |

---

## 6. Layer 3: Coordination Layer

### 6.1 Responsibility

```
Message routing and Agent scheduling -- the core of Human-Agent collaboration.
```

### 6.2 Why This Layer Is Needed

```
Problem: Humans and Agents need coordination

Core challenges:
  - A message arrives -- who should respond?
  - If an Agent, which Agent?
  - If multiple Agents could respond, which one?
  - What if the Agent is busy?

If this logic lived in the Thread Engine:
  - Thread Engine becomes overly complex
  - Agent scheduling logic is coupled with message storage

Independent Coordination Layer:
  - Clean routing logic
  - Agent scheduling can be optimized independently
  - Easy to extend with new routing rules
```

### 6.3 Components

```
+---------------------------------------------------------------------------+
|                   COORDINATION LAYER                                       |
|                                                                            |
|  +---------------------------------------------------------------+       |
|  |                   Orchestrator                                  |       |
|  |                                                                 |       |
|  |  +---------------------------------------------------+        |       |
|  |  |              Message Router                         |        |       |
|  |  |                                                     |        |       |
|  |  |  Input: Message                                     |        |       |
|  |  |  Logic:                                             |        |       |
|  |  |    1. Is there an @mention? -> Route to that Agent  |        |       |
|  |  |    2. Need AI response? -> Intent classification    |        |       |
|  |  |    3. Select appropriate Agent                      |        |       |
|  |  |    4. Or don't respond (pure human conversation)    |        |       |
|  |  |  Output: Route Decision                             |        |       |
|  |  +---------------------------------------------------+        |       |
|  |                                                                 |       |
|  |  +---------------------------------------------------+        |       |
|  |  |              Agent Scheduler                        |        |       |
|  |  |                                                     |        |       |
|  |  |  Input: Agent type + task                           |        |       |
|  |  |  Logic:                                             |        |       |
|  |  |    1. Find available instances of that Agent type   |        |       |
|  |  |    2. Check load and health status                  |        |       |
|  |  |    3. Select optimal instance                       |        |       |
|  |  |    4. If all busy, add to queue                     |        |       |
|  |  |  Output: Agent Instance + Task                      |        |       |
|  |  +---------------------------------------------------+        |       |
|  |                                                                 |       |
|  |  +---------------------------------------------------+        |       |
|  |  |              Event Dispatcher                       |        |       |
|  |  |                                                     |        |       |
|  |  |  Responsibilities:                                  |        |       |
|  |  |    - Distribute system events                       |        |       |
|  |  |    - Trigger Agent proactive behavior               |        |       |
|  |  |    - Webhook callbacks                              |        |       |
|  |  +---------------------------------------------------+        |       |
|  +---------------------------------------------------------------+       |
+---------------------------------------------------------------------------+
```

### 6.4 Routing Decision Logic

```typescript
interface RouteDecision {
  shouldRespond: boolean;

  // If response is needed
  agents?: {
    agentType: string;      // e.g., "@Scheduler"
    priority: "high" | "normal" | "low";
    context: AgentContext;
  }[];

  // Optional human escalation
  humanEscalation?: {
    reason: string;
    to: string[];
  };
}

function routeMessage(message: Message, thread: Thread): RouteDecision {
  // 1. Explicit @mention
  if (message.mentions.length > 0) {
    return {
      shouldRespond: true,
      agents: message.mentions.map(m => ({
        agentType: m,
        priority: "high",
        context: buildContext(thread, message)
      }))
    };
  }

  // 2. Intent detection
  const intent = classifyIntent(message.content);

  if (intent.needsAgent) {
    return {
      shouldRespond: true,
      agents: [{
        agentType: intent.suggestedAgent,
        priority: "normal",
        context: buildContext(thread, message)
      }]
    };
  }

  // 3. Pure human conversation, no response needed
  return { shouldRespond: false };
}
```

---

## 7. Layer 4: Core Services

### 7.1 Responsibility

```
Core business logic: Thread management, Agent execution, device management.
```

### 7.2 Three Core Services

```
+---------------------------------------------------------------------------+
|                     CORE SERVICES                                          |
|                                                                            |
|  +-----------------+ +-----------------+ +-----------------+              |
|  |  THREAD ENGINE  | |  AGENT RUNTIME  | | DEVICE SERVICE  |              |
|  |                 | |                 | |                 |              |
|  |  Manage convo   | |  Execute AI     | |  Manage hardware|              |
|  |  structure      | |  tasks          | |  devices        |              |
|  +-----------------+ +-----------------+ +-----------------+              |
+---------------------------------------------------------------------------+
```

---

### 7.3 Thread Engine

**Maps to requirements: R4 (Conversation branching), R7 (Real-time collaboration)**

```
Responsibilities:
  - Space management (create, configure, members)
  - Thread management (create, status, participants)
  - Feed management (message stream, real-time sync)
  - Branch/Merge (branching, merging)
```

**Data model:**

```
Space
  |
  +-- Thread (Topic)
  |       |
  |       +-- Branch: main
  |       |       +-- Feed: [Message, Message, ...]
  |       |
  |       +-- Branch: explore-option-a
  |       |       +-- Feed: [Message, Message, ...]
  |       |
  |       +-- Metadata
  |               +-- participants
  |               +-- status
  |               +-- memory_items (distilled knowledge)
  |
  +-- Thread ...
```

**Key operations:**

| Operation | Description | Analogy |
|------|------|------|
| `createThread` | Create new conversation | -- |
| `postMessage` | Send message | git commit |
| `createBranch` | Create branch from a message | git branch |
| `switchBranch` | Switch to viewing a branch | git checkout |
| `mergeBranch` | Merge a branch | git merge |

---

### 7.4 Agent Runtime

**Maps to requirements: R1 (Human-Agent same space), R8 (Extensible Agents)**

```
Responsibilities:
  - Agent lifecycle management
  - Task execution and isolation
  - Tool invocation
  - Memory access control
```

**Agent types:**

| Type | Description | Lifecycle | Example |
|------|------|----------|------|
| **Personal** | One per user | Permanent | My assistant |
| **Role** | Organizational role | Permanent | @CRO, @Scheduler |
| **Worker** | Temporary task | Destroyed on completion | Background research task |

**Execution model:**

```
+---------------------------------------------------------------------------+
|                     AGENT RUNTIME                                          |
|                                                                            |
|  +---------------------------------------------------------------+       |
|  |                    Agent Pool                                   |       |
|  |                                                                 |       |
|  |  +-----------+ +-----------+ +-----------+                      |       |
|  |  | Container | | Container | | Container |                      |       |
|  |  |           | |           | |           |                      |       |
|  |  | @Scheduler| | @CRO      | | @Support  |                      |       |
|  |  |           | |           | |           |                      |       |
|  |  | +-------+ | | +-------+ | | +-------+ |                      |       |
|  |  | | SOUL  | | | | SOUL  | | | | SOUL  | |                      |       |
|  |  | +-------+ | | +-------+ | | +-------+ |                      |       |
|  |  | +-------+ | | +-------+ | | +-------+ |                      |       |
|  |  | |Skills | | | |Skills | | | |Skills | |                      |       |
|  |  | +-------+ | | +-------+ | | +-------+ |                      |       |
|  |  | +-------+ | | +-------+ | | +-------+ |                      |       |
|  |  | |Memory | | | |Memory | | | |Memory | |                      |       |
|  |  | |Access | | | |Access | | | |Access | |                      |       |
|  |  | +-------+ | | +-------+ | | +-------+ |                      |       |
|  |  +-----------+ +-----------+ +-----------+                      |       |
|  +---------------------------------------------------------------+       |
|                                                                            |
|  Agents run in isolated containers, each with its own:                     |
|    - SOUL.md (identity definition)                                         |
|    - Skills (capability configuration)                                     |
|    - Memory Access (permission scope)                                      |
+---------------------------------------------------------------------------+
```

---

### 7.5 Device Service

**Maps to requirements: R10 (Device management), R3 (Multi-source)**

```
Responsibilities:
  - Device registration and authentication
  - Status monitoring (online/offline/healthy)
  - Capability declaration and management
  - Device assignment (bind to Space/User)
```

**Why Device is a First-Class Entity:**

```
Traditional approach: Device is just a data source
  Recording -> Data enters system -> Device disappears

Vibe AI approach: Device is a participant with identity
  - Can be assigned to a Space or User
  - Has status and health monitoring
  - Captured data is associated with the device
  - Supports remote commands
```

**Device data model:**

```typescript
interface Device {
  id: string;
  type: "vibe-bot" | "vibe-dot" | "board";

  // Identity
  name: string;
  serial: string;

  // Ownership
  workspaceId: string;
  assignedTo?: {
    type: "space" | "user" | "location";
    id: string;
  };

  // Capabilities
  capabilities: string[];

  // Status
  status: {
    online: boolean;
    health: "healthy" | "degraded" | "offline";
    lastSeen: Date;
  };

  // Location
  location?: {
    building?: string;
    room?: string;
  };
}
```

---

## 8. Layer 5: Memory Layer

### 8.1 Responsibility

```
Core data layer -- the most important part of the system.

All conversations, decisions, and knowledge flow into here,
and all queries and retrievals come from here.
```

### 8.2 Why Memory Has Its Own Layer

**Memory is the system's core asset (90% of value)**

```
Everything else can be swapped:
  - LLMs can be swapped (Claude <-> GPT)
  - Channels can be swapped (Slack <-> Web)
  - Agent definitions can be rewritten

Only Memory is cumulative and irreplaceable:
  - Stores all organizational knowledge
  - Becomes more valuable over time
  - Is the core reason for customer retention

Therefore Memory gets its own layer, designed with highest priority.
```

### 8.3 Components

```
+---------------------------------------------------------------------------+
|                      MEMORY LAYER                                          |
|                                                                            |
|  +---------------------------------------------------------------+       |
|  |                   Memory System                                 |       |
|  |                                                                 |       |
|  |  +-----------+ +-----------+ +-----------+                      |       |
|  |  |  Storage  | |  Vector   | |  Search   |                      |       |
|  |  |  Engine   | |  Index    | |  Engine   |                      |       |
|  |  |           | |           | |           |                      |       |
|  |  |- Structured| |- Embed   | |- Semantic |                      |       |
|  |  |- Relations | |- Similar-| |- Filter   |                      |       |
|  |  |- Transact- | |  ity     | |- Sort     |                      |       |
|  |  |  ions     | |           | |           |                      |       |
|  |  +-----------+ +-----------+ +-----------+                      |       |
|  |                                                                 |       |
|  |  +---------------------------------------------------+        |       |
|  |  |              Permission Control                     |        |       |
|  |  |                                                     |        |       |
|  |  |  - Hierarchical permissions                         |        |       |
|  |  |    (Workspace -> Space -> Thread)                   |        |       |
|  |  |  - Zoom Level filtering                             |        |       |
|  |  |  - Row Level Security                               |        |       |
|  |  +---------------------------------------------------+        |       |
|  +---------------------------------------------------------------+       |
|                                                                            |
|  Memory Hierarchy:                                                         |
|  +---------------------------------------------------------------+       |
|  | Workspace Memory (Global knowledge)                             |       |
|  |   +-- Space Memory (Department/project knowledge)               |       |
|  |       +-- Thread Memory (Conversation context)                  |       |
|  |           +-- Personal Memory (Private)                         |       |
|  +---------------------------------------------------------------+       |
+---------------------------------------------------------------------------+
```

### 8.4 Memory Item Structure

```typescript
interface MemoryItem {
  id: string;

  // Hierarchical ownership
  workspaceId: string;
  spaceId?: string;
  threadId?: string;

  // Type
  type: "decision" | "action_item" | "meeting_note" | "context" | "document";

  // Multi-level content (Zoom Levels)
  content: {
    l1: string;  // Executive: one sentence
    l2: string;  // Manager: structured summary
    l3: string;  // Full: complete content
  };

  // Vectors (semantic search)
  embeddings: {
    l1: number[];
    l2: number[];
    l3: number[];
  };

  // Entities (for filtering)
  entities: {
    people: string[];
    companies: string[];
    topics: string[];
  };

  // Source
  source: {
    type: "message" | "device" | "import";
    ref: string;
  };

  // Permissions
  visibility: "workspace" | "space" | "thread" | "personal";

  createdAt: Date;
  updatedAt: Date;
}
```

### 8.5 Zoom Levels Explained

Same data, different levels of detail:

```
Original data: 2-hour meeting

+---------------------------------------------------------------------------+
| L3 (Full) - Complete transcript                                            |
|                                                                            |
| [10,000 words, including every utterance, timestamps, speakers]            |
|                                                                            |
| Suitable for: Direct participants who need details                         |
+---------------------------------------------------------------------------+
                              |
                              v (compressed)
+---------------------------------------------------------------------------+
| L2 (Manager) - Structured summary                                          |
|                                                                            |
| Participants: Alice, Bob, Charlie                                          |
| Topic: Q1 pricing strategy                                                |
| Key discussion points:                                                     |
|   - Option A: 10% price increase                                          |
|   - Option B: Keep current pricing                                         |
| Decision: Chose Option A                                                   |
| Action Items:                                                              |
|   - Alice: Update price sheet                                              |
|                                                                            |
| [500 words]                                                                |
|                                                                            |
| Suitable for: Managers who need context                                    |
+---------------------------------------------------------------------------+
                              |
                              v (compressed)
+---------------------------------------------------------------------------+
| L1 (Executive) - One sentence                                              |
|                                                                            |
| "Q1 pricing strategy meeting decided on a 10% increase.                   |
|  Alice is responsible for execution."                                      |
|                                                                            |
| [50 words]                                                                 |
|                                                                            |
| Suitable for: Executives who only need conclusions                         |
+---------------------------------------------------------------------------+
```

---

## 9. Layer 6: Foundation Services

### 9.1 Responsibility

```
Base services that support the entire system.
```

### 9.2 Three Foundation Services

```
+---------------------------------------------------------------------------+
|                   FOUNDATION SERVICES                                      |
|                                                                            |
|  +-----------------+ +-----------------+ +-----------------+              |
|  |  CONFIG SVC     | |    IAM SVC      | |  INTEGRATION    |              |
|  |                 | |                 | |                 |              |
|  |  Industry       | |  Auth &         | |  External       |              |
|  |  configuration  | |  authorization  | |  systems        |              |
|  +-----------------+ +-----------------+ +-----------------+              |
+---------------------------------------------------------------------------+
```

---

### 9.3 Config Service

**Maps to requirement: R5 (Industry-configurable)**

```
Responsibilities:
  - 4-layer configuration management (Platform -> Template -> Workspace -> User)
  - Industry Template management
  - Admin Console support
```

**4-layer configuration:**

```
+---------------------------------------------------------------------------+
| Layer 1: Platform                                                          |
| Defined by Vibe, immutable                                                 |
| e.g. Security constraints, max token count                                 |
+---------------------------------------------------------------------------+
| Layer 2: Template                                                          |
| Industry template, can be locked                                           |
| e.g. HIPAA requirements for medical clinic                                 |
+---------------------------------------------------------------------------+
| Layer 3: Workspace                                                         |
| Admin configuration                                                        |
| e.g. Which Agents to enable, working hours                                 |
+---------------------------------------------------------------------------+
| Layer 4: User                                                              |
| Personal preferences (within Admin-allowed range)                          |
| e.g. Theme, notification settings                                          |
+---------------------------------------------------------------------------+
```

---

### 9.4 IAM Service

**Maps to requirement: R6 (Layered permissions)**

```
Responsibilities:
  - User authentication (login, SSO)
  - Role-based authorization (RBAC)
  - Workspace/Space membership management
  - Zoom Level control
```

**Permission model:**

```
User
  |
  +-- belongs_to -> Workspace
  |
  +-- has_role -> Role (physician, front_desk, admin)
  |                 |
  |                 +-- zoom_level: 3
  |                 +-- agents_access: [@Scheduler, @Insurance]
  |                 +-- permissions: [memory:read, thread:create]
  |
  +-- member_of -> Space[]
                    |
                    +-- Can only access Memory of Spaces they belong to
```

---

### 9.5 Integration Service

**Maps to requirement: R9 (External integrations)**

```
Responsibilities:
  - External system connectors
  - Data synchronization
  - API adaptation
```

**Integration architecture:**

```
+---------------------------------------------------------------------------+
|                   INTEGRATION SERVICE                                      |
|                                                                            |
|  +---------------------------------------------------------------+       |
|  |                  Integration Hub                                |       |
|  |                                                                 |       |
|  |  - Unified integration interface                                |       |
|  |  - Authentication management (OAuth, API Key)                   |       |
|  |  - Error handling and retries                                   |       |
|  +---------------------------------------------------------------+       |
|                          |                                                 |
|         +----------------+----------------+                                |
|         v                v                v                                |
|  +-----------+    +-----------+    +-----------+                           |
|  |    EHR    |    |    CRM    |    |    PM     |                           |
|  |           |    |           |    |           |                           |
|  | - Epic    |    |-Salesforce|    | - Procore |                           |
|  | - Cerner  |    | - HubSpot |    | - Monday  |                           |
|  +-----------+    +-----------+    +-----------+                           |
+---------------------------------------------------------------------------+
```

---

## 10. Data Flows

### 10.1 Complete Data Flow Diagram

```
+----------------------------------------------------------------------------+
|                                                                             |
|    [Bot]  [Dot]  [Slack]  [Web]                                            |
|      |      |       |       |                                               |
|      +------+-------+-------+                                               |
|                  |                                                           |
|                  v                                                           |
|          +--------------+                                                   |
|          |   CAPTURE    |  <- Standardize input                              |
|          +------+-------+                                                   |
|                 |                                                           |
|                 v                                                           |
|          +--------------+                                                   |
|          |     API      |  <- Authentication, routing                        |
|          +------+-------+                                                   |
|                 |                                                           |
|                 v                                                           |
|          +--------------+                                                   |
|          | COORDINATION |  <- Message routing, Agent scheduling              |
|          +------+-------+                                                   |
|                 |                                                           |
|    +------------+------------+                                              |
|    v            v            v                                              |
| +------+   +--------+   +--------+                                         |
| |Thread|   | Agent  |   | Device |  <- Core business                        |
| |Engine|   |Runtime |   |Service |                                         |
| +--+---+   +---+----+   +---+----+                                         |
|    |           |            |                                               |
|    +-----------+------------+                                               |
|                |                                                           |
|                v                                                           |
|          +--------------+                                                   |
|          |    MEMORY    |  <- Core data (90% of value)                       |
|          +------+-------+                                                   |
|                 |                                                           |
|    +------------+------------+                                              |
|    v            v            v                                              |
| +------+   +--------+   +--------+                                         |
| |Config|   |  IAM   |   |Integra-|  <- Supporting services                  |
| |      |   |        |   | tion   |                                         |
| +------+   +--------+   +--------+                                         |
|                                                                             |
+----------------------------------------------------------------------------+
```

### 10.2 Key Flows

| Flow | Path | Description |
|------|------|------|
| **Send message** | Capture -> API -> Coordination -> Thread -> Memory | User sends message, may trigger Agent |
| **Agent response** | Coordination -> Agent -> Memory -> Thread | Agent queries Memory, generates reply |
| **Device capture** | Capture -> Device -> Processing -> Thread -> Memory | Hardware recording becomes knowledge |
| **Memory query** | API -> Agent -> Memory | User asks question, retrieves answer |
| **Config change** | API -> Config -> Broadcast | Admin changes config, takes effect in real time |

---

## Summary

### From Requirements to Architecture

```
R1 (Human-Agent same space)    -> Unified message model + Coordination Layer
R2 (Organizational memory)     -> Independent Memory Layer
R3 (Multi-source)              -> Capture Layer abstraction
R4 (Conversation branching)    -> Git-like Thread Engine
R5 (Industry-configurable)     -> 4-layer config + Config Service
R6 (Layered permissions)       -> Zoom Levels + IAM Service
R7 (Real-time collaboration)   -> WebSocket + Realtime
R8 (Extensible Agents)         -> Agent Runtime + SOUL.md
R9 (External integrations)     -> Integration Service
R10 (Device management)        -> Device Service
```

### Core Architecture Principles

1. **Memory First** -- Memory is 90% of the value, gets its own layer
2. **Human-Agent Coordination** -- Coordination Layer handles routing
3. **Configuration as Adaptation** -- 4-layer config supports industry customization
4. **Data Standardization** -- Capture Layer isolates entry point complexity
5. **Agent Isolation** -- Containerized execution, secure and controllable

---

*Last updated: 2026-02-07*
*Status: Architecture Introduction - for review*
