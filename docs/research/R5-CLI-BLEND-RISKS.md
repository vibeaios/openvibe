# R5: CLI-Blend Architecture Risks & Pluggable Platform Design

> Researcher: platform-architect
> Date: 2026-02-07
> Status: Complete

---

## Research Questions

1. If agents execute tasks via CLI tools (Claude Code, custom CLIs), what are the risks when the CLI breaks, differs per OS, or needs to surface progress/errors to a Web UI?
2. What is the interface contract between a CLI backbone and a UI facade?
3. What is the risk matrix (technical, UX, operational) of a CLI-blend approach?
4. What are the alternative architectures (API-first, SDK-first, serverless)?
5. What does "pluggable" mean concretely -- plugin API, config schema, extension points?
6. How do successful platforms (Backstage, Retool) handle pluggability?
7. For Generative UI: what is realistically achievable vs hype?
8. Industry UI difference analysis: medical, legal, construction -- shared vs unique.

---

## Sources Consulted

### Design Documents Read
- `docs/architecture/DESIGN-SPEC.md` -- Core architecture: Memory-first, config-over-code, 4-layer config, containerized agents
- `docs/specs/CONFIG-SYSTEM.md` -- 4-layer config inheritance, Admin Console, merge/validation logic
- `docs/specs/VERTICALS.md` -- Industry templates for medical, legal, construction; template structure and marketplace
- `docs/design/M2-FRONTEND.md` -- Next.js frontend, Discord-like layout, thread branching UI
- `docs/architecture/MONOREPO.md` -- Nx monorepo, apps/services/libs/verticals/packages structure
- `docs/INTENT.md` -- Phase 1 research goals, 7 research questions, team composition
- `docs/design/GAP-ANALYSIS.md` -- Current coverage ~35%, core gaps identified

### External Research
- Vercel v0: AI-generated UI capabilities and limitations (v0.dev, Prismetric, VentureBeat, TrueFoundry, Taskade)
- Retool, Airplane.dev, Superblocks: Low-code/config-driven platforms (Superblocks, BoldTech, UI Bakery, ModelGate)
- Streamlit, Gradio: Dynamic UI generation frameworks (Squadbase, UnfoldAI, Towards Data Science)
- Terraform, Pulumi: CLI-first architectures with web UI overlay (Pulumi docs, ipSpace.net)
- Backstage (Spotify): Plugin architecture and extension points (backstage.io docs, InfoQ, GetDX, Cortex)
- Plasmic, Builder.io: Visual config-driven UI systems (Plasmic docs, GitHub, SurviveJS)
- Google A2UI: Agent-driven UI standard (Google Developers Blog, generativeui.github.io)
- Server-Driven UI (SDUI): Production patterns at Netflix, Airbnb, Meta (Apollo GraphQL, Digia, Nativeblocks)
- Multi-tenant SaaS customization patterns (Bix-Tech, Seedium, Microsoft Azure, WorkOS)
- CLI vs API architecture considerations (Postman, Nordic APIs, Algolia)
- Industry-specific UI: HIPAA scheduling (Sprinto, Demandforce, NexHealth), legal PM (Clio, MyCase, Filevine), construction PM (Raken, Autodesk, GoAudits)

---

## Part 1: CLI-Blend Architecture Risk Assessment

### 1.1 The CLI-Blend Model Defined

In the OpenVibe context, the proposed architecture would have agents executing tasks via CLI tools (Claude Code, custom CLIs) as the computational backbone, with a Web UI serving as a facade that displays results, streams progress, and collects user input. The CLI tool does the "real work" -- running code, querying APIs, manipulating files -- while the UI presents it.

This is similar to how Terraform Cloud wraps `terraform plan/apply` CLI operations in a web dashboard, or how Pulumi's Cloud Console provides a UI over `pulumi up` CLI executions.

### 1.2 Concrete Risk Scenarios

#### Risk 1: CLI Tool Updates/Breaks

| Dimension | Assessment |
|-----------|------------|
| **Probability** | High (monthly+) |
| **Impact** | Critical |
| **Example** | Claude Code updates its output format, flag syntax, or behavioral patterns between versions |

**What happens:**
- Agent behavior changes silently after a Claude Code update
- Output parsing breaks because structured output format changed
- New rate limits or token policies alter agent capability
- Breaking changes in MCP protocol versions

**Why this is worse than a normal dependency:**
CLI tools are not versioned the way libraries are. `npm install claude-code@3.2.1` does not exist. The tool updates on its own schedule, and the update surface is the entire tool behavior, not just an API contract. Terraform solved this partially with provider versioning, but even Terraform users routinely break on provider updates.

**Mitigation difficulty:** Hard. You cannot pin a CLI tool version the way you pin a library. You are dependent on the vendor's backwards compatibility discipline.

#### Risk 2: OS-Specific Behavior

| Dimension | Assessment |
|-----------|------------|
| **Probability** | Medium |
| **Impact** | High |

**What happens:**
- File path handling differs (Windows vs Unix)
- Shell behavior differs (bash vs zsh vs PowerShell)
- Available system tools differ (sed, awk, grep variants)
- Container runtime differences (Docker Desktop vs Colima vs Podman)
- Claude Code itself may have platform-specific bugs or missing features

**Relevance to OpenVibe:**
If agents run in containers (as DESIGN-SPEC proposes), the host OS matters less -- the container provides a consistent environment. But the CLI tool itself (Claude Code) may not be containerizable, or its containerized performance may differ from native.

#### Risk 3: Real-Time Progress in Web UI from CLI Execution

| Dimension | Assessment |
|-----------|------------|
| **Probability** | Certain |
| **Impact** | High (UX-defining) |

**What happens:**
- CLI tools output to stdout/stderr as unstructured text streams
- Progress information is embedded in human-readable output, not machine-parseable events
- Long-running CLI operations produce output sporadically, not at predictable intervals
- The Web UI needs to show: current step, percent complete, estimated time, actionable errors

**The fundamental problem:**
A CLI tool's output contract is "text for humans." Translating that into "structured events for UI" requires a fragile parsing layer that breaks whenever the output format changes. This is not a theoretical risk -- it is the central architectural tension of CLI-blend.

**Comparison:** Terraform Cloud solves this by having `terraform` emit structured JSON plan output (`terraform plan -json`), which the Cloud UI can parse reliably. Pulumi solves it by having the CLI communicate with the Pulumi Service via a well-defined API during execution. Both required the CLI to be designed for programmatic consumption, not retrofitted.

#### Risk 4: Error Translation from CLI to User-Friendly UI

| Dimension | Assessment |
|-----------|------------|
| **Probability** | Certain |
| **Impact** | High |

**What happens:**
- CLI error messages are developer-oriented ("ENOMEM: not enough memory" or "Error: context window exceeded")
- Stack traces and debug info leak into user-facing UI
- Error classification (retryable vs fatal vs configuration) requires parsing error text
- Different CLI tool versions produce different error formats

**Example chain:**
```
Claude Code stderr: "Error: conversation too long, context window limit reached"
  -> Parser: classify as "context_overflow"
  -> UI: "The task is too complex for a single step. Would you like to break it down?"
```
This chain works until Claude Code changes the error message wording.

### 1.3 Risk Matrix

| Risk | Prob | Impact | Category | Mitigation Cost |
|------|------|--------|----------|-----------------|
| CLI version breaks output parsing | High | Critical | Technical | High |
| OS-specific behavior differences | Medium | High | Technical | Medium (containers) |
| No structured progress events | Certain | High | UX | High |
| Error message translation fragility | Certain | High | UX | High |
| CLI startup latency (cold start) | High | Medium | Performance | Medium |
| CLI tool unavailability (rate limits, outages) | Medium | Critical | Operational | Low |
| Security: CLI has broader system access than needed | Medium | Critical | Security | Medium |
| Vendor lock-in to specific CLI tool | High | High | Strategic | High |
| Debugging: failures in CLI are opaque to platform | High | High | Operational | High |
| Scaling: one CLI process per agent task | Medium | High | Infrastructure | High |

### 1.4 The Interface Contract Problem

For a CLI-blend architecture to work, you need a well-defined contract between the CLI backbone and the UI facade.

**What the contract must specify:**

```
1. Input:   How does the UI tell the CLI what to do?
2. Output:  How does the CLI report results?
3. Events:  How does the CLI report progress?
4. Errors:  How does the CLI report failures?
5. State:   How does the CLI report its current state?
6. Cancel:  How does the UI cancel a running CLI operation?
7. Resume:  How does a failed operation resume?
```

**The problem:** If you are using someone else's CLI (Claude Code), you do not control this contract. You must adapt to whatever the CLI provides, and that can change without notice.

**If you build your own CLI:** Then you have just built an API with extra steps. The CLI becomes a transport mechanism with no inherent advantage over HTTP/gRPC/WebSocket.

---

## Part 2: Alternative Architectures

### Option A: CLI-Blend (Current Direction)

**Description:** Agents execute via CLI tools. Web UI wraps CLI execution with progress/error translation.

- **Pros:**
  - Leverages existing powerful tools (Claude Code) without rebuilding
  - Agents can use the full system (filesystem, network, other CLIs)
  - Fast prototyping -- can use Claude Code immediately
  - Human operators can also use the CLI directly for debugging

- **Cons:**
  - Fragile output parsing (see risk matrix above)
  - No structured progress/error contract
  - Scaling requires one process per task
  - Cannot control CLI update cadence
  - Security surface is the entire OS, not a sandboxed API

- **Why to consider:** Speed to MVP. Claude Code is incredibly capable today. Using it directly avoids months of agent runtime development.

- **Verdict:** Viable for dogfood/internal use. Not viable as production architecture for external customers.

### Option B: API-First (Recommended)

**Description:** All agent capabilities are exposed as APIs. The Web UI calls APIs directly. CLI tools are one of many API consumers.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Web UI     │     │   CLI Tool   │     │   SDK        │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   API Layer    │
                    │   (tRPC/REST)  │
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Agent   │  │  Memory  │  │  Config  │
        │  Runtime │  │  System  │  │  Engine  │
        └──────────┘  └──────────┘  └──────────┘
```

- **Pros:**
  - Structured contracts (request/response schemas, typed errors)
  - UI gets first-class progress events via WebSocket/SSE
  - Scales horizontally (load balancer + API instances)
  - Security: API layer enforces permissions, not OS-level access
  - Version control: API versions are explicit
  - Testing: APIs are testable, CLI output parsing is not

- **Cons:**
  - More upfront development (must build agent runtime)
  - Cannot directly leverage Claude Code's full OS-level capabilities
  - LLM orchestration must be built (or use LangChain/CrewAI/etc.)

- **Why adopted:** This is the standard architecture for production SaaS. Every successful platform in the research (Retool, Backstage, Supabase) uses API-first. The DESIGN-SPEC already proposes tRPC for the API layer.

### Option C: SDK-First

**Description:** Provide a TypeScript/Python SDK that developers use to build agent behaviors. The platform hosts and runs SDK-defined agents.

- **Pros:**
  - Maximum flexibility for agent developers
  - Strong typing and IDE support
  - Can be open-sourced for community contribution

- **Cons:**
  - Requires developers to write code for every new agent
  - Conflicts with "configuration over code" principle
  - Higher barrier to entry than config-driven approach

- **Why partially adopted:** The SDK is the right choice for the extension layer (packages/sdk/ in the monorepo) where developers create custom agents and skills. But it should not be the primary interface for admins configuring industry behavior.

### Option D: Hybrid -- API-First with CLI as Development Tool

**Description:** Production architecture is API-first. CLI tools (Claude Code, custom CLIs) are used for development, debugging, and as an alternative interface for power users. The CLI calls the same APIs the Web UI does.

```
Production Path:
  Web UI -> API -> Agent Runtime -> Results -> API -> Web UI

Development Path:
  CLI -> API -> Agent Runtime -> Results -> API -> CLI output

Internal/Dogfood Path (Phase 3-4):
  Claude Code -> (direct agent execution, bypassing API)
  -> Results written to Memory via API
  -> Web UI reads from Memory
```

- **Pros:**
  - Clean production architecture (API-first)
  - Developer productivity (CLI for debugging/testing)
  - Dogfood flexibility (can use Claude Code directly during Phase 3-4)
  - Migration path: start with CLI-direct, move to API-mediated

- **Cons:**
  - Two code paths to maintain (CLI-direct for dogfood, API for production)
  - Must eventually build the API layer regardless

- **Why recommended:** This gives the best of both worlds. Dogfood with Claude Code directly (Phase 3-4), but build the API layer incrementally. By Phase 5 (external users), the API layer is primary and CLI is a development tool only.

### Recommendation: Option D (Hybrid)

**Phased approach:**

| Phase | Architecture | CLI Role | API Role |
|-------|-------------|----------|----------|
| 3 (Implementation) | CLI-first | Primary execution | Minimal -- Memory read/write |
| 4 (Dogfood) | CLI + emerging API | Primary, but API growing | Agent CRUD, config, memory |
| 5+ (External) | API-first | Development/debug tool | Primary execution |

This avoids blocking Phase 3-4 on building a full API layer while ensuring the production architecture is sound.

---

## Part 3: What "Pluggable" Means Concretely

### 3.1 Pluggability Spectrum

Based on research into Backstage, Retool, and Plasmic, "pluggable" operates at multiple levels:

| Level | What is Plugged | Who Does It | Example |
|-------|----------------|-------------|---------|
| **L1: Configuration** | Values within fixed schema | Admin (no code) | Change working hours, enable/disable agents |
| **L2: Template Selection** | Pre-built component packages | Admin (no code) | Choose "medical-clinic" template |
| **L3: Component Composition** | Arrange existing components | Admin (low-code) | Drag agent card onto dashboard |
| **L4: Extension Development** | New components via SDK | Developer | Build custom EHR integration skill |
| **L5: Core Plugin** | New platform capabilities | Platform developer | Add new channel type (WhatsApp) |

OpenVibe's current design handles L1 well (4-layer config), L2 (vertical templates), and partially L4 (skills). L3 and L5 are not addressed.

### 3.2 How Backstage Handles Pluggability

Backstage's architecture is the most relevant reference for OpenVibe because it faces the same challenge: a single platform serving diverse organizations with different needs.

**Key patterns from Backstage:**

1. **Extension Points as Public API Surface:**
   Plugins expose extension points using `createExtensionPoint()`. Modules register against these extension points. The extension point interface is a public API that must be maintained over time.

2. **Package Architecture:**
   - `plugin-<id>-backend` -- plugin implementation
   - `plugin-<id>-node` -- extension points and utilities for modules
   - `plugin-<id>-backend-module-<moduleId>` -- modules extending the plugin

3. **Frontend Extensions:**
   Created using `createExtension()` with ID, attachment point, output definition, and factory function.

4. **Key lesson:** Backstage learned that designing extension point interfaces requires careful consideration because they become a public API surface. Poor extension point design leads to breaking changes that affect all module developers.

**Applicability to OpenVibe:**

The vertical template system maps well to Backstage's plugin model:
- Industry templates = Backstage plugins
- Skills = Backstage modules
- Config layers = Backstage extension points

The missing piece is a formal extension point API that skill/integration developers can program against, and a way to compose UI from registered components.

### 3.3 How Retool/Superblocks Handle Pluggability

These platforms take a different approach: they provide a canvas of pre-built components (tables, forms, charts, buttons) that connect to data sources via configuration.

**Key patterns:**

1. **Component Catalog:** Fixed set of UI primitives that cover 80% of internal tool needs
2. **Data Source Abstraction:** Connect any component to any data source (REST, GraphQL, SQL, etc.) via configuration
3. **Transformation Layer:** JavaScript/SQL transforms between data and UI
4. **Server-side execution (Superblocks):** Business logic runs server-side, UI is pure presentation

**Key limitation:** These platforms are excellent for internal tools but not for building products. The component catalog is rigid -- you cannot create fundamentally new interaction patterns (like Git-like thread branching) within their framework.

**Applicability to OpenVibe:** The Retool model works for the Admin Console (config management, user management, device management) but not for the core Workspace UI (thread interaction, agent collaboration). The Admin Console should feel like an internal tool; the Workspace UI needs custom components.

### 3.4 Recommended Plugin Architecture for OpenVibe

```
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Registry                            │
│                                                               │
│  Agents       Skills      Integrations     UI Components     │
│  ┌─────────┐  ┌────────┐  ┌─────────────┐  ┌────────────┐  │
│  │scheduler│  │ehr     │  │epic-ehr     │  │patient-card│  │
│  │followup │  │calendar│  │clio-legal   │  │case-view   │  │
│  │...      │  │...     │  │procore      │  │daily-log   │  │
│  └─────────┘  └────────┘  └─────────────┘  └────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────────┐
          ▼            ▼                ▼
   Extension      Extension       Extension
   Point:         Point:          Point:
   Agent          Skill           UI Component
   Registration   Registration    Registration
```

**Concrete plugin contract:**

```typescript
// Extension point for registering a new skill
interface SkillExtensionPoint {
  registerSkill(skill: SkillDefinition): void;
}

interface SkillDefinition {
  id: string;
  name: string;
  version: string;

  // What this skill can do
  actions: SkillAction[];

  // What config it needs
  configSchema: JSONSchema;

  // What permissions it requires
  permissions: string[];

  // Runtime requirements
  runtime: {
    timeout: number;
    memory: string;
    network: boolean;
  };
}

// Extension point for registering UI components
interface UIComponentExtensionPoint {
  registerComponent(component: UIComponentDefinition): void;
}

interface UIComponentDefinition {
  id: string;
  name: string;

  // Where this component can appear
  slots: ("sidebar" | "main" | "header" | "modal" | "card")[];

  // What data it needs
  dataSchema: JSONSchema;

  // The React component
  component: React.ComponentType<any>;

  // Which verticals it belongs to
  verticals: string[] | "all";
}
```

---

## Part 4: Generative UI -- Realistic Assessment

### 4.1 What is Achievable Today (2026)

Based on research into v0, Google A2UI, CopilotKit, and academic work on generative UI:

| Capability | Maturity | Confidence |
|------------|----------|------------|
| Generate a single React component from description | Production-ready | High |
| Generate a complete page layout from wireframe | Production-ready | High |
| Generate working CRUD forms from data schema | Production-ready | High |
| Generate industry-specific dashboards from config | Emerging | Medium |
| Generate complex interactive components (thread branching, drag-and-drop) | Not ready | Low |
| Generate accessible, performant, responsive UI automatically | Partial | Medium |
| LLM dynamically choosing which UI component to render | Production-ready (constrained) | High |

### 4.2 Template-Based vs Fully Generative: The Sweet Spot

**Fully generative (v0 style):**
The LLM generates complete React/HTML from a prompt. Good for prototyping, bad for production consistency. Every render could produce different UI. No design system enforcement.

**Template-based (Google A2UI style):**
The LLM selects from a catalog of pre-approved UI components and configures them with data. Predictable, accessible, consistent -- but limited to what the catalog contains.

**The sweet spot for OpenVibe: Constrained generative with template fallback.**

```
┌────────────────────────────────────────────────────────────┐
│                  UI Rendering Decision                       │
│                                                              │
│  1. Does a template exist for this data type?               │
│     YES -> Use template (fast, predictable, accessible)     │
│     NO  -> Continue                                         │
│                                                              │
│  2. Can we compose from existing components?                │
│     YES -> LLM selects and arranges components              │
│     NO  -> Continue                                         │
│                                                              │
│  3. Generate custom component (rare, admin-approved only)   │
│     LLM generates component -> Human reviews -> Deploy      │
└────────────────────────────────────────────────────────────┘
```

**For OpenVibe specifically:**

The core Workspace UI (threads, agents, channels) should be hand-built components -- these are the product's differentiation and must be polished. Generative UI should apply to the configurable parts: industry-specific dashboards, agent response cards, workflow step UIs, and admin-configured views.

### 4.3 What Admins Can Realistically Configure Without Developers

Based on Retool, Plasmic, and SDUI research:

| Admin Can Do (No Developer) | Admin Cannot Do (Needs Developer) |
|-----------------------------|----------------------------------|
| Enable/disable agents | Create new agent types |
| Configure agent parameters | Write agent behavior logic |
| Choose from pre-built dashboard layouts | Create new dashboard components |
| Set branding (logo, colors, fonts) | Create custom themes with animations |
| Configure workflow steps within templates | Create new workflow step types |
| Map data fields to display components | Create new data visualizations |
| Set role-based visibility rules | Implement custom access control logic |
| Choose notification preferences | Create new notification channels |
| Import/export configuration | Write custom integrations |

**Key insight from Retool's experience:** Even with drag-and-drop interfaces, "low-code" always requires someone who thinks like a developer. The promise of "no code needed" is accurate for ~60% of customization needs. The remaining 40% needs a developer, or a very technically capable admin.

**Recommendation for OpenVibe:** Design the system assuming admins are technically capable (IT admins, not receptionists) but not developers. The 4-layer config system covers L1-L2 well. Add a visual component composition layer (L3) for dashboard customization, using a Retool-like approach for admin-facing views.

---

## Part 5: Industry UI Difference Analysis

### 5.1 Medical Clinic UI Needs

**Unique requirements:**

| Element | Description | Why Unique |
|---------|-------------|------------|
| HIPAA banners/warnings | Persistent visual indicators that PHI is being accessed | Legal requirement, must be always visible |
| Patient timeline | Vertical timeline of encounters, ordered by date | Core workflow -- providers need history at a glance |
| Appointment calendar | Color-coded multi-provider calendar with slot management | Central to daily operations |
| Insurance verification status | Real-time eligibility display with badge indicators | Blocks workflow if not verified |
| Role-based field masking | Different zoom levels for physician vs front desk vs billing | HIPAA minimum necessary standard |
| Audit trail visibility | Who accessed what PHI, when | Compliance requirement |
| Device status panel | Vibe Bot/Dot online status per room/provider | Hardware integration is core |
| Clinical note templates | Structured SOAP note format with auto-fill | Industry-standard documentation |

**UI patterns:**
- Heavy use of status badges (insurance: verified/pending/denied)
- Timeline views (patient history, encounter flow)
- Modal confirmations before accessing PHI
- Persistent compliance indicators
- Multi-pane layouts (patient list | patient detail | encounter notes)

### 5.2 Law Firm UI Needs

**Unique requirements:**

| Element | Description | Why Unique |
|---------|-------------|------------|
| Case timeline | Horizontal timeline with milestones (intake -> treatment -> demand -> settlement) | Core workflow visualization |
| Document review interface | Side-by-side document comparison, annotation, categorization | Central to legal work |
| Time tracking integration | Persistent timer in UI, billable/non-billable classification | Revenue-critical |
| Conflict check alerts | Warning when case relationships overlap | Ethical/legal requirement |
| Statute of limitations tracker | Countdown/deadline display with escalating urgency | Malpractice prevention |
| Communication log | All client communications with privilege markers | Attorney-client privilege |
| Settlement calculator | Financial modeling with lien calculations | Unique to PI practice |
| Matter/case hierarchy | Matter -> sub-matters -> tasks organizational structure | Industry-standard organization |

**UI patterns:**
- Heavy use of timers and deadline indicators
- Document-centric views with annotation layers
- Financial tables and calculators
- Hierarchical navigation (firm -> practice area -> matter -> task)
- Activity feeds filtered by case

### 5.3 Construction UI Needs

**Unique requirements:**

| Element | Description | Why Unique |
|---------|-------------|------------|
| Site map / floor plan | Interactive map with pin/marker overlays | Spatial context is essential |
| Photo documentation grid | Photo gallery with metadata (date, location, tag, worker) | Primary evidence format |
| Safety checklist interface | Dynamic checklists with conditional branching, photo attachment | OSHA compliance |
| RFI tracking board | Kanban-style RFI management with status, assignee, response | Core construction workflow |
| Daily log form | Structured daily report: weather, labor, equipment, activities | Industry standard |
| Drawing/plan viewer | PDF/DWG viewer with markup and version overlay | Blueprint-centric work |
| Schedule impact tracker | Gantt-adjacent timeline showing delays and impacts | Project management core |
| Subcontractor directory | Contact list with compliance status (insurance, safety certs) | Coordination tool |

**UI patterns:**
- Mobile-first (field workers use phones/tablets)
- Heavy photo/media integration
- Spatial/map-based navigation
- Checklist/form-driven workflows
- Offline-capable (job sites may lack connectivity)
- Rugged UI (large tap targets, high contrast for outdoor use)

### 5.4 Shared vs Unique Analysis

```
SHARED ACROSS ALL THREE INDUSTRIES (~55%)
├── Thread/message interface (core conversation)
├── Agent status and interaction
├── User/role management
├── Notification center
├── Search
├── Settings/preferences
├── File upload/attachment
├── Calendar/scheduling (basic)
├── Task/to-do tracking
├── Reporting/analytics shell
└── Authentication/login

PARTIALLY SHARED (~20% -- same concept, different implementation)
├── Timeline views (patient timeline vs case timeline vs project timeline)
├── Dashboard layout (same grid, different widgets)
├── Document management (same upload/organize, different viewers)
├── Compliance indicators (HIPAA vs privilege vs OSHA)
├── Contact/entity management (patients vs clients vs subcontractors)
└── Workflow visualization (check-in flow vs case flow vs RFI flow)

FULLY UNIQUE (~25% -- industry-specific components)
├── Medical: HIPAA banners, clinical note templates, insurance verification
├── Legal: time tracking, conflict check, settlement calculator, LEDES billing
└── Construction: site map, photo documentation grid, safety checklists, drawing viewer
```

### 5.5 Implication for Config-Driven UI

The 55% shared layer is the platform core -- build once, use everywhere. This validates the "configuration over code" principle for the majority of the UI.

The 20% partially shared layer can be handled by parameterized components -- a generic "timeline" component that accepts different data schemas per industry. This is where the config system's vertical templates do their work.

The 25% fully unique layer is the hard part. These cannot be "configured" into existence -- they must be built as industry-specific components (or skills that render custom UI). This is where the plugin/extension system matters.

**Critical finding:** The DESIGN-SPEC's claim of "new industry = new configuration, no code" is approximately 75% true. The remaining 25% requires building new components, which means each new vertical has a meaningful development cost. The config system handles most customization, but not all.

---

## Part 6: Recommendation

### Primary Recommendation: API-First Hybrid Architecture

1. **Phase 3-4 (Dogfood):** Use Claude Code directly as agent runtime. Write results to Memory via a thin API layer. Web UI reads from Memory. Accept the CLI-blend risks for internal use.

2. **Phase 5+ (External):** API-first architecture. Agent runtime exposes structured APIs (tRPC as already planned). Web UI calls APIs. CLI becomes a development/debug tool.

3. **Plugin Architecture:** Adopt Backstage-inspired extension points for skills, integrations, and UI components. Define the extension point API early (Phase 2) even if few plugins exist initially. This is the long-term "pluggable" mechanism.

4. **Generative UI:** Use constrained generative (template catalog + LLM selection) for configurable views. Hand-build the core interaction UI (threads, branches, agents). Do not attempt fully generative UI for production.

5. **Industry Verticals:** Accept that each new industry requires ~25% custom component development. Budget this into vertical onboarding. The config system handles the other 75%.

### Interface Contract Specification

For the API layer between agents and UI, define these contracts explicitly:

```typescript
// Task submission
POST /api/tasks
{ agentId, taskType, input, priority }
-> { taskId, status: "queued" }

// Task progress (SSE stream)
GET /api/tasks/{taskId}/events
-> stream of: { type: "progress" | "output" | "error" | "complete", data }

// Task cancellation
POST /api/tasks/{taskId}/cancel
-> { status: "cancelling" | "cancelled" }

// Task result
GET /api/tasks/{taskId}/result
-> { status, output, errors, duration, tokenUsage }
```

This contract is the single most important architectural artifact. It decouples the agent runtime from the UI, regardless of whether the agent uses Claude Code, custom LLM calls, or any other execution method.

---

## Open Questions

1. **Claude Code containerization:** Can Claude Code run in a Docker container reliably? Performance characteristics? This determines whether the container-per-agent architecture from DESIGN-SPEC is viable with Claude Code as the runtime.

2. **MCP stability:** The MCP (Model Context Protocol) is evolving rapidly. How stable is the protocol? If OpenVibe builds skills as MCP tools, will they break across protocol versions?

3. **Agent runtime build vs buy:** Should OpenVibe build its own agent runtime, or adopt an existing framework (LangGraph, CrewAI, OpenAI Agents SDK)? This depends on R3 and R4 findings.

4. **Extension point governance:** Who approves new plugins/extensions? What is the review process? How are breaking changes to extension points communicated? Backstage's experience shows this governance is harder than the technical implementation.

5. **Offline construction use case:** Construction sites often lack reliable internet. If agents require LLM API calls, the construction vertical may need a fundamentally different architecture (local models? queued operations?). This intersects with R6 (Privacy/Hybrid).

6. **Cost of the 25%:** How much does it cost to build the unique 25% for each new vertical? If it takes 2-3 months of developer time per vertical, the business model must account for this. This is a go-to-market question, not just a technical one.

---

## Rejected Approaches

### Rejected: Pure CLI-Blend for Production

**What:** Use CLI tools (Claude Code) as the production agent runtime, with the Web UI as a thin wrapper.

**Why rejected:** The risk matrix is unacceptable for external customers. Fragile output parsing, no structured progress events, uncontrolled update cadence, and OS-specific behavior make this unsuitable for anything beyond internal use.

**Reconsider if:** Claude Code (or a similar tool) provides a stable, versioned, programmatic API (not just a CLI interface). If Anthropic ships a `@anthropic/agent-sdk` with structured event streams and semantic versioning, this changes the calculus entirely.

### Rejected: Fully Generative UI

**What:** Use LLMs to generate all UI dynamically based on data and context.

**Why rejected:** Inconsistent rendering, accessibility failures, performance overhead (LLM call per UI render), and the fundamental problem that your product's UI should not change unpredictably between sessions.

**Reconsider if:** LLM-generated UI achieves WCAG AA compliance by default, rendering latency drops below 50ms, and output consistency reaches >99% for the same input. Current state is far from this.

### Rejected: Retool-Style Drag-and-Drop for Core UI

**What:** Build the entire workspace UI using a Retool-like drag-and-drop builder.

**Why rejected:** The core interaction model (Git-like threads, multi-agent collaboration, branch/merge) requires custom components that cannot be expressed as arrangements of generic form fields and tables. Retool-style builders are excellent for admin panels but wrong for the core product.

**Reconsider if:** The thread interaction model is simplified to standard chat (no branching, no merge). If R1 concludes that Git-like threads are not viable, a simpler UI approach becomes feasible.

### Rejected: SDK-Only Extension Model

**What:** Require developers to write TypeScript/Python code for all customization.

**Why rejected:** Conflicts with "configuration over code" philosophy. Most workspace admins (IT admins at clinics, paralegals at law firms, PMs at construction companies) cannot write code. The 4-layer config system exists specifically to avoid this.

**Reconsider if:** The target customer shifts to developer-heavy organizations. If OpenVibe pivots from "industry SaaS" to "developer platform," an SDK-first model makes more sense.

---

*Completed: 2026-02-07*
*Researcher: platform-architect*
*Contributes to: R5 (primary), R2 (industry UI analysis)*
