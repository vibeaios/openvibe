# R2: Generative UI & Config-Driven Experience Research

> Can a single codebase serve medical clinics, law firms, and construction sites through configuration?

---

## Research Question

1. What UI elements can realistically be config-driven vs need code?
2. How different are medical clinic UI vs law firm UI vs construction site UI?
3. What is "Generative UI" technically? LLM-generated components? Template system?
4. Can an admin console realistically control the UX without code changes?
5. What are the boundaries of configurability?

---

## Sources Consulted

### Existing Design Docs
- `docs/specs/CONFIG-SYSTEM.md` -- 4-layer configuration hierarchy (Platform -> Template -> Workspace -> User)
- `docs/specs/VERTICALS.md` -- Template structure for medical/legal/construction, agents/skills/workflows/roles
- `docs/architecture/DESIGN-SPEC.md` -- "Configuration over Code" principle, vertical adaptation (section 8)
- `docs/design/M2-FRONTEND.md` -- Current frontend tech stack (Next.js, TailwindCSS, shadcn/ui, Zustand)
- `docs/design/GAP-ANALYSIS.md` -- Identifies generative UI as high risk (R2)

### External Research: Generative UI Frameworks
- **Vercel AI SDK 3.0** -- Associates LLM responses with streaming React Server Components. Uses tool calling to map LLM decisions to React components. Core pattern: model invokes tool -> tool returns data -> React component renders data. Note: AI SDK RSC development is currently **paused** by Vercel.
- **Google A2UI Protocol** (a2ui.org) -- Declarative UI protocol for agent-driven interfaces. v0.8 Public Preview (Dec 2025). Agents send JSON describing UI components, not code. Native-first rendering across web/mobile/desktop. Three layers: UI Structure, State, Rendering. Used by Google's Opal team for "AI mini-apps."
- **Vercel v0** -- AI-powered UI code generation. Generates React + Tailwind components from text prompts. Good for prototyping, struggles with complex logic and enterprise-scale apps. Focused on code generation, not runtime configuration.
- **Hashbrown** -- Exposes React/Angular components to LLM for dynamic view serving. Tool calling runs in the browser.
- **Flutter GenUI SDK** -- Alpha. LLM generates dynamic, personalized UI for Flutter apps.

### External Research: Config-Driven Platforms
- **Retool** -- Drag-and-drop UI builder with 100+ pre-built components. PostgreSQL stores all configuration and metadata. Isolated code execution for user-written JavaScript/Python. Effectively a config-driven UI platform, but for internal tools, not end-user products.
- **Streamlit** -- Python framework for data apps. Code-driven, not config-driven. Fast prototyping but not runtime configurable.

### External Research: Vertical SaaS
- Vertical SaaS market analysis (2025-2026): Industry-specific platforms dominate in healthcare (Epic, Cerner), legal (Clio, MyCase), construction (Procore, PlanGrid). No single platform successfully serves all three verticals.
- Key pattern: vertical SaaS succeeds through deep domain integration, not UI customization. The UI differences between industries are often less important than the workflow and data model differences.

---

## Options Explored

### Option A: LLM-Generated UI at Runtime (True Generative UI)

**Description:** The LLM dynamically generates UI components at runtime based on context. Each agent response can include UI elements (forms, charts, tables, buttons) that the frontend renders. Similar to Vercel AI SDK's streamUI or Google A2UI approach.

**Pros:**
- Maximum flexibility -- AI adapts UI to any situation
- No pre-built templates needed for new use cases
- Novel, differentiated experience
- Agents can create rich interactive responses beyond text

**Cons:**
- Extremely unpredictable -- LLM might generate broken/inconsistent UI
- Latency: generating UI adds to response time (~500ms+ on top of LLM call)
- Security: LLM-generated components could expose data or execute unintended actions
- Testing nightmare: infinite possible UI states, can't regression test
- Accessibility/compliance: generated UI may not meet WCAG, HIPAA display requirements
- Vercel paused AI SDK RSC development -- signal that this approach has unresolved issues
- A2UI is v0.8, still evolving -- not production-ready

**Why rejected for MVP:** Too risky, too unpredictable, too hard to certify for compliance. The compliance requirements of medical/legal verticals make unpredictable UI generation a non-starter. However, elements of this approach (agent responses including structured data that renders as rich components) are valuable and should be adopted selectively.

---

### Option B: Config-Driven Template System (Current Design Direction)

**Description:** Pre-built component library with YAML configuration controlling which components appear, their layout, data bindings, and behavior. The 4-layer config system from CONFIG-SYSTEM.md drives the UI. Admin Console allows workspace-level customization.

**Pros:**
- Predictable, testable, compliant
- 4-layer config system already designed in detail
- Admin can customize without code
- Industry templates provide opinionated defaults
- Familiar pattern (Retool, Salesforce admin, etc.)
- Can be validated, audited, and certified

**Cons:**
- Limited flexibility -- can only configure what was pre-built
- New component types require code changes
- Config complexity grows over time (Retool's config is massive)
- "Config-driven" often becomes "config-limited"
- Every new vertical needs new template development
- Risk of building a Retool/Salesforce config monster

**Why adopted as primary approach:** This is the proven path. Retool, Salesforce, and enterprise SaaS have validated config-driven customization. The 4-layer hierarchy already designed is solid. The key is to define the right boundaries of what's configurable.

---

### Option C: Hybrid (Config Templates + Selective Generative UI)

**Description:** Core UI is config-driven templates (Option B). Agent responses can include structured "cards" with pre-defined component types (not arbitrary LLM-generated UI). A curated component catalog defines what agents can render. Think of it as "generative content within fixed UI frames."

**Pros:**
- Predictable frame (config-driven) + dynamic content (agent-generated)
- Agents can render rich responses (tables, charts, forms, approvals) using a safe component set
- Component catalog can be validated and certified
- Admin configures the frame; agents generate the content
- Maps well to A2UI's "declarative, not code" philosophy
- Safer than pure generative UI; more flexible than pure config

**Cons:**
- Component catalog needs careful design and ongoing expansion
- Some agent responses won't fit available components and fall back to text
- More complex architecture than pure config-driven
- Need to define which components agents can use per vertical (compliance)

**Why adopted as enhancement to Option B:** This is the pragmatic middle ground. The frame is config-driven (predictable, compliant). Agent responses use a curated component catalog (rich but controlled). This avoids both the unpredictability of true generative UI and the rigidity of pure config.

---

### Option D: Code-Level Customization (Plugin/Extension System)

**Description:** Instead of config, provide an extension/plugin API for verticals. Developers write custom React components that plug into the platform.

**Pros:**
- Maximum flexibility for developers
- No config limitations
- Each vertical can have truly custom UI

**Cons:**
- Requires developers for every customization
- Breaks the "no code changes for new industry" vision
- Plugin quality/security is hard to control
- Extension APIs are hard to design well and keep stable
- Not accessible to admin users

**Why rejected as primary approach:** This contradicts the "Configuration over Code" principle. However, an escape hatch for custom components (like Retool's custom components or Salesforce Lightning Web Components) is pragmatic for edge cases. Should be a last resort, not the primary mechanism.

---

## Recommendation

### Recommended Approach: Option B (Config Templates) + Option C (Agent Component Catalog)

**Two-layer UI architecture:**

#### Layer 1: Config-Driven Frame (Admin-Controlled)

What the admin configures:

| Configurable | Config Mechanism | Example |
|-------------|-----------------|---------|
| **Sidebar content** | YAML: sections, order, visibility | Show/hide Agents panel, Device panel |
| **Channel structure** | YAML: default channels, permissions | #patients (medical), #cases (legal) |
| **Thread types** | YAML: available types, required fields | patient-encounter, case-thread |
| **Agent roster** | YAML: which agents appear, their order | @Scheduler, @Insurance (medical) |
| **Color/branding** | YAML: primary color, logo, theme | Clinic logo, brand colors |
| **Role-based views** | YAML: what each role sees | Physician sees all; front-desk sees limited |
| **Workflow triggers** | YAML: auto-actions on events | Patient arrives -> check-in workflow |
| **Notification rules** | YAML: who gets notified when | Doctor notified when patient checks in |
| **Compliance flags** | YAML: HIPAA mode, audit level | Enable/disable PHI visibility |

What the admin CANNOT configure (requires code):

| Not Configurable | Why | How to Extend |
|-----------------|-----|---------------|
| **New component types** | Need React code | Plugin/extension API |
| **Custom data visualizations** | Need rendering logic | Plugin/extension API |
| **Novel interaction patterns** | Need UX design + code | Platform update |
| **External system UI** | Depends on integration | Integration-specific code |
| **Accessibility patterns** | Need WCAG compliance | Platform-level |
| **Offline behavior** | Need service worker logic | Platform-level |

#### Layer 2: Agent Component Catalog (AI-Controlled Within Bounds)

Agents can render responses using a curated set of components:

```yaml
# Agent Component Catalog
components:
  # --- Content Components ---
  text:
    description: "Markdown-formatted text"
    agent_access: all

  table:
    description: "Structured data table"
    props: [headers, rows, sortable, filterable]
    agent_access: all

  code_block:
    description: "Syntax-highlighted code"
    props: [language, content, line_numbers]
    agent_access: all

  # --- Interactive Components ---
  action_buttons:
    description: "Row of action buttons"
    props: [buttons: [{label, action, variant}]]
    agent_access: all
    example: "Approve / Reject / Request More Info"

  form:
    description: "Input form"
    props: [fields: [{name, type, label, required}], submit_action]
    agent_access: role_agents_only  # Not worker agents
    compliance: requires_audit_log

  confirmation:
    description: "Yes/no confirmation dialog"
    props: [question, confirm_label, cancel_label, action]
    agent_access: all

  # --- Data Components ---
  summary_card:
    description: "Key-value summary"
    props: [title, items: [{label, value}], actions]
    agent_access: all
    example: "Patient summary, Case overview"

  timeline:
    description: "Chronological event list"
    props: [events: [{date, title, description, status}]]
    agent_access: all

  progress:
    description: "Progress indicator"
    props: [label, current, total, status]
    agent_access: all

  # --- Decision Components ---
  poll:
    description: "Multi-option vote"
    props: [question, options, allow_multiple, deadline]
    agent_access: all

  decision_record:
    description: "Structured decision capture"
    props: [question, options_considered, decision, rationale, decided_by]
    agent_access: all
    compliance: immutable_after_creation

  # --- Vertical-Specific Components ---
  # These are registered by vertical templates
  appointment_slot:
    vertical: medical
    description: "Available appointment time slot"
    props: [provider, date, time, duration, type]

  case_status:
    vertical: legal
    description: "Case status card"
    props: [case_id, status, next_action, deadline]

  rfi_card:
    vertical: construction
    description: "RFI summary card"
    props: [rfi_number, subject, status, assigned_to, due_date]
```

#### How This Works in Practice

```
User: "@Scheduler I need an appointment with Dr. Smith next week"

Agent (@Scheduler) response:
{
  "text": "Dr. Smith has these available slots next week:",
  "components": [
    {
      "type": "appointment_slot",
      "props": {
        "provider": "Dr. Smith",
        "slots": [
          {"date": "2026-02-10", "time": "10:00", "duration": 30},
          {"date": "2026-02-12", "time": "14:00", "duration": 30}
        ]
      }
    },
    {
      "type": "action_buttons",
      "props": {
        "buttons": [
          {"label": "Book 10:00 AM Tue", "action": "book_appointment", "data": {...}},
          {"label": "Book 2:00 PM Thu", "action": "book_appointment", "data": {...}},
          {"label": "Show more times", "action": "expand_search"}
        ]
      }
    }
  ]
}
```

The frontend renders this using pre-built, tested, accessible React components. The agent decides which component to use and provides the data, but cannot generate arbitrary UI.

---

## Detailed Answers to Research Questions

### 1. What UI elements can realistically be config-driven vs need code?

**Config-driven (realistic):**
- Layout and navigation (sidebar sections, tab order, visibility)
- Color scheme, branding, typography
- Which features/modules are enabled (agents, thread types, workflows)
- Field configurations (what metadata fields appear on threads)
- Permission-based visibility (role X sees Y)
- Default values and presets
- Notification rules and triggers
- Compliance flags (HIPAA mode, audit logging)
- Labels and terminology (configurable names for concepts)

**Need code (realistic):**
- New interactive component types
- Custom data visualizations
- Novel interaction patterns (e.g., a new type of fork resolution)
- Integration-specific UIs (EHR viewer, Procore dashboard)
- Complex form validation logic
- Accessibility patterns for new components
- Performance optimizations for specific data patterns

**The 80/20 rule:** Config handles ~80% of vertical differentiation (which features are visible, what they're called, who can access them). Code handles ~20% (vertical-specific components and deep integrations).

### 2. How different are medical clinic UI vs law firm UI vs construction site UI?

**Surprisingly: not that different at the conversation/thread level.**

| UI Dimension | Medical | Legal | Construction | Similarity |
|-------------|---------|-------|-------------|------------|
| **Chat/thread** | Same | Same | Same | 95% identical |
| **Sidebar** | Same structure | Same structure | Same structure | 90% identical |
| **Agent panel** | Different agents | Different agents | Different agents | 80% (config-driven) |
| **Thread metadata** | Patient, Provider, Visit Type | Case, Client, Matter | Project, Phase, Trade | 20% (need different fields) |
| **Workflow overlays** | Check-in flow, Insurance | Intake flow, Settlement | RFI flow, Safety report | 10% (need different components) |
| **Compliance UI** | HIPAA warnings, PHI indicators | Privilege markers | Safety alerts | 30% (need different indicators) |
| **Terminology** | Patient, Encounter, Provider | Client, Case, Attorney | Project, RFI, Superintendent | 0% (fully config-driven) |

**Key insight: The core conversation UI (threads, messages, forks, agent interactions) is identical across all verticals.** The differences are:

1. **Terminology** -- "Patient" vs "Client" vs "Project" (config: rename labels)
2. **Thread metadata** -- Different required fields (config: field definitions)
3. **Agent roster** -- Different specialist agents (config: agent list)
4. **Compliance indicators** -- Different compliance requirements (config: compliance flags + 2-3 coded compliance components)
5. **Workflow-specific UI** -- Vertical-specific components (~5 per vertical, coded as catalog entries)

**This means the 4-layer config system IS viable for most differentiation.** The remaining ~20% that needs code is isolated to vertical-specific catalog components and deep integrations.

### 3. What is "Generative UI" technically?

Three distinct meanings in the current landscape:

**a) LLM-Generated Code (Vercel v0 style)**
- LLM writes React/Tailwind code from prompts
- Output is source code, not runtime UI
- Good for development, not for production runtime
- Not applicable to our use case

**b) LLM-Streamed Components (Vercel AI SDK style)**
- LLM invokes tools that return React components
- Components stream to client via React Server Components
- Runtime-generated, but using pre-built component implementations
- Partially applicable: agent responses that render components

**c) Declarative UI Protocol (Google A2UI style)**
- Agent sends JSON describing UI intent
- Client renders using native component library
- No code execution, declarative specification only
- Most applicable to our use case

**Recommendation for OpenVibe:** Adopt the A2UI philosophy (declarative, not code) but with a proprietary component catalog (not the A2UI protocol itself, since it's still v0.8 and evolving). Agents describe what they want to show using a JSON format. The frontend maps this to pre-built React components. This is predictable, testable, and compliant.

### 4. Can an admin console realistically control the UX without code changes?

**Yes, for ~80% of customization needs. No, for the remaining ~20%.**

What Admin Console CAN control:
- Enable/disable features and agents
- Configure thread types and required fields
- Set branding and visual theme
- Define roles and permissions
- Configure notification rules
- Set compliance flags
- Customize terminology/labels
- Define default workflows
- Manage integrations (toggle, configure credentials)

What Admin Console CANNOT control:
- Adding entirely new component types
- Custom integration UIs
- Novel workflow step types
- Complex business logic
- Performance tuning

**The "new industry = new config" vision is 80% true.** A new industry that resembles existing ones (dental clinic based on medical-clinic template) needs zero code. A genuinely new industry with unique workflow requirements (maritime, aviation) needs a small amount of component development.

The current CONFIG-SYSTEM.md design with its 4-layer hierarchy, locking, and override rules is sound. The admin console commands (workspace, agent, role, config, device management) are the right abstractions.

### 5. What are the boundaries of configurability?

**The Configuration Boundary Model:**

```
                    Config-Driven
                    (Admin Console)
                         |
    +--------------------+--------------------+
    |                    |                    |
    v                    v                    v
  LAYOUT              CONTENT             BEHAVIOR
  - Which panels       - Terminology       - Which agents active
  - Tab order          - Help text         - Permission rules
  - Visibility         - Labels            - Notification triggers
  - Theme/colors       - Default values    - Workflow sequences
                                           - Compliance mode
                         |
                    -----+-----
                    |         |
                    v         v
               Code-Driven    Hybrid
               (Developer)    (Config + Code)
                    |              |
    +---------------+--+    +-----+--------+
    |               |  |    |              |
    v               v  v    v              v
  NEW             DEEP    VERTICAL      CUSTOM
  COMPONENTS    INTEG.   CATALOG      WORKFLOW
  - Custom viz   - EHR   - appt_slot   STEPS
  - Novel UX     - CRM   - case_status  - New step
  - Accessibility- PM    - rfi_card     types
```

**Hard boundaries of configurability:**
1. Cannot add new interaction paradigms through config (e.g., a new type of fork)
2. Cannot create new visual component types through config
3. Cannot override platform security/performance limits
4. Cannot add external system integrations without code
5. Cannot modify the core conversation data model

**Soft boundaries (could expand over time):**
1. Custom fields on threads -- start with config, might need code for complex types
2. Workflow steps -- basic steps config-driven, complex steps need code
3. Dashboard layouts -- config-driven for arrangement, code for new widget types
4. Report templates -- text formatting config-driven, new chart types need code

---

## Architecture Recommendation

### Component Architecture

```
Frontend Architecture:
+----------------------------------------------------------+
|  Platform Shell (coded, unchanging)                       |
|  - Authentication, navigation frame, real-time engine     |
|  +------------------------------------------------------+|
|  |  Config-Driven Layout (from workspace config)         ||
|  |  - Sidebar composition                                ||
|  |  - Panel visibility                                   ||
|  |  - Theme application                                  ||
|  |  +--------------------------------------------------+||
|  |  |  Core Components (coded, reusable)                |||
|  |  |  - ThreadView, MessageBubble, ForkSidebar         |||
|  |  |  - ChannelList, AgentCard, MessageInput           |||
|  |  |  +----------------------------------------------+|||
|  |  |  |  Agent Component Catalog (coded components,   ||||
|  |  |  |  data-driven by agent responses)              ||||
|  |  |  |  - Table, Form, ActionButtons, SummaryCard    ||||
|  |  |  |  - Timeline, Progress, Poll, DecisionRecord   ||||
|  |  |  |  - Vertical-specific: appointment_slot, etc.  ||||
|  |  |  +----------------------------------------------+|||
|  |  +--------------------------------------------------+||
|  +------------------------------------------------------+|
+----------------------------------------------------------+
```

### Config Resolution Flow

```
Admin saves config
       |
       v
Config API validates against schema
       |
       v
4-layer merge (platform -> template -> workspace -> user)
       |
       v
Resolved config cached (per workspace + per user)
       |
       v
Frontend fetches resolved config on load
       |
       v
Layout engine applies config to component tree
       |
       v
Agent responses reference catalog components
       |
       v
Catalog renderer maps agent JSON to React components
```

### Implementation Priority for MVP

**Phase 1 (Dogfood):**
- Core components coded (thread, message, fork, channel)
- Minimal config: theme, agent roster, channel structure
- Agent responses: text + basic catalog (table, action_buttons, summary_card)
- No admin console (config via YAML files during dogfood)

**Phase 2 (Pre-launch):**
- Full config system with 4-layer merge
- Admin console (CLI or web)
- Extended catalog (form, timeline, progress, poll, decision_record)
- First vertical template (internal/vibe)

**Phase 3 (Vertical expansion):**
- Vertical-specific catalog components (appointment_slot, case_status, rfi_card)
- Template marketplace
- Plugin/extension API for custom components

---

## Open Questions

1. **A2UI adoption**: Should OpenVibe adopt Google's A2UI protocol for the agent component catalog format, or design a proprietary format? A2UI is appealing for interoperability but is still v0.8. Recommendation: design proprietary format now, keep compatible with A2UI concepts, consider adoption when A2UI reaches v1.0.

2. **Component catalog governance**: Who decides which components get added to the catalog? Platform team only? Or allow vertical template developers to register new components? This affects the plugin/extension story.

3. **Server-side vs client-side rendering of agent components**: Vercel's approach (React Server Components) has advantages for security and performance but their RSC work is paused. Should we go client-side for simplicity? Recommendation: client-side rendering for MVP, evaluate SSR later.

4. **Config validation UI**: How does an admin know their config is valid before deploying? Need a "preview" mode or "dry run" capability. Important for compliance-sensitive verticals.

5. **Terminology customization depth**: How far does label customization go? Just nouns ("Patient" -> "Client") or also verbs ("Resolve" -> "Close")? And UI element names ("Fork" -> "Side Discussion")? Deeper customization = more config complexity.

6. **Mobile UI configurability**: Is the mobile layout also config-driven, or a separate concern? For MVP (no mobile), not relevant. But the config schema should be designed to support mobile layout rules eventually.

7. **Dark mode as config**: Should dark/light mode be a platform-level setting, a workspace setting, or a user preference? Recommendation: user preference (Layer 4), with workspace ability to set default (Layer 3).

---

## Rejected Approaches

### Pure LLM-Generated UI (Option A)
**Rejected because:** Unpredictable output incompatible with compliance requirements (HIPAA, legal privilege). Testing burden is infinite. Vercel pausing AI SDK RSC development is a strong signal. A2UI's declarative approach is the industry direction -- agents describe intent, clients render safely.

**Reconsider if:** LLM reliability reaches a point where generated UI is consistently correct, accessible, and secure. Also reconsider if A2UI reaches v1.0 and provides a standard protocol for safe generative UI.

### No Config System (Pure Code)
**Rejected because:** Contradicts the core business model. Each new vertical needing custom code means linear engineering cost growth. The 4-layer config system is a competitive advantage.

**Reconsider if:** It turns out that vertical differences are so deep that config cannot meaningfully capture them. (Unlikely based on the analysis above -- 80% of differences are config-driven.)

### Salesforce-Style Config Monster
**Rejected because:** Over-configuring everything leads to an admin experience as complex as coding. The goal is a focused set of high-impact configuration points, not a general-purpose app builder.

**Reconsider if:** Enterprise customers demand extremely granular control. Then consider a tiered admin experience (simple mode / advanced mode) rather than exposing everything.

### Adopt A2UI Protocol Now
**Rejected because:** Still v0.8 and evolving. Premature to build on an unstable specification. The concepts are sound but the protocol details may change significantly.

**Reconsider if:** A2UI reaches v1.0 with broad adoption. At that point, adopting the protocol provides interoperability with the broader agent ecosystem.

---

*Research completed: 2026-02-07*
*Researcher: thread-interaction-designer*
*Dependencies: Depends on R1 (Thread Model) for interaction patterns. Informs M2 (Frontend) redesign.*
