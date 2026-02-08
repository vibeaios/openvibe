# OpenVibe Visual Design Specification

> Status: Active | Date: 2026-02-08
> Authority: This is the definitive visual design reference for MVP implementation.
> Design tokens: `apps/web/src/app/globals.css`

---

## 1. Design Direction

### One Line
**Linear's restraint meets Discord's density, with a warm amber glow for Deep Dives.**

### Philosophy
- **Dark-mode only for MVP.** No light mode. This is a focused tool for teams who work in depth. Dark mode reduces visual fatigue during extended deep dive sessions and makes code blocks feel native.
- **Warm, not cold.** Discord leans cold blue-gray. We lean warm gray with barely-perceptible violet undertones (oklch hue 260). This prevents the "cold cave" feeling while remaining firmly dark-mode.
- **Two accent colors tell the story.** Indigo-violet (`--color-primary`, hue 275) for platform actions. Warm amber/gold (`--color-dive`, hue 75) for deep dives. When a user enters a dive, the UI subtly warms — that's the visual story of "going deeper."
- **Density over decoration.** Information density like Linear, not whitespace-heavy like Notion. Every pixel should communicate. No decorative elements.
- **Calm by default, active when needed.** The UI is quiet until something demands attention. Pulse animations only during active AI processing. Color saturation increases only for interactive states.

### References
| App | What We Take | What We Avoid |
|-----|-------------|---------------|
| Discord | 4-zone layout, channel list pattern, message density | Cold blue tones, rounded message groups, busy hover states |
| Linear | Typography restraint, information density, smooth transitions | Their specific gray palette (too neutral for our dual-accent system) |
| Cursor | AI streaming UX, code-first aesthetic, panel model | IDE-specific patterns that don't translate to chat |
| Claude.ai | Thinking indicator, progressive disclosure | Full-width layout (we need sidebar) |
| Raycast | Keyboard-first, command palette, crisp dark mode | macOS-native patterns that don't work on web |

---

## 2. Color System

Full token definitions: `apps/web/src/app/globals.css`

### Background Layer Hierarchy

```
Darkest ─────────────────────────────────────────── Lightest

 background    sidebar      surface      elevated
 oklch(0.11)   oklch(0.13)  oklch(0.16)  oklch(0.19)

 App shell     Channel      Main chat    Cards,
 behind        list,        area,        modals,
 everything    agent list   thread view  popovers
```

Each step is +0.03 lightness in oklch — subtle but perceptible. The sidebar is darker than the main content because the main content is where you read. The sidebar is navigation, not content.

### Dual Accent System

```
PRIMARY (Indigo-Violet, hue 275)         DEEP DIVE (Amber/Gold, hue 75)
───────────────────────────────          ──────────────────────────────
Buttons, links, active states            Dive buttons, dive surfaces,
Selection indicators, focus rings        dive results, publish actions
Channel active state                     "Thinking" status, dive badges

When user enters a deep dive:
  Primary accent stays for navigation
  Dive accent appears in:
    - Left border accent on dive panel
    - Dive surface background tint
    - Resolution card background
    - Publish button
    - Active thinking indicator
```

### Special Surface Colors

| Surface | Token | Usage |
|---------|-------|-------|
| Agent message | `--color-agent` | Subtle violet tint on AI responses |
| Deep dive context | `--color-dive-surface` | Warm tint when inside a dive |
| Resolution card | `--color-resolution` | Warm tint for dive result cards in main thread |
| Code block | `--color-codeblock` | Darker than surface, monospace context |
| Hover | `--color-hover` | Generic interactive hover |
| Active/selected | `--color-active` | Current selection, with violet hint |

---

## 3. Typography

### Font Stack

```css
--font-sans: "Geist", ui-sans-serif, system-ui, -apple-system, sans-serif;
--font-mono: "Geist Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
```

**Why Geist:** Designed by Vercel specifically for developer tools. Clean, modern, excellent weight range, great at small sizes on screens. Ships with Next.js. No additional font loading needed.

**Why NOT Geist Pixel:** Fun for branding, wrong for a productivity tool. Consider it for the logo mark or empty states only, not body text.

### Type Scale

| Level | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| `display` | 24px | 600 | 1.2 | -0.02em | Page titles (rare) |
| `title` | 18px | 600 | 1.3 | -0.01em | Thread titles, modal headers |
| `heading` | 15px | 600 | 1.4 | -0.005em | Section headers, channel names |
| `body` | 14px | 400 | 1.6 | 0 | Message text, descriptions |
| `small` | 13px | 400 | 1.5 | 0 | Timestamps, metadata, sidebar items |
| `caption` | 12px | 500 | 1.4 | 0.01em | Badges, labels, status text |
| `overline` | 11px | 600 | 1.3 | 0.05em | Section labels (uppercase), "CHANNELS", "DEEP DIVES" |

### Text Color Mapping

| Context | Color Token | Example |
|---------|-------------|---------|
| Message body | `foreground` | "We need to implement rate limiting" |
| Username | `foreground` + weight 600 | **Charles** |
| Timestamp | `secondary` | 2:30 PM |
| Channel name (active) | `foreground` | # engineering |
| Channel name (inactive) | `secondary` | # random |
| Placeholder text | `muted-foreground` | "Message #engineering..." |
| Disabled | `disabled` | Archived channel name |
| Dive label | `dive` | DEEP DIVE |
| System message | `secondary` | "Charles started a deep dive" |

### Code Typography

```
Font:     Geist Mono, 13px
Weight:   400
Line-height: 1.7 (generous for readability)
Background: var(--color-codeblock)
Padding:  16px
Radius:   var(--radius-lg) (8px)
```

Inline code: `Geist Mono, 13px, bg: var(--color-elevated), padding: 2px 6px, radius: 4px`

---

## 4. Layout Specification

### Overall Grid

```
+----+-----------+--------------------------------+---------------+
|    |           |                                |               |
| S  | Sidebar   |  Main Content                  | Detail Panel  |
| e  |           |                                | (conditional) |
| r  | 240px     |  flex (min 480px)              | 320px         |
| v  |           |                                |               |
| e  |           |                                |               |
| r  |           |                                |               |
|    |           |                                |               |
| 0  |           |                                |               |
| px |           |                                |               |
|    |           |                                |               |
+----+-----------+--------------------------------+---------------+

      Divider: 1px solid var(--color-divider)
      No gap between zones — borders create separation
```

**Server list (Zone 1): 0px for MVP.** No workspace switcher needed for dogfood. Kill the zone entirely — it wastes 48px of horizontal space for one workspace.

### Sidebar (Zone 2): 240px

```
+-----------------------------------+
| Workspace Name            [v] [+] |  44px, bg: sidebar
+-----------------------------------+
| [Search...]                       |  40px, bg: input, mx: 8px
+-----------------------------------+
|                                   |
| CHANNELS               overline   |  28px, text: muted-foreground
|                                   |
|  # general              small     |  32px, hover: sidebar-hover
|  # engineering          small     |  32px, active: sidebar-active-bg
|  # product              small     |  32px
|  # random               small     |  32px
|                                   |
+-----------------------------------+
|                                   |
| AGENTS                 overline   |  28px
|                                   |
|  [o] @Vibe     Online   small    |  36px, status dot: 8px
|  [o] @Coder    Online   small    |  36px
|                                   |
+-----------------------------------+
|                                   |
| DEEP DIVES (2)         overline   |  28px, text: dive (amber)
|  (when viewing a thread)          |
|                                   |
|  [*] Pricing Research    small   |  48px entry
|      Charles + @Vibe             |  avatars: 18px, overlapping
|      3 msgs, 2m ago             |  text: muted-foreground
|                                   |
|  [*] API Design          small   |  48px entry
|      Dev + @Coder                |
|      5 msgs, active             |  status: dive accent pulse
|                                   |
+-----------------------------------+
```

**Sidebar item anatomy:**
- Height: 32px (channels), 36px (agents), 48px (dive entries)
- Padding: 8px left, 8px right
- Icon/hash: 16px, color: `muted-foreground`
- Text: 13px, color: `sidebar-foreground` (inactive), `foreground` (active)
- Active indicator: `bg: sidebar-active-bg`, `border-left: 2px solid primary`
- Hover: `bg: sidebar-hover`
- Unread dot: 8px circle, `bg: primary`, right-aligned

### Main Content (Zone 3): flex

```
+----------------------------------------------------+
| Channel Header                                      |  48px
| # engineering  |  Topic: Rate Limiting   [Search]   |
+----------------------------------------------------+
|                                                     |
|  Thread View / Message List                         |  flex-1
|                                                     |  overflow-y: auto
|  [avatar] Charles                        2:30 PM   |
|  We need to implement rate limiting for             |
|  the public API. What approach should we            |
|  take?                                              |
|                         [React] [Reply] [Dive]      |
|                                                     |
|  [avatar] @Vibe (AI)                     2:31 PM   |
|  bg: agent                                          |
|  Three approaches to consider...                    |
|  [v Show full analysis]                             |
|                                                     |
|  ┌ Deep Dive Result ────────────────────────────┐   |
|  │ bg: resolution, border-left: 4px dive        │   |
|  │                                               │   |
|  │ DEEP DIVE RESULT          caption, dive color │   |
|  │ Charles explored rate limiting with @Vibe     │   |
|  │                                               │   |
|  │ Use Cloudflare Token Bucket                   │   |
|  │ heading, bold                                 │   |
|  │                                               │   |
|  │ - Handles 1000 req/s, ~$0.05/10K req         │   |
|  │ - No code changes — Cloudflare config only    │   |
|  │                                               │   |
|  │ View full deep dive (8 messages) ->           │   |
|  └──────────────────────────────────────────────┘   |
|                                                     |
+----------------------------------------------------+
| Compose Box                                         |  min 52px
| [Message #engineering...           @] [Send]        |  auto-grow
+----------------------------------------------------+
```

### Detail Panel (Zone 4): 320px, conditional

Only shown when:
- User clicks "View full deep dive" (shows dive panel)
- User explicitly opens thread details

```
+-----------------------------------+
| < Back    Dive: Pricing    [X]    |  48px header
+-----------------------------------+
| Forked from:                      |  context block
| "We need to implement..."         |  bg: elevated
| border-left: 3px dive-muted      |  40px
+-----------------------------------+
|                                   |
| Dive Messages                     |  flex-1
| (same message rendering as main)  |
|                                   |
+-----------------------------------+
| [Message in dive...       ] [Send]|  52px
+-----------------------------------+
```

---

## 5. Component Visual Specs

### 5.1 Message Bubble

Human and agent messages share the same basic structure but differ in visual treatment.

```
Human Message:
+----------------------------------------------------+
| [avatar] Charles                        2:30 PM     |
|                                                     |
| We need to implement rate limiting for the          |
| public API. What approach should we take?           |
|                                                     |
|                       [React] [Reply] [Deep Dive]   |  hover only
+----------------------------------------------------+

Avatar:     32px circle, radius-full, bg: elevated (initials) or image
Username:   13px, weight 600, color: foreground
Timestamp:  13px, weight 400, color: secondary
Body:       14px, weight 400, color: foreground, line-height: 1.6
Padding:    12px 16px (compact messages: 4px 16px when same author within 5min)
Hover bg:   var(--color-hover)
Actions:    appear on hover, 28px height, bg: elevated, radius-md, gap: 4px
```

```
Agent Message:
+----------------------------------------------------+
| bg: var(--color-agent)                              |
|                                                     |
| [robot-icon] @Vibe                      2:31 PM    |
|                                                     |
| Rate Limiting Strategy Analysis                     |  heading, 15px, bold
|                                                     |
| Three viable approaches for your scale:             |
|                                                     |
| 1. Token Bucket (Cloudflare native)                 |
|    Simplest, built into your infra                  |
|                                                     |
| 2. Sliding Window (Redis)                           |
|    Most accurate, needs Redis                       |
|                                                     |
| Recommendation: Token Bucket via Cloudflare.        |  bold
|                                                     |
| [v Show full comparison table]                      |  expand toggle
| [v Show implementation guide]                       |  text: secondary
|                                                     |
+----------------------------------------------------+

Background: var(--color-agent) — subtle violet tint
Avatar:     24px, bg: primary, robot/sparkle glyph in white
            NOT a realistic face. Geometric icon only.
Username:   13px, weight 600, color: primary
Badge:      "AI" caption next to name, bg: primary-muted, text: primary, radius-full
Border:     none (the background tint is sufficient)
Content:    full width, no max-width constraint
Expand:     13px, text: secondary, hover: text: foreground, cursor: pointer
            Chevron rotates on expand (transition: 200ms)
```

**Message grouping:** Messages from the same author within 5 minutes collapse into a "compact" format — no avatar, no name, just the message body with 4px top padding. Timestamp shows on hover.

### 5.2 Channel Header

```
+--------------------------------------------------------------------+
| # engineering  |  Rate limiting discussion   [Search] [Members] [*] |
+--------------------------------------------------------------------+

Height:     48px
Background: var(--color-surface)
Border:     bottom 1px solid var(--color-border)
Channel:    heading (15px, weight 600), color: foreground
Separator:  1px solid var(--color-border), height: 16px, margin: 0 12px
Topic:      small (13px), color: secondary, truncate with ellipsis
Icons:      20px, color: secondary, hover: foreground
            Search: magnifying glass
            Members: people icon
            Pin/more: ellipsis
```

### 5.3 Compose Box

```
+--------------------------------------------------------------------+
|  +--------------------------------------------------------------+  |
|  | Message #engineering...                                 @ |  |  |
|  |                                                             |  |  |
|  +--------------------------------------------------------------+  |
|  [Attach]                                              [Send ->]  |
+--------------------------------------------------------------------+

Container:   bg: surface, border-top: 1px solid var(--color-border)
             padding: 12px 16px
Input:       bg: var(--color-input), border: 1px solid var(--color-border)
             radius: var(--radius-lg) (8px)
             padding: 10px 14px
             font: 14px, line-height: 1.5
             min-height: 40px, max-height: 200px (auto-grow)
             focus: border-color: var(--color-primary), ring: 2px primary/20%
Placeholder: color: var(--color-muted-foreground)
Send button: bg: primary, radius: radius-md, 32px square
             icon: arrow-up, 16px, white
             disabled when empty: bg: primary-muted, cursor: not-allowed
Attach:      icon-only, 32px, color: secondary, hover: foreground
@ trigger:   triggers mention autocomplete dropdown
```

### 5.4 Deep Dive Button (on message hover)

```
[Deep Dive]

Background: var(--color-dive-muted)
Text:       var(--color-dive), 12px, weight 600
Border:     1px solid var(--color-dive-muted)
Radius:     var(--radius-md)
Padding:    4px 10px
Height:     28px
Icon:       Dive/magnifying-glass, 14px, left of text
Hover:      bg: var(--color-dive), text: var(--color-dive-foreground)
Transition: background 150ms, color 150ms
```

This button is visually distinct from Reply/React (which use neutral colors). The amber/gold dive accent makes it stand out as the differentiating action.

### 5.5 Deep Dive Result Card (in main thread)

```
+------------------------------------------------------------+
| bg: var(--color-resolution)                                |
| border-left: 4px solid var(--color-dive)                   |
| border: 1px solid var(--color-border)                      |
| radius: var(--radius-lg)                                   |
| padding: 16px 20px                                         |
|                                                            |
| DEEP DIVE RESULT              caption (11px), color: dive  |
| by Charles with @Vibe         small (13px), color: secondary|
|                                                            |
| Use Cloudflare Token Bucket   heading (15px), bold         |
| for Rate Limiting             color: foreground            |
|                                                            |
| - Handles 1000 req/s          body (14px), color: foreground|
| - No code changes needed      line-height: 1.6            |
| - ~$0.05 per 10K requests                                 |
|                                                            |
| ─────────────────────────────                              |
| View full deep dive (8 msgs) ->  small, color: dive       |
|                               hover: underline             |
+------------------------------------------------------------+

Max width: 100% of message area
Margin: 8px 0 (same as messages)
```

### 5.6 Mention Autocomplete

```
Trigger: "@" keystroke in compose box

+----------------------------+
| bg: elevated               |
| border: 1px border         |
| radius: radius-lg          |
| shadow: shadow-lg          |
| max-height: 240px          |
| width: 260px               |
|                            |
| AGENTS            overline |
|                            |
| [o] @Vibe                  |  36px row
|     Deep dive partner      |  caption, secondary
|                            |
| [o] @Coder                 |  36px row
|     Code assistant         |
|                            |
| MEMBERS           overline |
|                            |
| [avatar] Charles           |  36px row
| [avatar] Dev               |
+----------------------------+

Selected row: bg: var(--color-active)
Navigation: arrow keys + Enter
Dismiss: Escape or click outside
```

### 5.7 AI Thinking Indicator

```
Displayed when an agent is processing:

  [pulsing-dot] @Vibe is thinking...

Dot:        8px circle, bg: var(--color-primary)
            animation: pulse (scale 1.0 -> 1.3 -> 1.0, 1.5s ease, infinite)
Text:       13px, color: secondary, italic
Container:  padding: 8px 16px, same position where the response will appear
Transition: when first token arrives, dot fades out (150ms) as text fades in (200ms)
            NO layout shift — the text starts exactly where the indicator was

During a deep dive, the indicator uses dive accent:
  Dot:      bg: var(--color-dive)
  Text:     "@Vibe is researching..." (not "thinking" — different verb for dives)
```

### 5.8 Deep Dive Sidebar Entry

```
+-----------------------------------+
| [status] Pricing Research         |  13px, weight 600
|   Charles + @Vibe                 |  12px, secondary
|   3 msgs, 2m ago   [Active]      |  12px, muted / badge
+-----------------------------------+

Height:     48px
Padding:    8px 12px
Hover:      bg: sidebar-hover
Active:     bg: sidebar-active-bg, border-left: 2px solid dive

Status dot (left, 8px):
  Active (AI working):  bg: dive, pulse animation
  Waiting (human turn): bg: warning (amber), static
  Resolved:             bg: success, static

Badge:
  Active:   bg: dive-muted, text: dive, 10px, weight 600
  Resolved: bg: success/10%, text: success, 10px

Resolved entries:
  Dimmed: opacity 0.6
  Grouped under "RESOLVED" section header
  Collapsed by default, expand on click
```

### 5.9 Resolution Modal

```
+------------------------------------------------------------+
| Publish Deep Dive                                    [X]    |
+------------------------------------------------------------+
|                                                             |
| AI-generated summary:                                       |
| (edit before posting to thread)           caption, secondary|
|                                                             |
| Headline:                                                   |
| +--------------------------------------------------------+ |
| | Use Cloudflare Token Bucket for rate limiting          | |
| +--------------------------------------------------------+ |
|   input: bg: input, border: border, 15px, weight 600       |
|                                                             |
| Key Points:                                                 |
| +--------------------------------------------------------+ |
| | - Token Bucket via Cloudflare is simplest approach     | |
| | - Handles 1000 req/s, ~$0.05 per 10K requests         | |
| | - No code changes needed — Cloudflare config only      | |
| +--------------------------------------------------------+ |
|   textarea: bg: input, border: border, 14px, auto-grow     |
|                                                             |
| This will be posted to the main thread.                     |
|   caption, muted-foreground                                 |
|                                                             |
|           [Cancel]              [Publish to Thread]         |
|           secondary btn          bg: dive, text: dive-fg    |
+------------------------------------------------------------+

Container: bg: elevated, border: 1px border, radius: radius-xl (12px)
Shadow:    shadow-xl
Width:     520px (centered)
Overlay:   bg: background/60% (backdrop blur 4px)
Animation: overlay fade in (200ms), modal scale 0.95->1.0 + opacity (250ms)
```

### 5.10 Dive View Header (Focus Mode)

When viewing a deep dive, the main content header changes:

```
+--------------------------------------------------------------------+
| <- Back to thread   |   Dive: Pricing Research   [Discard] [Publish]|
+--------------------------------------------------------------------+
| Forked from Charles's message:                                      |
| "We need to implement rate limiting for the public API..."          |
| bg: elevated, border-left: 3px dive-muted, padding: 8px 12px      |
+--------------------------------------------------------------------+

Back button:  text: secondary, hover: foreground, 13px
              icon: arrow-left, 16px
Separator:    1px solid border, height: 16px
Dive title:   heading, weight 600, color: foreground
Discard btn:  ghost style, text: destructive, hover: bg destructive/10%
Publish btn:  bg: dive, text: dive-foreground, radius-md, weight 600

Context block:
  bg: elevated
  border-left: 3px solid dive-muted
  border-radius: radius-sm (right side only)
  padding: 8px 12px
  text: 13px, secondary, italic
  truncated to 2 lines with ellipsis
  click: scrolls main thread to source message
```

---

## 6. Interaction Patterns

### Hover States

| Element | Idle | Hover | Active/Click |
|---------|------|-------|-------------|
| Channel item | bg: transparent | bg: sidebar-hover | bg: sidebar-active-bg |
| Message row | bg: transparent | bg: hover, actions visible | n/a |
| Button (primary) | bg: primary | bg: primary-hover | scale: 0.98 |
| Button (ghost) | bg: transparent | bg: hover | bg: active |
| Dive button | bg: dive-muted | bg: dive, text inverts | scale: 0.98 |
| Sidebar dive entry | bg: transparent | bg: sidebar-hover | bg: sidebar-active-bg |
| Link | text: primary | text: primary, underline | opacity: 0.8 |

### Transitions

All transitions use `150ms ease` unless specified:

```css
/* Standard interactive transition */
transition: background-color 150ms ease, color 150ms ease, border-color 150ms ease;

/* Panel transitions (enter/exit) */
transition: transform 300ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease;

/* Expand/collapse */
transition: height 250ms ease, opacity 200ms ease;

/* Focus ring */
transition: box-shadow 150ms ease;
```

### Focus States

```css
/* Keyboard focus (visible only on keyboard navigation) */
:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-surface), 0 0 0 4px var(--color-ring);
}
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Open command palette / search |
| `Cmd+Enter` | Send message |
| `Cmd+Shift+D` | Start deep dive on selected message |
| `Escape` | Close panel / modal / return to thread |
| `Up/Down` | Navigate lists |
| `Enter` | Select / confirm |

---

## 7. Animation Specs

### Pulse (AI Thinking)

```css
@keyframes pulse-thinking {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}
/* Usage: animation: pulse-thinking 1.5s ease-in-out infinite; */
```

### Fade In (New Message)

```css
@keyframes message-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
/* Usage: animation: message-in 200ms ease-out; */
```

### Panel Slide (Deep Dive Panel)

```css
/* Enter */
@keyframes panel-enter {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
/* Duration: 300ms, easing: cubic-bezier(0.16, 1, 0.3, 1) */

/* Exit */
@keyframes panel-exit {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}
/* Duration: 250ms, easing: ease-in */
```

### Modal (Resolution Modal)

```css
/* Overlay */
@keyframes overlay-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
/* Duration: 200ms */

/* Modal content */
@keyframes modal-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
/* Duration: 250ms, easing: cubic-bezier(0.16, 1, 0.3, 1) */
```

### Streaming Cursor

```css
@keyframes blink-cursor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
/* Applied to a 2px wide, 16px tall bar in primary color */
/* animation: blink-cursor 1s step-end infinite; */
```

---

## 8. Progressive Disclosure

### Three-Layer Message Rendering

Every AI response has three potential layers. The display depends on context:

| Layer | Default State | When Shown |
|-------|--------------|------------|
| **Headline** (1 line) | Always visible | Notifications, dive result cards, search results |
| **Summary** (3-5 bullets) | Visible in dive result cards, collapsed in thread | Click "expand" in thread, default in dive view |
| **Full Output** | Collapsed everywhere | Click "Show full analysis" |

### Expand/Collapse Toggle

```
[v Show full analysis]       collapsed
[^ Hide full analysis]       expanded

Text:     13px, color: secondary
Icon:     chevron, 12px, rotates 180deg on toggle (200ms ease)
Hover:    color: foreground
Click:    content expands with height animation (250ms ease)
          Scroll position adjusted to keep toggle visible
```

### Code Block Collapse (>20 lines)

```
+------------------------------------------------------+
| typescript                                    [Copy]  |
+------------------------------------------------------+
|  1  const rateLimiter = new TokenBucket({            |
|  2    rate: 1000,                                    |
|  3    capacity: 5000,                                |
| ...                                                  |
| 15  // ... (truncated)                               |
+------------------------------------------------------+
| Show all 47 lines                            v       |
+------------------------------------------------------+

Fade: last 2 visible lines have a gradient overlay
      (codeblock -> transparent, 24px height)
Toggle: full-width button, bg: codeblock, border-top: 1px border
        13px, color: secondary, hover: foreground
```

---

## 9. Empty & Loading States

### Loading Skeleton

```
Message skeleton:
  [circle 32px]  [bar 120px x 13px]     [bar 48px x 13px]
                 [bar 280px x 14px]
                 [bar 200px x 14px]

Colors: bg: var(--color-elevated), shimmer animation
Shimmer: linear gradient sweep left to right, 1.5s, infinite
Opacity: 0.5 -> 0.3 -> 0.5
```

### Empty States

```
Channel with no threads:
  Center-aligned, max-width: 320px
  Icon: message-circle, 48px, color: muted-foreground
  Title: "No threads yet", heading, foreground
  Body:  "Start a conversation in #engineering", small, secondary
  CTA:   "New Thread" button, primary

Thread with no messages (impossible state but handle gracefully):
  Similar pattern, "Start the conversation" CTA
```

---

## 10. Responsive Behavior

| Breakpoint | Sidebar | Main | Detail Panel |
|------------|---------|------|-------------|
| Desktop (>1200px) | 240px fixed | flex | 320px when open |
| Tablet (768-1200px) | 240px collapsible (hamburger toggle) | flex | overlay or hidden |
| Mobile (<768px) | Full-screen sheet (swipe from left) | full width | full screen |

**MVP: Desktop only.** Tablet and mobile are deferred. The sidebar is always visible at 240px.

---

## 11. Icon System

Use **Lucide React** (already in shadcn/ui). Consistent 20px size for toolbar icons, 16px for inline, 14px for compact.

| Context | Icon Size | Stroke Width |
|---------|-----------|-------------|
| Toolbar / header | 20px | 1.5 |
| Sidebar items | 16px | 1.5 |
| Inline (badges, status) | 14px | 2 |
| Message actions | 16px | 1.5 |

Key icons:
- Deep Dive: `Telescope` or `Sparkles` (needs testing — pick the one that reads at 16px)
- Publish: `Send` (rotated 0deg, not the diagonal)
- Channel: `Hash`
- Agent: `Bot`
- Back: `ArrowLeft`
- Close: `X`
- Expand: `ChevronDown`
- Search: `Search`
- Attach: `Paperclip`
- Copy: `Copy`
- Reply: `Reply`

---

## 12. Component Catalog (Agent Responses)

### DataTable

```
+------------------------------------------------------+
| bg: elevated                                         |
| radius: radius-lg                                    |
| border: 1px border                                   |
| overflow: hidden                                     |
|                                                      |
| Header row: bg: surface, 36px height                 |
| th: 13px, weight 600, color: secondary, padding: 8px |
|                                                      |
| Body rows: 36px height                               |
| td: 13px, weight 400, color: foreground, padding: 8px|
| Alternating: even rows bg: hover (very subtle)       |
| Hover: bg: hover                                     |
+------------------------------------------------------+
```

### SummaryCard

```
+------------------------------------------------------+
| bg: elevated, radius: radius-lg, padding: 16px       |
| border: 1px border                                   |
|                                                      |
| Title          heading, bold                          |
|                                                      |
| label: value   14px, label bold, value normal         |
| label: value                                          |
| label: value                                          |
|                                                      |
| Recommendation                                        |
| bg: dive-muted, radius: radius-md, padding: 8px 12px |
| text: 14px, color: foreground                         |
+------------------------------------------------------+
```

### ActionButtons

```
Row of buttons, gap: 8px, flex-wrap

Primary action: bg: primary, text: primary-foreground, radius: radius-md
Secondary action: bg: transparent, border: 1px border, text: foreground, radius: radius-md
Height: 32px
Font: 13px, weight 500
Padding: 0 14px
```

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dark mode only | Yes | Focused tool, code-heavy content, reduced fatigue |
| Server list zone | Removed (0px) | Single workspace for dogfood, reclaim 48px |
| Geist font | Yes | Ships with Next.js, designed for dev tools |
| Geist Pixel | Logo only | Too playful for body text in a productivity tool |
| oklch color space | Yes | Perceptually uniform, better for dark mode gradients |
| Dual accent (violet/amber) | Yes | Tells the "going deeper" story through color |
| No message bubbles | Correct for AI | AI responses need full width for code/tables |
| Focus mode (not tabs) | Yes | Validated in THREAD-UX-PROPOSAL |
| 14px body text | Yes | Readable at density, not too large |
| 8px spacing base | Yes | Industry standard, works well with 4px subgrid |

---

*Created: 2026-02-08*
*Synthesized from: THREAD-UX-PROPOSAL, FRONTEND-ARCHITECTURE, M2-FRONTEND, PRODUCT-CORE-REFRAME*
*Design tokens implementation: `apps/web/src/app/globals.css`*
