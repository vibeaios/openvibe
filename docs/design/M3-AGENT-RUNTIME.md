> **SUPERSEDED**: This document is from the initial design phase. For implementation, refer to:
> - [`AGENT-DEFINITION-MODEL.md`](../research/phase-1.5/AGENT-DEFINITION-MODEL.md) — Agent config model
> - [`RUNTIME-ARCHITECTURE.md`](../research/phase-1.5/RUNTIME-ARCHITECTURE.md) — Runtime design

# M3: Agent Runtime (Containerized OpenClaw)

> Status: Draft | Priority: High | Dependency: M4

## Overview

Containerize OpenClaw so that each agent runs in an independent container with access to team memory, receiving tasks and returning results via API.

## Architecture

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
              │   (Shared Filesystem)   │
              └─────────────────────────┘
```

## Agent Configuration

```yaml
# agent-config.yaml
agent:
  id: "agent-coder-01"
  name: "Coder"
  type: "openclaw"

  # Base configuration
  model: "claude-sonnet-4-20250514"
  thinking: "low"

  # Memory configuration
  memory:
    team: "/team"        # Read-only team shared
    private: "/private"  # Read-write agent private

  # Skills
  skills:
    - coding-agent
    - github

  # Resource limits
  resources:
    cpu: "1"
    memory: "2Gi"
    timeout: 300  # Single task timeout (seconds)
```

## Container Definition

### Dockerfile

```dockerfile
FROM node:22-slim

# Install OpenClaw
RUN npm install -g openclaw

# Install common tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /agent

# Copy agent configuration
COPY agent-config.yaml /agent/config.yaml
COPY AGENTS.md SOUL.md /agent/

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

### entrypoint.sh

```bash
#!/bin/bash
set -e

# Initialize OpenClaw configuration
openclaw init --config /agent/config.yaml

# Start gateway (API mode)
openclaw gateway start --api-mode --port 8080

# Wait for tasks
exec openclaw agent listen
```

## API Interface

Agent containers expose an HTTP API for the Orchestration layer to call:

### Send Message to Agent

```
POST /api/message
{
  "threadId": "...",
  "branchId": "...",
  "message": {
    "content": "Write me a Python script...",
    "author": { "type": "human", "id": "charles", "name": "Charles" },
    "context": {
      "recentMessages": [...],  // Recent N messages for context
      "mentions": ["@agent-coder"]
    }
  }
}

Response:
{
  "status": "processing",
  "taskId": "task-xxx"
}
```

### Query Task Status

```
GET /api/task/:taskId

Response:
{
  "taskId": "task-xxx",
  "status": "completed",  // processing | completed | failed
  "result": {
    "content": "Here's the script I wrote...",
    "type": "code",
    "language": "python"
  },
  "duration": 12.5,
  "tokensUsed": 1500
}
```

### Agent Health Check

```
GET /api/health

Response:
{
  "status": "healthy",
  "uptime": 3600,
  "tasksCompleted": 42,
  "currentTask": null  // or task info
}
```

## Memory Mount Strategy

```
Container structure:
/agent/
├── config.yaml
├── AGENTS.md
├── SOUL.md
├── memory/           # Agent private (read-write)
│   └── agent-state.json
├── team/             # Team shared (read-only)
│   ├── context.md
│   ├── decisions/
│   └── docs/
└── workspace/        # Task working directory (read-write)
```

### Volume Mounts

```yaml
# docker-compose.yaml example
services:
  agent-coder:
    image: vibe-ai/agent:latest
    volumes:
      - team-memory:/agent/team:ro        # Read-only shared
      - agent-coder-private:/agent/memory  # Private
      - agent-coder-workspace:/agent/workspace
    environment:
      - AGENT_ID=agent-coder-01
      - OPENCLAW_API_KEY=${OPENCLAW_API_KEY}
```

## Lifecycle Management

### Agent States

```typescript
type AgentState =
  | 'idle'        // Idle, waiting for tasks
  | 'processing'  // Processing a task
  | 'thinking'    // LLM inference in progress
  | 'executing'   // Executing tool calls
  | 'cooldown'    // Task complete, cooling down
  | 'error'       // Error state
  | 'offline';    // Container stopped
```

### Auto-scaling

```typescript
interface ScalingPolicy {
  minAgents: 1;           // Minimum 1 maintained
  maxAgents: 10;          // Maximum 10
  scaleUpThreshold: 0.8;  // Scale up at 80% busy
  scaleDownThreshold: 0.2; // Scale down at 20% busy
  cooldownPeriod: 300;    // Scale-down cooldown period (seconds)
}
```

## Agent Type Templates

### Coder Agent

```yaml
agent:
  id: "coder"
  specialization: "coding"
  skills: [coding-agent, github]
  systemPrompt: |
    You are a coding specialist. Focus on:
    - Writing clean, tested code
    - Following project conventions
    - Explaining your decisions
```

### Researcher Agent

```yaml
agent:
  id: "researcher"
  specialization: "research"
  skills: [web_search, web_fetch]
  systemPrompt: |
    You are a research specialist. Focus on:
    - Finding relevant information
    - Synthesizing sources
    - Citing references
```

### Writer Agent

```yaml
agent:
  id: "writer"
  specialization: "writing"
  skills: []
  systemPrompt: |
    You are a writing specialist. Focus on:
    - Clear, concise communication
    - Proper formatting
    - Audience awareness
```

## Deployment Options

### Option A: Docker Compose (Development / Small Scale)

```yaml
services:
  agent-1:
    image: vibe-ai/agent:latest
    # ...
  agent-2:
    image: vibe-ai/agent:latest
    # ...
```

### Option B: Kubernetes (Production)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-pool
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vibe-agent
  template:
    spec:
      containers:
      - name: agent
        image: vibe-ai/agent:latest
        resources:
          limits:
            cpu: "1"
            memory: "2Gi"
```

### Option C: Fly.io (Quick Start)

```toml
# fly.toml
app = "vibe-agent"

[build]
  image = "vibe-ai/agent:latest"

[[services]]
  internal_port = 8080
  protocol = "tcp"

[mounts]
  source = "agent_data"
  destination = "/agent"
```

## Security Considerations

1. **Network isolation**: Agent containers can only access necessary networks
2. **Secrets management**: API keys injected via environment variables, not baked into images
3. **Resource limits**: CPU/Memory limits to prevent runaway processes
4. **Execution sandbox**: Dangerous commands are restricted (similar to DCG)
5. **Audit logging**: All operations are recorded

## MVP Scope

**Phase 1 (Must have)**:
- [ ] Single agent Dockerfile
- [ ] Basic API (message, health)
- [ ] Memory mount working
- [ ] Docker Compose running locally

**Phase 2 (Important)**:
- [ ] Multi-agent templates
- [ ] State management API
- [ ] Fly.io deployment
- [ ] Auto-restart

**Phase 3 (Scale)**:
- [ ] Auto-scaling
- [ ] K8s deployment
- [ ] Agent monitoring dashboard
- [ ] Cost tracking

## Open Questions

1. **Agent reuse**: One container handles multiple tasks vs new container per task?
2. **Context length**: How many historical messages to pass to the agent?
3. **Tool permissions**: Different agents get different tool permissions?
4. **Log retention**: How long to keep logs?

---

*To be refined after Charles confirms*
