# Phase 1.5: Admin-Configurable UI System

> How does an admin control and rearrange UI modules to serve different industries without custom code?

> Researcher: admin-ui-designer | Date: 2026-02-07 | Status: Complete

---

## Research Question

Phase 1 validated that config handles ~75% of vertical differentiation (R2, R5). The 4-layer config system (Platform -> Template -> Workspace -> User) is sound. But the actual admin experience for configuring UI -- how an admin arranges modules, controls layouts, manages components -- was never designed.

This research answers:
1. What exactly is configurable in the UI, and what is not?
2. What does the Admin Console look like for UI configuration?
3. How does config reach the frontend at runtime?
4. What is the MVP agent component catalog?
5. How does the same platform look different for 3 industries?
6. What is the minimum viable admin config for dogfood vs first customer?

---

## Sources Consulted

### Internal Design Docs
- `docs/architecture/DESIGN-SPEC.md` -- 4-layer config, "Configuration over Code" principle
- `docs/specs/CONFIG-SYSTEM.md` -- Full config schema, merge logic, Admin Console CLI commands
- `docs/specs/VERTICALS.md` -- Template structure for medical/legal/construction
- `docs/research/R2-GENERATIVE-UI.md` -- Config-driven template system + agent component catalog
- `docs/research/R5-CLI-BLEND-RISKS.md` -- Pluggability spectrum (L1-L5), Backstage/Retool analysis, industry UI difference (55/20/25 split)
- `docs/research/SYNTHESIS.md` -- 75% config-driven validation, deferred items list
- `docs/design/M2-FRONTEND.md` -- Discord-like layout, Next.js stack

### External Research
- **Retool** -- Drag-and-drop admin panel builder with 50+ pre-built components. Config stored as JSON in PostgreSQL. Components connect to data sources via configuration. Key insight: even with drag-and-drop, you need someone who thinks like a developer for 40% of customization.
- **Notion** -- Block-based architecture where everything is a block (text, images, pages). PostgreSQL backend, partitioned by workspace ID. Blocks have parent-child relationships forming a tree. Key insight: the block model is powerful for content, but Notion does NOT let admins configure the application shell -- only the content within it.
- **Backstage (Spotify)** -- Extension point architecture. Plugins register UI components via `createExtension()` with attachment points and output definitions. Frontend extensions communicate parent-to-child. Key insight: extension point interfaces are public APIs that require careful governance.
- **Shopify Themes** -- Sections + Blocks architecture. Admins drag-and-drop sections (up to 25 per template, 1250 blocks total). Theme customizer provides live preview. `theme.json` defines settings schema. 2025: Horizon theme system with nested blocks. 2026: AI-generated blocks from text prompts. Key insight: the sections/blocks model is the most mature admin-facing UI configuration system in production today.
- **Strapi** -- Admin panel is a React SPA customizable via `src/admin/app` config object. Content types are fully admin-configurable. Plugin architecture for dashboard widgets. Key insight: Strapi separates "content structure config" (admin) from "UI rendering" (developer), which maps well to OpenVibe's needs.
- **WordPress Full Site Editing** -- Block-based editing replacing the old Customizer. Block patterns = pre-arranged block groups. Global Styles via `theme.json`. 68% of professionals now prefer FSE themes over page builders (2025 poll). Key insight: the transition from "customizer with limited options" to "block-based full control" took WordPress 5+ years. Start simple.
- **Airbnb Ghost Platform (SDUI)** -- Server-driven UI with "Sections" and "Screens" as building blocks. Single GraphQL schema serves web, iOS, Android identically. `SectionComponentType` enum maps data to visual renderings. Key insight: SDUI decouples "what to show" (server/config) from "how to render" (client), which is exactly what OpenVibe needs.
- **Netflix SDUI** -- Client is a "rendering engine" displaying whatever the server describes. Changes deploy instantly without app updates. Key insight: the server-driven approach enables A/B testing and instant iteration, but requires a well-defined component registry.

---

## Part 1: What Is Configurable

### 1.1 Configurable Elements (Admin Can Change Without Code)

| Category | Element | Config Mechanism | Example |
|----------|---------|-----------------|---------|
| **Layout** | Sidebar position | `ui.layout.sidebarPosition: "left" | "right"` | Medical: left sidebar. Construction: right sidebar for wider content area |
| **Layout** | Panel visibility | `ui.panels.{panelId}.visible: boolean` | Hide device panel for non-hardware workspaces |
| **Layout** | Panel order | `ui.panels.{panelId}.order: number` | Agents panel above channels, or below |
| **Layout** | Default view | `ui.defaultView: "channels" | "threads" | "dashboard"` | Construction: open to project dashboard. Medical: open to today's schedule |
| **Components** | Sidebar sections | `ui.sidebar.sections: [{id, label, visible, order}]` | Show/hide "Agents", "Channels", "Devices", "Forks" sections |
| **Components** | Dashboard widgets | `ui.dashboard.widgets: [{type, position, size, config}]` | Grid of widgets: agent activity, recent threads, metrics |
| **Components** | Header actions | `ui.header.actions: [{id, label, icon, action}]` | Quick-action buttons in header: "New Thread", "Start Fork" |
| **Terminology** | All user-facing labels | `ui.terminology: {thread: "Case", fork: "Side Discussion", agent: "Assistant", channel: "Department"}` | Medical: "Patient Thread". Legal: "Case Thread". Construction: "Project Thread" |
| **Terminology** | Menu names | `ui.terminology.menu.*` | "Channels" -> "Departments" or "Projects" |
| **Terminology** | Status labels | `ui.terminology.status.*` | "Resolved" -> "Closed" or "Completed" |
| **Agent Roster** | Available agents | `agents.enabled: ["@Scheduler", "@Insurance"]` | Already in CONFIG-SYSTEM.md |
| **Agent Roster** | Agent display names | `agents.config.{id}.displayName` | "@FollowUp" -> "Follow-Up Nurse" |
| **Agent Roster** | Agent avatars | `agents.config.{id}.avatar` | Custom avatar per workspace |
| **Agent Roster** | Agent order in sidebar | `agents.config.{id}.order: number` | Primary agents first |
| **Permissions** | Role-based panel visibility | `permissions.roles.{role}.ui.panels: [...]` | Front desk sees limited panels vs physician |
| **Permissions** | Feature toggles per role | `permissions.roles.{role}.features: {forks: boolean, agentMention: boolean}` | Restrict fork creation to managers |
| **Branding** | Colors | `ui.branding.primaryColor, accentColor, backgroundColor` | Clinic blue, law firm dark gray |
| **Branding** | Logo | `ui.branding.logo: url` | Workspace logo in sidebar header |
| **Branding** | Favicon | `ui.branding.favicon: url` | Custom favicon |
| **Branding** | Workspace name | `workspace.displayName` | "Downtown Medical Clinic" |
| **Thread Behavior** | Default view mode | `threads.defaultView: "linear" | "threaded"` | Linear for simple workspaces |
| **Thread Behavior** | Fork settings | `threads.forks.enabled: boolean, maxDepth: 1` | Disable forks for simple use cases |
| **Thread Behavior** | Auto-summary threshold | `threads.autoSummary.messageThreshold: 15` | Trigger summary after N messages |
| **Notifications** | Default notification level | `notifications.default: "all" | "mentions" | "none"` | Per-workspace default |
| **Notifications** | Fork notification policy | `notifications.forks: "creators_only" | "all_participants"` | Control fork noise |
| **Agent Components** | Allowed components per workspace | `ui.agentComponents.allowed: ["text", "table", "action_buttons", ...]` | Restrict agents to simple responses in some workspaces |

### 1.2 What Is NOT Configurable (and Why)

| Element | Why Not Configurable | Risk If Made Configurable |
|---------|---------------------|--------------------------|
| **Core interaction patterns** (thread/message/reply/fork/resolve) | This is the product. Changing the interaction model changes the product identity. | Fragmented UX, impossible to document or support, user confusion across workspaces |
| **Message rendering pipeline** (markdown parsing, code highlighting, agent response rendering) | Performance-critical path. Must be optimized and tested as a unit. | Rendering bugs, XSS vulnerabilities, accessibility failures |
| **Auth flows** (login, signup, OAuth, session management) | Security-critical. Must follow security best practices exactly. | Authentication bypass, session hijacking, credential exposure |
| **Permission enforcement** (RLS policies, API authorization) | Security-critical. Config controls *what* permissions exist; code controls *how* they're enforced. | Privilege escalation, data leakage between workspaces |
| **Real-time message delivery** (Supabase Realtime subscriptions, WebSocket management) | Infrastructure-level. Performance and reliability depend on specific implementation. | Message loss, duplicate delivery, memory leaks |
| **Fork resolution algorithm** (how AI generates summaries) | Quality-critical. This is the "load-bearing wall" from SYNTHESIS.md. | Bad summaries pollute main threads, destroying trust in the system |
| **Accessibility patterns** (WCAG compliance, keyboard navigation, screen reader support) | Compliance-critical. Must work consistently regardless of configuration. | Legal liability (ADA), excluded users, broken experience |
| **Component rendering logic** (how React components render agent responses) | Stability-critical. Components must be tested, accessible, performant. | Broken UI, crashes, inconsistent behavior |
| **Data model structure** (database schema, table relationships) | Architectural foundation. Changes here cascade to every layer. | Data corruption, migration nightmares, query performance degradation |
| **Search infrastructure** (indexing, embedding generation, query parsing) | Performance-critical. Must be optimized for the data model. | Slow search, missing results, resource exhaustion |

### 1.3 The Boundary Rule

**Configurable = what, where, who, when.**
Config controls what appears, where it appears, who sees it, and when it triggers.

**Not configurable = how.**
Code controls how things render, how security is enforced, how data flows, how AI generates output.

This maps cleanly to Airbnb's SDUI principle: the server (config) decides "what to show," the client (code) decides "how to render it."

---

## Part 2: What Is NOT Configurable -- Deeper Analysis

### 2.1 What Would Break If Made Configurable

| If You Made This Configurable... | What Breaks |
|----------------------------------|-------------|
| Message ordering algorithm | Users in the same thread see different message orders. Conversations become incoherent. |
| Fork display location | Some users see forks inline, others in sidebar. Collaboration requires shared spatial context. |
| Agent response format | Agent sends structured JSON but workspace configured to render as plain text. Data loss. |
| Keyboard shortcuts | Users switching between workspaces lose muscle memory. Support burden increases. |
| Component prop types | Agent sends number, workspace config expects string. Runtime crash. |
| WebSocket reconnection behavior | Unreliable messaging in some workspaces. Users don't trust the system. |

### 2.2 The "Escape Hatch" for Genuine Custom Needs

When a workspace genuinely needs UI behavior outside the config boundary:

1. **Custom CSS** (cosmetic only): Allow workspace-scoped CSS overrides for branding. Low risk, high value.
2. **Custom components** (plugin API, Phase 5+): Backstage-style extension points. Developer writes a React component, registers it. Admin enables it.
3. **Feature request**: If multiple workspaces need the same "custom" thing, it should become a platform feature.

The escape hatch must NOT be available in dogfood or early customer phase. It adds complexity that is not justified until there are many workspaces with diverse needs.

---

## Part 3: Admin Console Design

### 3.1 Options Explored

#### Option A: YAML-First (Config Files)

**Description:** Admin edits YAML files directly. No visual interface. Config is versioned in the database (or Git for dogfood).

```yaml
# workspace-config.yaml
workspace:
  name: "Downtown Medical Clinic"
  template: "medical-clinic"

ui:
  layout:
    sidebarPosition: "left"
  branding:
    primaryColor: "#2563eb"
    logo: "/assets/clinic-logo.png"
  terminology:
    thread: "Patient Thread"
    fork: "Side Discussion"
    agent: "AI Assistant"
  sidebar:
    sections:
      - id: "agents"
        label: "AI Assistants"
        visible: true
        order: 1
      - id: "channels"
        label: "Departments"
        visible: true
        order: 2
      - id: "devices"
        visible: false
  dashboard:
    widgets:
      - type: "agent-activity"
        position: { row: 0, col: 0 }
        size: { width: 2, height: 1 }
      - type: "recent-threads"
        position: { row: 0, col: 2 }
        size: { width: 2, height: 1 }
```

**Pros:**
- Zero UI development needed
- Version-controllable (Git)
- Full flexibility for power users
- Fastest to implement
- Familiar to technical admins

**Cons:**
- Not accessible to non-technical admins
- No live preview
- Easy to make syntax errors
- No validation until save
- No discoverability (must know the schema)

**Verdict:** Right for dogfood. Wrong for customers.

#### Option B: Form-Based Web UI

**Description:** Traditional admin panel with forms, dropdowns, toggles. Similar to WordPress Customizer or Strapi admin panel.

```
+---------------------------------------------------+
| Admin Console                                      |
|                                                    |
| [Branding] [Layout] [Agents] [Permissions] [...]   |
|                                                    |
| == Branding ==                                     |
|                                                    |
| Workspace Name: [Downtown Medical Clinic    ]      |
| Primary Color:  [#2563eb] [color picker]           |
| Logo:           [clinic-logo.png] [Upload]         |
|                                                    |
| == Terminology ==                                  |
|                                                    |
| "Thread" displays as: [Patient Thread      ]       |
| "Fork" displays as:   [Side Discussion     ]       |
| "Agent" displays as:  [AI Assistant        ]       |
| "Channel" displays as:[Department          ]       |
|                                                    |
| [Save]  [Preview]  [Discard Changes]               |
+---------------------------------------------------+
```

**Pros:**
- Accessible to non-technical admins
- Guided experience (forms tell you what's possible)
- Built-in validation
- Standard pattern (everyone knows forms)

**Cons:**
- No spatial understanding (can't see how layout looks)
- Each new config option needs a form field
- Scales poorly with many options (becomes overwhelming)
- No way to see combined effect of changes

**Verdict:** Good for simple settings (branding, terminology). Insufficient for layout configuration.

#### Option C: Visual Builder (Retool/Shopify Style)

**Description:** Drag-and-drop visual builder where admin manipulates a representation of the actual UI. Sections and blocks can be reordered, resized, shown/hidden.

```
+---------------------------------------------------+
| Admin: Layout Builder                    [Preview] |
|                                                    |
| +-------+  +-----------------------------------+  |
| |Sidebar |  | Main Area                         |  |
| |        |  |                                   |  |
| |[Agents]|  | +------+ +------+ +------+        |  |
| | drag   |  | |Widget| |Widget| |Widget|        |  |
| |[Chann.]|  | |Agent | |Recent| |Metric|        |  |
| | drag   |  | |Activ.| |Thread| |      |        |  |
| |[Device]|  | +------+ +------+ +------+        |  |
| | hidden |  |                                   |  |
| |        |  | +---------------------------+     |  |
| |        |  | | Thread View               |     |  |
| |        |  | |                           |     |  |
| |        |  | +---------------------------+     |  |
| +-------+  +-----------------------------------+  |
|                                                    |
| Drag sections to reorder. Click to configure.      |
+---------------------------------------------------+
```

**Pros:**
- Intuitive spatial configuration
- Live preview of changes
- Discoverability (see all available widgets/sections)
- Matches mental model of "rearranging the UI"

**Cons:**
- Significant development effort (weeks, not days)
- Complex state management for drag-and-drop
- Must maintain parity between builder and actual UI
- Edge cases in responsive layout
- Shopify took years to mature their builder

**Verdict:** Right long-term vision. Too expensive for early phases.

#### Option D: Hybrid (Forms + Simplified Visual Preview)

**Description:** Form-based configuration with a live preview panel showing the actual workspace UI with config changes applied. Not drag-and-drop, but the admin sees the effect immediately.

```
+---------------------------------------------------+
|  Config                 |  Live Preview            |
|                         |                          |
|  == Sidebar ==          |  +------+  +----------+ |
|  Agents: [v] visible    |  |Agents|  | #general | |
|    Order: [1]           |  | @Sch.|  |          | |
|    Label: [AI Asst.]    |  | @Ins.|  |  Thread  | |
|                         |  |      |  |  view    | |
|  Channels: [v] visible  |  |Depts |  |          | |
|    Order: [2]           |  | #ER  |  |          | |
|    Label: [Departments] |  | #Lab |  |          | |
|                         |  |      |  |          | |
|  Devices: [ ] hidden    |  +------+  +----------+ |
|                         |                          |
|  == Branding ==         |  (preview updates live)  |
|  Color: [#2563eb]       |                          |
|                         |                          |
|  [Apply] [Discard]      |                          |
+---------------------------------------------------+
```

**Pros:**
- Admin sees effect of changes immediately
- Form-based (accessible, validated, guided)
- Preview provides spatial context without drag-and-drop complexity
- Incremental: start with form-only, add preview later
- Preview can be the actual app in an iframe with config overlay

**Cons:**
- Preview iframe adds complexity
- Two-panel layout requires wider screen
- Still form-based for ordering (no drag-and-drop)
- Must keep preview in sync with config changes

**Verdict:** Best balance of effort vs experience. Recommended.

### 3.2 Recommendation: Phased Admin Console

| Phase | Admin Interface | Who Uses It |
|-------|----------------|-------------|
| **Dogfood** | YAML files (Option A) | Vibe team (technical) |
| **First customers** | Form-based admin (Option B) + live preview (Option D) | IT admins |
| **Scale** | Visual builder (Option C) | Non-technical admins |

### 3.3 Admin Console Architecture

#### Tab Structure

```
Admin Console Tabs:
+--------+--------+---------+----------+--------+--------+--------+
|Overview|Branding| Layout  |  Agents  |  Roles |Threads |Advanced|
+--------+--------+---------+----------+--------+--------+--------+
```

**Overview Tab:**
- Workspace name, template, creation date
- Quick stats: users, agents, threads, storage
- Config health check (any warnings?)
- Recent config changes (audit log excerpt)

**Branding Tab:**
- Logo upload
- Color picker (primary, accent, background)
- Favicon upload
- Dark mode default (system/light/dark)

**Layout Tab:**
- Sidebar sections: list with visibility toggles and order
- Default landing view: dropdown (channels/threads/dashboard)
- Dashboard widget grid: add/remove/reorder widgets
- (Phase 2+: live preview panel)

**Agents Tab:**
- List of available agents (from template) with enable/disable toggles
- Per-agent config: display name, avatar, order, parameters
- Agent component restrictions (which response types allowed)

**Roles Tab:**
- List of roles with permissions matrix
- Per-role UI visibility (which panels, features)
- Create/edit custom roles

**Threads Tab:**
- Fork settings: enabled/disabled, max depth
- Auto-summary threshold
- Default thread type
- Notification defaults

**Advanced Tab:**
- Terminology overrides (key-value editor)
- Raw YAML editor (for power users)
- Config export/import
- Config history + rollback

### 3.4 Config Versioning and Rollback

Every config change creates a version:

```typescript
interface ConfigVersion {
  id: string;
  workspaceId: string;
  version: number;          // Auto-incrementing
  config: WorkspaceConfig;  // Full snapshot
  diff: ConfigDiff[];       // What changed from previous version
  changedBy: string;        // User ID
  changedAt: string;        // ISO timestamp
  description?: string;     // Optional change note
}

interface ConfigDiff {
  path: string;            // e.g., "ui.branding.primaryColor"
  oldValue: any;
  newValue: any;
}
```

**Rollback flow:**
1. Admin opens Config History
2. Sees list of versions with diffs
3. Clicks "Restore" on a version
4. System shows diff between current and target
5. Admin confirms
6. Creates a NEW version (not destructive revert) with the old config values
7. Audit log records the rollback

**Why snapshot-based, not event-sourced:** Event sourcing is elegant but overkill for config. Config is a small document (< 100KB). Full snapshots are simple, debuggable, and fast to restore. The diff is just for display.

### 3.5 Real-Time Preview vs Save-and-Reload

**Recommendation: Config changes apply on save, with optional preview.**

Why not real-time:
- Config changes can affect all users in the workspace
- Accidental changes should not propagate instantly
- Some config changes (e.g., agent enablement) have backend effects

Flow:
1. Admin makes changes in console
2. Changes are staged (not applied)
3. Preview panel shows what workspace will look like
4. Admin clicks "Apply"
5. Config saved to database as new version
6. Supabase Realtime pushes config update to all connected clients
7. Clients fetch new config and re-render affected components

Latency from "Apply" to visible change: < 2 seconds (Supabase Realtime + React re-render).

---

## Part 4: Technical Architecture

### 4.1 Config Storage

**Where:** PostgreSQL (Supabase) -- not files, not YAML on disk.

```sql
CREATE TABLE workspace_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id),
  version INT NOT NULL DEFAULT 1,
  config JSONB NOT NULL,
  diff JSONB,  -- Array of changes from previous version
  changed_by UUID REFERENCES users(id),
  changed_at TIMESTAMPTZ DEFAULT NOW(),
  description TEXT,

  UNIQUE(workspace_id, version)
);

-- Current config is always the latest version
CREATE VIEW current_configs AS
SELECT DISTINCT ON (workspace_id) *
FROM workspace_configs
ORDER BY workspace_id, version DESC;
```

**Why JSONB, not separate tables:**
- Config is a document, not relational data
- JSONB supports partial updates (`jsonb_set`)
- Can query nested paths (`config->'ui'->'branding'->'primaryColor'`)
- Schema validation happens in application layer, not database
- Easy to export/import as a single document

**Why not YAML files:**
- Files require filesystem access (doesn't work for multi-tenant SaaS)
- No atomic updates (partial writes corrupt files)
- No version history without Git
- No real-time notification of changes

**Exception for dogfood:** During Phase 3-4, config CAN be YAML files read at startup. The database-backed system is for Phase 5+. The config schema should be identical regardless of storage backend.

### 4.2 Config Delivery to Frontend

```
Admin saves config
       |
       v
PostgreSQL (workspace_configs table)
       |
       v
Supabase Realtime broadcasts "config_updated" event
       |
       v
All connected clients receive event
       |
       v
Client fetches resolved config via tRPC
       |
       v
Config stored in Zustand store (configStore)
       |
       v
React components re-render with new config
```

**API:**

```typescript
// tRPC router
const configRouter = router({
  // Get resolved config for current user
  getResolved: protectedProcedure
    .query(async ({ ctx }) => {
      const platform = await getPlatformDefaults();
      const template = await getTemplateConfig(ctx.workspace.templateId);
      const workspace = await getWorkspaceConfig(ctx.workspace.id);
      const user = await getUserPreferences(ctx.user.id);

      return mergeConfigs(platform, template, workspace, user);
    }),

  // Update workspace config (admin only)
  update: adminProcedure
    .input(z.object({
      updates: z.array(z.object({
        path: z.string(),
        value: z.any(),
      })),
      description: z.string().optional(),
    }))
    .mutation(async ({ ctx, input }) => {
      // 1. Validate against schema
      // 2. Check lock constraints
      // 3. Create new config version
      // 4. Broadcast update via Realtime
    }),
});
```

**Performance considerations:**
- Resolved config is cached per workspace+user in memory (Zustand)
- Cache invalidated on Realtime "config_updated" event
- Config fetch is a single query (latest version from workspace_configs)
- 4-layer merge is computed server-side, not client-side
- Config document is small (< 100KB) -- no pagination needed
- No rebuild required. Config is runtime data, not build-time data.

### 4.3 The 4-Layer Inheritance Model in Practice

```
Layer 1: Platform Defaults
  (hardcoded in codebase, versioned with releases)
  {
    ui.layout.sidebarPosition: "left",
    ui.branding.primaryColor: "#6366f1",
    threads.forks.enabled: true,
    threads.forks.maxDepth: 1,
    notifications.default: "mentions",
    agents.global.maxConcurrent: 10
  }
       |
       | Template can override (unless locked)
       v
Layer 2: Industry Template
  (stored in template registry, selected at workspace creation)
  {
    ui.terminology.thread: "Case",            // Legal-specific
    ui.terminology.channel: "Practice Area",
    agents.available: ["@Intake", "@Settlement"],
    compliance.attorneyClientPrivilege: true,  // locked: true
    threads.forks.enabled: true                // keep default
  }
       |
       | Admin can override (unless locked by template)
       v
Layer 3: Workspace Config
  (stored in workspace_configs table)
  {
    workspace.name: "Smith & Associates",
    ui.branding.primaryColor: "#1a1a2e",
    ui.branding.logo: "/uploads/smith-logo.png",
    agents.enabled: ["@Intake"],              // Admin chose to disable @Settlement
    agents.config.@Intake.displayName: "Case Coordinator"
  }
       |
       | User can override (only what workspace allows)
       v
Layer 4: User Preferences
  (stored in user_preferences table)
  {
    ui.theme: "dark",                         // Allowed by workspace
    notifications.default: "all",             // Allowed by workspace
    agents.pinned: ["@Intake"]                // Cosmetic preference
  }
```

**Resolved config for this user:**
```json
{
  "ui": {
    "layout": { "sidebarPosition": "left" },
    "branding": {
      "primaryColor": "#1a1a2e",
      "logo": "/uploads/smith-logo.png"
    },
    "terminology": {
      "thread": "Case",
      "channel": "Practice Area"
    },
    "theme": "dark"
  },
  "agents": {
    "enabled": ["@Intake"],
    "config": {
      "@Intake": { "displayName": "Case Coordinator" }
    },
    "pinned": ["@Intake"]
  },
  "compliance": {
    "attorneyClientPrivilege": true
  },
  "threads": {
    "forks": { "enabled": true, "maxDepth": 1 }
  },
  "notifications": { "default": "all" }
}
```

### 4.4 How Components Consume Config

**React Context + Hook pattern:**

```typescript
// ConfigProvider wraps the app
<ConfigProvider workspaceId={workspaceId} userId={userId}>
  <App />
</ConfigProvider>

// Any component reads config via hook
function Sidebar() {
  const config = useConfig();
  const t = useTerminology(); // Shorthand for config.ui.terminology

  return (
    <aside style={{ order: config.ui.layout.sidebarPosition === "right" ? 2 : 0 }}>
      {config.ui.sidebar.sections
        .filter(s => s.visible)
        .sort((a, b) => a.order - b.order)
        .map(section => (
          <SidebarSection key={section.id} label={section.label || t(section.id)}>
            {renderSectionContent(section.id)}
          </SidebarSection>
        ))
      }
    </aside>
  );
}

// Terminology hook
function ThreadHeader({ thread }) {
  const t = useTerminology();
  return <h2>{t("thread")}: {thread.title}</h2>;
  // Renders: "Case: Smith v. Jones" (legal)
  // Renders: "Patient Thread: John Doe Visit" (medical)
}
```

**Why React Context, not props drilling:**
- Config is needed by many components at different levels
- Props drilling would require every intermediate component to pass config
- Context provides a clean read path without coupling
- Zustand store behind the context handles caching and updates

**Why not Redux or global store directly:**
- Config is workspace-scoped, not global
- Context provides natural scoping per workspace
- Zustand is simpler than Redux for this use case
- The config hook is the public API; the store is an implementation detail

---

## Part 5: Agent Component Catalog -- MVP Set

### 5.1 MVP Components (7 Components)

R2 proposed ~15 components. For MVP, 7 cover the dogfood use cases.

#### 1. Text (Markdown)

```yaml
component: text
purpose: Default agent response. Markdown-formatted text with code blocks.
props:
  content: string     # Markdown content
  collapsible: boolean # For long responses, collapse after N lines
  maxLines: number     # Lines before "Show more"
admin_config: Always available. Cannot be disabled.
agent_selection: Default fallback. Agents use this unless a richer component fits.
```

#### 2. Table

```yaml
component: table
purpose: Structured data display. Sortable, filterable columns.
props:
  headers: [{key, label, sortable?, type?}]
  rows: [{key: value, ...}]
  filterable: boolean
  pageSize: number
  actions: [{label, action, row_key}]  # Optional per-row actions
admin_config: ui.agentComponents.allowed includes "table"
agent_selection: When response contains structured/tabular data (schedules, lists, comparisons).
example: "Here are Dr. Smith's available slots:" -> table of date/time/duration
```

#### 3. Action Buttons

```yaml
component: action_buttons
purpose: Row of clickable actions. The primary way agents present choices to users.
props:
  buttons: [{label, action, variant, data?, destructive?}]
  layout: "row" | "stack"
  exclusive: boolean  # Only one can be clicked (like radio buttons)
admin_config: ui.agentComponents.allowed includes "action_buttons"
agent_selection: When user needs to choose between discrete options.
example: "Book 10:00 AM Tue" / "Book 2:00 PM Thu" / "Show more times"
```

#### 4. Summary Card

```yaml
component: summary_card
purpose: Key-value summary of an entity. The agent's version of a "detail view."
props:
  title: string
  subtitle: string
  items: [{label, value, type?}]  # type: text, date, status, link
  actions: [{label, action}]       # Optional card-level actions
  status: {label, color}           # Optional status badge
admin_config: ui.agentComponents.allowed includes "summary_card"
agent_selection: When summarizing an entity (patient, case, project, thread).
example: Patient summary with name, DOB, insurance status, next appointment.
```

#### 5. Confirmation

```yaml
component: confirmation
purpose: Yes/no decision point. Used before agent takes consequential action.
props:
  question: string
  detail: string        # Additional context
  confirm_label: string # "Approve" / "Book" / "Send"
  cancel_label: string  # "Cancel" / "Not now"
  action: string        # What happens on confirm
  destructive: boolean  # Red styling for dangerous actions
admin_config: Always available (required for risk-based action classification).
agent_selection: Before any APPROVE-THEN-ACT action (from R3's risk classification).
example: "Send appointment confirmation to John Doe? This will text +1-555-1234."
```

#### 6. Progress

```yaml
component: progress
purpose: Show status of a long-running agent task.
props:
  label: string
  current: number
  total: number
  status: "running" | "paused" | "complete" | "failed"
  steps: [{label, status}]  # Optional step-by-step breakdown
  cancel_action: string      # Optional cancel button
admin_config: Always available (required for task lifecycle visibility).
agent_selection: When agent is executing a multi-step task (research, analysis, generation).
example: "Analyzing medical records... Step 3/5: Extracting treatment timeline"
```

#### 7. Form

```yaml
component: form
purpose: Collect structured input from the user. Agent-generated forms.
props:
  title: string
  fields: [{name, type, label, required, placeholder, options?, validation?}]
  submit_label: string
  submit_action: string
  cancel_label: string
admin_config: ui.agentComponents.allowed includes "form". compliance.auditLog required.
agent_selection: When agent needs structured input (not free text). Intake forms, data collection.
example: New patient intake: name, DOB, insurance provider, chief complaint.
```

### 5.2 How Admin Configures Component Availability

In workspace config:

```yaml
ui:
  agentComponents:
    allowed:
      - text           # Always available, cannot be removed
      - table
      - action_buttons
      - summary_card
      - confirmation   # Always available, cannot be removed
      - progress       # Always available, cannot be removed
      - form
    restricted:
      form:
        roles: ["physician", "admin"]  # Only these roles see forms
      action_buttons:
        requireConfirmation: true      # All actions require confirmation step
```

Admin can:
- Disable non-essential components (table, summary_card, form)
- Restrict components to specific roles
- Add confirmation requirements to action-producing components

Admin cannot:
- Disable text, confirmation, or progress (platform-locked)
- Change component rendering behavior
- Create new component types

### 5.3 How Agents Select Components

Agent responses include a `components` array in their structured output:

```json
{
  "text": "Dr. Smith has these available slots:",
  "components": [
    {
      "type": "table",
      "props": {
        "headers": [
          {"key": "date", "label": "Date"},
          {"key": "time", "label": "Time"},
          {"key": "duration", "label": "Duration"}
        ],
        "rows": [
          {"date": "2026-02-10", "time": "10:00 AM", "duration": "30 min"},
          {"date": "2026-02-12", "time": "2:00 PM", "duration": "30 min"}
        ]
      }
    },
    {
      "type": "action_buttons",
      "props": {
        "buttons": [
          {"label": "Book Tue 10:00", "action": "book_appointment", "data": {"slot": 1}},
          {"label": "Book Thu 14:00", "action": "book_appointment", "data": {"slot": 2}},
          {"label": "More times", "action": "expand_search"}
        ]
      }
    }
  ]
}
```

**Rendering pipeline:**

```
Agent produces response with components
       |
       v
Response reaches frontend
       |
       v
Component renderer checks:
  1. Is this component type in workspace's allowed list?
     NO  -> Fall back to text rendering of the data
     YES -> Continue
  2. Is this component restricted to certain roles?
     User not in allowed role -> Fall back to text
     User in allowed role -> Continue
  3. Render the component with provided props
       |
       v
React component renders with design system styling
```

**Fallback behavior is critical:** If a component type is disabled or restricted, the response must still be usable. Every component must have a meaningful text fallback. The agent's `text` field always contains a human-readable version of the response.

---

## Part 6: Industry Vertical Examples

### 6.1 Vibe Internal (Dogfood)

**Template:** `vibe-internal` (extends `_base`)

```yaml
workspace:
  name: "Vibe HQ"
  template: "vibe-internal"

ui:
  branding:
    primaryColor: "#6366f1"    # Indigo
    logo: "/assets/vibe-logo.svg"
  terminology:
    thread: "Thread"           # Default
    fork: "Fork"               # Default
    agent: "Agent"             # Default
    channel: "Channel"         # Default
  layout:
    sidebarPosition: "left"
    defaultView: "channels"
  sidebar:
    sections:
      - id: "channels"
        visible: true
        order: 1
      - id: "agents"
        visible: true
        order: 2
      - id: "devices"
        visible: false          # No hardware in dogfood
  dashboard:
    widgets:
      - type: "recent-threads"
      - type: "agent-activity"
      - type: "token-usage"    # Track costs

agents:
  enabled: ["@Assistant", "@Coder", "@Researcher"]
  config:
    "@Coder":
      displayName: "Code Agent"
      description: "Helps with code review, debugging, architecture"
    "@Researcher":
      displayName: "Research Agent"
      description: "Searches docs, summarizes, finds answers"

threads:
  forks:
    enabled: true
    maxDepth: 1
  autoSummary:
    messageThreshold: 20

ui.agentComponents:
  allowed: [text, table, action_buttons, summary_card, confirmation, progress, form]
```

**What it looks like:**
```
+----------+------------------------------------------+
| Vibe HQ  | #engineering                             |
|          |                                          |
| Channels | Thread: API redesign discussion           |
| #general |                                          |
| #engine. | @Charles: Let's rethink the auth flow     |
| #product |                                          |
| #random  | @Coder: I analyzed the current impl.     |
|          | [Summary Card: Current Auth Architecture] |
| Agents   | - Method: JWT + Refresh tokens            |
| @Assist. | - Issues: 3 identified                    |
| @Coder   | - Recommendation: Switch to session-based |
| @Resear. |                                          |
|          | [Action Buttons]                         |
|          | [See full analysis] [Create fork to      |
|          |  discuss alternatives]                   |
|          |                                          |
|          | Forks (2):                               |
|          | > Session-based auth exploration          |
|          | > OAuth2 provider comparison              |
+----------+------------------------------------------+
```

### 6.2 Medical Practice

**Template:** `medical-clinic`

```yaml
workspace:
  name: "Downtown Medical Clinic"
  template: "medical-clinic"

ui:
  branding:
    primaryColor: "#0891b2"     # Teal/medical
    logo: "/assets/dmc-logo.png"
  terminology:
    thread: "Patient Thread"
    fork: "Side Discussion"
    agent: "AI Assistant"
    channel: "Department"
  layout:
    sidebarPosition: "left"
    defaultView: "dashboard"    # Open to today's schedule
  sidebar:
    sections:
      - id: "channels"
        label: "Departments"
        visible: true
        order: 1
      - id: "agents"
        label: "AI Assistants"
        visible: true
        order: 2
      - id: "compliance"
        label: "HIPAA Status"
        visible: true
        order: 3
  dashboard:
    widgets:
      - type: "todays-schedule"        # Medical-specific widget
      - type: "insurance-verification" # Medical-specific widget
      - type: "agent-activity"
      - type: "recent-threads"

agents:
  enabled: ["@Scheduler", "@Insurance", "@Concierge"]
  config:
    "@Scheduler":
      displayName: "Scheduling Assistant"
      workingHours: "07:30-18:00"
      appointmentDuration: 20
    "@Insurance":
      displayName: "Insurance Verifier"
    "@Concierge":
      displayName: "Patient Concierge"
      greeting: "Welcome to Downtown Medical Clinic"

compliance:
  hipaa: true                          # locked: true by template
  auditLog: true                       # locked: true by template

permissions:
  roles:
    physician:
      ui.panels: ["all"]
      features: {forks: true, agentMention: true}
    front_desk:
      ui.panels: ["channels", "agents"]
      features: {forks: false, agentMention: true}
    billing:
      ui.panels: ["channels"]
      features: {forks: false, agentMention: false}

threads:
  forks:
    enabled: true
    maxDepth: 1
  types:
    default: "patient-encounter"

ui.agentComponents:
  allowed: [text, table, action_buttons, summary_card, confirmation, progress, form]
  restricted:
    form:
      roles: ["physician", "front_desk"]  # Billing can't submit forms
```

**What it looks like (Physician view):**
```
+----------+------------------------------------------+
| DMC      | Today's Schedule (Dashboard)             |
|          |                                          |
| Depts    | +--------+--------+--------+--------+    |
| #ER      | |10:00   |10:30   |11:00   |11:30   |   |
| #Primary | |J. Doe  |Empty   |A. Smith|Follow  |   |
| #Lab     | |Routine |        |New Pt  | -up    |   |
| #Billing | +--------+--------+--------+--------+    |
|          |                                          |
| AI Asst. | Insurance Verification                   |
| @Sched.  | J. Doe: [VERIFIED] Blue Cross PPO        |
| @Insur.  | A. Smith: [PENDING] Aetna HMO            |
| @Conci.  |                                          |
|          | Recent Patient Threads                    |
| HIPAA    | > J. Doe - Routine checkup (10:00)       |
| [Active] | > M. Johnson - Follow-up (Yesterday)     |
+----------+------------------------------------------+
```

**What it looks like (Front Desk view):**
```
+----------+------------------------------------------+
| DMC      | #Primary Care                            |
|          |                                          |
| Depts    | Patient Thread: John Doe - Routine       |
| #ER      |                                          |
| #Primary | @Concierge: Patient checked in.          |
| #Lab     | [Summary Card: Check-in Status]           |
|          | - Identity: Verified                      |
| AI Asst. | - Insurance: Blue Cross PPO - Verified    |
| @Sched.  | - Copay: $25 - Collected                  |
| @Conci.  | - Provider: Dr. Smith - Notified          |
|          |                                          |
|          | (No fork section - front desk can't fork) |
+----------+------------------------------------------+
```

### 6.3 Construction

**Template:** `construction`

```yaml
workspace:
  name: "BuildRight Projects"
  template: "construction"

ui:
  branding:
    primaryColor: "#ea580c"     # Orange/construction
    logo: "/assets/buildright.png"
  terminology:
    thread: "Project Thread"
    fork: "Investigation"
    agent: "Site Assistant"
    channel: "Project"
  layout:
    sidebarPosition: "left"
    defaultView: "dashboard"    # Open to project overview
  sidebar:
    sections:
      - id: "channels"
        label: "Projects"
        visible: true
        order: 1
      - id: "agents"
        label: "Site Assistants"
        visible: true
        order: 2
      - id: "safety"
        label: "Safety Status"
        visible: true
        order: 3
  dashboard:
    widgets:
      - type: "open-rfis"           # Construction-specific
      - type: "daily-log-status"    # Construction-specific
      - type: "safety-incidents"    # Construction-specific
      - type: "recent-threads"

agents:
  enabled: ["@RFI", "@DailyLog", "@Safety", "@DocSearch"]
  config:
    "@RFI":
      displayName: "RFI Manager"
    "@DailyLog":
      displayName: "Daily Log"
    "@Safety":
      displayName: "Safety Monitor"
    "@DocSearch":
      displayName: "Document Finder"

compliance:
  osha: true
  safetyReporting: true

threads:
  forks:
    enabled: true
    maxDepth: 1
  types:
    default: "project-thread"

ui.agentComponents:
  allowed: [text, table, action_buttons, summary_card, confirmation, progress, form]
```

**What it looks like:**
```
+----------+------------------------------------------+
| BuildRt  | Project Dashboard                        |
|          |                                          |
| Projects | Open RFIs: 7                             |
| #Main St | +-----+------------------+-------+----+ |
| #Oak Ave | |#042 |Foundation detail |@RFI   |3d  | |
| #Phase2  | |#041 |Steel spec change |@RFI   |5d  | |
|          | |#040 |Waterproofing     |@RFI   |7d  | |
| Site Ast | +-----+------------------+-------+----+ |
| @RFI     |                                          |
| @DailyL. | Daily Logs                               |
| @Safety  | Today: [NOT SUBMITTED]                   |
| @DocSrc. | Yesterday: Submitted (14 activities)     |
|          |                                          |
| Safety   | Safety: 42 days without incident         |
| [42 days]|                                          |
+----------+------------------------------------------+
```

### 6.4 What's Different, What's Same

| Element | Vibe Internal | Medical | Construction |
|---------|---------------|---------|--------------|
| **Shell layout** | SAME | SAME | SAME |
| **Sidebar structure** | SAME | SAME | SAME |
| **Thread/message/fork** | SAME | SAME | SAME |
| **Agent interaction** | SAME | SAME | SAME |
| **Search** | SAME | SAME | SAME |
| **Auth/login** | SAME | SAME | SAME |
| **Colors/logo** | Different | Different | Different |
| **Terminology** | Default | Medical terms | Construction terms |
| **Sidebar sections** | No devices | + HIPAA status | + Safety status |
| **Dashboard widgets** | Token usage | Schedule, Insurance | RFIs, Daily logs, Safety |
| **Agent roster** | Coder, Researcher | Scheduler, Insurance | RFI, DailyLog, Safety |
| **Role-based visibility** | Minimal | Physician vs front desk | PM vs superintendent |
| **Compliance indicators** | None | HIPAA banners | OSHA/safety |
| **Default landing** | Channels | Dashboard | Dashboard |

**The same platform core renders all three.** Differences are: terminology (100% config), branding (100% config), which widgets/agents/sections are visible (100% config), role-based restrictions (100% config). The only elements that need code are the industry-specific dashboard widgets (todays-schedule, insurance-verification, open-rfis, daily-log-status, safety-incidents) -- these are the ~25% from R5.

---

## Part 7: MVP vs Full Vision

### 7.1 Dogfood: Minimum Admin Config

For the Vibe team, the admin config system needs to be nearly invisible:

| What's Needed | How It's Done |
|---------------|---------------|
| Workspace name and branding | One YAML file, loaded at startup |
| Agent roster (which agents are available) | Same YAML file |
| Channel structure (#general, #engineering, etc.) | Created via UI, not config |
| User accounts | Supabase Auth, invite flow |
| Theme (dark/light) | User preference in browser |

**Total admin config for dogfood: ~30 lines of YAML.**

```yaml
# config/workspace.yaml (the only config file for dogfood)
workspace:
  name: "Vibe HQ"
  template: "_base"

agents:
  enabled: ["@Assistant", "@Coder", "@Researcher"]

ui:
  branding:
    primaryColor: "#6366f1"
  agentComponents:
    allowed: [text, table, action_buttons, summary_card, confirmation, progress]

threads:
  forks:
    enabled: true
```

No admin console UI is needed. The Vibe team edits this file directly. Changes require restart (acceptable for dogfood).

### 7.2 First External Customer: Minimum Admin Console

The first customer (likely a medical clinic or similar) needs:

| Feature | Priority | Effort |
|---------|----------|--------|
| Branding (logo, colors) | Must have | 2-3 days |
| Agent enable/disable | Must have | 1-2 days |
| Terminology customization | Must have | 2-3 days |
| Role-based visibility | Must have | 3-5 days |
| Dashboard widget selection | Should have | 3-5 days |
| Live preview | Should have | 5-7 days |
| Config history/rollback | Should have | 3-5 days |
| Sidebar section management | Nice to have | 2-3 days |
| YAML editor fallback | Nice to have | 1-2 days |

**Total: ~3-4 weeks of development for the form-based admin console.**

### 7.3 Phased Rollout Plan

```
Phase 3 (Dogfood):
  - YAML config file loaded at startup
  - ~30 lines of config
  - No admin console UI
  - Changes = edit file + restart
  - Duration: shipped with MVP

Phase 4 (Dogfood iteration):
  - Config moves to database (JSONB)
  - Simple admin page: branding + agents + terminology
  - No preview, no versioning
  - Changes apply on save (Supabase Realtime)
  - Duration: 1-2 weeks during iteration

Phase 5 (First customer):
  - Full form-based Admin Console (all tabs)
  - Config versioning + rollback
  - Role-based visibility controls
  - Live preview panel (iframe)
  - Industry template selection at workspace creation
  - Duration: 3-4 weeks

Phase 6+ (Scale):
  - Visual layout builder (drag-and-drop sections)
  - Dashboard widget composer
  - Template marketplace
  - Plugin/extension API for custom components
  - Config diffing between workspaces
  - Duration: ongoing
```

---

## Open Questions

1. **Component catalog governance:** Who decides when a new component is added? Platform team review? Community proposals? This affects how fast the catalog grows and how stable it remains. Recommendation: platform team only for MVP. Formal RFC process post-launch.

2. **Terminology depth:** How deep does label customization go? Just nouns ("Thread" -> "Case") or also verbs ("Resolve" -> "Close") and compound phrases ("Create Fork" -> "Start Investigation")? Recommendation: nouns only for MVP. Add verbs in Phase 6.

3. **Dark mode ownership:** Is dark mode a platform default, workspace default, or user preference? CONFIG-SYSTEM.md says user preference. But some workspaces (medical with high-contrast requirements) may want to enforce light mode. Recommendation: user preference, with workspace ability to lock.

4. **Config migration between template versions:** When the `medical-clinic` template is updated (new agent available, new widget type), how does an existing workspace get the update without losing its customizations? Recommendation: template updates are additive. New features appear as "available but not enabled." Breaking changes require explicit migration.

5. **Performance of config-driven rendering:** Does checking config for every component add meaningful render latency? Recommendation: unlikely to matter. Config is in-memory (Zustand). One `useConfig()` call per component is a plain object lookup. Profile during Phase 3 to verify.

6. **Mobile admin console:** Can admins configure the workspace from a phone? Recommendation: not for MVP. Admin console is desktop-only. The workspace itself should work on mobile eventually, but configuring it is a desktop task.

7. **Multi-workspace admin:** If one person admins multiple workspaces (e.g., a clinic chain), how do they manage configs across workspaces? Recommendation: out of scope until post-dogfood. Design the config API to be workspace-scoped, which naturally supports multi-workspace in the future.

---

## Rejected Approaches

### Rejected: Full Drag-and-Drop Visual Builder for MVP

**What:** Build a Retool/Shopify-style drag-and-drop interface as the first admin console.

**Why rejected:** 5-8 weeks of development for a feature that benefits zero dogfood users and maybe 1 early customer. The form-based approach covers the same functionality at 30% of the effort. WordPress took 5+ years to evolve from Customizer to Full Site Editing. We should not attempt it in Phase 5.

**Reconsider if:** We have 10+ customers who are non-technical and complain about the form-based admin. Or if a third-party library (like Plasmic or Builder.io) makes it trivial to embed.

### Rejected: GraphQL Schema for Config

**What:** Use a GraphQL schema to define config structure, with mutations for updates and subscriptions for real-time changes.

**Why rejected:** Over-engineering. Config is a single document, not a relational dataset. tRPC with JSONB is simpler, faster to implement, and sufficient. GraphQL adds a schema definition layer that duplicates what TypeScript types already provide.

**Reconsider if:** Config becomes complex enough that different admin views need different config projections. Or if multiple clients (web, mobile, CLI) need different config shapes.

### Rejected: Git-Based Config Storage

**What:** Store config as YAML files in a Git repository. Version history = Git history. Rollback = Git revert.

**Why rejected:** Works for dogfood (single workspace, technical users) but breaks for multi-tenant SaaS. Git requires filesystem access, doesn't support real-time notifications, and doesn't scale to thousands of workspaces. Also, admin users should not need to understand Git.

**Reconsider if:** OpenVibe pivots to a self-hosted-only model where each customer runs their own instance. Then Git-based config with GitOps workflows becomes appealing.

### Rejected: A2UI Protocol for Component Catalog

**What:** Adopt Google's A2UI protocol as the format for agent component responses.

**Why rejected:** A2UI is still v0.8 and evolving. Building on an unstable protocol creates a maintenance burden. The concepts are sound (declarative component descriptions, not code) and the catalog design follows A2UI principles. But the actual wire format should be OpenVibe-specific for now.

**Reconsider if:** A2UI reaches v1.0 with broad adoption. At that point, supporting A2UI as an input format (translated to internal catalog format) provides interoperability with third-party agents.

### Rejected: Per-User Layout Configuration

**What:** Allow individual users (not just admins) to rearrange their own layout: move sidebar sections, resize panels, choose dashboard widgets.

**Why rejected:** Complexity explosion. Every user has a unique layout. Support cannot reproduce user issues. Onboarding docs cannot show consistent screenshots. The value of per-user layout is low relative to the support burden.

**Reconsider if:** Power users demand it AND we have a robust "reset to workspace default" mechanism. Even then, limit to cosmetic changes (collapse sidebar, pin channels) rather than structural changes.

### Rejected: Runtime CSS-in-JS Theme Generation

**What:** Generate CSS dynamically at runtime based on config (colors, fonts, spacing). Every component reads theme from config.

**Why rejected:** CSS-in-JS has performance implications (runtime style computation, style injection). TailwindCSS with CSS custom properties (variables) achieves the same result with zero runtime cost. Set `--primary-color: #2563eb` from config, and all Tailwind utilities using that variable update automatically.

**How instead:** CSS custom properties set once on `<html>` from config. Tailwind references these variables. Zero runtime cost.

```css
/* Set once from config */
:root {
  --primary: theme('colors.indigo.500'); /* default */
}

/* Overridden by config at runtime */
<html style="--primary: #2563eb; --accent: #0891b2;">
```

---

*Research completed: 2026-02-07*
*Researcher: admin-ui-designer*
*Depends on: R2 (Generative UI), R5 (Pluggable Architecture), CONFIG-SYSTEM.md, SYNTHESIS.md*
*Informs: Phase 2 MVP spec (admin console design), M2 Frontend (config consumption), Phase 5 vertical expansion*
