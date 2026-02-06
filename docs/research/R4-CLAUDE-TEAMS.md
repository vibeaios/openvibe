# R4: Claude Code Team Agents Integration Research

> Status: Complete | Researcher: agent-lifecycle-researcher | Date: 2026-02-07

---

## Research Questions

1. What are Claude Code Team Agents' actual capabilities and limitations?
2. Can Team Agents be programmatically controlled, or only via interactive CLI?
3. How does context sharing work between teammates?
4. Integration paths: use as-is vs wrap vs fork vs build custom?
5. What's the gap between Team Agents' capabilities and OpenVibe's needs?
6. Risk: what if Anthropic changes the Team Agents API/feature?

---

## Sources Consulted

### Primary Sources
- Official Claude Code Agent Teams documentation (code.claude.com/docs/en/agent-teams)
- Claude Code headless/SDK documentation (code.claude.com/docs/en/headless)
- Anthropic Agent SDK reference - TypeScript (platform.claude.com/docs/en/agent-sdk/typescript)
- Claude Code release notes (releasebot.io/updates/anthropic/claude-code)

### Community Analysis
- Addy Osmani's "Claude Code Swarms" analysis (addyosmani.com/blog/claude-code-agent-teams)
- Paddo.dev's "Claude Code's Hidden Multi-Agent System" (reverse-engineering analysis)
- Kieran Klaassen's "Claude Code Swarm Orchestration Skill" (GitHub Gist, detailed TeammateTool analysis)
- Marc0.dev's parallel agents setup guide
- Architectural Comparison: Claude Flow V3 vs Claude Code TeammateTool (GitHub Gist, ruvnet)
- VentureBeat coverage of Claude Code Tasks (Jan 2026) and Opus 4.6 Agent Teams

### Cross-Reference
- R3-AGENT-LIFECYCLE.md findings on multi-agent frameworks
- docs/design/M3-AGENT-RUNTIME.md (current OpenVibe agent runtime design)
- docs/design/M5-ORCHESTRATION.md (current orchestration design)

---

## Question 1: Actual Capabilities and Limitations

### Capabilities

**Core Architecture:**
- One Claude Code session acts as "team lead," spawning multiple "teammate" sessions
- Each teammate is a full, independent Claude Code instance with its own context window
- TeammateTool discovered in v2.1.19 (Dec 2025) with 13 distinct operations for spawning, managing, and coordinating agents
- Support for multiple execution backends: in-process and tmux-based spawning

**Task Coordination:**
- Shared task list with dependency tracking (DAG-based)
- Inbox-based messaging system for inter-agent communication
- Teammates can self-claim work as they finish tasks
- Lead assigns tasks; teammates report completion back

**Context Efficiency:**
- Single-agent typically uses 80-90% of context window before needing reset
- Team orchestration uses ~40% per agent (each carries their own context)
- Effective context multiplication: 5 teammates = 5 x context windows

**Available Operations (TeammateTool):**
- Spawn teammates with specific roles and instructions
- Assign tasks to specific teammates
- Broadcast messages to all teammates
- Direct messaging between specific agents
- Plan mode coordination
- Join and approval workflows
- Status monitoring and health checks

**Tasks Feature (Jan 2026):**
- Persistent task-graph primitive stored on disk (`~/.claude/tasks`)
- Survives session resets and context compaction
- DAG with dependency blocking (task A blocks task B)
- Status tracking per task
- Designed for "coordinating work across sessions, subagents, and context windows"

### Known Limitations

| Limitation | Impact | Severity |
|-----------|--------|----------|
| **No session resumption** for in-process teammates | If a teammate crashes mid-task, work is lost | High |
| **Lead sometimes implements instead of delegating** | Coordination overhead, lead does work it should delegate | Medium |
| **No file-level locking** | Multiple teammates can conflict on same file | High |
| **Permissions set at spawn time** | Can't dynamically adjust teammate capabilities | Medium |
| **Teammates don't inherit lead's conversation history** | Teammates lack context about prior discussions | High |
| **No cross-machine coordination** | All teammates must run on same machine (tmux/process) | Critical for OpenVibe |
| **Token cost scales linearly** | 5 teammates = 5x minimum token consumption | High |
| **No persistent memory between team sessions** | Team learnings lost when lead session ends | High |
| **Local filesystem only** | Tasks and state stored in `~/.claude/tasks`, not a shared DB | Critical for OpenVibe |

---

## Question 2: Programmatic Control

### Available Interfaces

**1. CLI Headless Mode (`claude -p`)**
- Run Claude Code non-interactively
- Accepts prompt via `-p` flag
- Can be integrated into CI/CD, scripts, pre-commit hooks
- Outputs to stdout for piping

**2. Agent SDK (Python + TypeScript)**
- Full programmatic control as library packages
- Same tools, agent loop, and context management that power Claude Code
- Programmatic options override filesystem settings
- Permission modes: standard, auto-accept edits, bypass all checks, planning mode
- Available as npm/pip packages

**3. SDK Configuration Options**
```typescript
// TypeScript SDK usage pattern
import { Agent } from '@anthropic/agent-sdk';

const agent = new Agent({
  allowedTools: ['Read', 'Write', 'Bash', 'Glob', 'Grep'],
  permissionMode: 'auto-accept',  // or 'standard', 'bypass', 'plan'
  systemPrompt: 'You are a coding agent...',
});

const result = await agent.run('Fix the auth module');
```

**4. Current Limitations of Programmatic Control**
- Agent Teams/TeammateTool is primarily designed for interactive CLI use
- The SDK provides single-agent control; multi-agent orchestration requires manual coordination
- No REST API for team management (it's all local process management)
- Tasks are filesystem-based, no database API

### Assessment

Claude Code is **highly programmable as a single agent** via the SDK. However, **multi-agent orchestration (Agent Teams) is designed for interactive use** and lacks a clean programmatic API for:
- Spawning teams programmatically
- Monitoring team progress via API
- Collecting results from all teammates programmatically
- Running teams headlessly in CI/CD

**Bottom line:** You can programmatically control individual Claude Code agents. You cannot yet programmatically orchestrate teams of them.

---

## Question 3: Context Sharing Between Teammates

### How It Works Currently

```
Team Lead Session
├── Own context window (full conversation history)
├── CLAUDE.md loaded (project instructions)
├── MCP servers connected
└── Skills loaded

Teammate 1 Session
├── Own context window (FRESH - no lead history)
├── CLAUDE.md loaded (same project instructions)
├── MCP servers connected (same)
├── Skills loaded (same)
└── Task assignment from lead (initial context)

Teammate 2 Session
├── Own context window (FRESH - no sibling history)
├── CLAUDE.md loaded (same)
├── MCP servers connected (same)
├── Skills loaded (same)
└── Task assignment from lead (initial context)
```

### What IS Shared
- `CLAUDE.md` and project-level configuration
- MCP server connections (all have access to same tools)
- Skills definitions
- Permission settings (inherited from lead at spawn time)
- File system (all operate on same directory)
- Task list (shared, with dependency tracking)
- Inbox messages (direct or broadcast)

### What IS NOT Shared
- Conversation history (each has own context window)
- Reasoning process (teammates don't see each other's thinking)
- Tool call results (each sees only their own)
- In-flight state (no real-time awareness of what others are doing)
- Learning / memory (nothing persists across team sessions)

### Communication Patterns
1. **Lead -> Teammate**: Task assignment with context + instructions
2. **Teammate -> Lead**: Task completion report with results
3. **Teammate -> Teammate**: Direct messages via inbox system
4. **Lead -> All**: Broadcast messages
5. **Self-claim**: Teammates pick up unassigned tasks from shared list

### Context Sharing Gap Analysis

The critical insight: **Claude Code Team Agents share tools and files but NOT context.** Each teammate starts from a blank slate except for the task assignment. This means:

- The lead must front-load all relevant context into each task assignment
- Teammates cannot build on each other's discoveries without going through the lead
- There's no "team knowledge" that accumulates during the session
- This is fundamentally different from how human teams work (shared understanding grows over time)

---

## Question 4: Integration Paths

### Option A: Use As-Is (Wrap Claude Code Agent Teams)

**Description:** Run Claude Code Agent Teams as the agent runtime for OpenVibe. The Web UI sends tasks to a Claude Code lead agent, which spawns teammates.

**Architecture:**
```
OpenVibe Web UI
     |
     v
OpenVibe API Server
     |
     v
Claude Code SDK (headless)
     |
     v
Claude Code Lead Agent
     |
     +--> Teammate 1 (coder)
     +--> Teammate 2 (researcher)
     +--> Teammate 3 (writer)
```

**Pros:**
- Least development effort
- Leverages Anthropic's investment in agent coordination
- Gets improvements automatically as Anthropic updates
- Tasks persistence already built
- Good tooling (file operations, code execution, etc.)

**Cons:**
- **Single-machine limitation**: All teammates must run locally -- no distributed agents
- **Claude-only**: Locked to Anthropic's models (no Gemini, GPT, etc.)
- **No cross-runtime**: Can't coordinate with OpenClaw (Telegram) agents
- **Black box**: Limited visibility into agent decision-making
- **No persistent memory**: Team knowledge doesn't survive sessions
- **Token cost**: Opaque -- hard to optimize or control per-user billing
- **Anthropic dependency**: Feature changes could break OpenVibe

**Verdict: Reject as primary architecture.** Too many critical limitations for OpenVibe's cross-runtime, multi-model vision. However, valuable as one of several agent runtimes.

### Option B: Wrap + Extend (Claude Code as One Runtime)

**Description:** Use Claude Code SDK as one agent runtime among several. Build an abstraction layer that can dispatch tasks to Claude Code agents OR OpenClaw agents OR custom agents.

**Architecture:**
```
OpenVibe Orchestrator
     |
     +--> Claude Code Runtime (via SDK)
     |    +--> Uses Agent Teams internally
     |
     +--> OpenClaw Runtime (via API)
     |    +--> Telegram-based agents
     |
     +--> Custom Runtime (future)
          +--> Web-based agents
```

**Pros:**
- Best of both worlds: Claude Code's tooling where it excels, custom where it doesn't
- Not locked to any single runtime
- Claude Code handles coding tasks (its strength)
- OpenClaw handles conversational tasks (its strength)
- Shared context via OpenVibe's own Memory layer (M4), not Claude Code's filesystem

**Cons:**
- Higher development effort (abstraction layer)
- Two systems to maintain and monitor
- Context handoff between runtimes needs design (see R7)
- Claude Code's TeammateTool may not be stable API

**Verdict: Recommended approach.** This aligns with OpenVibe's multi-runtime architecture and Memory-first philosophy. Claude Code is a powerful tool but should be one runtime, not THE runtime.

### Option C: Fork Claude Code's Approach

**Description:** Study Claude Code's TeammateTool implementation and build a similar system from scratch, tailored to OpenVibe's needs.

**Pros:**
- Full control over implementation
- Can design for cross-runtime from day one
- No vendor dependency
- Can optimize for OpenVibe's specific patterns

**Cons:**
- Massive development effort (person-months to replicate)
- Loses automatic improvements from Anthropic
- Re-inventing what's already working
- Claude Code's SDK is already open for programmatic use

**Verdict: Reject.** Too much effort for too little marginal benefit. The wrap + extend approach (Option B) captures 90% of the value at 20% of the cost.

### Option D: Build Fully Custom (Ignore Claude Code)

**Description:** Build agent orchestration entirely from scratch using raw LLM APIs, custom tool frameworks, and OpenVibe's own agent runtime.

**Pros:**
- Maximum flexibility
- No external dependencies
- Can support any LLM provider
- Full control over costs and behavior

**Cons:**
- Years of development to match Claude Code's current capability
- Agent tool use (file operations, code execution, terminal) is extremely hard to build well
- Safety and sandboxing is non-trivial
- Would be competing with Anthropic, OpenAI, and Google on their home turf

**Verdict: Reject.** This is building a competing product, not building OpenVibe. Use existing tools where they excel.

### Recommended Integration Path

**Option B: Wrap + Extend**, with the following concrete plan:

1. **Phase 1 (MVP/Dogfood):** Use Claude Code SDK (headless) as the primary agent runtime for coding and complex tasks. Use OpenClaw API for conversational tasks via Telegram. Build a thin orchestration layer that can dispatch to either.

2. **Phase 2:** Add shared memory (M4) that both runtimes write to and read from. Implement context handoff protocol (see R3) for cross-runtime task continuation.

3. **Phase 3:** Add Web UI as third runtime. Evaluate additional runtimes as the agent ecosystem evolves.

---

## Question 5: Gap Between Team Agents and OpenVibe's Needs

### Critical Gaps

| OpenVibe Need | Claude Code Team Agents | Gap |
|---------------|-------------------------|-----|
| **Cross-runtime agents** (CLI + Telegram + Web) | Single-machine, single-CLI only | Critical -- needs custom orchestration |
| **Persistent team memory** | No persistent memory between sessions | Critical -- needs M4 integration |
| **Multi-model support** (Claude, GPT, Gemini, open-source) | Claude-only | High -- limits vendor flexibility |
| **Distributed agents** (multiple machines/containers) | Local process only | High -- needed for production scale |
| **Per-user cost tracking** | No token tracking per user/task | High -- needed for SaaS billing |
| **Custom auto-decision rules** | Fixed permission model (at spawn time) | Medium -- needs configurable escalation |
| **Thread-based context** (Git-like branching) | Linear conversation per agent | Medium -- OpenVibe's core differentiator |
| **Industry-specific compliance** (HIPAA, etc.) | General-purpose permissions | Medium -- needed for vertical templates |
| **Real-time agent status** (WebSocket to UI) | CLI output only | Medium -- UX requirement |
| **Task lifecycle state machine** | Tasks feature (Jan 2026) partially covers | Low -- Tasks feature is close, needs extension |

### What Claude Code Team Agents DO Well (Keep These)

| Capability | Quality | OpenVibe Should... |
|-----------|---------|-------------------|
| Code editing and generation | Excellent | Leverage via SDK for coding tasks |
| File system operations | Excellent | Leverage for local dev workflows |
| Terminal/Bash execution | Excellent | Leverage in sandboxed environments |
| CLAUDE.md project context | Good | Adapt pattern for OpenVibe's config system |
| Task DAG with dependencies | Good | Extend for cross-runtime task management |
| Agent safety/permissions | Good | Learn from, apply to all runtimes |
| MCP tool integration | Good | Build on MCP as shared tool layer |

### Net Assessment

Claude Code Team Agents are **excellent for developer tooling on a single machine** but **insufficient as a general-purpose multi-agent orchestration platform**. OpenVibe needs to treat Claude Code as a powerful backend runtime for coding/developer tasks while building its own orchestration, memory, and cross-runtime layers.

---

## Question 6: Anthropic Dependency Risk

### Risk Factors

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **API breaking changes** | Medium | High | Abstract via wrapper layer, pin SDK versions |
| **Feature removal** (TeammateTool is experimental) | Low-Medium | High | Don't depend on internal APIs, use official SDK |
| **Pricing increase** | Medium | Medium | Multi-model support, model routing, cost monitoring |
| **Rate limiting / capacity constraints** | Medium | Medium | Queue system, retry logic, model fallback |
| **Anthropic discontinues Claude Code** | Very Low | Critical | Agent SDK is separate from CLI tool |
| **Competitive conflict** (Anthropic builds a competitor) | Low-Medium | High | OpenVibe's value is Memory + Thread, not agent runtime |
| **Open-source license changes** | Low | Medium | Fork-friendly architecture, pin dependencies |

### Strategic Analysis

**Anthropic's trajectory:**
- Moving toward platform play: Agent SDK, MCP, Claude Code
- MCP donated to Linux Foundation (Dec 2025) -- signals openness
- Agent SDK is provider-agnostic (documented paths for non-OpenAI models -- they literally support competitors)
- Revenue model is API usage -- they want developers to use Claude, not compete with developer tools

**OpenVibe's natural defense:**
- Value is in Memory layer (M4), not agent runtime -- if Claude Code disappears, swap runtime, keep memory
- Thread model (R1) is OpenVibe's differentiation, not agent capability
- Multi-runtime by design -- Claude Code is one option, not the only option
- MCP as shared tool layer reduces coupling to any one runtime

### Risk Mitigation Strategy

1. **Abstraction layer**: Never call Claude Code SDK directly from business logic. Always go through an OpenVibe AgentRuntime interface.

2. **Interface-first design:**
```typescript
interface AgentRuntime {
  submitTask(task: Task, context: AgentContext): Promise<TaskResult>;
  getTaskStatus(taskId: string): Promise<TaskStatus>;
  cancelTask(taskId: string): Promise<void>;
}

class ClaudeCodeRuntime implements AgentRuntime { ... }
class OpenClawRuntime implements AgentRuntime { ... }
class WebAgentRuntime implements AgentRuntime { ... }
```

3. **Memory independence**: All important state lives in OpenVibe's Memory (M4), not in Claude Code's filesystem. If Claude Code goes away, memory survives.

4. **SDK version pinning**: Pin Claude Code SDK versions, test before upgrading, maintain compatibility tests.

5. **Gradual capability migration**: Over time, move critical capabilities into OpenVibe's own agent layer, using Claude Code less as more alternatives mature.

---

## Recommendation

### Overall Architecture Decision

**Use Claude Code as a powerful but replaceable agent runtime**, not as the orchestration backbone. Specifically:

1. **Adopt Claude Code SDK** as the primary runtime for coding/developer tasks during dogfood phase
2. **Build OpenVibe's own orchestration layer** (extending M5) for cross-runtime task management
3. **Build OpenVibe's own memory layer** (M4) as the source of truth for context, NOT Claude Code's filesystem
4. **Define a runtime-agnostic interface** that Claude Code, OpenClaw, and future runtimes all implement
5. **Use Claude Code's CLAUDE.md pattern** as inspiration for OpenVibe's project-level configuration, but don't couple to it

### Why This Is Right

- Claude Code excels at coding tasks and file operations -- use it for that
- OpenVibe's differentiators (Memory, Threads, cross-runtime) are orthogonal to Claude Code's strengths
- The Agent SDK makes Claude Code genuinely programmable -- no need to hack around CLI limitations
- Multi-runtime is not just a hedge -- it's a product requirement (OpenClaw for mobile, Web UI for browsers, CLI for developers)
- Memory-first means the runtime is commodity -- this is exactly the design philosophy from DESIGN-SPEC.md

### What NOT to Do

- Don't build the entire agent system on Claude Code Agent Teams -- it's a single-machine, single-provider tool
- Don't fork Claude Code -- maintain effort would be enormous
- Don't ignore Claude Code -- it's the best coding agent available and OpenVibe's team already uses it
- Don't try to replicate TeammateTool's internal APIs -- they're experimental and subject to change

---

## Open Questions

1. **SDK stability**: The Claude Code Agent SDK is relatively new. How stable is the API? Need to monitor release notes and plan for breaking changes.

2. **Tasks feature evolution**: Claude Code Tasks (Jan 2026) is evolving rapidly. Will Anthropic add database-backed persistence? Cross-machine support? This would significantly close the gap with OpenVibe's needs.

3. **Agent Teams as a service**: Will Anthropic offer hosted Agent Teams (similar to Google's Vertex AI Agent Engine)? This would change the build-vs-buy calculus.

4. **MCP compatibility**: Claude Code's MCP implementation vs OpenClaw's -- are they compatible enough to share tools? This feeds into R7.

5. **Concurrent license model**: Does the Claude Code SDK license allow running multiple agent instances in a server context? Enterprise pricing model?

---

## Rejected Approaches

### 1. Claude Code Agent Teams as Primary Orchestration

**Why rejected:** Single-machine, single-provider, no persistent memory, no cross-runtime support. Fundamentally incompatible with OpenVibe's multi-runtime architecture.

**Reconsider when:** Anthropic adds distributed agent support, persistent memory, and multi-provider model routing. Essentially, if Claude Code becomes a full agent orchestration platform rather than a CLI tool.

### 2. Forking Claude Code

**Why rejected:** Enormous maintenance burden. Claude Code is a complex system (binary distribution, not source-available in meaningful way). The SDK provides sufficient programmatic access for wrapping.

**Reconsider when:** Anthropic makes Claude Code fully open-source AND OpenVibe needs deep customization that the SDK can't support.

### 3. Building Custom Agent from Scratch (Ignoring Claude Code)

**Why rejected:** Would mean rebuilding code editing, file operations, terminal execution, safety sandboxing, and tool orchestration. This is years of work that Claude Code already does well.

**Reconsider when:** A competitive open-source coding agent reaches parity with Claude Code (possible from Cursor, Windsurf, or open-source projects -- but unlikely in the near term for the quality level needed).

### 4. Adopting TeammateTool's Internal API

**Why rejected:** Discovered via reverse engineering, not officially documented or supported. Could break at any time. The official Agent SDK is the right integration point.

**Reconsider when:** Anthropic officially documents and stabilizes the TeammateTool API as part of the public SDK.

---

*Research completed: 2026-02-07*
*Researcher: agent-lifecycle-researcher*
