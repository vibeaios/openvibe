# V3 Interface: Final Design

> Date: 2026-02-12
> Status: Final (Based on Discord-inspired architecture + B2B requirements)
> Purpose: Complete UI/UX design for OpenVibe V3

---

## Document Context

This document represents the **final interface design** for OpenVibe V3, based on:

1. **V3 Thesis** - Cognition as infrastructure, organizational transformation
2. **Discord-inspired architecture** - Dual sidebar, workspace isolation, extreme simplicity
3. **B2B requirements** - Workflows, agents, knowledge accumulation
4. **Iterative reasoning** - From initial thoughts → critical analysis → final decisions

**Key design decisions:**
- Discord's dual-sidebar model (✅ Adopted)
- Global functions in Home space (✅ Adopted)
- Extreme simplicity in workspace (✅ Adopted with B2B additions)
- Popup chat system for quick communication (✅ LinkedIn-inspired)
- Two-mode communication: Threads (structured) vs Chats (lightweight) (✅ Original design)
- Dual AI interaction: Thread AI (shared) vs Popup AI (personal) (✅ Original design)
- Private threads for formal sensitive discussions (✅ Topic-based, not group chats)

---

## Core Architecture

### Two-Layer Navigation (Discord-inspired)

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  Layer 1: Global         Layer 2: Workspace       │
│  (60px, icon-only)       (240px, expandable)      │
│                                                    │
│  ┌────┐                  ┌──────────────────┐    │
│  │ 🏠 │ Home            │ Workspace View   │    │
│  ├────┤                  │                  │    │
│  │ 🏢 │ Vibe ← Active   │ (Content)        │    │
│  │ 🏭 │ Client A         │                  │    │
│  │ 📦 │ Personal         │                  │    │
│  ├────┤                  │                  │    │
│  │ ➕ │ Add              │                  │    │
│  │ ⚙️ │ Settings         │                  │    │
│  └────┘                  └──────────────────┘    │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Design principle:**
- Layer 1 = Workspace switcher + Global personal space
- Layer 2 = Current workspace navigation + content
- Complete isolation between workspaces (like Discord servers)

---

## Layer 1: Global Navigation

### Home Space (Personal/Global)

```
┌────┐
│ 🏠 │ Home
│    │
│    │  When clicked, opens:
│    │
│    │  ┌─────────────────────────────────┐
│    │  │ Home                            │
│    │  ├─────────────────────────────────┤
│    │  │                                 │
│    │  │ ASK @VIBE (Global Agent)        │
│    │  │ ┌─────────────────────────────┐ │
│    │  │ │ 🤖 How can I help?          │ │
│    │  │ │                             │ │
│    │  │ │ Recent conversations:       │ │
│    │  │ │ • "Prepare board materials" │ │
│    │  │ │ • "Q1 performance summary"  │ │
│    │  │ └─────────────────────────────┘ │
│    │  │                                 │
│    │  │ MY TASKS (Cross-workspace)      │
│    │  │ ⚠️ 3 need your review            │
│    │  │ • Q1 Budget (Vibe > Finance)    │
│    │  │ • Strategy doc (Client A)       │
│    │  │ • Month-end (Vibe > Finance)    │
│    │  │                                 │
│    │  │ GLOBAL NOTIFICATIONS            │
│    │  │ 🔔 5 unread                     │
│    │  │ • Workflow approval (Vibe)      │
│    │  │ • @mention from Alice (Vibe)    │
│    │  │ • Analysis done (Client A)      │
│    │  │                                 │
│    │  │ RECENT ACTIVITY                 │
│    │  │ • Vibe > Finance                │
│    │  │ • Client A > Strategy           │
│    │  │ • Personal > Notes              │
│    │  └─────────────────────────────────┘
├────┤
│ 🏢 │ Vibe Workspace
│ 🏭 │ Client A
│ 📦 │ Personal Projects
├────┤
│ ➕ │ Add Workspace
│ ⚙️ │ Global Settings
└────┘
```

**Home space contains:**
1. **Ask @Vibe** - Global agent (master orchestrator)
2. **My Tasks** - Cross-workspace tasks and approvals
3. **Global Notifications** - Aggregated from all workspaces
4. **Recent Activity** - Quick jump to recent workspaces/spaces

**What's NOT in Home:**
- ❌ DM / Direct Messages (B2B product doesn't need global DM)
- ❌ Friends list (not a social product)

**Design rationale:**
- Follows Discord's pattern (global functions in Home)
- But adapted for B2B (tasks, agents, work-focused)

---

## Layer 2: Workspace View

### Overall Layout

```
┌──────────────────────────────────────────────────────────┐
│ Top Bar (Minimal, workspace-scoped)                      │
│ Finance > Q1 Budget Planning        [🔔 2]      [•••]    │
├────────────┬─────────────────────────────────────────────┤
│            │                                             │
│  Sidebar   │  Main Content Area                          │
│  (240px)   │  (Thread / Dashboard / Workflow detail)     │
│            │                                             │
│            │                                             │
│            │                                             │
│            │                                             │
│            │                                             │
└────────────┴─────────────────────────────────────────────┘
```

---

### Top Bar (Minimal - Learning from Discord)

```
┌──────────────────────────────────────────────────────────┐
│ Finance > Q1 Budget Planning              [🔔 2]  [•••]  │
└──────────────────────────────────────────────────────────┘
   ↑                                           ↑       ↑
Breadcrumb                               Workspace  More
(Current location)                       notifs   actions
```

**Only 3 elements:**
1. **Breadcrumb** - Shows current location (Space > Thread)
2. **[🔔 2]** - Workspace-scoped notifications
3. **[•••]** - More actions (workspace settings, admin)

**Why minimal?**
- Learned from Discord (no top bar in servers)
- But B2B needs breadcrumb (deeper hierarchy than Discord)
- Global functions moved to Home space (not here)

**[•••] More menu:**
```
┌─────────────────────┐
│ Workspace Settings  │
│ Manage Spaces       │
│ Manage Agents       │
│ Analytics           │
│ ────────────        │
│ Invite People       │
│ Integrations        │
└─────────────────────┘
```

---

### Sidebar (Two-Tier Structure)

**Design principle:** Top section (customizable functions) + Bottom section (fixed navigation)

```
┌───────────────────────────────┐
│ 🔍 Search            Cmd+K    │
├───────────────────────────────┤
│ TOP SECTION (User-customizable, priority-sorted)
│                               │
│ PINNED                     ▼  │ ← Optional, user-configured
│ • Q1 Budget (Finance)         │
│ • Bob Review (Finance)        │
├───────────────────────────────┤
│ 🏠 Workspace Home          ▶  │ ← Collapsible sections
│                               │
│ ⚙️ Workflows (5)           ▶  │
│                               │
│ 🤖 Agents                  ▶  │
│                               │
│ ••• More                   ▶  │
│                               │
├───────────────────────────────┤
│ BOTTOM SECTION (Fixed core navigation)
│                               │
│ SPACES                     ▼  │ ← Always visible, always expanded
│ • Finance (3)              ▼  │
│   • Q1 Budget Planning (12)   │
│   • Invoice Review (3)        │
│                               │
│ • RevOps (1)               ▶  │
│ • Executive                ▶  │
│ • Supply Chain             ▶  │
│                               │
│ [+ New Space]                 │
└───────────────────────────────┘
```

---

### Top Section: Customizable Functions

**Purpose:** Quick access to different workspace views (功能/视图入口)

**Key features:**
1. **User-customizable order** - Drag to reorder sections
2. **Show/hide sections** - Move unused sections to "More" menu
3. **Role-based defaults** - Different roles see different sections by default
4. **Expandable inline** - Click to expand, see details without leaving sidebar
5. **Badge indicators** - Show counts (e.g., "5 workflows need review")

---

#### Example: Workflows Section Expanded

```
⚙️ Workflows (5)           ▼  ← Expanded
┌─────────────────────────────┐
│ ⚠️ Need Review (5)           │
│   • Invoice #1234 ($12K)    │
│   • Vendor payment (urgent) │
│   • Lead score (Alice)      │
│   • Contract renewal        │
│   • Budget approval         │
│   [View All]                │
│                             │
│ ⟳ Active (23)               │
│   [View Dashboard]          │
│                             │
│ ✓ Completed Today (12)      │
│   [View History]            │
└─────────────────────────────┘
```

**Interaction:**
- Click section header → Toggle expand/collapse
- Click item (e.g., "Invoice #1234") → Main area jumps to that thread
- Click [View All] → Main area shows full Workflows Dashboard

**Benefits:**
- See details without leaving current thread context
- Quick scan of what needs attention
- One-click access to specific items

---

#### Example: Agents Section Expanded

```
🤖 Agents                  ▼
┌─────────────────────────────┐
│ @Finance_Agent    [L2] 🟢   │
│ ┌─────────────────────────┐ │
│ │ Now:                    │ │
│ │ • 15 workflows active   │ │
│ │ • 3 need your review    │ │
│ │                         │ │
│ │ Today:                  │ │
│ │ • 12 completed          │ │
│ │ • 94% success           │ │
│ │                         │ │
│ │ [View Details]          │ │
│ └─────────────────────────┘ │
│                             │
│ @RevOps_Agent     [L2] 🟢   │
│ ┌─────────────────────────┐ │
│ │ Now:                    │ │
│ │ • 8 workflows active    │ │
│ │ • 1 needs your review   │ │
│ │                         │ │
│ │ [View Details]          │ │
│ └─────────────────────────┘ │
│                             │
│ [Manage Agents]             │
└─────────────────────────────┘
```

---

#### More Menu

```
••• More                   ▶
┌─────────────────────────────┐
│ 📊 Analytics               │
│ ⚙️ Settings                 │
│ 👤 Admin                    │
│ 📁 Archive                  │
│                             │
│ Customize Sidebar...        │
└─────────────────────────────┘
```

**Contains:**
- Less frequently used sections
- Admin functions
- Settings and customization options

---

### Bottom Section: Fixed Navigation (SPACES)

**Purpose:** Core content navigation (内容导航入口)

**Key features:**
- **Always visible** - Cannot be hidden or moved
- **Always expanded** - At least showing space names
- **Primary navigation** - Main way to browse workspace content
- **Hierarchical** - Space > Threads structure

(Detailed Spaces section design continues below...)

---

### User Customization

#### Via Right-Click Menu

```
Right-click any top section header:

🏠 Workspace Home          ▶
  ↑ Right-click

┌─────────────────────┐
│ ✓ Show              │
│ ─────────────────── │
│ Move Up             │
│ Move Down           │
│ ─────────────────── │
│ Move to "More"      │ ← Hide to More menu
│ ─────────────────── │
│ Reset to Default    │
└─────────────────────┘
```

#### Via Settings UI

```
Settings > Sidebar Customization

Top Sections (drag to reorder):
┌─────────────────────────────┐
│ ⣿ Pinned                 ✓  │ ← Drag handle
│ ⣿ Workspace Home         ✓  │
│ ⣿ Workflows              ✓  │
│ ⣿ Agents                 ☐  │ ← Unchecked = hidden
│ ⣿ Analytics              ☐  │
└─────────────────────────────┘

Hidden (in More menu):
• Agents
• Analytics
• Admin

[Reset to Default]  [Save]
```

---

### Role-Based Default Configurations

**Individual Contributor:**
```
┌───────────────────────────────┐
│ 🏠 Workspace Home          ▶  │
│ ••• More                   ▶  │
├───────────────────────────────┤
│ SPACES                     ▼  │
│ ...                           │
└───────────────────────────────┘

(Workflows and Agents hidden in More)
```

**Dept Leader:**
```
┌───────────────────────────────┐
│ 🏠 Workspace Home          ▶  │
│ ⚙️ Workflows (5)           ▶  │
│ ••• More                   ▶  │
├───────────────────────────────┤
│ SPACES                     ▼  │
│ ...                           │
└───────────────────────────────┘

(Workflows visible by default)
```

**Admin:**
```
┌───────────────────────────────┐
│ 🏠 Workspace Home          ▶  │
│ ⚙️ Workflows (5)           ▶  │
│ 🤖 Agents                  ▶  │
│ ••• More                   ▶  │
├───────────────────────────────┤
│ SPACES                     ▼  │
│ ...                           │
└───────────────────────────────┘

(All sections visible)
```

**Users can always customize further.**

---

### Design Rationale

**Why two-tier structure?**

**Top Section = Function/View entry points**
- "How do I want to view this workspace?"
- Different perspectives: Home (overview), Workflows (process), Agents (executor)
- User-customizable: Everyone works differently

**Bottom Section = Content navigation**
- "Where is the specific content I need?"
- Fixed structure: Spaces > Threads
- Always accessible: Core navigation cannot be hidden

**Clear separation of concerns:**
- Top = "What view?" (功能入口)
- Bottom = "Which content?" (内容导航)

**Benefits:**
1. **Flexibility** - Users show only what they need
2. **Progressive disclosure** - New users see simple interface, power users add more
3. **Consistent** - All top sections use same expandable pattern
4. **Non-disruptive** - Expand in sidebar, don't switch main area context
5. **Future-proof** - Easy to add new sections to top area

---

### Spaces Section (Detailed)

```
SPACES                              ▼
┌─────────────────────────────────┐
│ Pinned (User-customized)        │
│ ⭐ Finance (3)                   │
│ ⭐ Executive                     │
│                                 │
│ Recent (Auto-sorted)            │
│ • RevOps (1)                    │
│ • Supply Chain                  │
│                                 │
│ All Spaces (Alphabetical)       │
│ • HR                            │
│ • Legal                         │
│ • Marketing                     │
│ [Show more...]                  │
│                                 │
│ ⊕ Create Space                  │
└─────────────────────────────────┘
```

**When a space is expanded (e.g., Finance):**

```
SPACES                              ▼
• Finance (3)                    ▼  ← Expanded

  Threads (5)
  • Q1 Budget Planning (12)
  • Invoice Review (3)
  • Month-End Close (8)

  Private (2)                    ▼  ← Can collapse
  🔒 Bob Performance Review
  🔒 Vendor Negotiation

• RevOps (1)
• Executive
```

**Key features:**
- Public and private threads both in the space
- Private threads have visual indicator (🔒)
- Unread counts shown in badges

---

### Workflows Section (Detailed)

```
WORKFLOWS                           ▼
┌─────────────────────────────────┐
│ ⚠️ Need Review (5)               │ ← Red badge, urgent
│    3 from Finance Agent         │
│    2 from RevOps Agent          │
│    [View Queue]                 │
│                                 │
│ ⟳ Active (23)                    │ ← Currently running
│    Invoice Processing (47/50)   │
│    Lead Scoring (Active)        │
│    Month-End Close (Paused)     │
│    [View All]                   │
│                                 │
│ ⏸ Paused (2)                     │ ← Waiting for input
│                                 │
│ ✓ Completed Today (12)           │
│                                 │
│ ────────────────────────────    │
│ 📊 View Full Dashboard          │
└─────────────────────────────────┘
```

**Click "Need Review (5)":**

```
Need Review Queue
┌─────────────────────────────────────┐
│ Bulk: [✓ Approve All] [Later]      │
├─────────────────────────────────────┤
│ □ Invoice #1234                     │
│   $12K (3x avg) - @Finance_Agent    │
│   Flagged: Unusual amount           │
│   [Approve] [Reject] [Details]      │
│                                     │
│ □ Vendor Payment #5678              │
│   New vendor "Acme Corp"            │
│   [Approve] [Reject] [Details]      │
│                                     │
│ □ Lead Score Update                 │
│   High-value lead detected          │
│   [Confirm] [Skip] [Details]        │
└─────────────────────────────────────┘
```

**Design for "frequent feedback" scenario:**
- One-click access from sidebar
- Bulk actions available
- Quick approve/reject without entering full thread

---

### Agents Section (Detailed)

```
AGENTS                              ▶  ← Collapsed by default

When expanded:
AGENTS                              ▼
┌─────────────────────────────────┐
│ @Finance_Agent       [L3] 🟢    │
│   15 workflows active           │
│   Success rate: 94%             │
│   [Configure] [Details]         │
│                                 │
│ @RevOps_Agent        [L2] 🟢    │
│   8 workflows active            │
│   Success rate: 87%             │
│   [Configure] [Details]         │
│                                 │
│ @QA_Agent            [L1] 🟡    │
│   Learning mode                 │
│   [Configure] [Details]         │
│                                 │
│ ⊕ Add Agent                     │
└─────────────────────────────────┘
```

**Shows:**
- Agent name and trust level
- Current status (🟢 Active, 🟡 Learning, 🔴 Error)
- Active workflows count
- Performance metrics
- Quick actions

---

## Main Content Area

### Workspace Home Dashboard

**Purpose:** Overview of the entire workspace - the "control panel" for daily work

**Access:**
- Click workspace icon in Layer 1 sidebar (🏢 Vibe)
- Click "🏠 Workspace Home" in Layer 2 sidebar
- Click workspace name in breadcrumb

**Layout:** Three-column dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Vibe Workspace                         [🔔 5]  [•••]        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Left Column           Center Column         Right Column   │
│  (Priority)            (Spaces Overview)     (Agents)       │
│                                                              │
│  ┌─────────────┐      ┌──────────────┐      ┌────────────┐ │
│  │ 📌 PRIORITY │      │ 📊 SPACES    │      │ 🤖 AGENTS  │ │
│  │             │      │              │      │            │ │
│  │ ⚠️ ACTION   │      │ Finance      │      │ @Finance   │ │
│  │   NEEDED(5) │      │ RevOps       │      │  Agent     │ │
│  │             │      │ Executive    │      │            │ │
│  │ 🔔 RECENT   │      │              │      │ @RevOps    │ │
│  │   UPDATES   │      │              │      │  Agent     │ │
│  │             │      │              │      │            │ │
│  └─────────────┘      └──────────────┘      └────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

#### Left Column: Priority & Updates

```
┌───────────────────────────────────┐
│ 📌 PRIORITY                       │
├───────────────────────────────────┤
│ ⚠️ ACTION NEEDED (5)              │
│                                   │
│ 🔴 Invoice #1234 needs approval   │
│    $12K (3x average)              │
│    Finance > Invoice Processing   │
│    [Review Now]                   │
│                                   │
│ 🟡 Q1 Budget needs decision       │
│    CFO @mentioned you             │
│    Finance > Budget Planning      │
│    [View Thread]                  │
│                                   │
│ 🟡 Vendor X payment delayed       │
│    @Finance_Agent flagged         │
│    Finance > Payments             │
│    [Check Status]                 │
│                                   │
│ [View All (5)]                    │
│                                   │
├───────────────────────────────────┤
│ 🔔 RECENT UPDATES (12)            │
│                                   │
│ • Finance: 3 workflows completed  │
│   2h ago                          │
│                                   │
│ • RevOps: Lead scoring updated    │
│   @Alice added analysis           │
│   4h ago                          │
│                                   │
│ • Executive: Board deck ready     │
│   @CFO approved                   │
│   Yesterday                       │
│                                   │
│ [View All]                        │
│                                   │
└───────────────────────────────────┘
```

**Design notes:**
- Priority first (needs my action)
- Sorted by urgency (🔴 urgent, 🟡 important, 🔵 info)
- One-click jump to specific thread/workflow
- Recent updates below (informational only)

---

#### Center Column: Spaces Overview

```
┌─────────────────────────────────────────┐
│ 📊 SPACES                               │
├─────────────────────────────────────────┤
│ Finance                              ▶  │
│ ┌─────────────────────────────────────┐ │
│ │ 📈 Activity Today                   │ │
│ │ • 23 workflows active               │ │
│ │ • 12 completed                      │ │
│ │ • 3 need review                     │ │
│ │                                     │ │
│ │ 🔥 Hot Threads (3 unread)           │ │
│ │ • Q1 Budget Planning (12)           │ │
│ │ • Invoice Review (3)                │ │
│ │                                     │ │
│ │ 🤖 @Finance_Agent: 94% success      │ │
│ │                                     │ │
│ │ [Open Finance Space]                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ RevOps                               ▶  │
│ ┌─────────────────────────────────────┐ │
│ │ 📈 Activity Today                   │ │
│ │ • 8 workflows active                │ │
│ │ • 5 completed                       │ │
│ │                                     │ │
│ │ 🔥 Hot Threads (1 unread)           │ │
│ │ • Lead Scoring Update (5)           │ │
│ │                                     │ │
│ │ 🤖 @RevOps_Agent: 87% success       │ │
│ │                                     │ │
│ │ [Open RevOps Space]                 │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Executive                            ▶  │
│ ┌─────────────────────────────────────┐ │
│ │ 📈 Activity Today                   │ │
│ │ • 2 threads active                  │ │
│ │ • Board Deck ready for review       │ │
│ │                                     │ │
│ │ [Open Executive Space]              │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Browse All Spaces]                     │
│                                         │
└─────────────────────────────────────────┘
```

**Design notes:**
- Each space = one card
- Shows today's activity (workflows, threads)
- Hot threads (with unread counts)
- Agent performance in that space
- Click card → Enter that Space

**This is Progressive Disclosure (architecture level):**
- Workspace Home = See all spaces at a glance
- Click space → See threads in that space
- Click thread → See detailed conversation

---

#### Right Column: Agents & Activity

```
┌───────────────────────────────────┐
│ 🤖 AGENTS                         │
├───────────────────────────────────┤
│ @Finance_Agent           [L2] 🟢  │
│ ┌───────────────────────────────┐ │
│ │ Today:                        │ │
│ │ • 15 workflows active         │ │
│ │ • 12 completed                │ │
│ │ • 94% success rate            │ │
│ │                               │ │
│ │ Recent:                       │ │
│ │ ✓ Invoice #1230-1242 approved │ │
│ │ ⚠️ Invoice #1234 flagged       │ │
│ │                               │ │
│ │ 📈 Performance (30d)          │ │
│ │ Success: 78% → 94% (+16%)     │ │
│ │ Trust ready for L3 upgrade ⬆️  │ │
│ │                               │ │
│ │ [View Details]                │ │
│ └───────────────────────────────┘ │
│                                   │
│ @RevOps_Agent            [L2] 🟢  │
│ ┌───────────────────────────────┐ │
│ │ Today:                        │ │
│ │ • 8 workflows active          │ │
│ │ • 5 completed                 │ │
│ │ • 87% success rate            │ │
│ │                               │ │
│ │ [View Details]                │ │
│ └───────────────────────────────┘ │
│                                   │
│ [Manage Agents]                   │
│                                   │
├───────────────────────────────────┤
│ 📊 WORKSPACE ACTIVITY             │
│                                   │
│ Today's Summary:                  │
│ • 31 workflows active             │
│ • 17 completed                    │
│ • 8 need review                   │
│ • 92% avg success rate            │
│                                   │
│ Top Contributors:                 │
│ 👤 CFO: 12 actions                │
│ 👤 Alice: 8 actions               │
│ 🤖 Finance Agent: 45 workflows    │
│                                   │
│ [View Analytics]                  │
│                                   │
└───────────────────────────────────┘
```

**Design notes:**
- Agent today's performance
- Growth trends (shows "workspace gets smarter")
- Trust level upgrade alerts
- Workspace overall metrics

**"Workspace gets smarter" embodied here:**
- Performance trends: 78% → 94% (+16%)
- Trust level upgrades: Ready for L3
- Reduced human review: 100% → 15%

---

#### Key Interactions

**1. From Priority to Thread:**
```
Click: Invoice #1234 [Review Now]
→ Main area: Finance > Invoice Processing thread
→ Sidebar: Finance space auto-expands to show that thread
→ Scroll to the specific message needing review
```

**2. From Space Card to Space:**
```
Click: Finance card [Open Finance Space]
→ Main area: Shows Finance space view
→ Sidebar: Finance section expands, showing all threads
```

**3. From Agent to Detail:**
```
Click: @Finance_Agent [View Details]
→ Main area: Agent Detail Page
  - Performance charts
  - Active workflows
  - Knowledge learned
  - Configuration
```

---

#### Dashboard vs Sidebar Sections

**Workspace Home Dashboard (this page):**
- Horizontal layout (three columns)
- Overview of entire workspace
- Used when: Starting work, checking overall status
- Portal (quick scan → jump to work)

**Sidebar Top Sections:**
- Vertical layout (expandable list)
- Detailed items in each section
- Used when: During work, quick checks
- Always accessible (don't leave current context)

**Complementary, not redundant:**
- Dashboard = Morning overview ("What's happening today?")
- Sidebar = During work ("Any new workflows need review?")

---

### Thread View (Human + Agent mixed)

```
Thread: "Q1 Budget Planning"
Space: Finance
Participants: CFO, Alice, @Finance_Agent

┌─────────────────────────────────────┐
│ CFO                    Today 2:30pm │ ← Human message
│ @Alice 我们需要调整Q2预算            │
│                                     │
│ [👍 1]  Reply                       │
├─────────────────────────────────────┤
│ Alice                  Today 2:32pm │ ← Human message
│ 好的，先看看数据                     │
├─────────────────────────────────────┤
│ CFO                    Today 2:33pm │ ← Human to Agent
│ @Finance_Agent 分析Q1 spend          │
├─────────────────────────────────────┤
│ [AI] @Finance_Agent    Today 2:34pm │ ← Agent message
│ 🤖 分析完成                         │
│                                     │
│ ■ Marketing超支15% ($45K over)      │ ← Progressive disclosure
│ ▸ View details...                   │
│                                     │
│ [👍] [👎] [Why?]  Reply             │
├─────────────────────────────────────┤
│ Alice                  Today 2:35pm │ ← Human message
│ 我看到了，那个campaign花太多         │
├─────────────────────────────────────┤
│ [AI] @Finance_Agent    Today 2:36pm │ ← Agent with artifact
│ 🤖 已生成详细报告                    │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ [Artifact] Q1 Spend Analysis    │ │
│ │ Last updated: 2:36 PM           │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│ │                                 │ │
│ │ Marketing:  $545K (Budget: $500K)│ │
│ │ Engineering: $720K (Budget: $800K)│ │
│ │                                 │ │
│ │ [Edit] [Export] [Share] [v1]    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [👍] [👎]  Reply                    │
└─────────────────────────────────────┘
```

**Key features:**
1. **Visual distinction** - [AI] badge and 🤖 icon for agent messages
2. **Unified UX** - Human and agent messages use same reply/react interface
3. **Artifacts embedded** - Deliverables shown inline but visually distinct
4. **Progressive disclosure** - Agent responses can be collapsed

---

### Workflow Dashboard View

```
Dedicated Workflow Interface (accessed from sidebar or thread link)

┌─────────────────────────────────────────────────────────┐
│ Workflows Dashboard                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ NEED REVIEW (5)                                    ⚠️   │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Invoice #1234        @Finance_Agent       [Act] │   │
│ │ $12K (3x avg)                                   │   │
│ │ [Approve] [Reject] [Details]                    │   │
│ ├─────────────────────────────────────────────────┤   │
│ │ Vendor Payment #5678  @Finance_Agent      [Act] │   │
│ │ New vendor                                      │   │
│ │ [Approve] [Reject] [Details]                    │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ACTIVE (23)                                             │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Invoice Processing   @Finance_Agent             │   │
│ │ ████████████████░░░░ 47/50 (94%)                │   │
│ │ [View Details]                                  │   │
│ ├─────────────────────────────────────────────────┤   │
│ │ Lead Scoring         @RevOps_Agent              │   │
│ │ ████████████████████ Running...                 │   │
│ │ [View Details]                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ BY AGENT                                                │
│ • @Finance_Agent (15 workflows, 94% success)            │
│ • @RevOps_Agent (8 workflows, 87% success)              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Accessed via:**
- Sidebar > Workflows > View Dashboard
- Thread > Agent workflow card > [View Details]

---

## Private Threads Design

### Core Principle: Private Thread ≠ DM

```
Slack DM:
- "Group: Alice, Bob, Charlie"
- No topic, no context
- Temporary grouping

OpenVibe Private Thread:
- "🔒 Bob Performance Review"
- Clear topic, has context
- Named conversation
```

**Key design decision:** Private threads must have a **topic name**, not just a list of participants.

---

### Creating a Private Thread

```
User clicks: [⊕ New Private Thread]

Step 1: Define Topic
┌─────────────────────────────────┐
│ Create Private Thread           │
├─────────────────────────────────┤
│ Thread Name* (Required)         │
│ [Bob Performance Review      ]  │
│                                 │
│ Space (Optional)                │
│ [Finance ▼]                     │ ← Can link to a space
│                                 │
│ Description (Optional)          │
│ [Discuss Bob's Q1 performance   │
│  and decide on next steps    ]  │
│                                 │
│ [Next: Invite Participants]     │
└─────────────────────────────────┘

Step 2: Invite Participants
┌─────────────────────────────────┐
│ Invite Participants             │
├─────────────────────────────────┤
│ [Search people...]              │
│                                 │
│ Selected:                       │
│ ✓ Alice Chen (you)              │
│ ✓ CFO                           │
│                                 │
│ Suggested (from Finance):       │
│ ○ Bob Wang                      │
│ ○ HR Manager                    │
│                                 │
│ [Back]  [Create Thread]         │
└─────────────────────────────────┘

Step 3: Confirmation
┌─────────────────────────────────┐
│ ✓ Private Thread Created        │
├─────────────────────────────────┤
│ Name: Bob Performance Review    │
│ Space: Finance                  │
│ Participants: You, CFO          │
│                                 │
│ ⚠️ Only invited participants     │
│ can see this thread.            │
│                                 │
│ [Go to Thread]                  │
└─────────────────────────────────┘
```

**Requirements:**
- ✅ Topic name is mandatory (no "Group: Alice, Bob")
- ✅ Can optionally link to a space (for context)
- ✅ Explicit participant list
- ❌ Cannot create "temporary group chat"

---

### Navigation: 3-Tier System

**Tier 1: Default in Space (90% of usage)**

```
Finance Space:

Threads
├─ Public
│  ├─ Q1 Budget Planning
│  └─ Invoice Review
│
└─ Private (2)                     ▼  ← Expandable
   ├─ 🔒 Bob Performance Review
   │   👤 CFO, Alice
   │   💬 Last: 2h ago
   │
   └─ 🔒 Vendor Negotiation
       👤 CFO, Alice, Bob
       💬 Last: 3 days ago
```

**UI in sidebar:**
```
┌───────────────────────────────┐
│ Finance                    ▼  │
├───────────────────────────────┤
│ Threads (5)                   │
│ • Q1 Budget Planning (12)     │
│ • Invoice Review (3)          │
│                               │
│ Private (2)                ▼  │ ← Collapse/expand
│ 🔒 Bob Performance Review     │
│ 🔒 Vendor Negotiation         │
└───────────────────────────────┘
```

---

**Tier 2: Pin to Sidebar Top (5% - urgent threads)**

```
Sidebar:
┌───────────────────────────────┐
│ PINNED                        │
│ 🔒 Bob Review (Finance)    !  │ ← Unread badge
│ ⭐ Q1 Strategy (Executive)    │
├───────────────────────────────┤
│ SPACES                        │
│ ...                           │
└───────────────────────────────┘
```

**User can pin important private threads to always be visible.**

---

**Tier 3: "All Private Threads" View (5% - finding old threads)**

```
Accessed via: Cmd+Shift+P or Search

┌─────────────────────────────────────┐
│ All Private Threads                 │
├─────────────────────────────────────┤
│ By Space:                           │
│                                     │
│ Finance (2)                      ▼  │
│ 🔒 Bob Performance Review           │
│    Last: 2h ago                     │
│    👤 CFO, Alice                    │
│                                     │
│ 🔒 Vendor Negotiation               │
│    Last: 3 days ago                 │
│    👤 CFO, Alice, Bob               │
│                                     │
│ Executive (1)                    ▼  │
│ 🔒 Board Meeting Prep               │
│    Last: 1 week ago                 │
│    👤 CFO, Board members            │
│                                     │
│ ───────────────────────────────     │
│ Recent Activity:                    │
│ • Bob Review (2h ago)               │
│ • Vendor Negotiation (3 days ago)   │
│ • Board Prep (1 week ago)           │
│                                     │
│ Status:                             │
│ • Active (3)                        │
│ • Inactive (5)                      │
│ • Archived (10) [Show...]           │
└─────────────────────────────────────┘
```

---

### Preventing Messy Problems

**Problem 1: Too many private threads**

```
System detection:
If user has >15 private threads:

┌─────────────────────────────────┐
│ 💡 Suggestion                    │
├─────────────────────────────────┤
│ You have 18 private threads in  │
│ Finance space.                  │
│                                 │
│ Consider:                       │
│ • Archive inactive threads (8)  │
│ • Make some public (if no       │
│   longer sensitive)             │
│ • Merge similar topics          │
│                                 │
│ [Review Threads]  [Dismiss]     │
└─────────────────────────────────┘
```

---

**Problem 2: Inactive threads cluttering**

```
Auto-archive mechanism:

If private thread has no activity for 30 days:

┌─────────────────────────────────┐
│ 🔒 Vendor Negotiation Strategy  │
│                                 │
│ ⚠️ No activity for 30 days       │
│                                 │
│ Options:                        │
│ [Keep Active]                   │
│ [Archive] ← Recommended         │
│ [Delete Permanently]            │
└─────────────────────────────────┘
```

**Archived threads:**
- Don't show in sidebar
- Searchable via Cmd+K or "All Private" view
- Can be un-archived anytime

---

**Problem 3: Sensitive discussions that are no longer sensitive**

```
AI suggestion after workflow/discussion completes:

┌─────────────────────────────────┐
│ 💡 @Finance_Agent noticed        │
├─────────────────────────────────┤
│ The vendor negotiation in this  │
│ private thread is now complete. │
│                                 │
│ Would you like to make this     │
│ public so the team can learn    │
│ from the process?               │
│                                 │
│ [Keep Private]  [Make Public]   │
└─────────────────────────────────┘
```

**Encourages transparency when appropriate.**

---

**Problem 4: Group chat vs named thread**

```
❌ Bad (like Slack):
Thread: "Group: CFO, Alice, Bob"
- No topic
- Don't know what it's about
- Hard to search

✅ Good (OpenVibe):
Thread: "🔒 Vendor X Pricing Negotiation"
Participants: CFO, Alice, Bob
Space: Finance
- Clear topic
- Searchable
- Has context
```

**Enforced by requiring topic name at creation.**

---

## Popup Chat System (Quick Communication)

> **Design Decision**: Separate lightweight, temporary communication (popup chats) from structured, persistent discussions (threads).

### Core Principle: Two Communication Modes

**Thread (Sidebar - Structured):**
- Formal discussions with clear topics
- Persistent, long-term storage
- Multi-participant collaboration
- Produces artifacts
- Example: "Q1 Budget Planning", "Bob Performance Review"

**Chat (Popup - Lightweight):**
- Quick questions and temporary conversations
- Short-term retention (7 days)
- 1:1 or small group
- Pure conversation
- Example: "Where is that data?", "Can you check this?"

---

### Information Architecture

```
Main Workspace (Sidebar):
┌─────────────────────────────────┐
│ SPACES                          │
│ • Finance                       │
│   - Q1 Budget Planning          │
│   - 🔒 Bob Performance Review   │
│                                 │
│ Structured, persistent content  │
└─────────────────────────────────┘

Bottom-right Popup Chats:
┌─────────────────────────────────┐
│ [💬 Alice] [🤖 Agent] [💬] [+]  │
│                                 │
│ Temporary, quick communication  │
└─────────────────────────────────┘
```

**Why this separation:**
- Reduces sidebar clutter
- Clear mental model (formal vs casual)
- Doesn't interrupt current workspace context
- Familiar pattern (LinkedIn, Facebook Messenger)

---

### UI Components

#### 1. Bottom Chat Bar

```
┌──────────────────────────────────────────┐
│                                          │
│  Main Workspace Content                 │
│  (Currently viewing: Q1 Budget thread)   │
│                                          │
└──────────────────────────────────────────┘
 [💬 Alice] [🤖 Finance Agent] [💬] [+]
    ↑          ↑                ↑    ↑
 Active     Active AI         Chat  New
 chat       chat              list  chat
```

**States:**
- **Minimized**: Shows as tab with name and unread badge
- **Active**: Popup window is open
- **Typing**: Shows "..." indicator on tab

---

#### 2. Chat Popup Window (Human-to-Human)

```
┌─────────────────────────────────┐
│ 💬 Alice Chen             [−][×]│
├─────────────────────────────────┤
│                                 │
│ Alice: 能帮我看一下这个数据吗？   │
│ 2 min ago                       │
│                                 │
│ You: 好的，在哪个thread？         │
│ Just now                        │
│                                 │
│ Alice: Q1 Budget Planning       │
│ Typing...                       │
│                                 │
├─────────────────────────────────┤
│ [Type a message...]        [🎤] │
│                            [📎] │
└─────────────────────────────────┘
     ↑                         ↑
  Message input          Voice/Attach
```

**Features:**
- Real-time typing indicator
- Read receipts (optional)
- Emoji reactions
- Can attach files/links
- Voice input

**Size:**
- Default: 320px × 400px
- Expandable: Up to 500px × 600px
- Multiple windows can be open simultaneously

---

#### 3. AI Chat Popup (Personal Assistant)

```
┌─────────────────────────────────┐
│ 🤖 Finance Agent          [−][×]│
│                           [↗️]   │ ← "Share in thread"
├─────────────────────────────────┤
│                                 │
│ You: 总结一下Q1 Budget           │
│      Planning这个thread          │
│ Just now                        │
│                                 │
│ 🤖 Agent: 📊 Summary            │
│                                 │
│ ■ Main topic: Q1 budget         │
│ ■ Key decision: Approve         │
│   $500K marketing spend         │
│ ■ Action items: 3               │
│ ▸ View full thread              │
│                                 │
│ [👍] [👎] [Why?]                │
│                                 │
├─────────────────────────────────┤
│ [Ask a question...]        [🎤] │
│                                 │
│ Quick actions:                  │
│ • Summarize current thread      │
│ • Explain this workflow         │
│ • What needs my attention?      │
└─────────────────────────────────┘
```

**Key difference from thread AI:**
- **Thread AI** (@mention in thread) = Team-visible, shared
- **Popup AI** = Personal, private, quick help

**Use cases:**
- "Summarize this thread for me"
- "Why did this workflow fail?"
- "What's the status of Finance space?"
- "Explain this decision"

---

#### 4. Chat List View

```
Click [💬] on chat bar:

┌─────────────────────────────────┐
│ Chats                      [+][×]│
├─────────────────────────────────┤
│ [Search chats...]               │
├─────────────────────────────────┤
│ PINNED                          │
│ 🤖 Finance Agent                │
│ 💬 Alice Chen                   │
│                                 │
│ RECENT                          │
│ 💬 Bob Wang                     │
│    "那个数据在哪..."             │
│    2h ago                       │
│                                 │
│ 💬 CFO                          │
│    "Approved"                   │
│    1d ago                  [1]  │ ← Unread badge
│                                 │
│ ARCHIVED (23)                ▶  │
│                                 │
│ ─────────────────────────       │
│ [New Chat]                      │
└─────────────────────────────────┘
```

**Organization:**
- Pinned: User-selected important chats
- Recent: Active in last 7 days
- Archived: Older than 7 days or manually archived

---

### Two Modes of AI Interaction

#### Mode 1: Thread AI (Team Shared)

```
In thread "Q1 Budget Planning":

CFO: @Finance_Agent analyze Q1 spend

[AI] @Finance_Agent:
📊 Analysis complete

■ Marketing: $545K (Budget: $500K)
  15% overspend

■ Engineering: $720K (Budget: $800K)
  10% under budget

[👍 2] [👎] [Why?]  Reply
```

**Characteristics:**
- All thread participants see the response
- Becomes part of thread history
- Can be referenced and discussed
- Trust level applies (L1/L2/L3)

---

#### Mode 2: Popup AI (Personal Assistant)

```
User opens AI chat popup:

You: Summarize Q1 Budget Planning thread

🤖 Finance Agent:
The thread discussed Q1 budget review.
Main decision: Approved $500K marketing
spend despite 15% overspend.

Rationale: ROI projections justify it.

[View full thread] [Ask follow-up]
```

**Characteristics:**
- Only you see the response
- Doesn't create thread messages
- Temporary conversation
- No trust level restrictions (always available)

**When to use which:**
- Thread AI: When team needs to see analysis/decision
- Popup AI: When you need personal understanding/help

---

### Quick Start Flows

#### Flow 1: Message a Person

```
1. Right-click on person's name (anywhere)
   → "Message Alice"

2. Popup opens immediately (bottom-right)
   No forms, no topic required

3. Type and send
   "Hey, where's that Q1 data?"

4. Alice responds in popup
   "Finance Dashboard, tab 3"

5. Close or minimize popup
   → Conversation auto-saved (7 days)
```

**0-friction startup.**

---

#### Flow 2: Ask AI a Quick Question

```
1. Click [+] on chat bar
   → Select "Finance Agent"
   (or use keyboard: Cmd+Shift+A)

2. AI popup opens

3. Type question
   "What workflows need my review?"

4. AI responds with list
   ⚠️ 3 workflows need review:
   • Invoice #1234
   • Vendor payment #5678
   • Lead score update

5. Click item to open in main view
   Or minimize popup
```

**AI help available instantly, anywhere.**

---

#### Flow 3: Multi-tasking with Multiple Chats

```
Bottom chat bar shows:
[💬 Alice] [🤖 Finance Agent] [💬 Bob]

User can:
- Have 3 chats open simultaneously
- Switch between them by clicking tabs
- Main workspace stays on current work
- No context switching needed
```

**Like LinkedIn's chat experience.**

---

### Chat → Thread Upgrade Path

#### Automatic Suggestion

```
When conversation grows (15+ messages or 2+ days):

┌─────────────────────────────────┐
│ 💬 Alice Chen             [−][×]│
│                           [↗️]   │
├─────────────────────────────────┤
│ [30 messages about vendor       │
│  negotiation strategy...]       │
│                                 │
│ ─────────────────────────       │
│ 💡 This conversation looks      │
│    important.                   │
│                                 │
│    Convert to thread?           │
│    AI suggested topic:          │
│    "Vendor X Negotiation"       │
│                                 │
│    Space: Finance               │
│    Visibility: 🔒 Private       │
│                                 │
│    [Convert] [Not Now]          │
└─────────────────────────────────┘
```

**After conversion:**
1. All chat messages → Thread messages
2. Thread appears in sidebar (Finance space)
3. Chat popup closes
4. Participants notified
5. Can continue in thread or invite more people

---

#### Manual Conversion

```
User clicks [↗️] button in chat popup:

┌─────────────────────────────────┐
│ Convert to Thread               │
├─────────────────────────────────┤
│ Topic name* (Required)          │
│ [Vendor X Negotiation]          │
│                                 │
│ Space                           │
│ [Finance ▼]                     │
│                                 │
│ Visibility                      │
│ ● Private (Alice, You)          │
│ ○ Public (All Finance members)  │
│                                 │
│ Include chat history?           │
│ ✓ Import all 32 messages        │
│                                 │
│ [Create Thread] [Cancel]        │
└─────────────────────────────────┘
```

---

### Chat History & Retention

#### Retention Policy

| Age | Status | Visibility | Actions Available |
|-----|--------|-----------|-------------------|
| 0-7 days | Active | Chat list (Recent) | Open, minimize, archive |
| 7-30 days | Auto-archived | Chat list (Archived) | Search, un-archive, delete |
| 30+ days | Auto-deleted | Not visible | Recoverable for 7 days |

**Important conversations:**
- Should be converted to threads before 30 days
- System reminds at 25 days: "Delete in 5 days"

---

#### Search & Recovery

```
Search chats:
[🔍 Search all chats...]

Results:
┌─────────────────────────────────┐
│ In conversation with Alice      │
│ "...那个Q1数据在Finance          │
│  Dashboard..."                  │
│ 3 days ago                      │
│                                 │
│ In conversation with Bob        │
│ "...vendor negotiation完成了..."│
│ 2 weeks ago (Archived)          │
└─────────────────────────────────┘
```

**Deleted chats:**
- 7-day recovery window
- Settings > Chats > Deleted
- Permanent deletion after 7 days

---

### Keyboard Shortcuts

```
Global:
Cmd+Shift+M     Open chat list
Cmd+Shift+N     New chat
Cmd+Shift+A     Chat with AI assistant

In chat:
Cmd+Enter       Send message
Cmd+K           Search in current chat
Cmd+W           Close chat popup
Cmd+↑/↓         Switch between chat tabs
Esc             Minimize chat popup
```

---

### Mobile Adaptation

**Desktop: Popup windows**
```
Main app + Multiple floating chat popups
(Optimal experience)
```

**Mobile: Bottom sheet or full-screen overlay**
```
Option 1: Bottom sheet (partial screen)
┌──────────────────────┐
│                      │
│ Main workspace       │
│                      │
├──────────────────────┤ ← Swipe up to expand
│ 💬 Alice Chen        │
│ "Hey, where's..."    │
└──────────────────────┘

Option 2: Full-screen overlay
Tap chat → Full screen chat view
[< Back] to return to workspace
```

---

### Notifications

#### Chat Notifications

```
New message in chat:
┌─────────────────────────────────┐
│ 💬 Alice Chen                   │
│ "那个数据在Finance Dashboard"   │
│                                 │
│ [Reply]  [View]  [Dismiss]      │
└─────────────────────────────────┘
```

**Badge behavior:**
- Chat tab shows unread count
- Minimized: Tab glows with badge
- Sound/vibration (user preference)

---

### Privacy & Security

#### Private vs Shared Context

**Chat context is private:**
- Popup AI chats: Only visible to you
- Human chats: Only visible to participants
- Not searchable by others
- Not indexed in workspace knowledge

**Thread context is shared:**
- Thread AI: Visible to all participants
- Indexed in workspace knowledge
- Contributes to agent learning

**This separation is intentional:**
- Users can ask "dumb questions" to AI in private
- Exploratory conversations don't pollute workspace
- Important findings can be shared by converting to thread

---

### Design Rationale: Why Popup Chats?

**Problems with sidebar-only approach:**
1. ❌ Sidebar gets cluttered (threads + chats mixed)
2. ❌ Quick chats need same friction as formal threads
3. ❌ No good place for personal AI assistant
4. ❌ Chat interrupts current workspace context

**Benefits of popup chat:**
1. ✅ Clear separation (formal vs casual)
2. ✅ 0-friction quick communication
3. ✅ Natural place for personal AI help
4. ✅ Doesn't interrupt current work
5. ✅ Familiar UX pattern (LinkedIn, Messenger)

---

### Thread vs Chat Decision Matrix

| Criteria | Use Thread | Use Chat |
|----------|-----------|----------|
| **Duration** | Long-term, ongoing | Short-term, one-off |
| **Participants** | 3+ people, team-wide | 1:1 or small group |
| **Purpose** | Decision-making, planning | Quick questions, clarifications |
| **Artifacts** | Produces deliverables | Pure conversation |
| **Discoverability** | Should be searchable by team | Private to participants |
| **AI involvement** | Team needs analysis | Personal help/understanding |

**Examples:**

**Thread:**
- "Q1 Budget Planning" (multi-week, team decision)
- "Bob Performance Review" (sensitive, needs structure)
- "Vendor X Negotiation" (produces contract artifacts)

**Chat:**
- "Where's that data?" (quick question)
- "Can you review this?" (1:1 request)
- "Summarize this thread" (personal AI help)

---

### Implementation Notes

#### Technical Requirements

**Backend:**
- Separate message tables: threads vs chats
- Auto-archival cron job (7 days)
- Retention policy enforcement (30 days)
- Search indexing (chats separate from threads)

**Frontend:**
- Popup window manager (z-index, positioning)
- Multiple concurrent popups
- Typing indicators (WebSocket)
- Notification system integration

**Mobile:**
- Responsive chat UI (bottom sheet or overlay)
- Gesture support (swipe to close, expand)
- Native notification handling

---

### Open Questions

1. **Max concurrent popup chats?**
   - Suggested: 3-5 popups max
   - Beyond that, suggest closing or converting

2. **Group chats in popup?**
   - Current design: 1:1 only
   - Alternative: Allow 2-3 person quick groups
   - Decision: TBD based on usage patterns

3. **Chat reactions?**
   - Like thread messages (👍 👎 ❤️)?
   - Or keep chats simpler?
   - Decision: Support reactions for consistency

4. **Voice/video calling?**
   - Should popup chats support calls?
   - Or integrate with external tools (Zoom, Meet)?
   - Decision: Phase 2 consideration

---

## @Mention System (Unified UX)

### People and Agents in Same List

```
In any thread, typing "@" shows:

┌─────────────────────────────────┐
│ Mention                         │
├─────────────────────────────────┤
│ People                          │
│ 👤 Alice Chen                   │
│ 👤 Bob Wang                     │
│ 👤 CFO                          │
│                                 │
│ Agents                          │
│ 🤖 @Finance_Agent               │
│ 🤖 @RevOps_Agent                │
│ 🤖 @Vibe (Global)               │
│                                 │
│ Spaces                          │
│ # Finance                       │
│ # Executive                     │
└─────────────────────────────────┘
```

**Unified experience:**
- Same UX for mentioning humans and agents
- Visual distinction (👤 vs 🤖)
- Can @mention spaces (notify all members)

---

## Notifications System

### Two-Level Notifications

**Level 1: Global (in Home space)**
```
Home > Global Notifications

Shows notifications from all workspaces:
• Vibe > Finance: Invoice needs review
• Client A > Strategy: @mention from Bob
• Personal: Task due tomorrow
```

**Level 2: Workspace-scoped (in top bar)**
```
Workspace top bar: [🔔 3]

Shows only this workspace's notifications:
• Finance: Workflow needs approval
• RevOps: @mention from Alice
• Executive: Thread update
```

---

### Notification Types

```
[🔔] Notifications

Tabs: [All] [@Me] [Workflows] [Updates]

┌─────────────────────────────────────┐
│ All                                 │
├─────────────────────────────────────┤
│ ⚠️ Workflow needs approval          │
│    Invoice #1234 - Finance Agent    │
│    Finance > Invoice Processing     │
│    2 min ago                        │
│    [Review]                         │
│                                     │
│ 💬 @mention from Alice              │
│    "Check this analysis"            │
│    Finance > Budget Thread          │
│    5 min ago                        │
│    [View]                           │
│                                     │
│ 🤖 @mention from Finance_Agent      │
│    "Analysis complete"              │
│    Finance > Budget Thread          │
│    10 min ago                       │
│    [View]                           │
│                                     │
│ 🔔 Thread update                    │
│    5 new messages in "Q1 Planning"  │
│    Executive                        │
│    1 hour ago                       │
│    [View]                           │
│                                     │
│ ────────────────────────────────    │
│ [Mark all as read]                  │
│ [Notification settings]             │
└─────────────────────────────────────┘
```

**Notification categories:**
- ⚠️ Workflow approvals (high priority)
- 💬 @mentions from humans
- 🤖 @mentions from agents
- 🔔 Thread updates
- ✅ Workflow completions

---

## Search System

### Global Search (Cmd+K)

```
[🔍 Search...]

As user types "budget":

┌─────────────────────────────────────┐
│ Search: budget                      │
├─────────────────────────────────────┤
│ Threads                             │
│ • Q1 Budget Planning (Finance)      │
│ • 2025 Budget Review (Executive)    │
│                                     │
│ Spaces                              │
│ • Finance (contains "budget")       │
│                                     │
│ Artifacts                           │
│ • Q1 Budget Plan.pdf                │
│ • Budget Template.xlsx              │
│                                     │
│ Messages                            │
│ • "The budget needs review..." (CFO)│
│   Finance > Q1 Planning             │
│                                     │
│ Workflows                           │
│ • Budget Approval Process           │
│   @Finance_Agent                    │
│                                     │
│ People                              │
│ • No matches                        │
└─────────────────────────────────────┘
```

**Search across:**
- Threads (public + private you have access to)
- Spaces
- Artifacts
- Messages
- Workflows
- People
- Agents

---

## Keyboard Shortcuts

```
Global:
Cmd+K        Quick search
Cmd+/        Shortcuts help
Cmd+Shift+P  All private threads
Cmd+N        New thread
Cmd+,        Settings

Navigation:
Cmd+1-9      Switch workspace
Cmd+[        Back
Cmd+]        Forward
Cmd+T        Jump to thread

Actions:
Cmd+Enter    Send message
Cmd+Shift+E  Toggle emoji
@            Mention menu
:            Emoji picker
```

---

## Mobile Considerations

**Simplified hierarchy for mobile:**

```
Mobile App Structure:

Tab Bar (bottom):
┌─────┬─────┬─────┬─────┬─────┐
│ Home│ Chat│ Work│ Notif│ More│
└─────┴─────┴─────┴─────┴─────┘
   ↑     ↑     ↑      ↑     ↑
 Global Threads Works  [🔔]  Profile
 agent  & DMs  flows         Settings
```

**Mobile-specific adaptations:**
- Collapsible sections by default
- Swipe gestures (swipe left on thread to archive/pin)
- Bottom sheet for quick actions
- Simplified notifications (grouped)

**Not covered in this doc (separate mobile design needed):**
- Detailed mobile UX flows
- Gesture interactions
- Responsive layouts

---

## Accessibility

### Key A11y Features

**Visual:**
- High contrast mode
- Adjustable text size (120%-200%)
- Screen reader support (ARIA labels)
- Keyboard navigation (all functions accessible)

**Notifications:**
- Visual + audio options
- Customizable notification sounds
- Banner + badge options

**Input:**
- Voice input for messages
- Keyboard shortcuts for all actions
- Screen reader compatibility

**Color blindness:**
- Not relying solely on color for status
- Icons + text labels (e.g., 🟢 Active, 🔴 Error)

---

## Dark Mode

**Default: System preference**

```
Settings > Appearance:
○ Light
○ Dark
● Auto (match system)
```

**Color tokens design:**
- Use CSS variables for all colors
- Semantic naming (--color-text-primary, --color-bg-surface)
- Easy theme switching

---

## Performance Considerations

### Lazy Loading

**Sidebar:**
- Load visible sections first
- Lazy load collapsed sections
- Virtualized lists for long thread lists

**Threads:**
- Load recent 50 messages
- "Load more" for older messages
- Virtualized message list

**Workflows:**
- Load summary first
- Details on demand

### Real-time Updates

**Use WebSocket for:**
- New messages
- Workflow status updates
- Notifications
- Presence (who's online)

**Optimistic UI:**
- Message appears immediately when sent
- Syncs in background
- Shows sync status if failed

---

## Animation & Transitions

**Principle: Subtle, fast, purposeful**

**Navigation:**
- Sidebar expand/collapse: 200ms ease-out
- Space expand: 150ms ease-out
- Thread open: Instant (no transition)

**Notifications:**
- Badge appear: Gentle pop (100ms scale)
- Toast notification: Slide from top (300ms)

**Feedback:**
- Button click: Subtle scale (50ms)
- Message sent: Quick fade-in (100ms)
- Workflow update: Smooth progress bar

**No animations:**
- ❌ Page transitions (too slow)
- ❌ Elaborate loading spinners
- ❌ Decorative animations

---

## Design System Tokens

### Spacing Scale

```
--space-xs:   4px
--space-sm:   8px
--space-md:   16px
--space-lg:   24px
--space-xl:   32px
--space-2xl:  48px
```

### Typography

```
--text-xs:    12px / 1.5
--text-sm:    14px / 1.5
--text-md:    16px / 1.5
--text-lg:    18px / 1.5
--text-xl:    24px / 1.5
```

### Border Radius

```
--radius-sm:  4px  (buttons, inputs)
--radius-md:  8px  (cards, modals)
--radius-lg:  12px (panels)
--radius-xl:  16px (large surfaces)
```

---

## Summary: Key Design Decisions

### 1. Discord-Inspired Architecture ✅

| Aspect | Discord | OpenVibe |
|--------|---------|----------|
| Dual sidebar | ✅ Yes | ✅ Yes |
| Global functions in Home | ✅ Yes | ✅ Yes (adapted for B2B) |
| Minimal top bar in workspace | ✅ None | ✅ Minimal (breadcrumb + notifs) |
| DM location | 🏠 Global | ❌ Not needed (use private threads) |

---

### 2. Human-to-Human Communication ✅

**Two-tier system (different from Discord):**

**Tier 1: Threads (Structured, in sidebar)**
- Public threads (default collaboration)
- Private threads (sensitive topics, still has context)
- Always has topic name
- Long-term retention

**Tier 2: Popup Chats (Quick, lightweight)**
- 1:1 quick messages (LinkedIn-style)
- No topic required
- 7-30 day retention
- Personal or small group

**Why not follow Discord's global DM:**
- B2B needs context (threads linked to spaces)
- Knowledge accumulation (important chats → threads)
- But still need quick communication (popup chats)
- Agent can participate in both modes

---

### 3. Private Threads Not Group Chats ✅

**Slack problem:**
```
Group: Alice, Bob, Charlie
→ No topic, hard to find, temporary
```

**OpenVibe solution:**
```
🔒 "Bob Performance Review"
Participants: CFO, Alice
Space: Finance
→ Clear topic, searchable, permanent
```

---

### 4. Navigation Hierarchy ✅

```
Layer 1: Global
  - Home (personal space)
  - Workspace switcher

Layer 2: Workspace
  - Top bar (minimal: breadcrumb + notifs)
  - Sidebar (spaces, workflows, agents)
  - Main content

Layer 3: Space
  - Public threads
  - Private threads

Layer 4: Thread
  - Messages (human + agent mixed)
  - Artifacts (embedded)
```

---

### 5. Dynamic Sections Based on Role ✅

**Individual contributor:**
- Sees: Spaces, Search
- Doesn't see: Workflows (unless frequent), Agents, Admin

**Department leader:**
- Sees: Spaces, Workflows, Search
- Doesn't see: Agents (collapsed), Admin

**Admin:**
- Sees: Everything (Spaces, Workflows, Agents, Admin)

**AI adjusts based on behavior + user can customize via natural language.**

---

### 6. Popup Chat System ✅

**Two-mode communication pattern:**

| Mode | Thread (Sidebar) | Chat (Popup) |
|------|-----------------|--------------|
| **Purpose** | Structured discussions | Quick communication |
| **Startup** | Requires topic | Instant, no forms |
| **Retention** | Permanent | 7-30 days |
| **Location** | Workspace sidebar | Bottom-right popup |
| **Example** | "Q1 Budget Planning" | "Where's that data?" |

**Dual AI interaction:**

| Mode | Thread AI | Popup AI |
|------|-----------|----------|
| **Visibility** | Team shared | Personal only |
| **Use case** | Team analysis | Personal help |
| **Trust level** | Applies (L1/L2/L3) | Always available |
| **Example** | "@Agent analyze spend" | "Summarize this thread" |

**Benefits:**
- ✅ 0-friction quick communication (like LinkedIn)
- ✅ Separates casual from formal (reduces clutter)
- ✅ Personal AI assistant available anywhere
- ✅ Natural upgrade path (chat → thread when needed)

---

## Missing Components / Design Gaps

> **Status**: Identified gaps between V3 Vision and current UI design
> **Last reviewed**: 2026-02-12

This section documents components that are present in V3 THESIS but not yet designed in the interface. Prioritized by importance to vision.

---

### P0 - Critical Gaps (Vision Core, UI Missing)

#### 1. Knowledge/Memory Layer Visualization ⭐⭐⭐

**Vision requirement:**
> "Workspace gets smarter over time"
> "Persistent context accumulates"
> "Knowledge pipeline (4-layer architecture)"

**Current UI status:** ❌ Completely missing

**What's needed:**

```
Sidebar section: KNOWLEDGE
┌─────────────────────────────────┐
│ KNOWLEDGE                    ▼  │
├─────────────────────────────────┤
│ Finance Workspace Memory        │
│                                 │
│ Vendors (47)                    │
│ • Vendor X: Always late         │
│   → Flag 3 days early           │
│ • Vendor Y: Net-60 preferred    │
│   → Auto-adjust payment dates   │
│                                 │
│ Processes (12)                  │
│ • Month-end close: 15 steps     │
│ • Invoice approval workflow     │
│   → Auto if <$1K                │
│                                 │
│ Edge Cases (8)                  │
│ • When vendor disputes invoice  │
│ • Unusual payment terms         │
│                                 │
│ Learning Progress               │
│ Month 1: 23 facts               │
│ Month 6: 189 facts              │
│ Growth: +720% 📈                │
│                                 │
│ [📊 Knowledge Graph]            │
│ [🔍 Search Knowledge]           │
└─────────────────────────────────┘
```

**Alternative locations:**
- Space-level "Knowledge" tab
- Agent detail page showing what agent knows
- Global knowledge base view

**Why critical:**
- This IS the moat (data flywheel)
- Without visibility, users can't see value accumulation
- Core differentiator vs chat tools

---

#### 2. Progressive Disclosure Specification ⭐⭐⭐

**Vision requirement:**
> Headline / Summary / Full - three distinct layers

**Current UI status:** ⚠️ Mentioned as "折叠/展开" but not specified

**What's needed:**

```
Standard agent message format:

[AI] @Finance_Agent              Today 2:34pm

🤖 ■ Marketing overspent 15% ($45K over budget)
      ↑
   HEADLINE (always visible, 1 line, actionable)

   ▸ Summary (click to expand)
     • Campaign X: $30K over ($20K budgeted)
       - ROI: 2.3x (justifies overspend)
     • Campaign Y: $15K over ($10K budgeted)
       - ROI: 1.1x (needs review)
     • Recommendation: Approve X, cut Y

   ▸ Full Report (click to expand)
     ┌─────────────────────────────┐
     │ Detailed Analysis           │
     ├─────────────────────────────┤
     │ [Charts, tables, raw data]  │
     │ [Analysis methodology]      │
     │ [Confidence scores]         │
     │ [Data sources]              │
     │ [Related threads]           │
     └─────────────────────────────┘

[👍] [👎] [Why?]  Reply
```

**Design specs needed:**
- Collapsed state appearance
- Expand/collapse interaction
- Nested disclosure (summary → full)
- Mobile adaptation
- Keyboard navigation

**Why critical:**
- Vision explicitly defines this
- User experience depends on information hierarchy
- Without it, agent output is overwhelming

---

#### 3. Context Assembly Visualization ⭐⭐

**Vision requirement:**
> 4-layer context assembly:
> - Conversation history
> - Related threads
> - Workspace knowledge
> - External knowledge

**Current UI status:** ❌ Completely missing

**What's needed:**

```
In expanded agent message:

[AI] @Finance_Agent

🤖 ■ Vendor X payment should wait 3 days

   ▸ Summary
     Historical pattern shows Vendor X
     typically pays us 5 days late.
     Delaying our payment maintains
     cash flow balance.

   ▸ Context Used (new!)
     ┌─────────────────────────────┐
     │ 📚 Context Sources          │
     ├─────────────────────────────┤
     │ 🔵 Conversation (this thread)│
     │ • CFO asked about timing    │
     │                             │
     │ 🟢 Related Threads (2)      │
     │ • "Vendor X Contract" (3mo) │
     │ • "Payment Terms Review"    │
     │                             │
     │ 🟡 Workspace Knowledge (5)  │
     │ • Vendor X: Net-60 actual   │
     │ • Payment pattern: +5d avg  │
     │ • Cash flow policy          │
     │                             │
     │ 🟠 External (1)             │
     │ • Vendor X credit rating    │
     │                             │
     │ [View Details]              │
     └─────────────────────────────┘
```

**Why critical:**
- Transparency builds trust
- Users need to verify agent reasoning
- Debugging when agent is wrong

---

### P1 - High Priority Gaps (Important for Completeness)

#### 4. Trust Level Upgrade/Downgrade Flow ⭐⭐

**Vision requirement:**
> Trust grows over time based on feedback
> Observer → Advisor → Executor

**Current UI status:** ⚠️ Badge shown `[L1] [L2]`, but no upgrade flow

**What's needed:**

**Upgrade suggestion:**
```
Toast notification:
┌─────────────────────────────────┐
│ 💡 Trust Level Upgrade Available │
├─────────────────────────────────┤
│ @Finance_Agent → L2 (Executor)  │
│                                 │
│ Performance:                    │
│ ✓ 94% success (50 workflows)   │
│ ✓ 0 critical errors             │
│ ✓ 87% positive feedback         │
│                                 │
│ New permissions:                │
│ • Auto-approve invoices <$5K    │
│ • Auto-reconcile accounts       │
│                                 │
│ [Review Performance] [Upgrade]  │
│ [Not Yet]                       │
└─────────────────────────────────┘
```

**Downgrade warning:**
```
┌─────────────────────────────────┐
│ ⚠️ Trust Level Review Needed     │
├─────────────────────────────────┤
│ @RevOps_Agent performance drop  │
│                                 │
│ Issues this week:               │
│ • 3 failed workflows            │
│ • Success: 78% (was 92%)        │
│ • 2 incorrect analyses          │
│                                 │
│ Suggested:                      │
│ Downgrade L2 → L1 until stable  │
│                                 │
│ [Keep L2] [Downgrade] [Pause]   │
└─────────────────────────────────┘
```

**Admin approval flow:**
```
Settings > Agents > Finance Agent

Trust Level Change Request
┌─────────────────────────────────┐
│ Requested: L1 → L2              │
│ Requester: System (auto)        │
│ Date: 2026-02-12                │
│                                 │
│ Performance Summary:            │
│ [Chart: Success rate over time] │
│                                 │
│ Risk Assessment:                │
│ • Low risk actions: 45          │
│ • Medium risk: 5                │
│ • High risk: 0                  │
│                                 │
│ New Permissions:                │
│ ✓ Auto-approve <$5K             │
│ ✓ Auto-reconcile                │
│ ✗ Cannot approve >$10K          │
│                                 │
│ [Approve] [Deny] [Modify]       │
└─────────────────────────────────┘
```

---

#### 5. Feedback → Behavior Connection ⭐⭐

**Vision requirement:**
> Feedback loop is the moat
> Human judgment → Agent behavior change

**Current UI status:** ⚠️ Buttons exist `[👍] [👎] [Why?]`, but no follow-up

**What's needed:**

**Step 1: Detailed feedback form**
```
After clicking [👎]:

┌─────────────────────────────────┐
│ What was incorrect?             │
├─────────────────────────────────┤
│ ○ Wrong data source             │
│ ○ Incorrect calculation         │
│ ● Missed important context      │
│ ○ Wrong recommendation          │
│                                 │
│ What context was missing?       │
│ ┌─────────────────────────────┐ │
│ │ Vendor X has special Net-60 │ │
│ │ terms negotiated last month │ │
│ └─────────────────────────────┘ │
│                                 │
│ Should agent have known this?   │
│ ● Yes (add to knowledge)        │
│ ○ No (one-time exception)       │
│                                 │
│ [Submit Feedback]               │
└─────────────────────────────────┘
```

**Step 2: Impact confirmation**
```
After submission:

┌─────────────────────────────────┐
│ ✓ Feedback Recorded             │
├─────────────────────────────────┤
│ Changes made:                   │
│                                 │
│ 1. Added to Finance Knowledge:  │
│    "Vendor X: Net-60 terms"     │
│                                 │
│ 2. Agent will now:              │
│    • Check vendor-specific      │
│      terms before payment       │
│      analysis                   │
│                                 │
│ 3. Updated similar cases: 3     │
│    • Invoice #1234 re-analyzed  │
│    • Payment #5678 adjusted     │
│                                 │
│ [View Knowledge] [Close]        │
└─────────────────────────────────┘
```

**Step 3: Visible learning**
```
Next time agent encounters similar:

[AI] @Finance_Agent

🤖 ■ Vendor X payment: Wait until Feb 15

   ▸ Summary
     Using Vendor X's Net-60 terms
     (learned from your feedback 3 days ago)

   📚 Knowledge applied:
     • "Vendor X: Net-60 terms" ← You taught me this
```

---

#### 6. Agent Learning Progress Visualization ⭐

**Vision requirement:**
> Month 1: Agents ask questions
> Month 6: Agents remember patterns
> Month 12: Agents predict issues

**Current UI status:** ❌ Missing

**What's needed:**

```
In Agents section > Finance Agent detail:

┌─────────────────────────────────┐
│ @Finance_Agent Learning         │
├─────────────────────────────────┤
│                                 │
│ [Chart: Knowledge Growth]       │
│  Facts                          │
│  250│         ╱────             │
│  200│       ╱                   │
│  150│     ╱                     │
│  100│   ╱                       │
│   50│ ╱                         │
│    0└────────────────────       │
│     M1  M2  M3  M4  M5  M6      │
│                                 │
│ Milestones:                     │
│ ✓ Month 1: Basic workflows      │
│ ✓ Month 3: Pattern recognition  │
│ ✓ Month 6: Proactive alerts     │
│ ⏳ Month 12: Predictive insights│
│                                 │
│ Knowledge Categories:           │
│ • Vendors: 47 facts             │
│ • Processes: 12 workflows       │
│ • Edge cases: 8 scenarios       │
│ • Best practices: 15 rules      │
│                                 │
│ Performance Trend:              │
│ Month 1: 78% success            │
│ Month 6: 94% success (+16%)     │
│                                 │
│ [View Knowledge Graph]          │
└─────────────────────────────────┘
```

---

### P2 - Medium Priority (Nice to Have)

#### 7. Workflow Builder/Editor UI

**Current status:** ❌ Missing

**Options to explore:**
- Conversational builder ("@Agent, create workflow for invoice processing")
- Visual flow builder (drag-and-drop nodes)
- Template library (Finance AIOps, RevOps)
- YAML/config editor for power users

---

#### 8. Agent Configuration/SOUL Editor

**Current status:** ❌ Missing

**Needs:**
- Trust level configuration
- Risk rules editor
- Tool access permissions
- Memory scope settings
- Personality/behavior tuning

---

#### 9. Artifacts - Detailed Design

**Current status:** ⚠️ Concept exists, details missing

**Needs:**
- Versioning UI (v1 → v2 → v3)
- Real-time collaboration (multiple editors)
- Conflict resolution
- History/diff view
- Export/share options
- Template system

---

#### 10. Onboarding & Empty States

**Current status:** ❌ Not designed

**Needs:**
- First-time workspace setup
- Agent activation wizard
- Knowledge base initialization
- Sample data/templates
- Interactive tutorial

---

#### 11. Settings & Admin Console

**Current status:** ⚠️ Mentioned `[•••]` but not detailed

**Needs:**
- Workspace settings
- Member management (invite, roles, permissions)
- Agent management (create, configure, delete)
- Space management
- Integrations (Slack, Google, GitHub)
- Billing & plans
- Audit logs
- Data export

---

#### 12. Cross-Workspace Features

**Current status:** ❌ Not designed (workspaces fully isolated)

**Possible needs:**
- Cross-workspace links (with permissions)
- Shared artifacts across workspaces
- Global search (all workspaces)
- Agent access to multiple workspaces

---

### Summary: Gap Severity

| Component | Vision Priority | UI Status | Severity |
|-----------|----------------|-----------|----------|
| **Knowledge/Memory Layer** | 🔴 Core moat | ❌ Missing | 🔴 Critical |
| **Progressive Disclosure** | 🔴 Explicitly defined | ⚠️ Vague | 🟡 High |
| **Context Assembly** | 🟡 Important | ❌ Missing | 🟡 High |
| **Trust Upgrade Flow** | 🟡 Important | ⚠️ Partial | 🟡 Medium |
| **Feedback Impact** | 🔴 Core moat | ⚠️ Partial | 🟡 Medium |
| **Agent Learning** | 🟡 Important | ❌ Missing | 🟢 Medium |
| **Workflow Builder** | 🟢 Nice to have | ❌ Missing | 🟢 Low |
| **Agent Config UI** | 🟢 Nice to have | ❌ Missing | 🟢 Low |
| **Artifacts Detail** | 🟡 Important | ⚠️ Partial | 🟢 Low |
| **Onboarding** | 🟢 Standard | ❌ Missing | 🟢 Low |
| **Settings/Admin** | 🟢 Standard | ⚠️ Partial | 🟢 Low |
| **Cross-workspace** | 🟢 Future | ❌ Missing | 🟢 Very Low |

---

### Recommended Action Plan

**Week 1 (This week):**
1. Design Knowledge/Memory Layer UI (P0 #1)
2. Specify Progressive Disclosure format (P0 #2)
3. Design Trust Level upgrade flow (P1 #4)

**Week 2:**
4. Design Context Assembly visualization (P0 #3)
5. Design Feedback → Behavior connection (P1 #5)
6. Design Agent Learning Progress (P1 #6)

**Week 3-4:**
7. Workflow Builder (P2 #7)
8. Agent Configuration UI (P2 #8)
9. Artifacts detailed design (P2 #9)

**Later:**
- Onboarding, Settings, Cross-workspace (as needed)

---

## Open Questions / Future Considerations

### 1. Agent Orchestration UI

**Question:** How to visualize multi-agent workflows?

**Current design:** Shows workflow status, but not agent-to-agent coordination

**Needs exploration:**
- Workflow execution graph
- Agent dependency visualization
- Debugging interface for failed workflows

---

### 2. Cross-Workspace Collaboration

**Question:** What if Finance in Vibe needs to reference something in Client A workspace?

**Current design:** Workspaces are isolated (like Discord servers)

**Possible solution:**
- Cross-workspace links (with permission checks)
- Shared artifacts across workspaces
- Global search can surface cross-workspace content

---

### 3. Workflow Builder UI

**Question:** How do users create/configure workflows?

**Current design:** Not specified (assumed to be through agent conversation or config UI)

**Needs design:**
- Conversational workflow builder ("@Agent, create a workflow for...")
- Visual flow builder (drag-and-drop)
- Template library (Finance AIOps, RevOps playbooks)

---

### 4. Trust Level Upgrade Flow

**Question:** How does trust level change, and how is it communicated in UI?

**Current design:** Shows trust level badge ([L1], [L2], etc.)

**Needs design:**
- Upgrade suggestion UI ("@Finance_Agent ready for L2 based on 94% success rate")
- Upgrade approval flow (admin review + confirm)
- Visual indication of trust level change

---

### 5. Artifact Versioning & Collaboration

**Question:** Multiple people editing same artifact - how to handle?

**Current design:** Shows version number ([v1], [v2])

**Needs design:**
- Real-time collaboration (like Google Docs)
- Or version control (like Git)
- Conflict resolution

---

## Implementation Priorities

### Phase 1: Core Navigation (Month 1-2)

**Must have:**
- ✅ Dual sidebar (Layer 1 + Layer 2)
- ✅ Home space with global agent
- ✅ Workspace view with minimal top bar
- ✅ Spaces list + thread list
- ✅ Basic thread view (human messages only)
- ✅ Search (basic)

---

### Phase 2: Agent Integration (Month 3-4)

**Must have:**
- ✅ Agent messages in threads
- ✅ @mention agents
- ✅ Agent responses with progressive disclosure
- ✅ Workflows section in sidebar
- ✅ Basic workflow dashboard
- ✅ Notifications (workspace + global)

---

### Phase 3: Advanced Features (Month 5-6)

**Must have:**
- ✅ Private threads
- ✅ Artifacts (embedded in threads)
- ✅ Workflow approval queue
- ✅ Agents section (for admins)
- ✅ Dynamic sections (role-based)

**Nice to have:**
- Keyboard shortcuts
- Dark mode
- Mobile responsive

---

### Phase 4: Polish & Scale (Month 7+)

**Must have:**
- Performance optimization (lazy loading, virtualization)
- Accessibility (screen reader, keyboard nav)
- Analytics (user behavior tracking)

**Nice to have:**
- Advanced workflow builder
- Cross-workspace features
- Mobile native app
- Advanced artifact collaboration

---

## Related Documents

- `THESIS.md` - V3 core thesis (cognition as infrastructure)
- `INTERFACE-INITIAL-THOUGHTS.md` - Design evolution process
- `AGENT-MODEL.md` - Agent architecture (SOUL, trust, memory)
- `AGENT-IN-CONVERSATION.md` - How agents participate
- `PERSISTENT-CONTEXT.md` - Memory & knowledge accumulation
- `FEEDBACK-LOOP.md` - Human judgment → agent behavior

---

*Last updated: 2026-02-12*
*Status: Major update - Sidebar redesign + Workspace Home dashboard*

**Completed (2026-02-12 update):**
- ✅ **Sidebar redesign:** Two-tier structure (customizable top + fixed bottom)
  - Top section: User-customizable, expandable function views (Home, Workflows, Agents)
  - Bottom section: Fixed Spaces navigation
  - Role-based defaults with full user customization
- ✅ **Workspace Home Dashboard:** Three-column overview
  - Left: Priority & Recent Updates
  - Center: Spaces overview cards
  - Right: Agents status & workspace metrics
  - Implements Progressive Disclosure (Workspace → Space → Thread)
- ✅ Core architecture (Discord-inspired dual sidebar)
- ✅ Thread system (public/private)
- ✅ Popup chat system (LinkedIn-inspired)
- ✅ Workflows, Agents, Notifications sections

**Key design decisions:**
1. **Two-tier sidebar** - Top (customizable functions) + Bottom (fixed navigation)
2. **Expandable sections** - All top sections expand inline, don't switch main area
3. **Workspace Home as portal** - Dashboard for daily overview, not a workspace
4. **Progressive disclosure** - Architecture level (Workspace → Space → Thread), not just UI component
5. **"Workspace gets smarter"** - Shown through agent performance trends, not explicit knowledge UI

**Still missing (documented in "Missing Components" section):**
- ⚠️ Progressive disclosure specification (message-level: headline → summary → full) - P0
- ⚠️ Context assembly visualization (4-layer context sources) - P0
- ⚠️ Trust level upgrade flow (UI for L1 → L2 → L3 transitions) - P1
- ⚠️ Feedback → behavior connection (showing what agent learned from feedback) - P1
- ⚠️ Agent learning progress visualization (knowledge growth over time) - P1

**Design philosophy validated:**
- Progressive disclosure is architectural (Workspace → Space → Thread), not just message folding
- "Workspace gets smarter" shown through results (performance trends), not explicit knowledge graphs
- User customization over rigid role-based views
