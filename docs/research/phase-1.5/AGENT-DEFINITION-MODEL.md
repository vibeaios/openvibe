# Agent Definition & Configuration Model

> Status: Complete | Researcher: agent-designer | Date: 2026-02-07

---

## Research Question

How should agents be defined, configured, and invoked in OpenVibe's MVP? What distinguishes an agent from a user? How does the configuration model relate to the existing OpenClaw pattern (SOUL.md, MEMORY.md, AGENTS.md)? What specific agents ship with the dogfood, and how does context assembly work per invocation?

---

## Sources Consulted

### Internal Design Documents
- `docs/research/SYNTHESIS.md` -- Fork/resolve model, revised module priorities, MVP scope, agent roster suggestions
- `docs/research/R3-AGENT-LIFECYCLE.md` -- Risk-based action classification, task lifecycle, cost model, framework comparison
- `docs/research/R4-CLAUDE-TEAMS.md` -- Claude Code SDK wrap+extend, AgentRuntime interface, context sharing analysis
- `docs/research/R7-CONTEXT-UNIFICATION.md` -- Context bus design, MCP server, minimum shared context (~4K tokens)
- `docs/research/phase-1.5/RUNTIME-ARCHITECTURE.md` -- Per-user runtime model, agent vs user runtime separation, MVP minimum
- `docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md` -- `agent_configs` table schema, agent integration layer, @mention pipeline
- `docs/design/M3-AGENT-RUNTIME.md` -- Original container-per-agent design, agent types (Coder/Researcher/Writer)
- `@claw/maxos/SOUL.md` -- OpenClaw personality definition pattern
- `@claw/maxos/AGENTS.md` -- OpenClaw workspace instructions, memory management, channel-aware context loading
- `@claw/maxos/MEMORY.md` -- OpenClaw long-term memory structure
- `@claw/maxos/OPENCLAW-CONFIG.md` -- OpenClaw workspace file injection, cross-system context sharing

### External Research
- [OpenAI Assistants API migration guide](https://platform.openai.com/docs/assistants/migration) -- Assistants deprecated Aug 2026, replaced by Responses API; Prompts hold config (model, tools, instructions); versioned in dashboard
- [Claude prompt engineering best practices](https://claude.com/blog/best-practices-for-prompt-engineering) -- System prompt as short contract: role (one line), goal, constraints, uncertainty handling, output format
- [Claude Code system prompts repository](https://github.com/Piebald-AI/claude-code-system-prompts) -- Claude Code subagent prompt patterns, lightweight vs heavyweight agents
- [Poe bot creation](https://creator.poe.com/docs/prompt-bots/how-to-create-a-prompt-bot) -- System prompt as personality, temperature as creativity dial, model selection per bot
- [Claude Skills explained](https://claude.com/blog/skills-explained) -- Skills as reusable prompt+tool packages, lighter than full agents
- [Custom GPT configuration patterns](https://help.openai.com/en/articles/8554397-creating-a-gpt) -- Name, instructions, conversation starters, knowledge files, capabilities toggles

---

## 1. What IS an Agent in OpenVibe

### Definition

An agent is a **configured AI identity** that can participate in conversations alongside humans. It is NOT a running process. It is a configuration record that, when invoked, produces an AI response within a specific context.

The key distinction between an agent and a user:

| Dimension | User | Agent |
|-----------|------|-------|
| **Identity source** | OAuth / email signup | Admin configuration |
| **Persistence** | Always exists | Exists as config; instantiated per task |
| **Autonomy** | Full (can do anything the UI allows) | Bounded by risk classification + capabilities |
| **Memory** | Personal (session preferences, read receipts) | Workspace-scoped (context items, thread history) |
| **Cost** | Infrastructure only | LLM tokens per invocation |
| **Invocation** | Self-initiated (types a message) | Triggered (@mention, fork resolution, system event) |
| **author_type** | `human` | `agent` |

An agent is closer to a "personality + capability template" than a running service. When someone types `@Coder fix the auth bug`, the system:
1. Looks up the `coder` agent configuration
2. Assembles context (thread history + user info + system prompt)
3. Makes an LLM API call with that configuration
4. Posts the response to the thread as the agent

The agent "exists" only during the LLM call. Between calls, it is a row in the `agent_configs` table.

### Agent Identity

Every agent has:

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Internal identifier | `assistant` |
| `slug` | @mention trigger | `assistant` (user types `@assistant`) |
| `display_name` | Shown in UI | `Assistant` |
| `avatar_url` | Visual identity | A distinct icon or generated avatar |
| `description` | One-line purpose | "General-purpose AI assistant for the team" |

### Agent Personality

An agent's personality is defined entirely by its **system prompt**. This is the single most important configuration field. It determines how the agent speaks, what it focuses on, how it handles uncertainty, and what it will and will not do.

The system prompt structure, informed by OpenClaw's SOUL.md and Claude prompt engineering best practices:

```
[IDENTITY]      Who you are (1-2 sentences)
[PURPOSE]       What you're for (1 sentence)
[CONSTRAINTS]   What you must/must not do (3-5 rules)
[TONE]          How you communicate (1-2 sentences)
[CONTEXT RULES] What context matters for your responses
```

This is NOT the full prompt sent to the LLM. The full prompt is assembled at invocation time: `system_prompt + workspace context + thread history + user message`. The system prompt is the stable, reusable identity layer.

### Agent Memory

For MVP, agents have **no persistent personal memory**. Each invocation starts fresh with:
- The agent's system prompt (from config)
- Thread history (from database)
- Workspace shared context (~4K tokens, from R7's minimum shared context)

This is a deliberate simplification. OpenClaw has MEMORY.md (persistent long-term memory) and daily logs. OpenVibe agents don't need this for MVP because:
- Thread history IS the memory (it's in the database, always available)
- Workspace context items serve as shared knowledge
- Per-agent memory adds complexity without clear benefit for a 20-person team where all agents serve the whole team, not individual users

**Post-MVP evolution:**
- Phase 4: `agent_memory` table -- per-agent accumulated knowledge (decisions made, patterns learned)
- Phase 5: Letta-style memory blocks -- agents actively manage their own context

### Agent Types for MVP

Three categories based on how they are triggered:

| Type | Trigger | Example |
|------|---------|---------|
| **@mention agent** | User explicitly invokes via `@name` | @Assistant, @Coder, @Researcher |
| **System agent** | Triggered by platform events | Fork resolution summary generator |
| **Background agent** | Triggered by conditions (future) | Thread summary when >20 messages (Phase 4) |

For MVP, only **@mention agents** and **system agents** exist. Background agents require monitoring infrastructure that is deferred.

---

## 2. MVP Agent Roster

### Why These Agents

SYNTHESIS.md suggests: @Assistant, @Coder, @Researcher, @Summarizer. After analysis, the roster is adjusted:

**Ship with 2 agents, not 4.** Reasoning:
- The Vibe team's immediate need is "better Slack," not a suite of specialized AI agents
- More agents = more configuration surface = more things that can be wrong
- A good general-purpose agent handles 80% of needs
- Specialization can be added in weeks 3-4 of dogfood based on actual usage patterns
- BACKEND-MINIMUM-SCOPE.md already designs for this: seed data includes 2-3 agent configs

### Agent 1: @Vibe (General Assistant)

**Purpose:** The primary AI teammate. Handles questions, analysis, writing, and general assistance. Named @Vibe to reinforce the product identity rather than the generic "Assistant."

**System Prompt:**
```
You are Vibe, the AI teammate for the Vibe team's collaboration platform.

PURPOSE: Help the team think, write, analyze, and make decisions. You participate in threads alongside humans.

CONSTRAINTS:
- Be direct and concise. Skip pleasantries.
- When you don't know something, say so. Don't fabricate.
- If a question is ambiguous, ask one clarifying question before answering.
- Never share information from other threads unless explicitly asked to search.
- When presenting decisions, show options with tradeoffs, not just recommendations.

TONE: Professional but not corporate. Like a sharp colleague, not a customer service bot. Match the formality of whoever is talking to you.

CONTEXT: You have access to this thread's history. Use it. Don't ask for information that was already discussed. If someone asks "what did we decide about X?" and it's in the thread, reference it directly.
```

**Configuration:**
| Field | Value |
|-------|-------|
| model | `claude-sonnet-4-5` |
| capabilities | `['general', 'analysis', 'writing', 'summarization']` |
| trigger | @mention (`@vibe`) |
| max_tokens | 4096 |
| temperature | 1.0 (Claude default, let the system prompt handle tone) |

**When it activates:** Any @vibe mention in any thread or fork.

**Context it receives:** System prompt + last 50 thread/fork messages + user identity (name, role).

### Agent 2: @Coder (Code Specialist)

**Purpose:** Handles code-related questions: reviewing code snippets, suggesting implementations, debugging, explaining technical concepts. Does NOT execute code (MVP limitation -- no Claude Code SDK integration yet).

**System Prompt:**
```
You are Coder, the Vibe team's code specialist.

PURPOSE: Help with code reviews, implementation suggestions, debugging, and technical architecture discussions. You work in conversation threads, not in an IDE.

CONSTRAINTS:
- Always include code in fenced code blocks with language tags.
- When reviewing code, focus on: correctness first, readability second, performance third.
- If asked to "write" something complex, provide the key implementation and explain the approach. Don't generate 500-line files in a chat thread.
- Be honest about language/framework limitations. If you're uncertain about a specific API version, say so.
- When suggesting fixes, explain WHY the current code is wrong, not just what to change.

TONE: Technical but accessible. Assume the reader is a competent developer but might not know the specific domain.

OUTPUT: Use markdown code blocks with language identifiers. For multi-file changes, clearly label each file. Keep explanations brief -- the code should speak for itself.
```

**Configuration:**
| Field | Value |
|-------|-------|
| model | `claude-sonnet-4-5` |
| capabilities | `['code', 'review', 'debugging', 'architecture']` |
| trigger | @mention (`@coder`) |
| max_tokens | 8192 (longer for code output) |
| temperature | 1.0 |

**When it activates:** Any @coder mention in any thread or fork.

**Context it receives:** System prompt + last 50 thread/fork messages + user identity.

### System Agent: Fork Resolver

**Purpose:** Generates resolution summaries when a fork is resolved. Not user-invokable -- triggered by the `fork.resolve` API call.

**System Prompt:**
```
You are a resolution summarizer. A team discussion happened in a side thread (fork). Your job is to distill it into a concise summary that captures:

1. CONCLUSION: What was decided or concluded (1-2 sentences)
2. KEY POINTS: The most important arguments or findings (2-4 bullet points)
3. ACTION ITEMS: Any next steps identified (if any)

RULES:
- Be factual. Only include what was actually discussed, not what you think should have been discussed.
- If the conversation ended without a clear conclusion, say so: "No clear conclusion reached. Key perspectives were: ..."
- Keep the total summary under 200 words.
- Do not add your own analysis or recommendations.
- If there was disagreement, represent both sides fairly.
```

**Configuration:**
| Field | Value |
|-------|-------|
| model | `claude-sonnet-4-5` (quality matters for summaries -- per SYNTHESIS.md) |
| capabilities | `['summarization']` |
| trigger | System event (fork.resolve) |
| max_tokens | 1024 |
| is_active | true (always available, not user-configurable) |

**Context it receives:** The parent message that the fork branched from + all messages in the fork + the fork description.

### Deferred Agents (Add Based on Dogfood Feedback)

| Agent | When to Add | Signal |
|-------|-------------|--------|
| **@Researcher** (web search, deep analysis) | Week 3-4 of dogfood | Team asks questions that need external information |
| **@Writer** (drafts, editing, messaging) | Week 4-5 | Team frequently asks @vibe to draft emails/docs |
| **Thread Summarizer** (background) | Phase 4 | Threads consistently exceed 20 messages |
| **Agent Suggester** (suggests forks) | Phase 4 | Fork adoption is high but discovery is low |

**Why not @Researcher on day 1:** Web search requires MCP tool integration. MVP agents use direct Claude API calls only. Adding MCP tools is Phase 4.

**Why not @Summarizer as a separate agent:** Fork resolution handles the summarization need. Thread-level summarization (for long linear threads) is a background trigger, not an @mention agent. Defer until threads actually get long during dogfood.

---

## 3. Agent Configuration Schema

### Storage: Database Records (Not Files)

OpenClaw uses markdown files (SOUL.md, MEMORY.md). OpenVibe agents are stored in the `agent_configs` database table. Why:

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Markdown files** (OpenClaw pattern) | Human-readable, version-controlled, agent can edit own config | No multi-user access, no real-time config changes, no workspace isolation | Reject for platform |
| **YAML files** | Structured, readable, declarative | Same as markdown + harder to render in admin UI | Reject |
| **Database records** | Multi-tenant, real-time updates, workspace isolation, queryable | Less human-readable, requires admin UI | **Adopt** |
| **Database + YAML seed** | Best of both: seed from YAML, manage in DB | Slight complexity for seeding | **Adopt for MVP** |

MVP approach: Define initial agents in a YAML seed file. Import into database on workspace creation. All subsequent changes happen via the `agent.*` tRPC endpoints (or directly in Supabase dashboard for dogfood).

### Complete Configuration Schema

```typescript
interface AgentConfig {
  // === Identity ===
  id: string;                    // UUID, auto-generated
  workspace_id: string;          // Which workspace this agent belongs to
  name: string;                  // Internal name: 'vibe', 'coder'
  slug: string;                  // @mention trigger: 'vibe', 'coder'
  display_name: string;          // UI display: 'Vibe', 'Coder'
  description: string;           // One-line purpose
  avatar_url?: string;           // Agent avatar (optional, generate default)

  // === Personality ===
  system_prompt: string;         // The core personality definition
  // No 'tone' or 'constraints' as separate fields -- everything is in system_prompt
  // This is intentional: the system prompt IS the personality, keeping it
  // as one text field gives maximum flexibility and avoids field proliferation

  // === Capabilities ===
  capabilities: string[];        // Tags: ['general', 'code', 'research', 'summarization']
  // For MVP, capabilities are descriptive only (no permission enforcement)
  // They're used for: UI display, future routing decisions, documentation

  // === Model ===
  model: string;                 // 'claude-sonnet-4-5' | 'claude-haiku-4-5' | 'claude-opus-4-6'
  max_tokens: number;            // Max response length (default: 4096)
  // No temperature field -- use Claude's default (1.0) for all agents
  // Reasoning: temperature tuning is a premature optimization that
  // creates more confusion than value for non-ML-engineers configuring agents

  // === Behavior ===
  is_active: boolean;            // Can this agent be invoked? (admin toggle)
  // trigger_conditions: deferred -- MVP only supports @mention
  // auto_join_channels: deferred -- all agents available in all channels

  // === Cost (tracking, not limits) ===
  // Per-invocation limits are NOT in config -- they're system-wide settings
  // Token usage is tracked in the tasks table, not agent_configs

  // === Metadata ===
  created_at: Date;
  updated_at: Date;
}
```

### What is NOT in the Schema (and Why)

| Field | Why Excluded |
|-------|-------------|
| `tools` / `mcp_servers` | MVP agents don't use tools. They're pure LLM text generation. Tool access is Phase 4 (MCP integration). |
| `allowed_actions` / `risk_classification` | MVP uses a global risk policy, not per-agent. All agents are read-only + text generation (AUTONOMOUS). No agent writes to external systems. |
| `temperature` | Creates false sense of control. Claude's default temperature works well. If an agent needs different behavior, adjust the system prompt. |
| `context_window_budget` | All agents use the same context assembly strategy. Per-agent budgets are optimization for later. |
| `trigger_conditions` | MVP is @mention only. Background triggers and channel auto-join are Phase 4. |
| `token_budget_per_task` | System-wide rate limiting, not per-agent. 20 trusted internal users don't need per-agent budgets. |
| `daily_limit` | Same reasoning as above. Track at workspace level, not agent level. |
| `version` | Deferred. MVP agents are mutable. Versioning matters when multiple workspaces customize agents simultaneously. |

### Seed Configuration (YAML)

```yaml
# seeds/agent-configs.yaml
# Imported into agent_configs table on workspace creation

agents:
  - name: vibe
    slug: vibe
    display_name: Vibe
    description: General-purpose AI teammate for questions, analysis, and writing
    model: claude-sonnet-4-5
    max_tokens: 4096
    capabilities: [general, analysis, writing, summarization]
    system_prompt: |
      You are Vibe, the AI teammate for the Vibe team's collaboration platform.

      PURPOSE: Help the team think, write, analyze, and make decisions. You participate in threads alongside humans.

      CONSTRAINTS:
      - Be direct and concise. Skip pleasantries.
      - When you don't know something, say so. Don't fabricate.
      - If a question is ambiguous, ask one clarifying question before answering.
      - Never share information from other threads unless explicitly asked to search.
      - When presenting decisions, show options with tradeoffs, not just recommendations.

      TONE: Professional but not corporate. Like a sharp colleague, not a customer service bot. Match the formality of whoever is talking to you.

      CONTEXT: You have access to this thread's history. Use it. Don't ask for information that was already discussed.

  - name: coder
    slug: coder
    display_name: Coder
    description: Code specialist for reviews, debugging, and technical discussions
    model: claude-sonnet-4-5
    max_tokens: 8192
    capabilities: [code, review, debugging, architecture]
    system_prompt: |
      You are Coder, the Vibe team's code specialist.

      PURPOSE: Help with code reviews, implementation suggestions, debugging, and technical architecture discussions. You work in conversation threads, not in an IDE.

      CONSTRAINTS:
      - Always include code in fenced code blocks with language tags.
      - When reviewing code, focus on: correctness first, readability second, performance third.
      - If asked to "write" something complex, provide the key implementation and explain the approach. Don't generate 500-line files in a chat thread.
      - Be honest about language/framework limitations.
      - When suggesting fixes, explain WHY the current code is wrong, not just what to change.

      TONE: Technical but accessible.

      OUTPUT: Use markdown code blocks with language identifiers. Keep explanations brief.

  - name: fork-resolver
    slug: _fork-resolver
    display_name: Fork Resolver
    description: System agent that generates resolution summaries for forks
    model: claude-sonnet-4-5
    max_tokens: 1024
    capabilities: [summarization]
    is_system: true  # Not user-invokable
    system_prompt: |
      You are a resolution summarizer. A team discussion happened in a side thread (fork). Distill it into a concise summary:

      1. CONCLUSION: What was decided or concluded (1-2 sentences)
      2. KEY POINTS: The most important arguments or findings (2-4 bullet points)
      3. ACTION ITEMS: Any next steps identified (if any)

      RULES:
      - Be factual. Only include what was actually discussed.
      - If no clear conclusion was reached, say so explicitly.
      - Keep the total summary under 200 words.
      - Do not add your own analysis or recommendations.
      - If there was disagreement, represent both sides fairly.
```

### Admin Configuration

For dogfood, agents are configured via:
1. **Seed data** (YAML above imported on first deployment)
2. **Supabase dashboard** (direct DB edits for quick changes)
3. **tRPC admin endpoints** (`agent.create`, `agent.update`, `agent.toggleActive`)

No admin console UI is built for MVP. An admin page with a form for editing agent configs is Phase 4 work (SYNTHESIS.md explicitly defers admin console).

### Versioning

**MVP: No versioning.** Updating an agent_config takes effect on the next invocation. In-flight tasks use the config that was loaded when the task started (the system prompt is captured in the task input, not re-fetched).

**Post-MVP versioning model:**
- `agent_config_versions` table with `version_number`, `system_prompt`, `model`, `updated_at`
- Each task records the `agent_config_version_id` used
- Admin can "publish" a new version or "rollback" to a previous one
- This is the OpenAI Prompts model: config versions are immutable snapshots, active version is a pointer

---

## 4. Agent Invocation Flow

### Step-by-Step: User types `@Vibe what's our deployment timeline?`

```
1. USER SENDS MESSAGE
   Browser: User types "@Vibe what's our deployment timeline?" in thread-5
   Client: Calls message.send tRPC mutation

2. MESSAGE SAVED + @MENTION DETECTED
   Server: Insert message into messages table
   Server: Parse content for @mentions using regex: /@(\w+)/g
   Server: Match 'vibe' against agent_configs.slug WHERE workspace_id = user's workspace
   Result: Found agent_config for 'vibe'
   Supabase Realtime: broadcasts message.created to all thread-5 subscribers

3. TASK CREATED
   Server: Insert task row:
     {
       workspace_id: workspace-1,
       thread_id: thread-5,
       fork_id: null,
       trigger_message_id: msg-123,
       agent_config_id: vibe-config-id,
       status: 'queued',
       task_type: 'message_response',
       input: { prompt: "what's our deployment timeline?", contextMessageIds: [...] }
     }
   Server: Return message + task to client immediately (don't wait for agent)
   Supabase Realtime: broadcasts task.status_changed (queued)
   Frontend: Shows "Vibe is thinking..." indicator

4. CONTEXT ASSEMBLY (the critical step -- see Section 5)
   Server (async): Load agent config (system_prompt, model, max_tokens)
   Server (async): Load thread context:
     - Last 50 messages from thread-5 (ordered by created_at)
     - If in a fork: parent message + all fork messages instead
   Server (async): Load user context:
     - Requesting user's name and role (for the agent to address them)
   Server (async): Assemble final prompt:
     system: agent.system_prompt
     messages: [
       { role: 'user', content: '[Thread context formatted as conversation]' },
       { role: 'user', content: 'Charles (admin) asks: what\'s our deployment timeline?' }
     ]

5. LLM API CALL
   Server: Update task.status = 'running'
   Server: Call anthropic.messages.create({
     model: agent.model,
     max_tokens: agent.max_tokens,
     system: assembled_system_prompt,
     messages: assembled_messages,
     stream: true
   })

6. RESPONSE STREAMING
   Server: Collect streamed tokens into full response
   (MVP: collect full response, then insert as message.
    Phase 2: insert empty message immediately, update via Realtime as tokens arrive)

7. RESPONSE POSTED
   Server: Insert agent message:
     {
       thread_id: thread-5,
       fork_id: null,
       parent_id: msg-123,
       author_id: vibe-config-id,
       author_type: 'agent',
       content: "Based on the thread discussion, our deployment timeline is...",
       metadata: { agentConfigId: vibe-config-id, taskId: task-123 }
     }
   Supabase Realtime: broadcasts message.created to all thread-5 subscribers
   Frontend: Renders agent message with distinct agent styling

8. TASK COMPLETED
   Server: Update task:
     {
       status: 'completed',
       completed_at: now(),
       token_usage: { input_tokens: 1234, output_tokens: 567, model: 'claude-sonnet-4-5' },
       output: { messageId: agent-msg-456, responseLength: 523 }
     }
   Supabase Realtime: broadcasts task.status_changed (completed)
   Frontend: Removes "thinking" indicator
```

### Error Cases

| Error | Detection | Behavior |
|-------|-----------|----------|
| **Agent not found** | @mention slug doesn't match any active agent | Ignore the @mention. The message is still posted as a normal message. No error shown -- the user might have @mentioned a human whose name happens to start with a capital letter. |
| **Anthropic API 500/503** | HTTP error response | Retry 3 times with exponential backoff (1s, 5s, 15s). If all fail, mark task as `failed`. Post system message: "Vibe couldn't respond. The AI service is temporarily unavailable." |
| **Rate limit (429)** | Anthropic returns `retry-after` header | Wait for specified duration, then retry. Update task metadata with wait time. |
| **Context too large** | Token count exceeds model's context window | Truncate oldest messages from context (keep last 20 instead of 50). Retry once. If still too large, summarize the thread context using Haiku before sending to the primary model. |
| **Response timeout (>120s)** | Timer exceeds threshold | Mark task as `failed`. Post system message: "Vibe's response timed out. The question may be too complex for a single response." |
| **Malformed response** | LLM returns empty or garbage | Mark task as `failed`. Post system message: "Vibe produced an unexpected response. Try rephrasing your question." |
| **Multiple agents mentioned** | Message contains `@vibe` and `@coder` | Create separate tasks for each agent. Both respond independently in the thread. No coordination between them. |
| **Agent mentioned in own response** | Agent output contains `@coder` | Do NOT trigger another agent invocation. Agent responses never trigger @mention detection. Only `author_type='human'` messages trigger agent invocations. |

---

## 5. Agent Context Assembly

This is the most important section. The quality of agent responses depends entirely on what context the agent receives.

### Context Layers

Every agent invocation assembles context from four layers:

```
LAYER 1: Agent Identity (stable, from config)
  = system_prompt from agent_configs table
  ~500-2000 tokens depending on agent

LAYER 2: Thread Context (dynamic, from messages table)
  = Recent messages in the conversation
  Variable: 1K-20K tokens depending on thread length

LAYER 3: User Context (lightweight, from users table)
  = Who is asking (name, role)
  ~50 tokens

LAYER 4: Workspace Context (future -- deferred for MVP)
  = Shared team knowledge, active decisions, project context
  ~4K tokens (from R7 estimate)
  NOT IMPLEMENTED in MVP -- see Post-MVP section
```

### Layer 1: Agent Identity

The system prompt from `agent_configs.system_prompt`. Injected as the `system` parameter in the Claude API call.

**Token budget: 500-2000 tokens.** Keep system prompts concise. The Claude prompt engineering guidance is clear: a system prompt should read like a short contract. OpenClaw's SOUL.md is ~400 tokens -- a good benchmark.

### Layer 2: Thread Context (the bulk of the context)

**Strategy: Last N messages with fork awareness.**

```typescript
async function assembleThreadContext(
  threadId: string,
  forkId: string | null,
  triggerMessageId: string
): Promise<ContextMessage[]> {

  if (forkId) {
    // In a fork: include the parent message + all fork messages
    const parentMsg = await getParentMessage(forkId);
    const forkMessages = await getMessagesByFork(forkId, { limit: 50 });
    return [
      { role: 'context', content: `[This conversation forked from: "${parentMsg.content.slice(0, 200)}..."]` },
      ...forkMessages.map(formatAsConversation)
    ];
  } else {
    // In main thread: last 50 messages
    const messages = await getMessagesByThread(threadId, {
      limit: 50,
      before: triggerMessageId,  // Don't include the trigger message
      order: 'asc'              // Chronological
    });
    return messages.map(formatAsConversation);
  }
}

function formatAsConversation(msg: Message): ContextMessage {
  const authorLabel = msg.author_type === 'agent'
    ? `${msg.metadata.agentDisplayName} (AI)`
    : `${msg.authorName}`;

  return {
    role: msg.author_type === 'human' ? 'user' : 'assistant',
    content: `[${authorLabel}]: ${msg.content}`
  };
}
```

**Why 50 messages?**
- 50 messages at ~100 tokens each = ~5K tokens. Well within budget.
- Covers most "recent discussion" context needs.
- If a thread has 200 messages, the oldest 150 are excluded. This is acceptable -- if the user needs the agent to know about something from message #15, they can quote it.

**Fork context assembly is different:**
- When the agent is invoked in a fork, it gets the parent message (the fork point) + all fork messages.
- This means the agent understands WHAT the fork is about (the parent message) and WHAT has been discussed in the fork.
- It does NOT get the full parent thread history. This is intentional: the fork is a focused side-discussion. Loading the entire parent thread would pollute the context with irrelevant information.

### Layer 3: User Context

Minimal but important for personalization:

```typescript
function buildUserContext(user: User, workspaceMember: WorkspaceMember): string {
  return `The person asking is ${user.name} (role: ${workspaceMember.role}).`;
}
```

This is injected as a prefix to the user's message, not as a separate system instruction. It lets the agent address the user by name and understand their authority level (admin can ask for config changes, member cannot).

**Token budget: ~50 tokens.** Keep it tiny.

### Layer 4: Workspace Context (Deferred)

R7 designs a full context bus with ~4K tokens of shared context (active tasks, recent decisions, project info, team members). This is NOT implemented for MVP.

**Why defer:**
- The 20-person Vibe team has shared context through their daily work. They don't need an AI to inject "who's on the team" into every prompt.
- Adding 4K tokens to every invocation costs ~$100/month in additional tokens (from R3 cost analysis).
- The workspace context system requires the `context_items` table to be populated, which requires agents or humans to actively write context items. No one will be doing this on day 1.

**When to add:**
- When users complain that agents "don't know about our project"
- When cross-runtime integration (OpenClaw) requires shared context
- When the team grows beyond people who all know each other

### Context Budget

For Claude Sonnet 4.5 with 200K context window:

| Layer | Tokens | % of Window |
|-------|--------|-------------|
| Agent system prompt | 500-2000 | ~1% |
| Thread context (50 messages) | 3000-8000 | ~2-4% |
| User context | 50 | <0.1% |
| **Total context** | **3500-10000** | **~2-5%** |
| Available for response | 4096-8192 | ~2-4% |
| **Unused** | **~180K** | **~90%** |

The context window is nowhere near full. This means:
- No context priority system needed for MVP
- No truncation logic needed for most cases
- The "context too large" error case only triggers for extremely long threads (500+ messages)

### Context Priority (When Window IS Full)

If a thread is so long that 50 messages exceed the budget (unlikely with 200K windows), drop in this order:

1. **Drop oldest thread messages** (keep last 20 instead of 50)
2. **Summarize thread prefix** (use Haiku to compress messages 1-30 into a 500-token summary, keep messages 31-50 verbatim)
3. **Drop workspace context** (if implemented)
4. **Never drop**: Agent system prompt, user context, the trigger message

This is the R3 layered strategy (progressive summarization) applied to the invocation context.

---

## 6. Agent-to-Agent Interaction

### MVP: No Agent-to-Agent Communication

When `@Vibe` and `@Coder` are both mentioned in the same message, they each respond independently. They do not see each other's responses. They do not coordinate.

This is a deliberate MVP constraint. Agent-to-agent interaction introduces:
- Ordering problems (which agent goes first?)
- Infinite loops (Agent A references Agent B, which triggers Agent A...)
- Cost multiplication (N agents = N API calls, each seeing the others' output)
- UX confusion (whose response is authoritative when agents disagree?)

### Future Architecture (Phase 4-5)

If agent-to-agent interaction is needed (e.g., @Coder writes code, @Reviewer reviews it):

```
Option A: Sequential Pipeline (Simple)
  User: "@Coder write the auth module, @Reviewer review it"
  System: Creates task for @Coder. On completion, creates task for @Reviewer
          with @Coder's output as input context.
  UX: Both responses appear sequentially in the thread.

Option B: Fork-Based Collaboration
  User: "@Coder and @Reviewer, collaborate on the auth module"
  System: Auto-creates a fork. @Coder posts first. @Reviewer responds to @Coder.
          They take turns until one declares "done." Fork is auto-resolved.
  UX: Collaboration happens in a fork, summary posted to parent thread.

Option C: Orchestrator Agent
  User asks a complex question.
  System: An orchestrator (meta-agent) decomposes into subtasks,
          dispatches to specialized agents, synthesizes results.
  This is Claude Code Agent Teams applied to OpenVibe threads.
```

**Recommendation for future:** Option A (sequential pipeline) is simplest and covers most use cases. Option B is more aligned with the fork/resolve model. Option C is the full vision but requires Phase 5+ orchestration work.

---

## 7. Agent Personality & Trust

### How Personality Works

Agent personality is entirely defined by the system prompt. There is no separate "personality engine" or "tone selector." The system prompt IS the personality.

This is the same pattern as OpenClaw's SOUL.md. SOUL.md says: "Be genuinely helpful, not performatively helpful. Skip the 'Great question!' and 'I'd be happy to help!' -- just help." That IS the personality. It's not a toggle or a dropdown -- it's written instructions.

**Why this is the right approach:**
- System prompts are the most flexible personality mechanism available
- Every attempt to decompose personality into structured fields (tone: "formal/casual", verbosity: 1-5) produces worse results than good prose
- The Claude prompt engineering research confirms: "heavy-handed role prompting is often unnecessary, and overly specific roles can limit the AI's helpfulness"
- An admin who can write good instructions produces better agents than an admin filling out a form

### Trust & Risk Classification

R3 established three action categories. For MVP, the mapping is simple:

| Category | Actions | Agent Can Do This? |
|----------|---------|-------------------|
| **AUTONOMOUS** | Read thread messages, generate text responses, search within context, write to thread | **YES** -- this is all agents do in MVP |
| **APPROVE-THEN-ACT** | Post to Slack, send email, modify shared docs, commit code | **NO** -- agents have no tool access in MVP |
| **ESCALATE** | Delete data, change permissions, spend money | **NO** -- agents cannot take any of these actions |

**For MVP, the risk classification is implicit and total: agents can only generate text in threads.** There are no tool calls, no external actions, no side effects beyond posting a message. This is the safest possible starting point.

### Trust Configuration Per Agent

Not needed for MVP. All agents operate at the same trust level (text generation only).

**Post-MVP trust model:**

```typescript
interface AgentTrustConfig {
  // Risk classification overrides per agent
  autonomous_actions: string[];     // Default: ['read', 'respond']
  approve_actions: string[];        // Default: [] (none)
  escalate_actions: string[];       // Default: [] (none)

  // Workspace-level overrides
  workspace_trust_level: 0 | 1 | 2 | 3;  // R3's progressive autonomy levels

  // Per-action approval rules
  approval_rules: {
    action: string;
    requires: 'any_member' | 'admin' | 'specific_user';
    timeout: number;  // seconds before auto-escalate
  }[];
}
```

This aligns with R3's recommendation: start with action classification (Option B), evolve to progressive autonomy (Option C) as agents prove themselves.

---

## 8. Relationship to OpenClaw

### OpenClaw's Configuration Model

OpenClaw (Maxos) is configured via markdown files in `@claw/maxos/`:

| File | Purpose | Equivalent in OpenVibe |
|------|---------|----------------------|
| `SOUL.md` | Personality, behavior rules, tone | `agent_configs.system_prompt` |
| `AGENTS.md` | Workspace instructions, session startup, memory management | Part of `system_prompt` + platform-level behavior |
| `MEMORY.md` | Long-term accumulated knowledge, indexed references | `context_items` table (deferred) |
| `USER.md` | Human profile, preferences | `users` table + `workspace_members` |
| `IDENTITY.md` | Bot identity details | `agent_configs.display_name` + `description` |
| `TOOLS.md` | Available tool documentation | `agent_configs.capabilities` (descriptive for MVP) |
| `HEARTBEAT.md` | Proactive behavior triggers | Background agents (Phase 4) |
| `KNOWLEDGE-MAP.md` | Index to knowledge files | Workspace context / context_items (Phase 4) |
| `config/*.md` | Specific feature configurations | `ui_configs` table |

### Can an OpenClaw-Like Agent Be Defined in This Model?

**Yes, with limitations.**

An OpenClaw-equivalent agent in OpenVibe would be:

```yaml
name: maxos
slug: maxos
display_name: Maxos
description: Personal AI assistant with deep knowledge of the team
model: claude-sonnet-4-5
max_tokens: 4096
capabilities: [general, personal, family, work, proactive]
system_prompt: |
  [Contents of SOUL.md]

  [Condensed version of AGENTS.md session rules]

  [Key facts from MEMORY.md -- the "Core Memories" section]

  [Channel-aware context rules from AGENTS.md]
```

**What's preserved:**
- Personality (SOUL.md content in system_prompt)
- Core knowledge (condensed MEMORY.md in system_prompt)
- Behavior rules (AGENTS.md rules in system_prompt)

**What's lost:**
- Self-editing memory (OpenClaw updates MEMORY.md; OpenVibe agents can't modify their own config)
- Daily logs (OpenClaw writes `memory/YYYY-MM-DD.md`; OpenVibe has no per-agent log mechanism)
- Heartbeat proactive behavior (OpenClaw acts without being asked; OpenVibe agents only respond to @mentions)
- Channel-aware context loading (OpenClaw reads different files based on topic; OpenVibe agents get thread context, not topic-specific knowledge)
- Tool access differences (OpenClaw has Telegram API, email, calendar; OpenVibe agents have no tools in MVP)

### Migration Path

If the founder wants to bring Maxos into OpenVibe as an agent:

**Phase 3 (MVP):**
- Create `@maxos` agent config with SOUL.md content as system_prompt
- Manually include key MEMORY.md facts in the system_prompt
- Accept limitation: Maxos in OpenVibe is a personality without persistent memory or tools

**Phase 4 (Post-dogfood):**
- Implement `agent_memory` table for persistent per-agent knowledge
- Build MCP tool integration so Maxos can access Calendar, Gmail, Slack
- Implement background agent triggers (heartbeat equivalent)
- Add channel/topic-aware context loading to the context assembly layer

**Phase 5 (Full parity):**
- Agent can edit own system_prompt (self-evolving personality)
- Cross-runtime context: Maxos in Telegram and Maxos in OpenVibe share context via the context bus (R7)
- This is the point where "OpenClaw becomes an OpenVibe agent" is fully realized

### What's Shared Between OpenClaw and OpenVibe Agents

| Component | Shared? | How |
|-----------|---------|-----|
| **Personality** | Partially | Same text, different injection mechanism (file vs DB field) |
| **Tools (MCP)** | Future | Both use MCP; OpenVibe's context MCP server (R7) would bridge them |
| **Memory** | Future | Context bus (R7) would sync context items between runtimes |
| **User identity** | No (different systems) | Would require user identity mapping in context unification layer |

---

## 9. MVP vs Full Vision

### MVP Minimum (What Ships with Dogfood)

| Component | MVP Implementation | Effort |
|-----------|-------------------|--------|
| Agent configuration | Database table + YAML seed + tRPC admin endpoints | 1 day (already in BACKEND-MINIMUM-SCOPE.md) |
| Agent roster | 2 @mention agents (Vibe, Coder) + 1 system agent (Fork Resolver) | 0.5 day (write system prompts, insert seed data) |
| @mention detection | Regex parsing in message.send handler | 0.5 day |
| Context assembly | Last 50 messages + system prompt + user name | 1 day |
| LLM invocation | Direct Anthropic Messages API call, collect full response | 1 day |
| Response posting | Insert as agent message, Realtime broadcast | Included in invocation |
| Agent "thinking" UI | Typing indicator driven by task.status_changed Realtime event | 0.5 day |
| Error handling | Retry with backoff, system error messages in thread | 0.5 day |
| **Total** | | **5 days** |

This aligns with BACKEND-MINIMUM-SCOPE.md's estimate of 4 days for Work Package #7 (Agent Integration) + 2 days for #8 (Fork Resolution).

### What's Deferred

| Feature | Phase | Trigger to Build |
|---------|-------|-----------------|
| **Additional specialized agents** (@Researcher, @Writer) | Phase 3.5 | Dogfood feedback: "I wish the agent could search the web" |
| **MCP tool integration** (calendar, email, web search) | Phase 4 | Agent needs to DO things, not just talk |
| **Per-agent memory** | Phase 4 | Agents make the same mistakes repeatedly |
| **Background/proactive agents** | Phase 4 | Team wants auto-summaries, auto-suggestions |
| **Agent versioning** | Phase 4 | Multiple workspaces customizing same agent |
| **Multi-agent orchestration** | Phase 5 | Complex tasks requiring agent coordination |
| **Agent Teams** (Claude Code style) | Phase 5 | Need for hierarchical task decomposition |
| **Custom tool creation** | Phase 5+ | Users want agents to access their own APIs |
| **Agent marketplace** | Phase 6+ | Multiple workspaces sharing agent configs |
| **Agent-to-agent communication** | Phase 5 | Confirmed need from dogfood usage |
| **Progressive autonomy** (R3 trust levels) | Phase 4-5 | Agents get tools; need graduated permissions |
| **Cross-runtime agents** (same agent in OpenClaw + OpenVibe) | Phase 5 | OpenClaw integration via context bus |
| **Self-evolving personality** (agent edits own config) | Phase 5+ | Maxos migration |
| **Streaming response rendering** (token-by-token in UI) | Phase 3.5 | Users complain about waiting for full response |

### The "Do Less, Do It Well" Principle

The MVP agent system is deliberately simple:
- 2 agents, not 5
- Text-only, no tools
- @mention-only, no background triggers
- No persistent memory, no self-evolution
- Single model per agent, no routing
- Global trust policy, not per-agent

This is correct for the same reason the RUNTIME-ARCHITECTURE.md recommendation is "boring": the differentiation is in fork/resolve, not in agent sophistication. A mediocre agent system with great thread UX beats a sophisticated agent system with mediocre threads.

---

## Options Explored

### System Prompt vs Structured Personality Fields

**Option A: System prompt only (adopted)**
- Single text field contains all personality instructions
- Maximum flexibility for admin
- Matches industry standard (OpenAI, Claude, Poe all use this)

**Option B: Structured fields (tone, verbosity, formality, domain)**
- Decompose personality into configurable dimensions
- Generate system prompt from structured fields + templates
- More "admin-friendly" UI (dropdowns, sliders)

**Why A wins:** Structured fields always end up either too restrictive (can't express "be like a sharp colleague, not a customer service bot" as a dropdown) or too complex (20 fields that interact in non-obvious ways). OpenAI's GPT Builder tried structured fields and ended up with a free-form "Instructions" text box as the primary control. Every platform converges on this.

### Database vs Filesystem for Agent Config

**Option A: Database records (adopted)**
- Multi-tenant ready
- Real-time updates
- Queryable
- Works with existing Supabase stack

**Option B: Filesystem (SOUL.md pattern)**
- Works for single-user (OpenClaw)
- Fails for multi-workspace platform
- Agents can't self-edit in a database without tool access (which is fine for MVP)

### Single General Agent vs Multiple Specialized Agents

**Option A: Multiple agents from day 1 (rejected for MVP)**
- @Assistant, @Coder, @Researcher, @Summarizer, @Writer
- More capable surface area
- Risk: agents with similar capabilities confuse users ("should I ask @Assistant or @Writer?")

**Option B: One agent does everything (considered)**
- Single @Vibe agent handles all requests
- Model routing (Haiku for simple, Sonnet for complex) happens internally
- Simplest possible UX

**Option C: Two agents + system agent (adopted)**
- General + Code specialist covers 90% of use cases
- Clear mental model: "ask @Vibe for general stuff, @Coder for code stuff"
- System agent handles fork resolution (users don't need to think about this)
- Additional agents added based on actual usage data

### Agent Naming: Generic vs Branded

**Option A: Generic names (@Assistant, @Coder)**
- Clear what they do
- Boring; feels like commodity

**Option B: Branded names (@Vibe, @Code, @Max)**
- Product identity reinforcement
- More personality
- Risk: unclear what they do without description

**Option C: Hybrid (adopted)**
- @Vibe (branded for the main agent -- reinforces product)
- @Coder (descriptive for the specialist -- clear purpose)
- Fork Resolver (system agent, not user-facing name)

---

## Rejected Approaches

### 1. Container-Per-Agent (Original M3 Design)

**What:** Each agent runs in a Docker container with its own OpenClaw instance, memory mount, and API endpoint.

**Why rejected:** RUNTIME-ARCHITECTURE.md conclusively shows this is wasteful for 20 users. An agent is a configuration, not a process. The LLM API call happens in the application server; no separate container is needed.

**Reconsider when:** Agents need isolated execution environments (code execution, filesystem sandboxing). At that point, use Claude Code SDK in a sandboxed environment, not a full container per agent.

### 2. Agent Memory via Markdown Files

**What:** Each agent gets its own `{agent-name}/MEMORY.md` file, like OpenClaw.

**Why rejected:** Doesn't work in a multi-user web platform. Files aren't queryable, don't support concurrent access, and can't be shared across runtime environments. Database records (context_items table) serve this purpose.

**Reconsider when:** Never for the platform. The file-based pattern is appropriate for single-user tools (OpenClaw, Claude Code) but not for multi-tenant services.

### 3. LLM-Generated Agent Configuration

**What:** An admin describes what they want in natural language ("I want a legal research agent that's cautious and always cites sources"), and an LLM generates the agent_config (including system prompt).

**Why rejected:** Meta-prompt engineering adds a layer of indirection that's hard to debug. When the generated agent behaves wrong, the admin has to figure out whether the problem is in their description, the generator prompt, or the generated system prompt. Direct system prompt authoring is more transparent.

**Reconsider when:** The platform serves non-technical admins who can't write system prompts. At that point, offer this as an "AI-assisted agent creation wizard" alongside direct editing.

### 4. Temperature/Top-P/Top-K as Agent Config Fields

**What:** Expose LLM sampling parameters in the agent configuration.

**Why rejected:** These parameters create a false sense of control. In practice, Claude's default temperature (1.0) with good system prompts produces better results than temperature-tuned prompts. Exposing these to non-ML-engineers leads to superstitious tuning ("set temperature to 0.3 for factual tasks") that doesn't meaningfully improve output quality.

**Reconsider when:** An agent needs reproducible/deterministic output (e.g., for testing pipelines). At that point, add `temperature: 0` as a specific option, not a general slider.

### 5. Per-Agent Context Window Budgets

**What:** Each agent config specifies how many tokens of thread context to include, what priority order for context types, etc.

**Why rejected:** All agents in MVP use the same context assembly strategy (last 50 messages). Per-agent budgets are optimization that requires understanding which agent needs more context vs less. We don't have that data yet.

**Reconsider when:** Agents with vastly different context needs emerge (e.g., a "deep research" agent that needs 100K tokens of context vs. a "quick answer" agent that needs 2K). This is a Phase 4 optimization.

---

## Open Questions

1. **Agent avatar generation:** Should agents have distinct visual avatars? If so, generate them (Anthropic's image API? A static set?) or let admins upload? For dogfood, a colored initial (V for Vibe, C for Coder) is sufficient.

2. **Agent response attribution:** When the Fork Resolver posts a resolution summary, should it be attributed to "Fork Resolver" (system agent) or just "System"? The distinction matters for UX: should users see system agents as "agents" or as "platform features"?

3. **Agent mentioning in already-started thread context:** If a user @mentions @Coder in message #47 of a 100-message thread, the agent gets messages #1-46 as context. But what if message #10 was a previous @Coder response? Should the agent's own previous responses in the thread be marked as "your previous response" in the context? This helps the agent maintain consistency.

4. **System prompt visibility:** Should users be able to see an agent's system prompt? This affects trust. Full transparency (show the prompt) vs. partial transparency (show capabilities description only). For internal dogfood with trusted users, full transparency is fine.

5. **Agent response length control:** Should the UI let users request shorter/longer responses from an agent? (e.g., "be brief" appended to context). Or is this the agent's personality to figure out?

6. **Fork resolution as agent message vs. system message:** Should the resolution summary appear as a message from "Fork Resolver" (an agent) or as a special "resolution" message type with distinct rendering? The former is simpler (just a message); the latter allows richer UI treatment.

---

*Research completed: 2026-02-07*
*Researcher: agent-designer*
