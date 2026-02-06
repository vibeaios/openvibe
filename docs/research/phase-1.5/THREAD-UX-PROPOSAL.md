# Phase 1.5: Thread-Based UX Proposal

> Making the AI research loop a first-class part of team conversation
> Status: Complete | Researcher: thread-ux-designer | Date: 2026-02-07

---

## Research Question

The founder described the actual workflow driving this product:

1. Team asks a question in Slack
2. Founder copies it to AI, gives context, researches
3. Gets result, pastes back to Slack
4. AI output is too long/dense for team to read
5. Team members ALSO copy it to AI to digest
6. Then respond back

This creates three compounding problems: **context loss** (AI research happens outside the conversation), **information overload** (AI outputs are too verbose for group consumption), and **copy-paste hell** (manual shuttling between tools).

The core insight: **Fork/Resolve is not about "branching discussions between humans." It is about making the AI research loop a first-class part of the conversation.** Each person should have their own runtime (like OpenClaw) and be able to do research within the thread context.

This proposal addresses: In a thread where humans AND agents can create infinite branches/forks, how do you solve this in UX? Branch/merge is just ONE possible solution.

---

## Sources Consulted

### Internal Documents
- `docs/research/R1-THREAD-MODEL.md` -- Fork/Resolve model, three-tier adoption, prototype scenarios
- `docs/research/R2-GENERATIVE-UI.md` -- Config-driven UI + agent component catalog
- `docs/research/R3-AGENT-LIFECYCLE.md` -- Task lifecycle, context overflow strategies, auto-decision framework
- `docs/research/R7-CONTEXT-UNIFICATION.md` -- Cross-runtime context architecture
- `docs/research/SYNTHESIS.md` -- Phase 1 integration, contradictions, gaps
- `docs/research/COMPETITIVE-LANDSCAPE.md` -- Slack AI, Notion AI, ChatGPT branching analysis
- `docs/PRODUCT-REASONING.md` -- Original product derivation, "each person has an OpenClaw"
- `docs/design/M1-THREAD-ENGINE.md` -- Original Git-like thread data model
- `docs/design/M2-FRONTEND.md` -- Original frontend layout and interaction design

### External Research: Conversation Branching Products
- **ChatGPT Branching** (Sep 2025, mobile Dec 2025) -- "Branch in new chat" from any message. Single-user. No merge. No tree view in core product. Third-party extensions (BranchGPT, Conversation Tree Visualizer) add tree visualization, confirming demand for spatial awareness.
- **LibreChat** (v0.7.8+) -- Open-source ChatGPT alternative with fork feature. Three fork modes: visible messages only, visible + branches, entire target. Fork creates a new conversation copy. No merge/resolve. Demonstrates that fork-as-copy is the simplest viable approach.
- **Perplexity** -- Community requests for branching/forking (forum thread #1074). Unmet demand signal.
- **OpenAI Developer Forum** -- "Session Forking / Branching Conversations" request (#1266483). Users want to explore directions without losing original thread.

### External Research: Progressive Disclosure for AI Responses
- **Nick Babich, UX Planet (Jan 2026)** -- "Progressive Disclosure in AI-Powered Product Design": AI interfaces must layer complexity, starting with essentials and revealing detail on demand.
- **AI Positive Newsletter (2026)** -- "Progressive Disclosure Matters: Applying 90s UX Wisdom to 2026 AI Agents": Gemini CLI adopted Agent Skills as a progressive disclosure mechanism. Information architecture for AI must combat decision paralysis.
- **Algolia (2025)** -- "Information density and progressive disclosure -- the keys to good search UX": Search results demonstrate the summary-first, expand-on-demand pattern that applies directly to AI research results.
- **AIUX Design Guide** -- Progressive Disclosure pattern catalog for AI interfaces. Key principle: "the interface starts with basics and introduces advanced concepts only when relevant to the user's current task."

### External Research: Slack Noise Problem
- **ClearFeed (2025)** -- "Slack Noise Isn't Just a Slack or an AI Problem": Slack's dual role as communication + knowledge hub creates irreducible noise. AI summaries help but don't solve the structural problem.
- **QuestionBase (2025)** -- "Slack Notification Overload: AI Solutions": 40% of internal queries are repeated. Experts spend 6 hours/week on redundant questions.
- **Slack (Dec 2025)** -- "Notifications 2.0" overhaul: simplified channel notifications, clearer push controls. Signals that even Slack acknowledges the problem is structural.
- **Slack (Jan 2026)** -- Slackbot AI agent GA for Business+/Enterprise+. AI-driven Workflow Builder recommendations. 80% of AI adopters report productivity increases, saving 3.6 hours/week.

### External Research: UX Paradigms
- **Nikita Vergis, Medium (2025)** -- "AI Chat Tools Don't Match How We Actually Think: Exploring the UX of Branching Conversations": Visual maps help users understand thinking journey. Branching matches cognition. Merge is the hard problem.
- **Artium AI (2025)** -- "Beyond Chat: How AI is Transforming UI Design Patterns": Shift from chat-as-interface to chat-as-orchestration. AI responses should be structured outputs, not just text.
- **Jakob Nielsen (2026)** -- Prediction: 2026 is the year AI agents shift from passive tools to active systems. Progressive disclosure becomes the dominant pattern for managing agent output.

---

## Part 1: The Infinite Branching Problem

### Problem Statement

In a thread with N humans and M agents, every participant can potentially fork the conversation at any point. With agents that can auto-fork for research, the branching is theoretically unbounded. If the founder forks to research with AI, and two team members each fork to digest the result with their own agents, and each agent creates sub-forks for deeper investigation -- you get a combinatorial explosion.

The question is not "should we support branching?" but "how do we present potentially dozens of concurrent explorations without overwhelming the user?"

### All UX Approaches Evaluated

#### Approach 1: Flat Thread with AI Summaries (Enhanced Slack)

**Description:** Linear thread, no branching at all. AI research happens as inline messages. When results are long, AI auto-generates collapsible summaries. All activity is visible in one stream.

**Pros:**
- Zero learning curve from Slack
- No cognitive overhead of managing branches
- Works for every user regardless of technical sophistication
- Simple to implement

**Cons:**
- Does NOT solve the founder's problem. The AI research loop still clutters the main thread. A 5-minute research task produces 20 messages that everyone has to scroll past.
- No parallel exploration. If two people want to research different angles simultaneously, their messages interleave and become unreadable.
- Agent noise dominates. With multiple agents active, the thread becomes a firehose.
- This is what Slack + AI bots already does. No differentiation.

**Verdict:** Insufficient. Solves none of the three core problems (context loss, overload, copy-paste). Rejected as primary model.

#### Approach 2: Fork/Resolve (R1 Recommendation)

**Description:** Any message can spawn a side-thread (fork). Forks are visible in a sidebar. When done, a fork is "resolved" with an AI summary posted to the parent. The fork is archived.

**Pros:**
- Directly addresses the founder's workflow: "take this to AI" becomes "fork and research"
- Keeps main thread clean -- research happens in forks, only conclusions come back
- AI summary bridges the gap between "researcher did 5 minutes of work" and "team needs 10 seconds to understand"
- Proven concept in single-user tools (ChatGPT branching, LibreChat forks)

**Cons:**
- With many participants + agents, fork count can explode
- Sidebar becomes its own management problem at 10+ active forks
- Fork-from-fork creates nesting that recreates the Reddit problem
- "Resolve" depends on AI summary quality -- bad summaries poison the main thread
- New concept for most users: "what is a fork? when should I fork?"

**Verdict:** Strong foundation, but needs constraints to prevent explosion. The sidebar cannot be a simple list at scale.

#### Approach 3: Nested Threads (Reddit/HN Model)

**Description:** Every reply can have sub-replies, forming a tree. Depth is unlimited. Collapse/expand controls manage visibility.

**Pros:**
- Natural for organic discussion branching
- No new concepts -- everyone understands reply trees

**Cons:**
- Deep nesting is unreadable (Discourse's 15+ years of data confirm this)
- No clear "resolution" mechanism -- threads just trail off
- Agent outputs at depth 5+ are invisible to casual readers
- Mobile UX is terrible for deep nesting
- Doesn't distinguish "I'm researching" from "I'm replying"

**Verdict:** Rejected. Deep nesting actively hurts readability and has no resolution semantics.

#### Approach 4: Canvas/Spatial Layout

**Description:** Thread rendered as a 2D canvas. Messages are nodes. Branches spread spatially. Users pan and zoom to navigate. Think Miro/FigJam but for conversation.

**Pros:**
- Visually expressive -- can show relationships between ideas
- Natural for brainstorming and exploration
- No depth limit problems (space is 2D, not 1D)
- Differentiated UX -- no chat tool does this

**Cons:**
- Extremely high cognitive load. Users must manage spatial arrangement.
- Breaks the fundamental mental model of "conversation as timeline"
- Real-time collaboration on a canvas is a hard technical problem (CRDT/OT)
- Mobile support is essentially impossible
- Doesn't solve the information density problem at all -- it spreads it across more space
- "Where did Bob's research end up?" requires visual scanning instead of scrolling

**Verdict:** Rejected for primary UX. Could be a secondary "visualization" mode for complex threads, but not the default interaction.

#### Approach 5: Tabs (Browser-Like)

**Description:** Each fork becomes a tab at the top of the thread view. Switch between tabs to see different forks. Main thread is always the first tab.

**Pros:**
- Familiar metaphor (browser tabs)
- Clean separation between explorations
- Easy to switch between contexts

**Cons:**
- Tabs don't scale. At 8+ forks, the tab bar becomes unmanageable (exactly the browser tab problem)
- No hierarchy -- all forks appear equal regardless of importance
- No visual indication of what's happening in other tabs without switching
- Doesn't show the relationship between forks and their parent messages

**Verdict:** Rejected as primary navigation. R1 already noted "not tabs -- tabs don't scale." The M2 design's branch tabs are the wrong pattern.

#### Approach 6: Focus Mode with Peripheral Awareness

**Description:** The user is always focused on ONE context (main thread or a specific fork). Other active explorations appear as minimal status indicators in a peripheral panel. Users explicitly choose to switch focus. AI manages the peripheral indicators.

**Pros:**
- Solves the cognitive overload problem by showing only one thing at a time
- Peripheral awareness prevents missing important updates
- Scales to any number of forks -- the peripheral panel is just a status list
- Agent activity is visible but not intrusive
- Maps well to how people actually work: deep focus on one thing, awareness of others

**Cons:**
- Requires good status indicators (what's happening in forks I'm not looking at?)
- Context switching between forks requires loading a new view
- Harder to compare two forks side by side
- Relies on AI to generate meaningful status summaries for peripheral panel

**Verdict:** Strong candidate. This is the most scalable approach for managing many concurrent explorations.

#### Approach 7: Conversation Layers (Stacked View)

**Description:** The thread is a vertical stack. The main conversation is the base layer. Forks are layers that slide in from the right, partially overlapping the main thread. Multiple forks can be stacked/unstacked. The "depth" of the stack shows how many active explorations exist.

**Pros:**
- Visual metaphor of "going deeper" into a topic
- Can see the main thread while reading a fork (partial overlap)
- Stack depth provides at-a-glance complexity indicator
- Natural "resolve = close the layer" gesture

**Cons:**
- Stack beyond 3-4 layers becomes confusing
- Partial overlap means some content is always hidden
- No standard UI pattern for this -- users must learn a new mental model
- Implementation complexity is high (layered scroll views)

**Verdict:** Interesting for 2-3 levels of depth. Not viable for many concurrent forks. Consider as a visual treatment for the recommended approach.

### Recommendation: Hybrid Focus Mode + Lightweight Fork Sidebar

**The winning approach combines Focus Mode (Approach 6) with Fork/Resolve (Approach 2) and adds a Layer hint (Approach 7).**

The key insight: the problem is not "how to show all branches" but "how to let each person focus on their current exploration while staying aware of what others are doing."

Design principles:
1. **One focus at a time.** The main view shows either the main thread OR a single fork. Never both interleaved.
2. **Peripheral awareness panel.** A compact sidebar shows all active forks with real-time status (who's in it, what's happening, how many messages).
3. **AI-generated status lines.** Each fork's sidebar entry is a single AI-generated line summarizing current activity: "Charles researching pricing models with @Agent-Researcher (7 msgs, 3 min ago)".
4. **Resolve pushes summary to parent.** When a fork completes, the AI summary appears in the parent context. The fork itself collapses to a link.
5. **Fork depth limit: 1.** Forks from forks are not allowed in MVP. If you need to go deeper, create a new top-level fork with context from the current one.
6. **Maximum 7 active forks per thread.** After 7, the system suggests resolving or abandoning existing forks before creating new ones. (7 = Miller's number for working memory.)

---

## Part 2: Agent Interaction Model in Threads

### How Agents Participate

Three interaction triggers, from most explicit to most autonomous:

#### 1. @Mention (Explicit Invocation)
```
User: "@Researcher what are the pricing models our competitors use?"
```
The agent receives the message + thread context up to that point. It responds in-line. This is the Slack model, familiar to everyone.

**When to use:** Specific questions, direct requests, bringing an agent into a conversation.

#### 2. Auto-Join on Fork (Implicit Assignment)
When a user creates a fork and mentions an agent in the fork description, the agent automatically joins and begins working.

```
[User clicks Fork on a message]
Fork description: "Research competitor pricing with @Researcher"
-> @Researcher automatically begins working in this fork
```

**When to use:** Research tasks, analysis tasks, anything where the fork IS the agent's workspace.

#### 3. Ambient Monitoring (Agent-Suggested Actions)
Agents can monitor threads they're assigned to (via workspace config) and suggest actions without being explicitly asked. These suggestions appear as subtle, dismissible notifications.

```
Agent-Strategy (monitoring #product):
  "This discussion has two distinct topics: pricing and packaging.
   Suggest: Fork 'packaging' into a separate exploration?"
  [Fork] [Dismiss]
```

**When to use:** Thread hygiene, detecting diverging topics, proactive assistance. Must be conservative -- ambient suggestions should be rare (max 1 per 20 messages) or they become Slack-level noise.

**MVP recommendation:** Implement only @mention and auto-join on fork. Ambient monitoring is Phase 2+.

### Agent Context Model

**What context does an agent see?**

| Agent Location | Context Provided |
|---------------|-----------------|
| @mentioned in main thread | Full main thread up to the mention point |
| Working in a fork | Parent thread up to fork point + all fork messages |
| @mentioned in a fork | Parent thread up to fork point + all fork messages up to mention |
| Generating a resolution summary | Full fork content + parent thread context around the fork point |

The critical design: **forks inherit parent context but NOT sibling fork context.** Agent-A working in Fork-1 does not see what Agent-B is doing in Fork-2. This is intentional:
- Prevents context explosion (each fork's agent doesn't need to track N other forks)
- Preserves independent exploration (the point of forking is to explore independently)
- Resolution summaries are how fork results cross-pollinate

**Exception:** When resolving, the resolution agent CAN be given summaries of sibling forks if explicitly requested ("Resolve this fork, considering what Fork-2 found").

### Can Agents Interact with Each Other?

**In the same fork:** Yes. Multiple agents can be @mentioned in a fork and they respond in sequence. Agent-A's output becomes context for Agent-B. This supports the "researcher + writer" pattern:

```
Fork: "Analyze pricing"
User: "@Researcher pull competitor data"
@Researcher: [produces analysis]
User: "@Writer summarize this for the team"
@Writer: [produces concise summary using Researcher's output]
```

**Across forks:** No direct interaction. Agents in different forks communicate indirectly through resolution summaries posted to the parent thread. This prevents the combinatorial explosion of cross-fork agent chatter.

**Agent-to-agent delegation:** Not in MVP. An agent cannot spawn another agent. This requires the orchestration layer from R3/M5 and adds complexity that isn't needed for dogfood. Add in Phase 2 when the Vibe team demonstrates need.

### What "Each Person Has Their Own Runtime" Means for Thread UX

From PRODUCT-REASONING.md: "Each person has a Personal Agent, like their own OpenClaw."

**UX implications:**

1. **Personal research is private until shared.** When a user takes something to their Personal Agent (outside any thread), the research is invisible to the team. The user can then "bring it back" by posting the result or a summary to the thread. This mirrors the founder's current workflow but makes it explicit.

2. **Thread-context research is visible.** When a user forks within a thread and works with an agent there, the fork is visible in the sidebar. Others can see "Charles is researching in Fork: Pricing Analysis" but cannot read the fork content until Charles resolves it or explicitly shares it.

3. **The distinction is: thread fork = team-visible research; Personal Agent DM = private research.** The user chooses visibility.

**What "taking something to AI" looks like IN the thread:**

```
Option A: Fork (visible to team)
  User right-clicks a message -> "Research this" -> Creates a fork
  -> Personal Agent or specified agent begins working in the fork
  -> Sidebar shows: "Charles: researching [topic]"
  -> When done: "Resolve" pushes summary to parent

Option B: DM to Personal Agent (invisible to team)
  User selects message text -> "Ask my agent" -> Opens DM with Personal Agent
  -> Agent receives the selected text + user-provided context
  -> Research happens in the private DM
  -> User manually copies/pastes the relevant conclusion back to thread
  OR -> User clicks "Share to thread" to post the agent's conclusion

MVP: Implement Option A only. Option B is the current Slack workflow
(copy to AI, paste back) and doesn't need to be built -- users will
do it naturally. The value of OpenVibe is making Option A the
frictionless default.
```

---

## Part 3: Information Density Problem

### The Core Problem

An agent researches for 5 minutes and produces 2000 words. This is useful to the person who initiated the research. It is useless to the 4 other people in the thread who just need the conclusion.

The information density problem has three aspects:
1. **For the researcher:** The full output is valuable. They need to read, verify, and decide what's important.
2. **For team members:** They need the conclusion (2-3 sentences) and the ability to drill down IF they want to.
3. **For future reference:** The full output should be preserved for search and context.

### Solution: Three-Layer Message Rendering

Every agent response is rendered with three layers. The user sees the layer appropriate to their role and context.

#### Layer 1: Headline (Always Visible)
A single line that captures the essence. Generated by the agent or extracted by the system.

```
@Researcher: Competitor pricing analysis complete -- 3 models found,
tiered recommended. [Expand]
```

This is what appears in the main thread when a fork is resolved. It is also what appears in notification previews.

#### Layer 2: Summary (Default Expanded in Fork, Collapsed in Main Thread)
A structured summary: 3-5 bullet points covering key findings, recommendations, and caveats.

```
@Researcher: Competitor pricing analysis

Key findings:
- Per-seat: $15-25/user/month. Simple but penalizes growth.
- Usage-based: $0.01-0.05/API call. Aligns cost with value but unpredictable bills.
- Tiered: Free/Pro/Enterprise. Most common, best retention metrics.

Recommendation: Tiered with usage-based overages for API-heavy customers.
Confidence: High (based on 12 competitors analyzed).

[Show full analysis...]
```

This is what the fork initiator sees when reading the fork. It is what team members see if they click "Expand" on the headline.

#### Layer 3: Full Output (On-Demand)
The complete agent output: data tables, reasoning chain, sources, caveats. Only shown when explicitly requested ("Show full analysis").

This layer is stored in memory and searchable. It powers the summary layers above.

### Implementation: Progressive Disclosure Components

Agent responses use the component catalog from R2, extended with disclosure controls:

```yaml
# Agent response structure
response:
  headline: "Competitor pricing analysis complete -- tiered recommended"
  summary:
    type: summary_card
    props:
      title: "Competitor Pricing Analysis"
      items:
        - label: "Per-seat"
          value: "$15-25/user/month. Simple but penalizes growth."
        - label: "Usage-based"
          value: "$0.01-0.05/API call. Aligns cost with value."
        - label: "Tiered"
          value: "Free/Pro/Enterprise. Most common, best retention."
      recommendation: "Tiered with usage-based overages"
      confidence: "High"
  full_output:
    type: text
    props:
      content: "[2000 words of detailed analysis...]"
      collapsible: true
      default_collapsed: true
```

### How Results Get Presented to Others

When someone who did NOT initiate the research sees the result:

**In the main thread (after fork resolution):**
```
[Fork resolved: Pricing Analysis]
Charles researched competitor pricing with @Researcher.

Conclusion: Tiered pricing (Free/Pro/Enterprise) is recommended.
Most common model among competitors, best retention metrics.
Tiered with usage-based overages for API-heavy customers.

[View full research (23 messages)] [React] [Reply]
```

The resolution summary is the ONLY thing that appears in the main thread. The full research is one click away but not forced on anyone.

**In notifications:**
```
#product thread: Charles resolved "Pricing Analysis"
-> Tiered pricing recommended. [View]
```

Notifications show the headline only. Click to see the summary. Two clicks to see the full research.

### Handling the "Agent Produced a Wall of Text" Problem

Even within a fork, agent responses should use progressive disclosure:

1. **Thinking indicator:** While the agent works, show: `@Researcher is analyzing... (12 sources found, comparing pricing models)` -- real-time status, not just a spinner.

2. **Structured output:** Agent responses default to summary_card format, not raw text. The agent is prompted to produce structured output: headline, key points, recommendation, caveats.

3. **Chunked delivery:** For long research (>60 seconds), the agent posts intermediate updates: "Found 5 competitors so far. Continuing..." This gives the user early visibility and the option to redirect ("Focus on SaaS competitors only").

4. **Edit before resolve:** When the fork initiator clicks "Resolve," they see the AI-generated summary and can edit it before it's posted to the parent. This prevents bad summaries from polluting the main thread.

---

## Part 4: Concrete Interaction Flows

### Scenario A: Team Asks Technical Question, Founder Researches with AI

**The founder's current workflow, reimagined in OpenVibe:**

```
#engineering channel, Thread: "API Rate Limiting Strategy"

Dev: "We need to implement rate limiting for the public API.
      What approach should we take?"

[3 team members react with thumbs up]

Charles: "Let me research this."
[Charles clicks Fork on Dev's message]
[Fork created: "Rate Limiting Research"]

--- Fork: Rate Limiting Research ---

Charles: "@Researcher analyze rate limiting strategies for
          REST APIs. Consider our scale (1000 req/s peak)
          and that we use Cloudflare."

@Researcher: [thinking... checking Cloudflare docs, analyzing
              token bucket vs sliding window vs leaky bucket...]

@Researcher:
  Rate Limiting Strategy Analysis

  Three viable approaches for your scale:
  1. Token Bucket (Cloudflare native) -- simplest,
     built into your existing infra
  2. Sliding Window (Redis) -- most accurate,
     requires Redis dependency
  3. Adaptive (AI-driven) -- adjusts limits based on
     client behavior, complex to implement

  Recommendation: Token Bucket via Cloudflare's Rate
  Limiting product. Handles 1000 req/s easily. ~$0.05
  per 10K requests. No code changes needed beyond
  Cloudflare config.

  [Show full comparison table...]
  [Show implementation guide...]

Charles: "Good. Let me refine the Cloudflare option."
Charles: "@Researcher what are the Cloudflare rate limiting
          rules we'd need for our endpoints?"

@Researcher: [produces specific Cloudflare config...]

Charles: [Clicks "Resolve"]
[Resolution editor shows AI-generated summary]
[Charles edits summary slightly]
[Clicks "Post to thread"]

--- Back in main thread ---

[Fork resolved: Rate Limiting Research]
Charles researched rate limiting strategies with @Researcher.

Conclusion: Use Cloudflare's native Rate Limiting (Token Bucket).
Handles our 1000 req/s scale. ~$0.05/10K requests. No code changes
-- just Cloudflare config. Token bucket is simpler than sliding
window and sufficient for our accuracy needs.

[View full research (8 messages)]

Dev: "Makes sense. I'll set up the Cloudflare rules this sprint."
```

**What changed vs Slack workflow:**
- Research happened IN the thread context, not in a separate ChatGPT window
- The team sees the conclusion immediately without reading 8 messages of research
- The full research is preserved and searchable
- No copy-paste between tools

### Scenario B: Two People Fork the Same Topic, Research Independently

```
#product channel, Thread: "Q2 Growth Strategy"

Charles: "We need to decide between expanding to legal vertical
          or doubling down on medical."

VP-Sales: "I have data on both. Let me pull it together."
[VP-Sales forks: "Legal Vertical Data"]

Charles: "I want to look at this from the product angle."
[Charles forks: "Product Capacity Analysis"]

--- Sidebar shows: ---
Active forks (2):
  [Legal Vertical Data] - VP-Sales + @Researcher (4 msgs, active)
  [Product Capacity Analysis] - Charles + @Analyst (2 msgs, active)
---

--- Fork 1: Legal Vertical Data ---
VP-Sales: "@Researcher pull our pipeline data for legal
           prospects from last quarter"
@Researcher: [produces analysis of 15 legal prospects,
              conversion rates, deal sizes]
VP-Sales: "And compare to medical pipeline."
@Researcher: [comparison table]
VP-Sales: [Resolves fork]

--- Fork 2: Product Capacity Analysis ---
Charles: "@Analyst given our engineering team size, can we
          support a second vertical in Q2?"
@Analyst: [analyzes current sprint capacity, estimates
           integration work for legal vertical]
Charles: [Resolves fork]

--- Back in main thread ---

[Fork resolved: Legal Vertical Data]
VP-Sales analyzed pipeline data. Legal has 15 qualified prospects
(vs 23 medical). Average deal size 40% higher but conversion rate
is half. Net revenue potential is roughly equal.
[View full research]

[Fork resolved: Product Capacity Analysis]
Charles analyzed engineering capacity. Adding legal vertical in Q2
requires 2 dedicated engineers for 8 weeks. Current team can
absorb this only if we defer the dashboard redesign.
[View full research]

Charles: "So the question is: trade dashboard redesign for legal
          vertical entry. Legal revenue potential is equal to
          medical but at higher deal sizes. Let's discuss."

VP-Sales: "Given the higher deal sizes, I'd prioritize legal.
           Fewer deals to manage with same revenue."

Charles: "Agreed. Q2 OKR: Launch legal vertical, defer dashboard
          to Q3. @Agent-Writer capture this decision."
```

**What this shows:**
- Two people independently researched different aspects of the same question
- Neither person's research cluttered the other's view
- Both resolution summaries appear in the main thread in chronological order
- The decision was made on the basis of both research streams
- The main thread reads as a clean narrative: question -> research -> data -> decision

### Scenario C: Agent Does Long Research, Team Needs to Digest

```
#strategy channel, Thread: "Competitor Feature Analysis"

Charles: "I need a comprehensive feature comparison of our product
          vs the top 5 competitors. @Deep-Researcher this is going
          to be thorough -- take your time."

[Charles forks: "Comprehensive Competitor Analysis"]

--- Fork: Comprehensive Competitor Analysis ---

@Deep-Researcher: Starting comprehensive analysis.
  Identifying top 5 competitors...
  [2 minutes later]
  Competitors identified: Slack, Teams, Notion, Linear, Asana.
  Analyzing feature sets across 8 categories...
  [3 minutes later]
  Feature matrix complete (40 features x 5 competitors).
  Generating insights and gap analysis...
  [2 minutes later]

@Deep-Researcher:
  Competitive Feature Analysis Complete (7 minutes)

  HEADLINE: We lead in AI-native features but lag in
  integrations and mobile experience.

  KEY GAPS:
  - No mobile app (all 5 competitors have one)
  - Integration count: us 3, average competitor 45
  - No calendar integration (4/5 competitors have it)

  KEY ADVANTAGES:
  - Fork/Resolve threading (unique, 0 competitors)
  - In-thread AI research (partial overlap with Slack AI)
  - Agent component catalog (unique)

  [Show full 40-feature matrix...]
  [Show gap analysis details...]
  [Show recommended priorities...]

Charles: "Good analysis. Let me clean up the summary before
          sharing with the team."
[Charles clicks Resolve]
[Edits the summary to emphasize the mobile gap]
[Posts to thread]

--- Back in main thread ---

[Fork resolved: Comprehensive Competitor Analysis]
@Deep-Researcher produced a 40-feature comparison across
5 competitors (7-minute analysis).

Key finding: We lead in AI-native features (fork/resolve,
in-thread research, agent components) but have critical
gaps in mobile (no app -- all 5 competitors have one) and
integrations (3 vs average 45).

Recommended priority: Mobile app in Q3, calendar
integration in Q2.

[View full analysis with feature matrix]

--- Team reads the 3-sentence summary ---

CTO: "Mobile is a known gap. Calendar integration is
      easy -- I can have it in 2 weeks."

Designer: "I want to see the full feature matrix."
[Clicks "View full analysis" -- opens the fork in read mode]
[Reads through the detailed comparison at their own pace]

Designer: "The UX comparison section is interesting.
          I'll fork from there to analyze our design gaps."
[Designer forks from a specific message within the resolved fork]
```

**What this shows:**
- Long-running agent research (7 minutes) is contained in a fork
- Real-time progress updates keep the researcher informed without bothering the team
- The resolution summary condenses 7 minutes of work into 3 sentences
- Team members can choose their depth: headline (notification), summary (main thread), or full output (open the fork)
- A resolved fork can still be opened and even forked from for further exploration

### Scenario D: Rapid Back-and-Forth Between Human and Agent, Others Watching

```
#engineering channel, Thread: "Production Database Migration"

DBA: "We need to migrate the users table from INT to UUID primary
      keys. @DB-Agent let's work through this."

[DBA forks: "UUID Migration Planning"]

--- Fork: UUID Migration Planning ---
--- Sidebar shows: DBA + @DB-Agent, rapid activity ---

DBA: "What's our current row count and index status for users?"
@DB-Agent: "47M rows. 12 indexes. 3 foreign key references
            from orders, sessions, preferences."

DBA: "Generate the migration plan with zero downtime."
@DB-Agent: "Zero-downtime plan:
            1. Add uuid column (nullable)
            2. Backfill with gen_random_uuid()
            3. Create parallel indexes on uuid
            4. Dual-write phase (app writes both)
            5. Switch FK references
            6. Drop old INT column
            Estimated time: 4-6 hours for 47M rows."

DBA: "What about the backfill performance? Can we batch it?"
@DB-Agent: "Yes. Batch of 10K rows per transaction.
            47M / 10K = 4,700 batches.
            At ~50ms per batch = ~4 minutes total.
            Negligible impact on production reads."

DBA: "Good. Generate the SQL scripts."
@DB-Agent: [produces 6 SQL scripts with rollback procedures]

DBA: "One more thing -- what happens if the dual-write
      phase fails halfway?"
@DB-Agent: [explains recovery procedure]

[This exchange: 12 messages in 4 minutes]

--- Meanwhile, in the sidebar ---

CTO sees: "UUID Migration Planning - DBA + @DB-Agent
           (12 msgs, 4 min, active)"

CTO: [Clicks to peek at the fork -- reads in real-time
      without participating]
CTO: [Satisfied, goes back to main thread]

--- DBA finishes ---

DBA: [Resolves fork]

--- Back in main thread ---

[Fork resolved: UUID Migration Planning]
DBA worked out a zero-downtime UUID migration plan with @DB-Agent.
6-step process: add column, backfill (4 min for 47M rows), parallel
indexes, dual-write, switch FKs, drop old column. Total: 4-6 hours.
SQL scripts and rollback procedures generated.

[View full plan with SQL scripts (12 messages)]

CTO: "Reviewed. Looks solid. Schedule for this weekend."
```

**What this shows:**
- Rapid back-and-forth is contained in a fork, not polluting the main thread
- The CTO can "peek" at the fork in real-time without interrupting
- 12 messages of technical detail become a 3-sentence summary
- The full SQL scripts are preserved and accessible
- The team acts on the summary without needing to read the technical details

---

## Part 5: Notification Model

### Design Principles

1. **Minimize noise by default.** The whole point of forks is to REDUCE the noise that makes Slack painful. If forks generate more notifications, the product fails.
2. **Conclusions notify. Process does not.** When someone is researching in a fork, that generates zero notifications to non-participants. When the fork resolves, the summary notifies relevant people.
3. **The user controls their level of awareness.** Some people want to know everything. Some want just decisions. Both should be served.

### Notification Rules

| Event | Who Gets Notified | Notification Content |
|-------|-------------------|---------------------|
| New message in main thread | All thread participants | Full message preview |
| New message in a fork | Only fork participants | Full message preview |
| Fork created | Thread participants (if they opted in to fork activity) | "Charles started researching [topic]" |
| Fork resolved | All thread participants | Resolution headline + summary |
| @mention in fork | The mentioned person | "Charles mentioned you in fork: [topic]" |
| Agent completed research | Fork creator only | "Research complete. Review and resolve?" |
| Agent suggested a fork | Thread creator + last 3 active participants | Suggestion text + [Fork] [Dismiss] |

### Notification Tiers (User-Configurable)

```
Level 1: Conclusions Only (default for most users)
  - Fork resolutions (summaries) in threads they participate in
  - Direct @mentions
  - Nothing else

Level 2: Conclusions + Fork Activity (for active participants)
  - Everything in Level 1
  - "New fork created" in threads they participate in
  - Agent completion notifications for forks they're watching

Level 3: Everything (for thread owners / managers)
  - Everything in Level 2
  - Messages in all forks of threads they own
  - Agent intermediate progress updates
```

**Default:** Level 1. Users must explicitly opt into higher levels. This is the opposite of Slack's default (notify everything, user must mute).

### Fork Resolution Notification Flow

```
1. Fork resolves
   |
   v
2. AI generates summary
   |
   v
3. Fork creator reviews/edits summary
   |
   v
4. Summary posted to parent thread
   |
   v
5. Notification sent to all parent thread participants:
   "[Person] resolved [fork name]: [headline]"
   |
   v
6. Thread participants see the summary in their normal thread view
   |
   v
7. Participants can:
   - Read the summary (10 seconds)
   - Click to see full research (optional)
   - React or reply to the summary
   - Fork from the summary for further exploration
```

### Who Sees What, When

```
During research (fork active):
  Fork participants: See all messages in real-time
  Thread participants: See sidebar entry "Fork: [name] (active)"
  Others: See nothing (unless @mentioned)

After resolution:
  Thread participants: See summary in thread + notification
  Channel members: See summary in thread feed (if they visit the thread)
  Others: See nothing (unless searching)
```

---

## Part 6: Recommendation

### Recommended UX Approach: "Focus + Fork + Progressive Disclosure"

The recommended thread UX is built on three interlocking patterns:

**1. Focus Mode (one context at a time)**
The primary view always shows one context: either the main thread or a single fork. There is no interleaved view. The user explicitly switches between contexts via the fork sidebar. This prevents cognitive overload from concurrent explorations.

**2. Fork/Resolve (contained research loops)**
Research and exploration happen in forks, not in the main thread. Forks are first-class objects with lifecycle management (active -> resolved/abandoned). The resolution summary is the only artifact that enters the main thread. This keeps the main thread clean and decision-oriented.

**3. Progressive Disclosure (layered information density)**
Every agent output has three layers: headline (1 line), summary (3-5 bullets), and full output (on-demand). The default view matches the viewer's relationship to the content: researchers see summaries, non-participants see headlines.

### MVP Scope (Phase 3, Weeks 1-6)

**Must build:**

1. **Main thread view** -- Linear message list with markdown rendering, author distinction (human/agent), reactions, reply.

2. **Fork creation** -- One-click "Fork" action on any message. Auto-generated description. Optional manual description. Creates a new conversation context anchored to the source message.

3. **Fork sidebar** -- Compact panel showing all forks for the current thread. Each entry shows: fork name, participants, message count, time since last activity, one-line AI status. Click to switch focus to that fork.

4. **Fork view** -- Same layout as main thread but with: breadcrumb showing "Main Thread > Fork: [name]", back button to return to main, "Resolve" button.

5. **Resolution flow** -- Click "Resolve" -> AI generates summary (headline + 3-5 points) -> User edits if needed -> Posts to parent thread -> Fork marked as resolved.

6. **Progressive disclosure on agent responses** -- Agent messages render with expandable sections: summary visible by default, full output collapsed. "Show more / Show less" toggle.

7. **Fork-aware notifications** -- Resolution summaries notify thread participants. Fork-internal messages notify only fork participants. Default to Level 1 (conclusions only).

**Should build (Weeks 5-8):**

8. **"Agent is thinking" indicator** -- Real-time status: "Researching... (3 sources checked)" instead of generic spinner. Uses streaming to show agent progress.

9. **Peek mode** -- Click a fork in the sidebar to see a read-only preview without switching focus. Useful for the "CTO checks on the DBA's work" scenario.

10. **Resolution edit history** -- Track edits to resolution summaries. The AI-generated version is preserved alongside the human-edited version.

11. **Fork from resolved fork** -- A resolved fork can be opened and a new fork created from any message within it. Supports "going deeper" on a completed research stream.

**Defer to Phase 2+:**

12. **Ambient agent suggestions** ("This thread is diverging, suggest forking")
13. **Personal Agent DM integration** (private research -> share to thread)
14. **Cross-fork comparison** (side-by-side view of two fork resolutions)
15. **Fork templates** ("Research", "Decision Analysis", "Code Review")
16. **Thread-level AI summary** (condensed view of entire thread + all resolutions)
17. **Mobile layout** for forks
18. **Agent-to-agent delegation** within forks

### Wireframe-Level Descriptions

#### Main Thread View
```
+---------------------------------------------------------------+
| #engineering > Rate Limiting Strategy         [Search] [Bell]  |
+-------------------------------------------+-------------------+
|                                           |  FORKS (2)        |
|  Thread Messages                          |                   |
|  ======================================   |  > Rate Limit     |
|                                           |    Research        |
|  [avatar] Dev                    2:30 PM  |    Charles +      |
|  We need to implement rate limiting       |    @Researcher     |
|  for the public API. What approach        |    8 msgs, 5m ago |
|  should we take?                          |    [Active]        |
|                  [React] [Reply] [Fork]   |                   |
|                                           |  > Performance    |
|  [avatar] Charles                2:32 PM  |    Benchmarks      |
|  Let me research this.                    |    DBA +           |
|                                           |    @DB-Agent       |
|  [Fork resolved: Rate Limiting Research]  |    3 msgs, 1m ago |
|  Charles researched rate limiting         |    [Active]        |
|  strategies with @Researcher.             |                   |
|                                           +-------------------+
|  Conclusion: Use Cloudflare's native      |                   |
|  Rate Limiting (Token Bucket). Handles    |  RESOLVED (1)     |
|  our 1000 req/s scale. No code changes.   |                   |
|                                           |  > Rate Limit     |
|  [View full research (8 msgs)]            |    Research        |
|                                           |    [Resolved]      |
|  [avatar] Dev                    2:45 PM  |                   |
|  Makes sense. I'll set up the Cloudflare  |                   |
|  rules this sprint.                       |                   |
|                                           |                   |
|  ======================================   |                   |
|  [Message input...          @] [Send]     |                   |
+-------------------------------------------+-------------------+
```

#### Fork View
```
+---------------------------------------------------------------+
| < Back to thread    Fork: Rate Limiting Research    [Resolve]  |
+-------------------------------------------+-------------------+
|                                           |  FORK INFO        |
|  Fork Messages                            |                   |
|  ======================================   |  Created by:      |
|                                           |  Charles           |
|  [Forked from Dev's message:]             |  From: Dev's msg   |
|  "We need to implement rate limiting..."  |  Status: Active    |
|                                           |  Messages: 8       |
|  [avatar] Charles                2:32 PM  |  Duration: 5 min  |
|  @Researcher analyze rate limiting        |                   |
|  strategies for REST APIs. Consider       |  Participants:     |
|  our scale (1000 req/s peak) and that     |  Charles            |
|  we use Cloudflare.                       |  @Researcher        |
|                                           |                   |
|  [robot] @Researcher             2:33 PM  |                   |
|  Rate Limiting Strategy Analysis          |                   |
|                                           |                   |
|  Three viable approaches:                 |                   |
|  1. Token Bucket (Cloudflare native)      |                   |
|     -- simplest, built into your infra    |                   |
|  2. Sliding Window (Redis)                |                   |
|     -- most accurate, needs Redis         |                   |
|  3. Adaptive (AI-driven)                  |                   |
|     -- adjusts limits, complex            |                   |
|                                           |                   |
|  Recommendation: Token Bucket via         |                   |
|  Cloudflare's Rate Limiting.              |                   |
|                                           |                   |
|  [v Show full comparison table]           |                   |
|  [v Show implementation guide]            |                   |
|                                           |                   |
|  ======================================   |                   |
|  [Message input...          @] [Send]     |                   |
+-------------------------------------------+-------------------+
```

#### Resolution Flow
```
+---------------------------------------------------------------+
| Resolve Fork: Rate Limiting Research                   [X]     |
+---------------------------------------------------------------+
|                                                               |
|  AI-generated summary:                                        |
|  (edit before posting to thread)                              |
|                                                               |
|  +-----------------------------------------------------------+
|  | Headline:                                                  |
|  | [Use Cloudflare Token Bucket for rate limiting       ]     |
|  |                                                            |
|  | Summary:                                                   |
|  | [- Token Bucket via Cloudflare is simplest approach   ]    |
|  | [- Handles 1000 req/s, ~$0.05/10K requests            ]    |
|  | [- No code changes needed -- Cloudflare config only   ]    |
|  | [- Sliding Window (Redis) rejected: unnecessary       ]    |
|  | [  accuracy for our use case                          ]    |
|  +-----------------------------------------------------------+
|                                                               |
|  This summary will be posted to the main thread.              |
|  The fork will be marked as resolved and archived.            |
|                                                               |
|         [Cancel]              [Post to Thread]                |
+---------------------------------------------------------------+
```

### Why This Approach Wins

1. **Solves the founder's actual problem.** The "copy to AI, research, paste back" loop becomes "fork, research, resolve." Same workflow, zero copy-paste, full context preservation.

2. **Solves information overload.** Progressive disclosure means non-researchers see a 3-sentence summary. Researchers see the full output. Both are served by the same system.

3. **Scales to many concurrent explorations.** Focus mode + sidebar means the user is never overwhelmed by multiple forks. The sidebar is a status board, not a content feed.

4. **Differentiates from Slack.** Slack cannot add forks without redesigning its thread model. This is a structural advantage, not a feature that can be bolted on.

5. **Preserves R1's core insight.** Fork/Resolve is retained but the UX is refined: focus mode replaces tab switching, progressive disclosure replaces raw AI output, notification tiers replace blanket alerts.

6. **Keeps the main thread as the "source of truth."** Decisions and conclusions live in the main thread. Research and exploration live in forks. The main thread reads like a clean decision log, not a noisy chat history.

---

## Open Questions

1. **Fork naming UX.** Auto-generated names (from the forked message content) vs. user-provided names vs. both? Auto-generation reduces friction but may produce unhelpful names. Recommendation: auto-generate with option to rename.

2. **"Watching" a fork.** Can a non-participant "watch" a fork to get real-time notifications without posting? Useful for managers monitoring without interrupting. Recommendation: yes, add a "Watch" button on fork sidebar entries. Deferred to Phase 2.

3. **Fork archival and retrieval.** How long do resolved forks remain accessible? Recommendation: forever, but they move from "Active" to "Resolved" section in sidebar, and eventually only findable via search.

4. **Resolution summary format.** Structured (headline + bullets + recommendation) vs. freeform paragraph? Recommendation: structured by default (prompts the AI to organize), with freeform override.

5. **Fork ownership and permissions.** Can anyone resolve a fork, or only the creator? Recommendation: creator + thread owner can resolve. Others can suggest resolution. MVP: creator only.

6. **Agent response streaming in forks.** Should agent responses stream token-by-token (like ChatGPT) or appear as complete messages? Recommendation: stream for long responses (>5 seconds), complete for short ones. This gives real-time feedback during research.

7. **Cross-thread fork search.** When searching, should fork content be included in results? Recommendation: yes, with a filter to include/exclude fork content. Fork messages are tagged with their fork context in search results.

8. **Maximum fork message count.** Should there be a limit on how many messages a fork can have before suggesting resolution? Recommendation: soft limit at 30 messages ("This fork is getting long. Consider resolving or splitting."). No hard limit.

9. **Fork from resolved fork.** R1 says allow one level of nesting max. But Scenario C shows "Designer forks from within a resolved fork." How does this work? Recommendation: forking from a resolved fork creates a new top-level fork with the relevant context loaded. It is NOT a nested fork -- it's a new fork with a reference to the source.

10. **Personal Agent context bridge.** If a user researches privately with their Personal Agent and wants to share the result to a thread, how does the context transfer? Recommendation: "Share to thread" button in Personal Agent DM that posts a formatted summary. The DM content itself stays private.

---

## Rejected Approaches

### Full Git Visualization (Branch Graph)
**Rejected because:** R1 already rejected this. Phase 1.5 confirms: the problem is information management, not version visualization. A git graph adds visual complexity without solving the density problem.

**Reconsider if:** The Vibe team explicitly requests a way to "see the shape of the discussion." Then build a simplified visualization (not a full git graph) as an optional toggle.

### Canvas/Spatial Layout as Primary View
**Rejected because:** Breaks the timeline mental model, impossible on mobile, doesn't solve information density, adds massive cognitive load. Research from Artium AI confirms that "conversation as orchestration" (structured responses) is the emerging pattern, not "conversation as spatial map."

**Reconsider if:** A future use case (brainstorming, design critique) specifically benefits from spatial arrangement. Then add as a specialized thread type, not the default.

### Tab-Based Fork Navigation
**Rejected because:** Tabs don't scale past 5-7 items and provide no status information about inactive tabs. The sidebar with status lines is strictly superior: it shows what's happening in each fork at a glance without requiring the user to click through tabs.

**Reconsider if:** User testing reveals that sidebar-based navigation is too "hidden" and users want more prominent fork presence. In that case, consider a hybrid: 3 most recent forks as tabs, rest in sidebar overflow.

### No Fork Depth Limit
**Rejected because:** Unlimited fork depth recreates the Reddit nesting problem that Discourse spent 15 years fighting against. Each level of depth makes content harder to find and reduces the likelihood of resolution.

**Reconsider if:** A specific workflow (legal case analysis with multiple sub-issues) genuinely requires nested exploration. Then allow fork depth of 2 for that thread type only.

### Agent-Initiated Auto-Forking
**Rejected for MVP because:** Agents creating forks without explicit human request would create noise and confusion. The team would not trust auto-created forks. The agent should SUGGEST forks, not CREATE them.

**Reconsider if:** After 4+ weeks of dogfood, the team explicitly says "I wish the agent would just fork automatically when it detects diverging topics."

### Real-Time Cross-Fork Awareness (Split Screen)
**Rejected because:** Showing two forks side by side adds complexity and doesn't serve the primary use case (one person researching in one fork at a time). The sidebar provides sufficient awareness of other forks.

**Reconsider if:** The "two people researching different angles" scenario (Scenario B) happens frequently and users explicitly want to compare results before resolution.

---

*Research completed: 2026-02-07*
*Researcher: thread-ux-designer (Phase 1.5)*
*Dependencies: Builds on R1 (Thread Model), R2 (Generative UI), R3 (Agent Lifecycle). Feeds directly into Phase 2 MVP design spec.*
