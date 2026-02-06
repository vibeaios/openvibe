# Vibe AI Workspace - Design Specification

> Detailed design decisions and rationale

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Core Architecture Decisions](#2-core-architecture-decisions)
3. [Memory System](#3-memory-system)
4. [Agent Architecture](#4-agent-architecture)
5. [Thread Engine](#5-thread-engine)
6. [Device System](#6-device-system)
7. [Configuration System](#7-configuration-system)
8. [Vertical Adaptation](#8-vertical-adaptation)
9. [Data Flow Design](#9-data-flow-design)
10. [Security and Permissions](#10-security-and-permissions)

---

## 1. Design Philosophy

### 1.1 Core Principles

#### Memory First

**Why:** LLMs are a commodity and can be swapped at any time. Channels are a commodity -- Slack/Discord are interchangeable. Only Memory is a cumulative asset that becomes more valuable with use.

**Implication:**
- The Memory system is the architectural core; everything else is built around it
- Invest 90% of design effort in the Memory layer
- All data should ultimately flow into Memory

```
Value Distribution:
┌────────────────────────────────────────────────────────────┐
│ Memory System                                    90%       │
├────────────────────────────────────────────────────────────┤
│ Agent Definitions                           │    7%       │
├─────────────────────────────────────────────┼─────────────┤
│ Channel Integration              │    2%   │             │
├──────────────────────────────────┼─────────┼─────────────┤
│ Tools/Skills          │    1%    │         │             │
└──────────────────────────────────┴─────────┴─────────────┘
```

#### Configuration over Code

**Why:** Different industries need different Agents, workflows, and permissions, but the underlying capabilities are the same. Adapt through configuration rather than code.

**Implication:**
- One codebase serves all industries
- Industry differences are expressed through YAML configuration
- New industry = new configuration package, not new code

#### Device as Entity

**Why:** Vibe's hardware (Bot, Dot, Board) is not just a data source -- it is a participant with identity, capabilities, and state.

**Implication:**
- Devices have first-class status in the system
- They can be assigned, managed, and monitored
- Data captured by devices automatically flows into Memory

#### Layered Permissions

**Why:** Enterprises need fine-grained permission control, but this should not increase complexity for regular users.

**Implication:**
- 4-layer configuration: Platform -> Template -> Workspace -> User
- Admin controls the boundaries, User operates freely within those boundaries
- Permissions inherit downward, constraints propagate upward

---

### 1.2 Architecture Goals

| Goal | Description | Priority |
|------|------|--------|
| **Extensible** | New industry = new config, no code changes | P0 |
| **Data Sovereignty** | Users can choose where data is stored | P0 |
| **Developer Friendly** | Clear SDK and extension mechanisms | P1 |
| **Simple Operations** | Single monorepo, unified deployment process | P1 |
| **Performance** | Real-time collaboration, low latency | P1 |
| **Cost Controllable** | Token tracking, resource isolation | P2 |

---

## 2. Core Architecture Decisions

### 2.1 Why Monorepo

**Decision:** Use Nx to manage a single monorepo

**Alternatives Considered:**
- Polyrepo (separate repo per service)
- Turborepo
- Lerna

**Reasons for Choosing Nx:**

| Factor | Nx | Polyrepo | Turborepo |
|------|-----|----------|-----------|
| Code sharing | Native | Requires npm publish | Native |
| Dependency graph | Visualization | None | Basic |
| Code generation | Powerful | None | None |
| CI optimization | affected | Full build | affected |
| Learning curve | Medium | Low | Low |
| Enterprise readiness | Mature | Complex management | Limited features |

**Specific Advantages:**

1. **Unified version control**: All code in one commit, atomic changes
2. **Dependency graph visualization**: `nx graph` shows module relationships
3. **Affected optimization**: Only build/test impacted parts
4. **Code generators**: `nx g @vibe/vertical` generates industry template scaffolding

### 2.2 Why Separate apps/services/libs

**Decision:** Three-tier directory structure

```
apps/     # Deployable units
services/ # Business services
libs/     # Shared libraries
```

**Rationale:**

| Layer | Responsibility | Deployment | Dependency Direction |
|------|------|------|----------|
| **apps** | Entry points, assemble services | Directly deployed | Depends on services, libs |
| **services** | Business logic | Referenced by apps | Depends on libs |
| **libs** | Pure functions, types, utilities | Not independently deployed | Only depends on other libs |

**Benefits:**
- Clear dependency boundaries
- Prevents circular dependencies
- Facilitates code reuse

### 2.3 Why Supabase

**Decision:** Use Supabase as the primary database

**Alternatives Considered:**
- Self-hosted PostgreSQL
- PlanetScale (MySQL)
- MongoDB

**Reasons for Choosing Supabase:**

| Requirement | Supabase | Self-hosted PG | PlanetScale |
|------|----------|---------|-------------|
| Managed PostgreSQL | Built-in | Requires ops | MySQL |
| pgvector | Built-in | Requires installation | Not available |
| Row Level Security | Native | Requires configuration | Not available |
| Realtime subscriptions | Built-in | Requires additional setup | Not available |
| Auth | Built-in | Requires custom build | Not available |
| Storage | Built-in | Requires adding S3 | Not available |
| Quick start | Minutes | Days | Minutes |

**Future Migration Path:**
- Supabase runs standard PostgreSQL underneath
- Can migrate to self-hosted PG if needed
- Data format is not locked in

---

## 3. Memory System

### 3.1 Why Memory Is the Core

**Observation:** In AI products:
- LLMs can be swapped (Claude <-> GPT <-> Llama)
- Channels can be swapped (Slack <-> Discord <-> Teams)
- Agent definitions can be rewritten

**The only irreplaceable thing is Memory** -- the knowledge, decisions, and context a company accumulates.

**Data Flywheel:**
```
More usage -> More Memory -> Smarter AI -> More usage -> ...
```

**Business Significance:**
- Memory is the switching cost
- Memory is the moat
- Memory is the reason customers won't leave

### 3.2 Memory Hierarchy Design

```
┌───────────────────────────────────────────────────────────┐
│                  Workspace Memory                          │
│                  (Company/Organization level)               │
│                                                            │
│   ┌─────────────────────────────────────────────────────┐ │
│   │              Space Memory                            │ │
│   │              (Department/Project level)               │ │
│   │                                                      │ │
│   │   ┌───────────────────────────────────────────────┐ │ │
│   │   │           Thread Memory                       │ │ │
│   │   │           (Conversation level)                │ │ │
│   │   │                                               │ │ │
│   │   │   ┌─────────────────────────────────────────┐ │ │ │
│   │   │   │       Personal Memory                   │ │ │ │
│   │   │   │       (Personal/Private)                │ │ │ │
│   │   │   └─────────────────────────────────────────┘ │ │ │
│   │   └───────────────────────────────────────────────┘ │ │
│   └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

**Why 4 Layers:**

| Layer | Purpose | Permissions | Example |
|------|------|------|------|
| **Workspace** | Company-wide shared knowledge | All members can read | Company strategy, product docs |
| **Space** | Department/project knowledge | Space members | Marketing plans, project progress |
| **Thread** | Conversation context | Thread participants | Decisions from a specific discussion |
| **Personal** | Private memory | Owner only | Personal notes, drafts |

### 3.3 Zoom Level Design

**Problem:** Different roles need different levels of detail

**Solution:** Permission Zoom Level

```
Raw Data (Full Resolution)
Meeting recording: 2-hour full transcript
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Zoom L1 │ │ Zoom L2 │ │ Zoom L3 │
│Executive│ │ Manager │ │   IC    │
│         │ │         │ │         │
│1-paragraph│ │Structured│ │Full     │
│ summary  │ │ summary  │ │record   │
│Key       │ │Action    │ │All      │
│decisions │ │Items     │ │details  │
│          │ │          │ │Raw      │
│ ~100     │ │ ~500     │ │convo    │
│ words    │ │ words    │ │~5000    │
│          │ │          │ │words    │
└─────────┘ └─────────┘ └─────────┘
```

**Implementation:**
```typescript
interface MemoryItem {
  content: {
    l1: string;  // Executive summary
    l2: string;  // Manager detail
    l3: string;  // Full content
  };
  embedding: {
    l1: number[];  // Embedding per level
    l2: number[];
    l3: number[];
  };
}
```

**Why:**
- Executives don't need to read a 2-hour meeting transcript
- Managers need action items and conclusions
- ICs may need the full context
- Same data, different views

### 3.4 Pluggable Storage

**Requirement:** Different deployment scenarios need different storage backends

**Design:**
```
┌───────────────────────────────────────────────────────┐
│                 Unified Memory API                     │
│                                                        │
│  • query(filters, zoom_level)                         │
│  • write(item)                                        │
│  • search(embedding, top_k)                           │
│  • sync(remote)                                       │
└───────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
 │  PostgreSQL │  │   SQLite    │  │    File     │
 │  + pgvector │  │ + sqlite-vec│  │   System    │
 │             │  │             │  │             │
 │  Cloud/VPS  │  │   Local     │  │  OpenClaw   │
 │  Multi-user │  │  Single-user│  │  Compatible │
 └─────────────┘  └─────────────┘  └─────────────┘
```

**Scenario Mapping:**

| Scenario | Storage Backend | Rationale |
|------|----------|------|
| SaaS multi-tenant | PostgreSQL + pgvector | Performance, concurrency |
| Local desktop | SQLite + sqlite-vec | Lightweight, no server required |
| OpenClaw compatible | File (.md) | Interoperable with existing tools |
| Offline/Air-gap | Local PostgreSQL | Data never leaves the network |

---

## 4. Agent Architecture

### 4.1 Agent Types

```
┌──────────────────────────────────────────────────────────────┐
│                      Agent Types                              │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Personal   │  │    Role     │  │   Worker    │          │
│  │   Agent     │  │   Agent     │  │   Agent     │          │
│  │             │  │             │  │             │          │
│  │ 1:1 with   │  │ Company role│  │ Task-based  │          │
│  │ user       │  │ @CRO @PMM   │  │ Created     │          │
│  │ Private    │  │ Shared      │  │ on demand   │          │
│  │ Memory     │  │ Memory      │  │ Destroyed   │          │
│  │ Personalized│  │             │  │ on complete │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

**Why Three Types:**

| Type | Purpose | Lifecycle | Memory Access |
|------|------|----------|-------------|
| **Personal** | Personal assistant | Permanent | Personal + Shared within permission scope |
| **Role** | Company role (CRO, PMM) | Permanent | Workspace + related Spaces |
| **Worker** | One-off task | Temporary | Task-relevant scope only |

### 4.2 Containerized Agents

**Decision:** Each Agent runs in an isolated container

**Why:**
- **Isolation**: One Agent crashing doesn't affect others
- **Security**: Restricted resource access
- **Scalability**: Can scale horizontally
- **Cost**: Start/stop on demand, saving resources

**Architecture:**
```
┌──────────────────────────────────────────────────────┐
│                   Agent Pool                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Container 1 │  │ Container 2 │  │ Container N │   │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │   │
│  │ │OpenClaw │ │  │ │OpenClaw │ │  │ │OpenClaw │ │   │
│  │ └────┬────┘ │  │ └────┬────┘ │  │ └────┬────┘ │   │
│  │      │      │  │      │      │  │      │      │   │
│  │ ┌────▼────┐ │  │ ┌────▼────┐ │  │ ┌────▼────┐ │   │
│  │ │ Memory  │ │  │ │ Memory  │ │  │ │ Memory  │ │   │
│  │ │ Mount   │ │  │ │ Mount   │ │  │ │ Mount   │ │   │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │      Team Memory        │
              │   (Mounted Read-Only)   │
              └─────────────────────────┘
```

### 4.3 Orchestrator Design

**Responsibilities:**
- Message routing (who handles this message)
- Agent scheduling (which Agent instance to use)
- Load balancing
- Failure recovery

**Routing Logic:**
```typescript
function routeMessage(message: Message): RouteDecision {
  // 1. Explicit @ mention
  if (message.mentions.length > 0) {
    return { targets: message.mentions, priority: 'high' };
  }

  // 2. Auto-route based on content
  const intent = classifyIntent(message.content);
  if (intent === 'coding') {
    return { targets: [{ type: 'coder' }] };
  }

  // 3. Default: do not auto-respond
  return { targets: [], requiresResponse: false };
}
```

---

## 5. Thread Engine

### 5.1 Git-like Conversations

**Core Concept:** Apply Git's version control concepts to conversations

**Why:**
- Conversations often need to "explore different directions"
- Need to "go back to a previous point and start over"
- Need to "merge conclusions from multiple discussions"
- Git has already solved these problems

**Operation Mapping:**

| Git Operation | Thread Operation | User Scenario |
|----------|-------------|----------|
| commit | reply | Normal reply |
| branch | branch | Explore a different direction from a point |
| checkout | switch | Switch to view a different branch |
| merge | merge | Merge branch discussion back to main |
| diff | diff | Compare discussions across two branches |
| log | history | View complete conversation history |

### 5.2 Data Model

```typescript
interface Message {
  id: string;
  threadId: string;
  parentId: string | null;  // Linked list structure
  branchId: string;
  author: Author;
  content: Content;
  timestamp: number;
  metadata: {
    branchPoint?: boolean;
    mergedFrom?: string[];
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
  name: string;
  headMessageId: string;
  baseMessageId: string;  // Which message it branched from
  createdBy: Author;
}
```

### 5.3 Merge Strategies

**Problem:** Conversations are not like code -- there are no real "conflicts"

**Solutions:**

| Strategy | Description | Use Case |
|------|------|----------|
| **Append** | Simply append both branches, marking sources | Exploratory discussions |
| **Summary** | AI generates a merge summary as the merge commit | Decision-oriented discussions |
| **Manual** | User manually selects content to keep | Fine-grained control |

---

## 6. Device System

### 6.1 Device as First-Class Entity

**Traditional approach:** Devices are just "data sources" -- after recording, data enters the system

**Our approach:** Devices are participants with identity, capabilities, and state

**Why:**
- Vibe's hardware is a core competitive advantage
- Devices need to be managed, assigned, and monitored
- Data produced by devices needs to be associated with the device
- Supports more complex device interactions in the future

### 6.2 Device Data Model

```typescript
interface Device {
  id: string;
  type: "vibe-bot" | "vibe-dot" | "board" | "external";

  // Identity
  name: string;
  serial?: string;

  // Ownership
  workspaceId: string;
  assignedTo?: {
    type: "space" | "user" | "location";
    id: string;
  };

  // Capabilities
  capabilities: DeviceCapability[];

  // Status
  status: {
    online: boolean;
    lastSeen: Date;
    health: "healthy" | "degraded" | "offline";
  };

  // Location
  location?: {
    building?: string;
    floor?: string;
    room?: string;
  };
}

type DeviceCapability =
  | "audio_capture"
  | "video_capture"
  | "transcription"
  | "speaker_id"
  | "screen_share"
  | "whiteboard"
  | "realtime_translate"
  | "meeting_summary";
```

### 6.3 Device Management Scenarios

**Medical Clinic:**
```yaml
devices:
  - id: bot-frontdesk
    type: vibe-bot
    location: "Front Desk"
    assignedTo:
      type: space
      id: waiting-room
    capabilities: [audio_capture, transcription, check_in]

  - id: dot-dr-smith
    type: vibe-dot
    assignedTo:
      type: user
      id: dr-smith
    capabilities: [audio_capture, transcription, meeting_summary]
```

**Construction Site:**
```yaml
devices:
  - id: bot-trailer
    type: vibe-bot
    location: "Site Trailer"
    assignedTo:
      type: location
      id: job-site-123
    capabilities: [audio_capture, transcription, safety_alerts]
```

---

## 7. Configuration System

### 7.1 4-Layer Configuration

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Platform Defaults                                   │
│ (Defined by us, inherited by everyone)                       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Industry Template                                   │
│ (Industry template, e.g. medical-clinic)                     │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Workspace Config                                    │
│ (Admin configuration, e.g. Downtown Clinic)                  │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: User Preferences                                    │
│ (Personal preferences, within Admin-allowed boundaries)      │
└─────────────────────────────────────────────────────────────┘
```

**Why 4 Layers:**
- **Platform**: Ensures baseline consistency and security
- **Template**: Industry best practices, works out of the box
- **Workspace**: Admin customizes to organizational needs
- **User**: Personalization, but within boundaries

### 7.2 Configuration Inheritance and Overrides

```yaml
# Layer 1: Platform Defaults
platform:
  agents:
    max_concurrent: 10
    timeout_sec: 300

# Layer 2: Industry Template (medical-clinic)
vertical:
  extends: platform
  agents:
    available: ["@Scheduler", "@FollowUp", "@Insurance"]
  compliance:
    hipaa: required
  workflows:
    check_in:
      locked: true  # Cannot be modified

# Layer 3: Workspace Config
workspace:
  extends: medical-clinic
  agents:
    enabled: ["@Scheduler", "@Insurance"]
    config:
      "@Scheduler":
        working_hours: "08:00-17:00"
  user_override:
    theme: allowed
    agents: within_role  # Can only select within role scope

# Layer 4: User Preferences
user:
  role: front_desk
  preferences:
    theme: "dark"
    agents_pinned: ["@Scheduler"]
```

### 7.3 Override Permission Control

```typescript
interface ConfigItem {
  value: any;

  // Who can edit
  editable_by: "platform" | "template" | "admin" | "user";

  // Whether locked (lower layers cannot modify)
  locked: boolean;

  // User override policy
  user_override: "allowed" | "forbidden" | "within_options";

  // If within_options, available choices
  options?: any[];
}
```

---

## 8. Vertical Adaptation

### 8.1 Industry Difference Analysis

| Dimension | Medical Clinic | PI Lawyer | Construction |
|------|----------------|-----------|--------------|
| **Core Unit** | Patient/Encounter | Case | Project/Phase |
| **Compliance** | HIPAA strict | Attorney privilege | OSHA/Safety |
| **Workflows** | Locked examination process | Flexible | Document-driven |
| **Device Scenarios** | Front desk Bot | Meeting recording | Job site Bot |
| **External Systems** | EHR | Legal CRM | Project management |

### 8.2 Template Structure

```
verticals/medical-clinic/
├── agents/
│   ├── scheduler.md      # @Scheduler Agent SOUL
│   ├── followup.md       # @FollowUp Agent SOUL
│   ├── insurance.md      # @Insurance Agent SOUL
│   └── concierge.md      # @Concierge Agent SOUL
│
├── skills/
│   ├── ehr-integration/  # EHR integration skill
│   ├── hipaa-guard/      # HIPAA compliance check
│   └── appointment/      # Appointment management
│
├── thread-types/
│   ├── patient-encounter.yaml   # Patient visit thread
│   ├── insurance-auth.yaml      # Insurance authorization thread
│   └── followup-sequence.yaml   # Follow-up sequence thread
│
├── roles/
│   ├── physician.yaml    # Physician role permissions
│   ├── front-desk.yaml   # Front desk role permissions
│   └── billing.yaml      # Billing role permissions
│
├── workflows/
│   ├── check-in.yaml     # Check-in process (locked)
│   └── prescription.yaml # Prescription process (locked)
│
└── config.yaml           # Industry configuration overview
```

### 8.3 Why Separate agents/skills/workflows

| Component | Responsibility | Customizability |
|------|------|----------|
| **Agents** | WHO -- who handles it | Admin can enable/disable |
| **Skills** | HOW -- how to handle it | Developer extensible |
| **Workflows** | WHAT -- process steps | Partially locked |
| **Thread Types** | CONTEXT -- conversation structure | Defined by Template |
| **Roles** | PERMISSION -- who can do what | Configured by Admin |

---

## 9. Data Flow Design

### 9.1 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA CAPTURE                           │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Vibe Bot │  │Vibe Dot │  │  Slack  │  │  Web UI │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       └───────────┴────────────┴────────────┘               │
│                          │                                   │
│                  services/devices/capture                    │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                        PROCESS                                │
│                                                               │
│  Transcription → Summary → Entity Extraction → Embedding     │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Input: 2-hour meeting audio                              │ │
│  │ Output:                                                  │ │
│  │   - L3: Full transcript                                  │ │
│  │   - L2: Structured summary + action items                │ │
│  │   - L1: One-paragraph summary + key decisions            │ │
│  │   - Entities: People, companies, topics                  │ │
│  │   - Embeddings: Vectors per level                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     STORE (Memory)                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Workspace Memory                                          │ │
│  │  └─ Space Memory (by department/project)                  │ │
│  │      └─ Thread Memory                                     │ │
│  │          └─ Personal Memory                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  + Vector Index (RAG)                                        │
│  + Metadata Index (search)                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                         QUERY                                 │
│                                                               │
│  User: "@CRO What was discussed in last week's meeting       │
│         with Acme?"                                          │
│                                                               │
│  1. Permission check (which Memory the user can access)      │
│  2. Zoom Level filter (how much detail the user can see)     │
│  3. Memory retrieval (semantic search + filters)             │
│  4. RAG augmentation (relevant context)                      │
│  5. Agent synthesizes answer                                 │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                          ACT                                  │
│                                                               │
│  Agent performs actions:                                      │
│  - Send email                                                │
│  - Update CRM                                                │
│  - Create task                                               │
│  - Write new Memory                                          │
└──────────────────────────────────────────────────────────────┘
```

### 9.2 Real-time Sync

**Using Supabase Realtime:**

```typescript
// Subscribe to Thread updates
supabase
  .channel(`thread:${threadId}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'messages',
    filter: `thread_id=eq.${threadId}`
  }, (payload) => {
    addMessage(payload.new);
  })
  .subscribe();

// Subscribe to Device status
supabase
  .channel(`devices:${workspaceId}`)
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'devices'
  }, (payload) => {
    updateDeviceStatus(payload.new);
  })
  .subscribe();
```

---

## 10. Security and Permissions

### 10.1 Authentication

**MVP: Supabase Auth**
- Email/Password
- Google OAuth
- GitHub OAuth

**Future: Enterprise SSO**
- SAML 2.0
- OpenID Connect

### 10.2 Authorization Model

**Row Level Security (RLS):**

```sql
-- Users can only view data from their own Workspace
CREATE POLICY "Users can view own workspace"
ON memory_items FOR SELECT
USING (
  workspace_id IN (
    SELECT workspace_id FROM workspace_members
    WHERE user_id = auth.uid()
  )
);

-- Zoom Level filtering
CREATE POLICY "Users see appropriate zoom level"
ON memory_items FOR SELECT
USING (
  zoom_level <= (
    SELECT zoom_level FROM user_permissions
    WHERE user_id = auth.uid()
    AND space_id = memory_items.space_id
  )
);
```

### 10.3 API Key for Agents

```typescript
interface ApiKey {
  id: string;
  teamId: string;
  name: string;
  keyHash: string;      // bcrypt hash
  prefix: string;       // "vibe_" for identification
  permissions: string[];
  expiresAt?: Date;
}

// Usage: Authorization: Bearer vibe_xxxxx
```

### 10.4 Security Checklist

- [ ] All APIs require authentication
- [ ] RLS covers all tables
- [ ] API Keys use bcrypt hash
- [ ] HTTPS enforced
- [ ] Rate limiting to prevent brute force
- [ ] Audit log records sensitive operations
- [ ] Input validation to prevent injection
- [ ] Agent container resource limits

---

## Appendix: Open Questions

### Decisions Requiring Confirmation from Charles

1. **Number of Zoom Levels**: Are 3 levels enough, or do we need finer granularity?
2. **Memory Retention Period**: How long should the default retention be? Should enterprise plans retain data permanently?
3. **Agent Billing**: Per token or per task?
4. **Device Offline Handling**: How should data captured offline be synced?
5. **Multi-Workspace**: Can a single user belong to multiple Workspaces?
6. **Free Tier Limits**: How many users/Memory/Agents?

---

*Last updated: 2026-02-07*
*Status: Draft - pending review*
