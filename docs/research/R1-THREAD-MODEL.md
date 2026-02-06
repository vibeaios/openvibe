# R1: Thread Interaction Model Research

> Git-like Thread semantics for Human + Multi-Agent collaboration

---

## Research Question

What does "Git-like threads" mean concretely for a collaboration product? Specifically:
1. What does "branch" mean in a conversation? When would a user branch?
2. What does "merge" mean? How do you merge two conversation branches?
3. What is a "conflict" in conversation context? Does it even make sense?
4. How do AI agents participate in branches? Can they create branches?
5. What's the minimum Git-like interaction that's useful without being confusing?
6. How would the Vibe team migrate from Slack? What Slack workflows map to threads?
7. What are 2-3 concrete interaction prototypes?
8. What's the minimum dogfood MVP scope for thread interaction?

---

## Sources Consulted

### Existing Design Docs
- `docs/design/M1-THREAD-ENGINE.md` -- Current data model and API design (branch/merge/switch/diff)
- `docs/design/M2-FRONTEND.md` -- UI layout, branch tabs, merge flow mockups
- `docs/architecture/DESIGN-SPEC.md` -- Thread Engine section (5.1-5.3), merge strategies
- `docs/design/GAP-ANALYSIS.md` -- Identifies thread model as highest risk (R1)
- `docs/INTENT.md` -- Dogfood context, forum-like interaction model, ~500ms latency

### External Research: Git-like Conversation Tools
- **GitChat** (github.com/DrustZ/GitChat) -- Treats messages as nodes in a flowchart, supports branch/merge/rewire for LLM interactions. Single-user LLM tool, not multi-user collaboration.
- **Forky** (github.com/ishandhanani/forky) -- DAG-based conversation management with git-style fork/merge for LLM chats. Uses LLM-generated summaries for merge (squash-merge analog). Conflict detection mentioned but not detailed.
- **Threds.dev** -- "Versioned reasoning tree with explicit branch/merge semantics" for LLM research. Designed for researchers doing deep dives with side-quest branches. HN discussion (item 46876469).
- **Git Context Controller (GCC)** -- Academic paper (arxiv 2508.00031) integrating COMMIT/BRANCH/MERGE into LLM agent reasoning loops. Framework for agents to checkpoint and explore alternate strategies.

### External Research: ChatGPT Branching
- ChatGPT's native branching feature (launched September 2025): Fork at any message, creates independent conversation. No merge capability. No tree view. No multi-user. Primarily for A/B testing prompts.
- Claude Code feature request (anthropics/claude-code #10370, #16236): Requests for conversation branching with selective merging back to main.

### External Research: Forum/Discussion Models
- **Discourse** -- Deliberately flat threading. Jeff Atwood and Joel Spolsky argue branching "doesn't correspond to the way conversations take place in the real world" and creates "disjointed, distracting" experiences. 22,000+ communities validate flat model. Chat threads added later as lightweight feature.
- **Reddit** -- Tree-structured reply model. Branching is natural but reading deeply nested threads is poor UX. Collapse/expand pattern is noisy.
- **Discord Forum Channels** -- Posts expand into threads. Flat within each thread. Tags for filtering. No nesting within threads. Designed for "organized chaos."
- **GitHub Discussions** -- Q&A-oriented threading. One level of nesting (replies to comments). Criticized as "modeled poorly for open-ended conversations." Works for structured Q&A, fails for free-form discussion.
- **Linear** -- Threaded comments on issues. Flat within each issue. AI-generated discussion summaries (19+ comments). Focus on structured work, not free-form conversation.

### External Research: Slack/Bot Agent Interactions
- Slack's Slackbot evolved into AI agent (GA January 2026). Agents participate via @mention in channels, DMs, threads. Slack data enriches agent context.
- Kilo -- AI Slack bot that turns threads into code changes and GitHub PRs.
- Slack pain points driving migration: noise, cost, complexity, "maze of twisty little passages," deep work impossible.

---

## Options Explored

### Option A: Full Git Semantics (Literal Translation)

**Description:** Map every Git operation directly to conversation: commit = reply, branch = branch, checkout = switch, merge = merge, diff = diff, log = history. Users explicitly manage branches like a Git repository.

**Pros:**
- Maximum differentiation from competitors
- Familiar mental model for developers
- Powerful for complex, multi-path discussions
- Complete audit trail of exploration

**Cons:**
- Git UX is notoriously bad -- even developers struggle with it
- Non-technical users (doctors, lawyers, construction workers) will not adopt
- "Merge conflict" in conversation is philosophically undefined
- Overhead: creating a branch for every tangent is friction
- No existing product has succeeded with this approach at scale
- ChatGPT's branching is simpler and already struggles with tree-view navigation

**Why rejected:** The gap between "this is conceptually elegant" and "users will actually use this" is massive. Every existing attempt (GitChat, Forky, Threds.dev) is a single-user developer tool, not a team collaboration product. Discourse explicitly rejected threading after years of experience. This is the biggest risk the GAP-ANALYSIS identified, and the risk is real.

---

### Option B: Lightweight Branching (Fork + Summarize)

**Description:** Simplified Git metaphor. Only three operations: Fork (create a side conversation from any message), Continue (the default linear thread), and Summarize (AI distills a fork into a summary that gets appended to the main thread). No explicit "merge" or "conflict resolution."

**Pros:**
- Much simpler mental model: "I want to explore this tangent without cluttering the main thread"
- Summarize replaces merge -- AI does the hard work
- Maps to real behavior: Slack threads are already informal forks
- Non-technical users can understand "fork" as "sidebar conversation"
- Keeps main thread clean and readable
- Forky's squash-merge approach validates this pattern

**Cons:**
- Less powerful than full Git semantics
- AI summarization quality is critical -- bad summaries poison the main thread
- "Fork" might still confuse non-technical users
- No diff view (comparing branches side by side)
- Loses the "Git-like" marketing differentiation somewhat

**Why adopted (with modifications):** This is the pragmatic sweet spot. It preserves the core value proposition ("explore without losing context") while removing the parts users would never use (explicit merging, conflict resolution, checkout). The key insight from Forky is that LLM-generated summaries are a viable merge strategy. The key insight from Discourse is that threading complexity kills communities. This option threads the needle.

---

### Option C: Smart Threads (Enhanced Slack Model)

**Description:** Start with Slack-like threads but add intelligence: AI-generated summaries, automatic tagging of decisions/action items, thread lifecycle management (open/resolved/archived). No branching at all.

**Pros:**
- Easiest migration from Slack -- same mental model
- Proven UX pattern used by billions
- Low learning curve for any industry
- Focus on AI augmentation rather than new interaction paradigm

**Cons:**
- Not differentiated -- this is Slack with AI stapled on
- Doesn't address the "explore different directions" use case
- Slack AI already does some of this (discussion summaries)
- No competitive moat -- any chat tool can add AI summaries
- Doesn't justify building a new product

**Why rejected:** If this is all OpenVibe offers, there's no reason to switch from Slack. The whole point of the product is a new interaction model. This option solves the "is it useful?" question but fails the "is it differentiated?" question.

---

### Option D: Decision Tree Threads

**Description:** Threads are structured as decision trees. Each message is either a statement, a question, or a decision. Branching happens automatically at decision points. AI agents propose options, humans choose, and the thread records the decision graph.

**Pros:**
- Highly structured -- good for regulated industries (medical, legal)
- AI can proactively suggest decision points
- Clear audit trail of decisions
- Maps well to workflow/process scenarios

**Cons:**
- Too rigid for free-form discussion
- Not all conversations are decision-oriented
- Requires users to categorize every message
- Feels like a form, not a conversation
- High friction for casual communication

**Why rejected:** This works for specific workflow scenarios (patient check-in, case intake) but fails as a general communication tool. Could be a specialized thread type within the broader system, but not the default interaction model.

---

## Recommendation

### Recommended Approach: Option B + Elements of C and D

**"Forkable Threads with AI-Powered Resolution"**

The interaction model has three tiers, progressively adopted:

#### Tier 1: Smart Threads (Day 1 -- Slack Replacement)
- Linear, flat threads within channels (Discourse-style)
- AI-generated summaries when threads get long (Linear's approach: auto-summary at ~19 messages)
- Decision/action item extraction
- @mention agents to invoke them
- Thread status: active / resolved / archived

This alone justifies migration from Slack because the AI augmentation is built-in, not an add-on.

#### Tier 2: Forkable Threads (Week 2+ -- Core Differentiator)
- Any message can be forked into a side thread
- Fork is a lightweight operation: one click, optional name
- Forks are visible as "branches" in a compact sidebar (not tabs -- tabs don't scale)
- AI can auto-suggest: "This discussion is diverging. Fork into separate threads?"
- **Resolution** (not "merge"): When a fork reaches a conclusion, the user clicks "Resolve" and the AI generates a summary that gets posted to the parent thread. The fork is archived but still accessible.
- No explicit merge, no conflict resolution, no diff view in MVP

#### Tier 3: Structured Threads (Month 2+ -- Vertical Value)
- Thread types from config (patient-encounter, case-thread, rfi-thread)
- Phase-based progression (check-in -> exam -> checkout)
- Auto-assigned agents per thread type
- Decision capture and audit trail

#### Complete Reasoning Chain

1. **The Discourse lesson is paramount.** Years of data show that deep threading kills engagement. Flat + occasional branching is the right default.

2. **"Resolution" instead of "merge" is the key semantic reframe.** In Git, merge is mechanical -- combine two code trees. In conversation, merge is philosophical -- what does it mean to combine two discussions? The answer is: you don't combine them. You resolve the fork by summarizing the conclusion and bringing it back. This is what humans do naturally: "We discussed X on the side, and the conclusion was Y."

3. **AI agents are first-class fork participants.** An agent can be asked to "explore option A in this fork" while the human continues exploring option B in the main thread. This is the multi-agent differentiation -- the agent works in parallel, in a fork, and reports back with a summary.

4. **Forks, not branches.** "Branch" is developer jargon. "Fork" is more natural and already used by ChatGPT. A fork is a temporary exploration, not a permanent parallel track.

5. **Fork visibility matters.** Reddit's problem is that forks (replies) are hidden behind collapse/expand. Discord's problem is that threads are temporary and easy to lose. The fork sidebar should show all active forks with one-line summaries, making the exploration state visible without cluttering the main thread.

---

## Detailed Answers to Research Questions

### 1. What does "branch" mean in a conversation?

**Reframed: "Fork"** -- A fork is a temporary side conversation that starts from a specific message in the main thread. It preserves the context up to that point and allows independent exploration. Forks are expected to be resolved (summarized back to main) or abandoned (archived), not maintained indefinitely.

**When would a user fork?**
- Exploring a tangent without derailing the main discussion
- Asking an AI agent to research something in parallel
- Having a sub-discussion with a subset of participants
- Testing alternative approaches before committing to one
- Breaking a large discussion into manageable pieces

### 2. What does "merge" mean?

**Reframed: "Resolve"** -- There is no merge in the Git sense. When a fork reaches its conclusion, the user (or AI) creates a resolution summary that gets posted to the parent thread. The fork is then marked as resolved and archived (still accessible for reference).

**Resolution strategies:**
- **AI Summary** (default): AI reads the fork and generates a 2-3 sentence summary of the conclusion, posted to the parent thread with a link to the full fork
- **Manual Summary**: User writes their own summary
- **Abandon**: Fork is archived without summary (dead end exploration)
- **Promote**: Fork becomes its own thread (discussion outgrew the parent)

### 3. What is a "conflict" in conversation context?

**Answer: It doesn't meaningfully exist, and that's fine.**

In code, a conflict is two people editing the same line. In conversation, two people can say contradictory things in different forks, but that's not a "conflict" -- it's a discussion. The resolution summary is where contradictions get reconciled by a human or AI.

The closest analog to a conflict is when two forks reach different conclusions about the same question. The resolution for this is a new message in the parent thread that acknowledges both conclusions and makes a decision. This is a human judgment, not a mechanical merge.

**Deliberately not implementing conflict detection avoids the biggest UX trap** -- trying to force a code-oriented concept onto human communication.

### 4. How do AI agents participate in branches?

**Agents are natural fork participants.** Key patterns:

- **Agent-initiated fork**: Agent detects the discussion is exploring multiple directions and suggests forking. "I see you're discussing both pricing and packaging. Want me to fork the packaging discussion?"
- **Agent-as-researcher**: User forks and @mentions an agent: "Research the pros and cons of option A in this fork." Agent works asynchronously, posts findings, and suggests resolution.
- **Agent-per-fork**: In multi-agent scenarios, different agents can be assigned to different forks. "Agent-1, explore option A. Agent-2, explore option B." Both report back with resolution summaries.
- **Agent resolution**: Agent can auto-generate the resolution summary when the fork creator marks it as complete.

**Can agents create forks?** Yes, but with guardrails:
- Agents can suggest forks (human confirms)
- Agents can create forks when explicitly asked ("Go explore this")
- Agents should NOT auto-fork without being asked -- this would create noise
- When an agent creates a fork, it's clearly labeled as agent-initiated

### 5. What's the minimum Git-like interaction that's useful without being confusing?

**The minimum viable thread model:**
1. **Linear thread** (reply in order -- the "main" branch)
2. **Fork from any message** (one-click operation)
3. **View forks** (sidebar showing active forks with one-line descriptions)
4. **Switch between main and forks** (click to view)
5. **Resolve fork** (AI summary posted to parent, fork archived)

**Explicitly NOT in minimum:**
- Branch visualization (git graph)
- Diff view (comparing forks side by side)
- Explicit merge with conflict resolution
- Branch naming conventions
- Cherry-pick (selecting specific messages from a fork)
- Rebase (rewriting fork history)

### 6. How would the Vibe team migrate from Slack?

**Slack-to-OpenVibe Migration Map:**

| Slack Concept | OpenVibe Concept | Notes |
|---------------|------------------|-------|
| Channel | Channel | 1:1 mapping |
| Message | Message | 1:1 mapping |
| Thread (reply) | Thread | Same concept, but smarter |
| Thread (tangent) | Fork | This is the upgrade |
| @mention bot | @mention agent | Same UX, more powerful |
| Emoji reactions | Reactions | Keep it |
| Slack Connect | n/a | Not needed for dogfood |
| Huddle | n/a | Not in MVP |
| Canvas | n/a | Not in MVP |

**Migration path for Vibe team:**

1. **Week 1: Channels + Threads** -- Set up same channel structure as Slack (#general, #engineering, #product, #random). Post and reply works identically to Slack. AI summaries are the immediate upgrade.

2. **Week 2: Agent Integration** -- @mention AI agents in threads. Replace the pattern of "ask in Slack, someone finds the answer" with "ask in thread, agent finds the answer."

3. **Week 3: Forks** -- Start using forks for design discussions, brainstorming, and decision-making. "Let's fork this and have Agent-1 research option A while we discuss option B."

4. **Ongoing: Organic adoption** -- Team naturally discovers when forks are useful vs. when linear threads suffice.

**Key Slack pain points addressed:**
- "Thread spaghetti" (too many threads, hard to track) -> Fork sidebar shows all active forks with status
- "Lost decisions" (decisions buried in threads) -> AI extracts decisions and action items
- "Bot noise" (bots posting in channels) -> Agents work in forks, post resolution summaries
- "Context switching" (leave Slack to use other tools) -> Agents can do research within the thread

### 7. Concrete Interaction Prototypes

#### Prototype A: The Design Discussion

```
#product channel

Charles: "We need to finalize the pricing model. @Agent-Researcher
          can you pull competitive pricing data?"

Agent-Researcher: "Here's what I found: [competitive analysis]
                   Three main models in our space: per-seat, per-usage,
                   tiered. Want me to analyze each in detail?"

Charles: "Let's explore per-seat and tiered in parallel."
         [Clicks "Fork" on Agent-Researcher's message]

  Fork 1: "Explore Per-Seat Pricing"
  ├── Charles: "@Agent-Researcher analyze per-seat for our use case"
  ├── Agent-Researcher: "Per-seat analysis: [detailed breakdown]"
  ├── Allie: "Per-seat is simpler but penalizes growth"
  └── [Resolve] -> Summary: "Per-seat is simpler to communicate
      but creates negative incentive against adding users.
      Best for stable teams. Risk: churn when teams grow."

  Fork 2: "Explore Tiered Pricing"
  ├── Charles: "@Agent-Researcher analyze tiered for our use case"
  ├── Agent-Researcher: "Tiered analysis: [detailed breakdown]"
  ├── Dev: "Tiered aligns incentives better with usage"
  └── [Resolve] -> Summary: "Tiered pricing aligns revenue with
      value delivered. More complex to communicate but better
      long-term alignment. Recommended tiers: Free/Pro/Enterprise."

[Back in main thread:]
Charles: "Based on both analyses, let's go with tiered.
          @Agent-Writer draft the pricing page."
```

#### Prototype B: The Engineering Investigation

```
#engineering channel

Dev: "Production latency spiked 3x in the last hour.
      @Agent-Ops what's going on?"

Agent-Ops: "Investigating. Initial findings:
            - Database CPU at 92%
            - 3 slow queries identified
            - No deployment in last 6 hours"

Dev: "Let's investigate the slow queries and check if
      it's a data issue separately."
     [Forks from Agent-Ops message]

  Fork 1: "Slow Query Investigation"
  ├── Agent-Ops: "Query analysis: [3 queries with execution plans]"
  ├── Dev: "Query #2 is missing an index on user_sessions"
  ├── Agent-Ops: "Confirmed. Adding index would reduce from
  │               4.2s to 0.03s. Want me to draft the migration?"
  └── [Resolve] -> Summary: "Root cause: missing index on
      user_sessions.created_at. Migration drafted,
      ready for review."

  Fork 2: "Data Volume Check"
  ├── Agent-Ops: "Data growth analysis: user_sessions table
  │               grew 340% in last week due to bot traffic"
  ├── Dev: "We need rate limiting on the session endpoint"
  └── [Resolve] -> Summary: "Contributing factor: 340% data
      growth from bot traffic. Need rate limiting on
      POST /sessions."

[Main thread continues:]
Dev: "Two issues found. Index fix is urgent, rate limiting
      goes to sprint backlog."
```

#### Prototype C: The AI-Assisted Decision Meeting

```
#leadership channel

Charles: "Q2 OKR planning. Three candidate objectives:
          1. Ship v2 of core product
          2. Expand to 3 new verticals
          3. Reduce churn by 50%

          @Agent-Strategy evaluate each against our current position."

Agent-Strategy: "Analysis of all three: [overview]
                 Recommending we fork into separate evaluations
                 for depth."

Charles: "Good idea. Fork all three."

  Fork 1: "OKR: Ship v2"
  ├── Agent-Strategy: [detailed feasibility analysis]
  ├── CTO: "Engineering capacity supports this if we
  │          descope features X and Y"
  └── [Resolve] -> Summary: "Feasible if descoped.
      Estimated 10 weeks. High impact on retention."

  Fork 2: "OKR: 3 New Verticals"
  ├── Agent-Strategy: [market analysis per vertical]
  ├── Sales Lead: "Legal vertical has warmest pipeline"
  └── [Resolve] -> Summary: "Recommend 1 vertical (legal)
      not 3. Three is spread too thin given team size."

  Fork 3: "OKR: Reduce Churn 50%"
  ├── Agent-Strategy: [churn analysis with root causes]
  ├── CS Lead: "Top churn reason is onboarding friction"
  └── [Resolve] -> Summary: "50% reduction achievable by
      fixing onboarding (40% of churn) + adding
      health scoring alerts."

[Main thread:]
Charles: "Decision: Q2 OKRs are:
          1. Ship v2 (descoped)
          2. Legal vertical only
          3. Fix onboarding + health scoring

          @Agent-Writer create the OKR doc from these resolutions."
```

### 8. Minimum Dogfood MVP Scope

**MVP = Tier 1 + Tier 2 (no Tier 3 structured threads)**

#### Must Have (Week 1-4)
- [ ] Channels (create, join, list)
- [ ] Linear threads within channels (create, reply, list)
- [ ] Real-time message updates (Supabase Realtime, ~500ms is fine)
- [ ] @mention agents (route message to agent, agent replies in thread)
- [ ] Fork from any message (one-click, auto-named)
- [ ] View fork sidebar (list of active forks with descriptions)
- [ ] Switch between main thread and forks
- [ ] Resolve fork (AI-generated summary posted to parent)
- [ ] Thread status (active / resolved)
- [ ] Basic markdown rendering
- [ ] Message author distinction (human vs agent, with different styling)

#### Should Have (Week 5-8)
- [ ] AI-generated thread summaries (auto at threshold or on-demand)
- [ ] Decision/action item extraction
- [ ] Agent-suggested forks ("This discussion is diverging...")
- [ ] Fork archive (resolved forks still viewable)
- [ ] Search across threads and forks
- [ ] Reactions/emoji
- [ ] File attachments (images, docs)

#### Not in MVP
- Branch visualization (git graph)
- Diff view
- Structured thread types (patient-encounter etc.)
- Thread templates
- Private forks
- Fork permissions (separate from thread permissions)
- Mobile UI
- Notifications (use email/Slack bridge initially)

---

## Data Model Implications

Based on the recommended approach, the data model from M1-THREAD-ENGINE.md needs these adjustments:

```
Current M1 model:           Recommended model:
- Thread                    - Thread (unchanged)
- Branch                    - Fork (replaces Branch)
  - name: string              - description: string (auto or manual)
  - headMessageId             - headMessageId (same)
  - baseMessageId             - parentMessageId (fork point)
  - createdBy                 - createdBy (same)
                              - status: active | resolved | abandoned
                              - resolution?: string (AI summary)
                              - resolvedAt?: timestamp
```

Key change: "Branch" becomes "Fork" with a lifecycle (active -> resolved/abandoned) and a resolution summary field. No merge semantics needed.

---

## Open Questions

1. **Fork depth**: Can you fork from a fork? Recommendation: allow one level of nesting max (fork from fork), but not deeper. Deep nesting recreates the Reddit/threading problem. Need to validate with dogfood.

2. **Fork visibility permissions**: Should forks be visible to everyone in the channel, or only to participants? For dogfood, keep it simple: all forks visible to all channel members. Revisit for enterprise/compliance verticals.

3. **AI summary quality**: The entire "resolve" flow depends on AI generating good summaries. What happens when summaries are bad? Need a feedback mechanism (thumbs up/down on resolution) and the ability to manually edit.

4. **Agent autonomy in forks**: How much should agents do unprompted in a fork? Should they continue researching until told to stop? Or only respond when addressed? Needs R3 (Agent Lifecycle) research to answer fully.

5. **Thread vs. Fork naming**: Is "fork" the right term for non-technical users? Alternatives: "side discussion," "tangent," "exploration," "branch" (familiar from ChatGPT). Need user testing.

6. **Notification model**: When someone posts in a fork, who gets notified? All thread participants? Only fork participants? This affects the signal-to-noise ratio that makes Slack painful.

7. **Fork limit**: M1 proposed max 10 branches per thread. For forks, recommendation: max 5 active forks per thread (resolved forks don't count). Too many active forks indicates the thread should be restructured into multiple threads.

---

## Rejected Approaches

### Full Git Semantics (Option A)
**Rejected because:** No evidence that general users can or want to manage conversation branches like Git repositories. Every existing implementation (GitChat, Forky, Threds.dev) is a developer-focused single-user tool. Discourse's 15+ years of data shows deep threading hurts engagement. The concept is intellectually appealing but practically unworkable for a team collaboration product targeting non-technical verticals.

**Reconsider if:** User research during dogfood reveals strong demand for diff views, explicit merges, or multi-level branching. If the Vibe team (all technical) consistently wants these features, consider them as power-user features with a simplified default mode.

### No Branching at All (Option C)
**Rejected because:** Insufficient differentiation from Slack. If OpenVibe is just "Slack + AI," there's no compelling reason to migrate. The fork model provides a unique value proposition that can't be replicated by adding an AI bot to Slack.

**Reconsider if:** Dogfood reveals the team never uses forks and the AI augmentation (summaries, agent integration) is the sole value driver. In that case, pivot to being "the AI-native team chat" rather than "Git-like threads."

### Decision Tree Threads (Option D)
**Rejected because:** Too rigid for general communication. Good for specific workflow scenarios but not as the default interaction model.

**Reconsider if:** Vertical customers (medical, legal) explicitly request structured decision flows. Then implement as a Thread Type (Tier 3) rather than the default model.

### Actual Git Backend (mentioned in M1 as Option B)
**Rejected because:** Over-engineering. Using actual Git to store conversations adds enormous complexity (Git server, repository management, access control via Git) for minimal benefit. Postgres with a fork table achieves the same semantics with much simpler operations. The GAP-ANALYSIS already flagged this.

**Reconsider if:** There's a genuine need for offline-first conversation storage, peer-to-peer sync, or integration with developer tools that natively speak Git.

---

*Research completed: 2026-02-07*
*Researcher: thread-interaction-designer*
*Dependencies: Feeds into R2 (Generative UI), informs R3 (Agent Lifecycle)*
