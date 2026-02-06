# Phase 1.5: BDD Implementation Plan

> Status: Complete | Researcher: implementation-planner | Date: 2026-02-07

---

## Research Question

How should the OpenVibe MVP be decomposed into testable behavior specifications (BDD/Gherkin) that enable incremental implementation, where each step produces a working (if incomplete) system? What is the critical path, sprint plan, and testing strategy for 1-2 developers building a dogfood-ready product in 8 weeks?

---

## Sources Consulted

### Internal Design Documents
- `docs/INTENT.md` -- Phase roadmap, dogfood context, 7 research questions
- `docs/research/SYNTHESIS.md` -- Phase 1 research synthesis, fork/resolve model, data model, tech stack
- `docs/research/phase-1.5/BACKEND-MINIMUM-SCOPE.md` -- Complete data model (10 tables), ~30 tRPC procedures, Supabase Realtime events, implementation estimates
- `docs/research/phase-1.5/THREAD-UX-PROPOSAL.md` -- Focus Mode + Fork Sidebar + Progressive Disclosure, interaction scenarios, notification model
- `docs/research/phase-1.5/RUNTIME-ARCHITECTURE.md` -- Per-user runtime, MVP simplification, cost model
- `docs/research/phase-1.5/FRONTEND-ARCHITECTURE.md` -- App structure, Zustand stores, component hierarchy, Realtime subscriptions
- `docs/research/phase-1.5/ADMIN-CONFIGURABLE-UI.md` -- Config schema, `useConfig()` hook, agent components

### External Research
- [BDD Testing with Next.js and Playwright](https://konabos.com/blog/bdd-testing-with-next-js-and-playwright-scalable-readable-reliable) -- Scalable BDD patterns for Next.js
- [Playwright-BDD documentation](https://vitalets.github.io/playwright-bdd/) -- Generates Playwright tests from Gherkin
- [Playwright + BDD with TypeScript (Dec 2025)](https://medium.com/@sreekanth.parikipandla/playwright-bdd-with-typescript-a-practical-guide-to-fast-readable-e2e-tests-6bd1dca6b3d1) -- Practical integration guide
- [Unit and E2E Tests with Vitest & Playwright](https://strapi.io/blog/nextjs-testing-guide-unit-and-e2e-tests-with-vitest-and-playwright) -- Next.js testing strategy
- [BDD for Agile Teams (Scrum Alliance)](https://resources.scrumalliance.org/Article/agile-teams-use-behavior-driven-development-build-better-software) -- Using BDD scenarios as acceptance criteria
- [BDD Essential Guide for 2026 (monday.com)](https://monday.com/blog/rnd/behavior-driven-development/) -- Current BDD best practices
- [Next.js Testing Guide](https://nextjs.org/docs/app/guides/testing) -- Official Vitest + Playwright setup

---

## 1. BDD Feature Specifications

### Epic 1: Foundation

#### Feature 1.1: User Signup

```gherkin
Feature: User Signup
  As a new Vibe team member
  I want to create an account on OpenVibe
  So that I can access the team workspace

  Background:
    Given the OpenVibe application is running
    And the Supabase Auth service is available

  Scenario: Sign up with email and password
    Given I am on the signup page
    When I enter a valid email "alice@vibe.dev"
    And I enter a password "SecureP@ss123"
    And I click "Sign Up"
    Then I should see the workspace join page
    And a user record should exist in the database

  Scenario: Sign up with Google OAuth
    Given I am on the signup page
    When I click "Sign in with Google"
    And I authorize the OAuth consent
    Then I should be redirected to the callback page
    And a user record should be created from my Google profile
    And I should see the workspace join page

  Scenario: Sign up with existing email
    Given a user with email "alice@vibe.dev" already exists
    And I am on the signup page
    When I enter email "alice@vibe.dev"
    And I enter a password "AnotherP@ss123"
    And I click "Sign Up"
    Then I should see an error "An account with this email already exists"

  Scenario: Sign up with invalid password
    Given I am on the signup page
    When I enter a valid email "bob@vibe.dev"
    And I enter a password "123"
    And I click "Sign Up"
    Then I should see a password validation error
```

#### Feature 1.2: User Login

```gherkin
Feature: User Login
  As an existing Vibe team member
  I want to log in to OpenVibe
  So that I can access my workspace

  Background:
    Given a user exists with email "alice@vibe.dev" and password "SecureP@ss123"
    And the user is a member of workspace "Vibe Team"

  Scenario: Log in with email and password
    Given I am on the login page
    When I enter email "alice@vibe.dev"
    And I enter password "SecureP@ss123"
    And I click "Log In"
    Then I should be redirected to the "Vibe Team" workspace
    And I should see the channel sidebar

  Scenario: Log in with Google OAuth
    Given I am on the login page
    When I click "Sign in with Google"
    And I authorize the OAuth consent
    Then I should be redirected to the "Vibe Team" workspace

  Scenario: Log in with wrong password
    Given I am on the login page
    When I enter email "alice@vibe.dev"
    And I enter password "WrongPassword"
    And I click "Log In"
    Then I should see an error "Invalid login credentials"

  Scenario: Session persists across page refresh
    Given I am logged in as "alice@vibe.dev"
    When I refresh the page
    Then I should still be logged in
    And I should see the workspace I was last viewing
```

#### Feature 1.3: Workspace Creation

```gherkin
Feature: Workspace Creation
  As a new user who just signed up
  I want to create a workspace for my team
  So that we have a place to collaborate

  Scenario: Create a new workspace
    Given I am logged in as a new user with no workspace
    And I am on the workspace setup page
    When I enter workspace name "Vibe Team"
    And I click "Create Workspace"
    Then a workspace "Vibe Team" should be created
    And I should be the admin of "Vibe Team"
    And I should see default channels "#general" and "#random"
    And I should be redirected to the "#general" channel

  Scenario: Workspace slug is auto-generated
    Given I am on the workspace setup page
    When I enter workspace name "Vibe Team"
    Then the slug field should auto-populate with "vibe-team"

  Scenario: Workspace name already taken
    Given a workspace with slug "vibe-team" already exists
    When I try to create a workspace with name "Vibe Team"
    Then I should see an error "This workspace name is already taken"
```

#### Feature 1.4: Workspace Invitation

```gherkin
Feature: Workspace Invitation
  As a workspace admin
  I want to invite team members to my workspace
  So that they can join and collaborate

  Background:
    Given I am logged in as admin of workspace "Vibe Team"

  Scenario: Invite a user by email
    When I go to workspace settings
    And I invite "bob@vibe.dev" with role "member"
    Then an invitation should be created for "bob@vibe.dev"
    And "bob@vibe.dev" should be able to join "Vibe Team"

  Scenario: Invited user joins workspace
    Given "bob@vibe.dev" has been invited to "Vibe Team"
    And "bob@vibe.dev" is logged in
    When "bob@vibe.dev" accepts the invitation
    Then "bob@vibe.dev" should be a member of "Vibe Team"
    And "bob@vibe.dev" should see all public channels

  Scenario: Non-admin cannot invite
    Given I am logged in as a member (not admin) of "Vibe Team"
    When I try to invite "carol@vibe.dev"
    Then I should see a permission error

  Scenario: Invite link (shareable)
    Given I am on the workspace settings page
    When I generate an invite link
    Then I should receive a shareable URL
    And anyone with the link who signs up should be able to join "Vibe Team"
```

---

### Epic 2: Channels & Messaging

#### Feature 2.1: Channel Creation

```gherkin
Feature: Channel Creation
  As a workspace member
  I want to create channels for specific topics
  So that conversations are organized by subject

  Background:
    Given I am logged in as a member of workspace "Vibe Team"

  Scenario: Create a public channel
    When I click "Create Channel"
    And I enter channel name "engineering"
    And I enter description "Engineering discussions"
    And I click "Create"
    Then a channel "#engineering" should appear in the sidebar
    And all workspace members should see "#engineering"

  Scenario: Channel name must be unique within workspace
    Given a channel "#engineering" already exists in "Vibe Team"
    When I try to create a channel named "engineering"
    Then I should see an error "A channel with this name already exists"

  Scenario: Channel name validation
    When I try to create a channel with name ""
    Then I should see a validation error
    When I try to create a channel with name "Engineering Team"
    Then the channel should be created as "#engineering-team"
```

#### Feature 2.2: Post a Message in a Channel

```gherkin
Feature: Post a Message
  As a workspace member
  I want to post messages in a channel
  So that I can communicate with my team

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I am in channel "#engineering"

  Scenario: Send a text message
    When I type "Hello team, let's discuss the API design" in the message input
    And I press Enter
    Then a new thread should be created in "#engineering"
    And the message should appear in the thread list
    And the message should show my name and avatar
    And the message should show the current timestamp

  Scenario: Send a message with markdown
    When I type "Here is some **bold** and `code`" in the message input
    And I press Enter
    Then the message should render with bold text and inline code

  Scenario: Send a multi-line message
    When I type a multi-line message with Shift+Enter for newlines
    And I press Enter
    Then the full multi-line message should be posted

  Scenario: Empty message is not sent
    When the message input is empty
    And I press Enter
    Then no message should be sent
    And no thread should be created
```

#### Feature 2.3: View Messages in Real-Time

```gherkin
Feature: Real-Time Messages
  As a workspace member viewing a channel
  I want to see new messages appear in real-time
  So that I stay up-to-date without refreshing

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I am viewing thread "API Design Discussion" in "#engineering"
    And "bob@vibe.dev" is also viewing the same thread

  Scenario: New message appears in real-time
    When "bob@vibe.dev" posts "I think we should use REST"
    Then I should see Bob's message appear without refreshing
    And the message should appear at the bottom of the thread
    And the scroll position should adjust to show the new message

  Scenario: Multiple messages from different users appear in order
    When "bob@vibe.dev" posts "First message"
    And "carol@vibe.dev" posts "Second message"
    Then I should see both messages in chronological order

  Scenario: Thread list updates when new thread is created
    Given I am viewing the "#engineering" channel thread list
    When "bob@vibe.dev" posts a new message creating a new thread
    Then the new thread should appear in my thread list
    And it should show the first message preview

  Scenario: Message from agent appears in real-time
    Given an agent "@assistant" is responding in the thread
    When the agent posts a response
    Then the response should appear with agent styling (distinct from human messages)
    And the "agent is thinking" indicator should disappear
```

#### Feature 2.4: Message Rendering

```gherkin
Feature: Message Rendering
  As a workspace member
  I want messages to render rich content properly
  So that technical discussions are readable

  Scenario: Render markdown formatting
    Given a message with content "**bold** _italic_ ~~strike~~ `inline code`"
    Then the message should render bold, italic, strikethrough, and inline code

  Scenario: Render code blocks with syntax highlighting
    Given a message with a fenced code block tagged "typescript"
    Then the code block should render with TypeScript syntax highlighting
    And the code block should have a copy button

  Scenario: Render multi-line content
    Given a message with bullet points and numbered lists
    Then the lists should render with proper formatting

  Scenario: Human vs Agent message styling
    Given a message from a human user
    Then it should render with the user's avatar and name
    Given a message from an agent
    Then it should render with the agent's icon and display name
    And it should have a visually distinct background or border

  Scenario: System messages render differently
    Given a system message "Fork resolved: Rate Limiting Research"
    Then it should render as a compact, informational block
    And it should not have a user avatar
```

---

### Epic 3: Threads

#### Feature 3.1: Reply to a Message (Create Thread)

```gherkin
Feature: Thread Replies
  As a workspace member
  I want to reply to a message in a thread
  So that discussions stay organized under the original topic

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I am viewing channel "#engineering"
    And there is a thread started by "bob@vibe.dev" with message "Let's discuss the API"

  Scenario: Reply to a message in a thread
    When I click on the thread "Let's discuss the API"
    And the thread panel opens
    And I type "I agree, let's use tRPC" in the reply input
    And I press Enter
    Then my reply should appear in the thread
    And the thread should show 2 messages total
    And the thread list should update to show "2 replies"

  Scenario: Thread panel shows original message
    When I click on the thread
    Then the thread panel should show the original message at the top
    And all replies should appear below it in chronological order

  Scenario: Thread view has its own compose box
    When I open a thread
    Then the thread view should have its own message input
    And sending a message should add it to the thread (not the channel root)
```

#### Feature 3.2: View Thread in Panel

```gherkin
Feature: Thread Panel View
  As a workspace member
  I want to view thread conversations in a panel
  So that I can read the full discussion without losing my channel context

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I am in channel "#engineering"
    And there is a thread with 10 messages

  Scenario: Open thread in side panel
    When I click on a thread in the channel
    Then a panel should open on the right side
    And the panel should show all thread messages
    And the channel view should still be visible on the left

  Scenario: Close thread panel
    Given the thread panel is open
    When I click the close button on the panel
    Then the panel should close
    And the full channel view should be restored

  Scenario: Switch between threads
    Given I have thread panel open for "Thread A"
    When I click on "Thread B" in the channel
    Then the panel should switch to show "Thread B" messages
```

#### Feature 3.3: Thread with Multiple Participants

```gherkin
Feature: Multi-Participant Threads
  As a workspace member
  I want to see who is participating in a thread
  So that I know the discussion context

  Background:
    Given a thread exists in "#engineering"
    And "alice@vibe.dev", "bob@vibe.dev", and "carol@vibe.dev" have posted replies

  Scenario: Thread shows participant avatars
    When I view the thread in the channel list
    Then I should see avatars of alice, bob, and carol
    And I should see the reply count

  Scenario: Thread shows participant count
    When I view the thread header
    Then it should show "3 participants"

  Scenario: New participant joins thread by replying
    Given "dave@vibe.dev" has not posted in this thread
    When "dave@vibe.dev" posts a reply
    Then the participant count should update to 4
    And Dave's avatar should appear in the thread participants
```

---

### Epic 4: Forks

#### Feature 4.1: Fork from a Message

```gherkin
Feature: Fork from a Message
  As a workspace member
  I want to fork a conversation from any message
  So that I can explore a topic without cluttering the main thread

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I am viewing a thread in "#engineering"
    And there is a message from "bob@vibe.dev": "We need to decide on rate limiting"

  Scenario: Create a fork from a message
    When I click the "Fork" action on Bob's message
    Then a fork creation dialog should appear
    And the description should be auto-generated from the message content
    When I click "Create Fork"
    Then a new fork should be created
    And I should be switched to the fork view
    And the fork should show Bob's original message as context
    And the fork sidebar should show 1 active fork

  Scenario: Create a fork with custom description
    When I click "Fork" on Bob's message
    And I change the description to "Research rate limiting approaches"
    And I click "Create Fork"
    Then the fork should be created with description "Research rate limiting approaches"

  Scenario: Fork sidebar shows active forks
    Given a fork "Rate Limiting Research" exists on the thread
    When I view the thread
    Then the fork sidebar should show "Rate Limiting Research"
    And it should show the creator, participant count, and message count
    And it should show the time since last activity

  Scenario: Cannot fork from a fork (depth limit = 1)
    Given I am viewing a fork
    When I look at messages in the fork
    Then the "Fork" action should not be available on fork messages
```

#### Feature 4.2: Work in a Fork

```gherkin
Feature: Work in a Fork
  As a workspace member
  I want to post messages within a fork
  So that I can explore a topic in a contained space

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I have created a fork "Rate Limiting Research" in a thread
    And I am viewing the fork

  Scenario: Post a message in a fork
    When I type "Let me research token bucket algorithms" in the fork compose box
    And I press Enter
    Then the message should appear in the fork
    And the fork sidebar should update the message count

  Scenario: Fork shows breadcrumb navigation
    Then I should see a breadcrumb "Main Thread > Fork: Rate Limiting Research"
    And clicking "Main Thread" should switch me back to the main thread view

  Scenario: Back button returns to main thread
    When I click the back button
    Then I should see the main thread view
    And the fork sidebar should still show the fork as active

  Scenario: Another user can view and participate in my fork
    Given "bob@vibe.dev" is viewing the same thread
    When "bob@vibe.dev" clicks on "Rate Limiting Research" in the fork sidebar
    Then Bob should see the fork messages
    And Bob can post a reply in the fork

  Scenario: Messages in a fork appear in real-time
    Given "bob@vibe.dev" is also viewing the fork
    When I post a message in the fork
    Then Bob should see my message appear without refreshing
```

#### Feature 4.3: Resolve a Fork

```gherkin
Feature: Resolve a Fork
  As a fork creator
  I want to resolve a fork with an AI-generated summary
  So that the conclusion is posted to the main thread

  Background:
    Given I am logged in as "alice@vibe.dev" (fork creator)
    And a fork "Rate Limiting Research" exists with 8 messages
    And the fork contains research about token bucket vs sliding window

  Scenario: Resolve a fork (happy path)
    When I click "Resolve" in the fork view
    Then an AI should generate a resolution summary
    And I should see a resolution editor with:
      | Field    | Content                                      |
      | Headline | Use Cloudflare Token Bucket for rate limiting |
      | Summary  | 3-5 bullet points of key findings             |
    And I should be able to edit the summary
    When I click "Post to Thread"
    Then the summary should appear as a message in the main thread
    And the message should have metadata indicating it is a resolution
    And the fork status should change to "resolved"
    And the fork should move from "Active" to "Resolved" in the sidebar

  Scenario: Edit resolution summary before posting
    When I click "Resolve"
    And the AI generates a summary
    And I edit the headline to "Token Bucket via Cloudflare - no code changes needed"
    And I click "Post to Thread"
    Then the edited summary should appear in the main thread

  Scenario: Cancel resolution
    When I click "Resolve"
    And the AI generates a summary
    And I click "Cancel"
    Then the fork should remain active
    And no summary should be posted to the main thread

  Scenario: Non-creator cannot resolve
    Given I am logged in as "bob@vibe.dev" (not the fork creator)
    When I view the fork "Rate Limiting Research"
    Then the "Resolve" button should not be available to me

  Scenario: Resolution summary appears in real-time for other users
    Given "bob@vibe.dev" is viewing the main thread
    When I resolve the fork
    Then Bob should see the resolution summary appear in the main thread
    And the fork sidebar should update to show the fork as "Resolved"
```

#### Feature 4.4: View Fork Sidebar

```gherkin
Feature: Fork Sidebar
  As a workspace member viewing a thread
  I want to see all forks in a sidebar
  So that I know what explorations are happening

  Background:
    Given I am viewing a thread in "#engineering"
    And the following forks exist:
      | Name                  | Creator | Status   | Messages | Last Activity |
      | Rate Limiting         | alice   | active   | 8        | 2 min ago     |
      | Performance Testing   | bob     | active   | 3        | 5 min ago     |
      | Auth Implementation   | carol   | resolved | 12       | 1 hour ago    |

  Scenario: Sidebar shows active forks
    Then the fork sidebar should show a section "Active (2)"
    And it should list "Rate Limiting" and "Performance Testing"
    And each entry should show creator, message count, and last activity

  Scenario: Sidebar shows resolved forks
    Then the fork sidebar should show a section "Resolved (1)"
    And it should list "Auth Implementation"
    And it should be visually subdued compared to active forks

  Scenario: Click fork to switch view
    When I click "Rate Limiting" in the sidebar
    Then the main content area should switch to show the fork messages
    And the sidebar should highlight "Rate Limiting" as currently viewed

  Scenario: Fork sidebar updates in real-time
    When a new fork "Database Migration" is created by "dave@vibe.dev"
    Then "Database Migration" should appear in the Active section
    And the active count should update to 3
```

#### Feature 4.5: Abandon a Fork

```gherkin
Feature: Abandon a Fork
  As a fork creator
  I want to abandon a fork that is no longer needed
  So that the sidebar stays clean

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I created a fork "Dead End Research" with 3 messages

  Scenario: Abandon a fork
    When I click "Abandon" in the fork view
    Then I should see a confirmation dialog
    When I confirm abandonment
    Then the fork status should change to "abandoned"
    And the fork should disappear from the active section of the sidebar
    And no resolution summary should be posted to the main thread

  Scenario: Abandoned fork is still accessible via search
    Given the fork "Dead End Research" has been abandoned
    When I search for "dead end research"
    Then the fork messages should appear in search results
```

---

### Epic 5: Agent Integration

#### Feature 5.1: @mention an Agent

```gherkin
Feature: @mention an Agent
  As a workspace member
  I want to @mention an agent in a message
  So that the agent responds to my question

  Background:
    Given I am logged in as "alice@vibe.dev"
    And workspace "Vibe Team" has an active agent "@assistant" (model: claude-sonnet-4-5)
    And I am viewing a thread in "#engineering"

  Scenario: @mention triggers agent response
    When I type "@assistant what are the best practices for JWT tokens?"
    And I press Enter
    Then my message should appear in the thread
    And a task should be created with status "queued"
    And an "agent is thinking" indicator should appear
    And after the agent processes, a response should appear
    And the response should be from "@assistant" with agent styling

  Scenario: @mention autocomplete suggests available agents
    When I type "@" in the message input
    Then I should see an autocomplete dropdown
    And it should list available agents: "@assistant", "@coder", "@researcher"
    When I select "@assistant"
    Then "@assistant" should be inserted into the message

  Scenario: @mention agent in a fork
    Given I am in a fork "API Research"
    When I type "@researcher analyze REST vs GraphQL for our use case"
    And I press Enter
    Then the agent should respond within the fork context
    And the agent should have access to the fork messages + parent thread context

  Scenario: Invalid @mention (non-existent agent)
    When I type "@nonexistent what time is it?"
    And I press Enter
    Then the message should be posted as plain text
    And no agent task should be created
```

#### Feature 5.2: Agent Responds in Thread

```gherkin
Feature: Agent Response in Thread
  As a workspace member
  I want to see agent responses in the thread
  So that AI assistance is part of the conversation

  Background:
    Given I am logged in as "alice@vibe.dev"
    And I am in a thread in "#engineering"
    And I have sent "@assistant explain rate limiting strategies"

  Scenario: Agent response appears as a message
    When the agent finishes processing
    Then a new message should appear from "@assistant"
    And it should have distinct visual styling (agent avatar, border)
    And it should contain the response content
    And the "agent is thinking" indicator should disappear

  Scenario: Agent response includes markdown
    When the agent responds with a markdown-formatted answer
    Then the response should render with proper markdown formatting
    And code blocks should have syntax highlighting

  Scenario: Agent response is visible to all thread participants
    Given "bob@vibe.dev" is also viewing this thread
    When the agent posts its response
    Then Bob should see the response appear in real-time

  Scenario: Task status tracking
    When I send a message with @mention
    Then I should see task status progress:
      | Status    | Visual Indicator                |
      | queued    | "Agent is processing..."        |
      | running   | "Agent is thinking..." (typing) |
      | completed | Response message appears        |
      | failed    | Error message: "Agent failed"   |
```

#### Feature 5.3: Agent Responds in Fork

```gherkin
Feature: Agent Response in Fork
  As a workspace member working in a fork
  I want agents to respond within the fork context
  So that research stays contained in the fork

  Background:
    Given I am in a fork "Pricing Research" in thread "Q2 Strategy"
    And the fork was created from a message about pricing models
    And there are 3 prior messages in the fork

  Scenario: Agent sees fork context + parent thread context
    When I type "@researcher compare per-seat vs usage-based pricing"
    And I press Enter
    Then the agent should generate a response based on:
      | Context Source      | What's Included                        |
      | Parent thread       | Messages up to the fork point          |
      | Fork messages       | All 3 prior messages + my new message  |
      | System prompt       | Agent's configured system prompt       |

  Scenario: Agent response stays in fork
    When the agent responds
    Then the response should appear only in the fork
    And it should NOT appear in the main thread
    And other thread participants should only see fork sidebar activity
```

#### Feature 5.4: Agent Response with Progressive Disclosure

```gherkin
Feature: Progressive Disclosure of Agent Responses
  As a workspace member
  I want agent responses to show a summary first
  So that I can choose how deep to read

  Scenario: Agent response shows summary by default
    Given an agent has responded with a long analysis (>500 words)
    Then the response should render with:
      | Layer    | Visibility        | Content                        |
      | Headline | Always visible    | Single-line summary            |
      | Summary  | Expanded by default in fork, collapsed in main | 3-5 bullet points |
      | Full     | Collapsed         | Complete output                |
    And I should see a "Show more" toggle for the full output

  Scenario: Expand full output
    Given an agent response with collapsed full output
    When I click "Show more"
    Then the full output should expand below the summary
    And I should see a "Show less" toggle

  Scenario: Short agent responses show fully
    Given an agent response with fewer than 100 words
    Then the response should display in full without progressive disclosure

  Scenario: Resolution summary shows headline in main thread
    Given a fork was resolved with a summary
    When I view the resolution in the main thread
    Then I should see the headline and summary
    And I should see a "View full research (N messages)" link
    When I click the link
    Then I should navigate to the resolved fork view
```

#### Feature 5.5: Agent "Thinking" Indicator

```gherkin
Feature: Agent Thinking Indicator
  As a workspace member
  I want to see when an agent is processing my request
  So that I know a response is coming

  Scenario: Thinking indicator shows while agent processes
    Given I have sent a message with @mention to an agent
    When the task status changes to "running"
    Then I should see an indicator showing the agent's avatar
    And it should display "Agent is thinking..."
    And it should have a subtle animation (pulsing dots or similar)

  Scenario: Thinking indicator disappears on completion
    Given the agent thinking indicator is showing
    When the agent's response message appears
    Then the thinking indicator should disappear

  Scenario: Thinking indicator shows on error
    Given the agent thinking indicator is showing
    When the agent task fails
    Then the indicator should be replaced with an error message
    And the error should say "Agent encountered an error. Try again?"

  Scenario: Multiple agents thinking simultaneously
    Given I have @mentioned two agents in a fork
    When both agents are processing
    Then I should see two thinking indicators
    And each should show the respective agent's name
```

---

### Epic 6: Search

#### Feature 6.1: Search Messages Across Workspace

```gherkin
Feature: Workspace Search
  As a workspace member
  I want to search messages across the entire workspace
  So that I can find past discussions and decisions

  Background:
    Given I am logged in as "alice@vibe.dev"
    And the workspace has messages across multiple channels and threads

  Scenario: Search for a keyword
    When I open the search interface
    And I type "rate limiting" in the search box
    And I press Enter
    Then I should see search results containing "rate limiting"
    And each result should show:
      | Field      | Example                                    |
      | Content    | Message text with "rate limiting" highlighted |
      | Author     | alice@vibe.dev                               |
      | Location   | #engineering > Rate Limiting Discussion       |
      | Timestamp  | 2 hours ago                                  |
    And results should be ordered by relevance

  Scenario: Click search result navigates to message
    Given I have search results for "rate limiting"
    When I click on a search result
    Then I should be navigated to the thread containing that message
    And the message should be highlighted or scrolled into view

  Scenario: Search finds messages in forks
    Given a fork contains a message about "rate limiting"
    When I search for "rate limiting"
    Then the fork message should appear in search results
    And the location should indicate it is from a fork

  Scenario: Search with no results
    When I search for "xyznonexistentterm123"
    Then I should see "No results found for 'xyznonexistentterm123'"

  Scenario: Search handles empty query
    When I submit an empty search query
    Then no search should be performed
```

#### Feature 6.2: Search Within a Channel

```gherkin
Feature: Channel-Scoped Search
  As a workspace member
  I want to search within a specific channel
  So that I can find discussions in a particular context

  Background:
    Given I am logged in and viewing channel "#engineering"

  Scenario: Search scoped to current channel
    When I open search within "#engineering"
    And I search for "deployment"
    Then results should only include messages from "#engineering"
    And results should NOT include messages from other channels

  Scenario: Channel filter in search results
    When I search workspace-wide for "deployment"
    Then I should see a filter to narrow results by channel
    When I select "#engineering" filter
    Then only "#engineering" results should be shown
```

---

### Epic 7: Admin Config

#### Feature 7.1: Load Workspace Config

```gherkin
Feature: Load Workspace Config
  As a workspace admin
  I want to configure the workspace via settings
  So that the workspace behavior matches our team's needs

  Background:
    Given I am logged in as admin of workspace "Vibe Team"

  Scenario: Default workspace config on creation
    Given the workspace was just created
    Then the following defaults should be active:
      | Config Key          | Default Value                              |
      | sidebar_layout      | channels first, then agents                |
      | theme               | system (follows OS preference)             |
      | max_forks_per_thread| 7                                          |
      | default_agent       | assistant                                  |

  Scenario: Update workspace config
    When I go to workspace settings
    And I change "max_forks_per_thread" to 5
    And I save the config
    Then the config should be updated
    And all workspace members should see the new fork limit

  Scenario: Agent roster configuration
    When I go to agent settings
    Then I should see the list of configured agents:
      | Name       | Model             | Status |
      | @assistant | claude-sonnet-4-5 | Active |
      | @coder     | claude-sonnet-4-5 | Active |
      | @researcher| claude-opus-4-6   | Active |
    And I should be able to edit agent system prompts
    And I should be able to activate/deactivate agents
```

#### Feature 7.2: Config Affects UI Rendering

```gherkin
Feature: Config-Driven UI
  As a workspace member
  I want the UI to reflect workspace configuration
  So that the interface matches our team's setup

  Scenario: Agent roster reflects config
    Given the admin has deactivated "@coder"
    When I type "@" in a message input
    Then the autocomplete should NOT show "@coder"
    And only active agents should be suggested

  Scenario: Fork limit enforced
    Given the workspace config sets max_forks_per_thread to 5
    And a thread already has 5 active forks
    When I try to create a new fork
    Then I should see a message "Maximum active forks reached (5). Resolve or abandon an existing fork first."

  Scenario: Sidebar layout matches config
    Given the workspace config sets sidebar_layout to "agents first"
    Then the sidebar should show the agent list above the channel list
```

---

## 2. Implementation Order (Critical Path)

### Dependency Graph

```
                    +-----------------------+
                    | Milestone 0           |
                    | Monorepo + CI + DB    |
                    | + Deploy Pipeline     |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    | Feature 1.1-1.2       |
                    | Signup + Login        |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    | Feature 1.3           |
                    | Workspace Creation    |
                    +-----------+-----------+
                                |
              +-----------------+------------------+
              |                                    |
   +----------v----------+              +----------v----------+
   | Feature 1.4         |              | Feature 2.1         |
   | Workspace Invite    |              | Channel Creation    |
   +---------------------+              +----------+----------+
                                                   |
                                        +----------v----------+
                                        | Feature 2.2         |
                                        | Post a Message      |
                                        +----------+----------+
                                                   |
                                        +----------v----------+
                                        | Feature 2.3         |
                                        | Real-Time Messages  |
                                        +----------+----------+
                                                   |
                               +-------------------+-------------------+
                               |                   |                   |
                    +----------v---+     +---------v--------+  +------v--------+
                    | Feature 2.4  |     | Feature 3.1-3.3  |  | Feature 6.1   |
                    | Msg Render   |     | Threads          |  | Search        |
                    +--------------+     +---------+--------+  +------+--------+
                                                   |                  |
                                        +----------v----------+      |
                                        | Feature 4.1         |      |
                                        | Fork from Message   |      |
                                        +----------+----------+      |
                                                   |                  |
                                   +---------------+-------+          |
                                   |                       |          |
                        +----------v----------+ +----------v-----+   |
                        | Feature 4.2         | | Feature 4.4    |   |
                        | Work in Fork        | | Fork Sidebar   |   |
                        +----------+----------+ +----------------+   |
                                   |                                  |
                     +-------------+-------------+                    |
                     |                           |                    |
          +----------v----------+     +----------v----------+        |
          | Feature 5.1-5.3     |     | Feature 4.5         |  +-----v-------+
          | Agent @mention +    |     | Abandon Fork        |  | Feature 6.2 |
          | Response in         |     +---------------------+  | Channel     |
          | Thread + Fork       |                               | Search      |
          +----------+----------+                               +-------------+
                     |
          +----------v----------+
          | Feature 5.4-5.5     |
          | Progressive         |
          | Disclosure +        |
          | Thinking Indicator  |
          +----------+----------+
                     |
          +----------v----------+
          | Feature 4.3         |
          | Resolve Fork        |
          | (AI Summary)        |
          +----------+----------+
                     |
          +----------v----------+
          | Feature 7.1-7.2     |
          | Admin Config        |
          +---------------------+
```

### Critical Path

The critical path (longest dependency chain) is:

```
Milestone 0 -> 1.1/1.2 (Auth) -> 1.3 (Workspace) -> 2.1 (Channels)
-> 2.2 (Messages) -> 2.3 (Realtime) -> 3.1-3.3 (Threads)
-> 4.1 (Fork) -> 4.2 (Work in Fork) -> 5.1-5.3 (Agent Integration)
-> 4.3 (Resolve Fork with AI Summary)
```

**The "it works" criteria at each step:**

| Step | Testable Behavior | "It Works" Criteria |
|------|-------------------|---------------------|
| Milestone 0 | App deploys, DB connects | `npm run build` passes, Vercel preview URL loads |
| Auth (1.1-1.2) | User can sign up and log in | Sign up with email, log out, log back in |
| Workspace (1.3) | User creates workspace | After signup, workspace exists with default channels |
| Channels (2.1) | User creates a channel | New channel appears in sidebar for all members |
| Messages (2.2) | User posts a message | Message appears, persists across refresh |
| Realtime (2.3) | Two users see messages in real-time | Open two browser tabs, message in one appears in other |
| Threads (3.1-3.3) | User replies to a message | Thread panel opens, replies appear |
| Fork (4.1) | User forks from a message | Fork appears in sidebar |
| Work in Fork (4.2) | User posts in fork | Messages appear within fork context |
| Agent (5.1-5.3) | Agent responds to @mention | Type `@assistant hello`, get response |
| Resolve (4.3) | Fork resolves with AI summary | Summary posted to main thread |

---

## 3. Sprint Plan

### Sprint 0 (Pre-Sprint, 2-3 days): Milestone 0

**Goal:** Deployable empty shell with CI/CD.

**Work:**
- Nx monorepo setup with Next.js App Router application
- Supabase project creation (database, auth, realtime configured)
- Database migration: all 10 tables + RLS policies + indexes
- Seed data: default workspace, 4 channels (#general, #random, #engineering, #product), 3 agent configs
- tRPC scaffold (routers with placeholder procedures)
- Vercel deployment connected to GitHub
- GitHub Actions CI: lint + typecheck + build
- Environment variables configured

**Testable:** `https://openvibe-preview.vercel.app` loads a blank page. Database tables exist. CI passes.

**Definition of Done:**
- [ ] `npm run build` succeeds
- [ ] Vercel preview deployment accessible
- [ ] All 10 DB tables created with correct constraints
- [ ] RLS policies enabled
- [ ] Supabase Realtime enabled on messages, forks, tasks, threads
- [ ] Seed data present in database

---

### Sprint 1 (Weeks 1-2): Foundation + Basic Messaging

**Goal:** Users can sign up, create/join a workspace, and send messages in channels. Two users can see each other's messages in real-time.

**Features Implemented:**
- Feature 1.1: User Signup
- Feature 1.2: User Login
- Feature 1.3: Workspace Creation
- Feature 1.4: Workspace Invitation (basic -- invite link, not email)
- Feature 2.1: Channel Creation
- Feature 2.2: Post a Message
- Feature 2.3: Real-Time Messages
- Feature 2.4: Message Rendering (markdown basics)

**What a demo looks like:**
1. Open app in browser -> see login page
2. Sign up with Google -> redirected to workspace creation
3. Create "Vibe Team" -> see #general channel with sidebar
4. Post a message in #general -> message appears immediately
5. Open a second browser/tab -> log in as different user
6. Both users see each other's messages in real-time
7. Messages render with markdown (bold, code blocks, lists)

**Definition of Done:**
- [ ] All Feature 1.1-1.4 scenarios pass
- [ ] All Feature 2.1-2.4 scenarios pass
- [ ] Two concurrent users can exchange messages in real-time
- [ ] Messages persist across page refresh
- [ ] Channel sidebar shows all channels
- [ ] Auth redirects work (login, signup, OAuth callback, logout)

**Risk/Blocker Watch:**
- Supabase Auth + Google OAuth configuration can be fiddly. Budget an extra half-day.
- Supabase Realtime requires correct publication setup. Test early.
- Message rendering: use a proven markdown library (react-markdown + remark-gfm). Do not build custom renderer.

---

### Sprint 2 (Weeks 3-4): Threads + Basic Agent Integration

**Goal:** Thread-based conversations work. @mention an agent, get a response. This is where OpenVibe becomes more than a basic chat.

**Features Implemented:**
- Feature 3.1: Reply to a Message (Thread Creation)
- Feature 3.2: Thread Panel View
- Feature 3.3: Multi-Participant Threads
- Feature 5.1: @mention an Agent
- Feature 5.2: Agent Responds in Thread
- Feature 5.5: Agent "Thinking" Indicator

**What a demo looks like:**
1. Click on a message -> thread panel opens on the right
2. Reply in the thread -> reply appears for both users
3. Thread list shows reply count and participant avatars
4. Type `@assistant what is rate limiting?` -> agent thinking indicator appears
5. Agent responds with formatted markdown -> response appears in thread
6. Other users see the agent response in real-time

**Definition of Done:**
- [ ] All Feature 3.1-3.3 scenarios pass
- [ ] All Feature 5.1-5.2, 5.5 scenarios pass
- [ ] Thread panel opens/closes correctly
- [ ] Agent @mention autocomplete works
- [ ] Agent responses appear with distinct styling
- [ ] Agent thinking indicator shows/hides correctly
- [ ] Agent task lifecycle (queued -> running -> completed/failed) tracked in database

**Risk/Blocker Watch:**
- Anthropic API integration: ensure API key is set up, streaming works. Test with a simple "hello" first.
- Agent context building: keep it simple (last 50 messages). Do not over-engineer context management.
- Thread panel layout: the Discord-like side panel is the trickiest frontend component. Use a proven resizable panel library.

---

### Sprint 3 (Weeks 5-6): Forks + Fork Resolution (The Differentiator)

**Goal:** Fork/Resolve works end-to-end. This is the core product differentiator. Users can fork from any message, work with agents in forks, and resolve forks with AI-generated summaries.

**Features Implemented:**
- Feature 4.1: Fork from a Message
- Feature 4.2: Work in a Fork
- Feature 4.3: Resolve a Fork (AI Summary)
- Feature 4.4: Fork Sidebar
- Feature 4.5: Abandon a Fork
- Feature 5.3: Agent Responds in Fork
- Feature 5.4: Progressive Disclosure (basic -- expand/collapse on long responses)

**What a demo looks like:**
1. In a thread, click "Fork" on a message -> fork created, sidebar shows it
2. Work in the fork: post messages, @mention agent -> agent responds in fork
3. Fork sidebar shows: fork name, participants, message count, activity
4. Click "Resolve" -> AI generates summary -> edit headline/summary -> post to thread
5. Resolution summary appears in main thread with "View full research" link
6. Click "Abandon" on another fork -> fork disappears from active list
7. Agent responses in forks show progressive disclosure (expand/collapse for long content)

**Definition of Done:**
- [ ] All Feature 4.1-4.5 scenarios pass
- [ ] All Feature 5.3-5.4 scenarios pass
- [ ] Fork lifecycle: active -> resolved -> abandoned
- [ ] Resolution summary quality is acceptable (test with real Vibe team conversations)
- [ ] Fork sidebar updates in real-time
- [ ] Agent in fork has correct context (parent thread + fork messages)
- [ ] Breadcrumb navigation between main thread and fork works

**Risk/Blocker Watch:**
- AI summary quality is THE risk. Test the resolution prompt early with real conversations. Iterate the prompt.
- Fork context for agents: ensure the agent sees parent thread up to fork point + fork messages. Context truncation may be needed.
- Fork sidebar real-time updates: subscribe to fork table changes via Supabase Realtime.
- This is the most complex sprint. If behind schedule, defer Feature 5.4 (progressive disclosure) to Sprint 4.

---

### Sprint 4 (Weeks 7-8): Search, Config, Polish, Dogfood Prep

**Goal:** Search works. Admin config works. The product is polished enough for the Vibe team to use daily. Dogfood launch.

**Features Implemented:**
- Feature 6.1: Search Messages Across Workspace
- Feature 6.2: Search Within a Channel
- Feature 7.1: Load Workspace Config
- Feature 7.2: Config Affects UI Rendering
- Polish: loading states, error states, empty states, responsive layout

**What a demo looks like:**
1. Open search (Cmd+K) -> type "rate limiting" -> results with highlights
2. Click result -> navigate to the thread and message
3. Filter search by channel
4. Admin opens settings -> see agent roster -> toggle agent active/inactive
5. Deactivated agent no longer appears in @mention autocomplete
6. Everything has loading spinners, error messages, empty states
7. The app feels "production-quality" for 20 internal users

**Definition of Done:**
- [ ] All Feature 6.1-6.2 scenarios pass
- [ ] All Feature 7.1-7.2 scenarios pass
- [ ] Full-text search returns relevant results with highlights
- [ ] Admin can manage agent configs
- [ ] No blank/broken states in the UI
- [ ] Error messages are actionable
- [ ] App is deployed to production URL
- [ ] Vibe team members can sign up and start using it
- [ ] Onboarding instructions written for the team
- [ ] Default channels seeded with welcome messages

**Risk/Blocker Watch:**
- Search: PostgreSQL tsvector should work out of the box. Test with real content.
- Polish always takes longer than expected. Prioritize: error states > loading states > empty states.
- Onboarding: write a brief guide for the Vibe team. Assign a champion to answer questions.
- Config: keep the admin UI minimal. A simple settings page, not a full admin console.

---

### Sprint-to-Milestone Mapping

| Sprint | Milestone | What's Deployable |
|--------|-----------|-------------------|
| Sprint 0 | M0: Infrastructure ready | Empty shell deploys, DB provisioned |
| Sprint 1 | M1: First message stored and displayed in real-time | Users chat in channels with real-time sync |
| Sprint 2 | M2: First agent response | Users get AI responses to @mentions in threads |
| Sprint 3 | M3: First fork created and resolved | Full fork lifecycle with AI summaries |
| Sprint 4 | M4: Dogfood launch | Complete MVP deployed for Vibe team |

---

## 4. Testing Strategy

### Test Pyramid

```
            /  E2E  \          ~15 tests (Playwright)
           /  (slow)  \        Critical user flows only
          /____________\
         /              \
        / Integration    \     ~40 tests (Vitest + Supabase test DB)
       /  (medium)        \    tRPC router tests with real DB
      /____________________\
     /                      \
    /       Unit Tests       \  ~80 tests (Vitest)
   /        (fast)            \ Pure functions, Zustand stores, utils
  /__________________________\
```

**Target: ~135 total tests at dogfood launch.**

### Unit Tests (Vitest) -- ~80 tests

**What to test:**
| Area | Example Tests | Count |
|------|--------------|-------|
| Message parsing | @mention extraction, markdown detection | 8 |
| URL/slug generation | Workspace slug, channel name normalization | 5 |
| Date/time formatting | Relative timestamps ("2 min ago") | 5 |
| Zustand stores | Message store actions, fork store state transitions | 15 |
| tRPC input validation | Zod schema validation for all routers | 20 |
| Search query processing | Query sanitization, highlight extraction | 5 |
| Agent context building | Context window construction, token counting | 8 |
| Resolution prompt building | System prompt assembly for fork resolution | 5 |
| Config defaults | Default values when config is missing | 5 |
| Utility functions | Various helpers | 4 |

**Framework config:**
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['**/*.test.ts', '**/*.test.tsx'],
    exclude: ['**/e2e/**'],
    coverage: {
      reporter: ['text', 'html'],
      include: ['src/lib/**', 'src/stores/**', 'src/server/**'],
    },
  },
})
```

### Integration Tests (Vitest + Supabase) -- ~40 tests

**What to test:**
| Area | Example Tests | Count |
|------|--------------|-------|
| Auth router | Session retrieval, sign out | 3 |
| Workspace router | Create, update, list members, invite | 5 |
| Channel router | List, create, get, update, delete | 5 |
| Thread router | List, get, create, update status | 4 |
| Fork router | Create, resolve, abandon, list | 5 |
| Message router | Send, list, update, delete, @mention detection | 6 |
| Agent router | List, create, update, toggle | 4 |
| Task router | Get, list, cancel | 3 |
| Search router | Full-text search, channel-scoped search | 3 |
| Config router | Get, set, list | 2 |

**Setup:**
- Use Supabase local development (Docker) for integration tests
- Each test file gets a fresh database state (truncate tables in beforeEach)
- Tests call tRPC procedures directly (no HTTP, no network)

```typescript
// Example integration test
import { createCaller } from '@/server/trpc/router'
import { createTestContext } from '@/test/helpers'

describe('message.send', () => {
  let caller: ReturnType<typeof createCaller>

  beforeEach(async () => {
    const ctx = await createTestContext({ user: 'alice' })
    caller = createCaller(ctx)
  })

  it('creates a message and detects @mentions', async () => {
    const result = await caller.message.send({
      threadId: 'thread-1',
      content: '@assistant what is rate limiting?',
    })

    expect(result.content).toContain('@assistant')
    // Verify task was created for the @mention
    const tasks = await caller.task.list({ status: 'queued' })
    expect(tasks).toHaveLength(1)
    expect(tasks[0].agent_config_id).toBeDefined()
  })
})
```

### E2E Tests (Playwright) -- ~15 tests

**What to test (critical user flows only):**

| # | Flow | Steps | Priority |
|---|------|-------|----------|
| 1 | Sign up and see workspace | Signup -> create workspace -> see #general | P0 |
| 2 | Log in and post message | Login -> navigate to channel -> send message -> see it | P0 |
| 3 | Real-time messaging | Two browser contexts, message in one appears in other | P0 |
| 4 | Thread creation and reply | Click message -> thread panel -> reply -> see reply | P0 |
| 5 | @mention agent and get response | Type @assistant -> send -> see thinking -> see response | P0 |
| 6 | Create a fork | Click Fork on message -> fork created -> sidebar shows it | P0 |
| 7 | Work in a fork | Navigate to fork -> post message -> message appears | P0 |
| 8 | Resolve a fork | In fork -> Resolve -> edit summary -> post to thread | P0 |
| 9 | Abandon a fork | In fork -> Abandon -> fork removed from active list | P1 |
| 10 | Search messages | Open search -> type query -> see results -> click result | P1 |
| 11 | Agent response in fork | In fork -> @mention agent -> response appears in fork | P1 |
| 12 | Fork sidebar real-time | Create fork in one tab -> appears in other tab's sidebar | P1 |
| 13 | Admin toggle agent | Settings -> deactivate agent -> agent not in autocomplete | P2 |
| 14 | Google OAuth flow | Click Google sign-in -> complete OAuth -> see workspace | P2 |
| 15 | Progressive disclosure | Agent long response -> summary shown -> expand full output | P2 |

**Framework config:**
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Sequential to avoid state conflicts
  retries: 1,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
  },
})
```

### What NOT to Test for Dogfood

| Skip | Why |
|------|-----|
| Edge cases for 100+ concurrent users | Dogfood is 20 users |
| Load/stress testing | Supabase free tier handles 20 users easily |
| Mobile responsiveness tests | Desktop-only for dogfood |
| Accessibility (a11y) compliance | Important but not blocking dogfood |
| Browser compatibility beyond Chrome | Vibe team uses Chrome |
| Offline behavior | Internet always available |
| Email delivery (invitation emails) | Using invite links, not emails |
| Rate limiting/abuse | Trusted internal users |
| Data export/GDPR | Internal tool, no external users |
| Multi-workspace scenarios | Single workspace for dogfood |
| File upload testing | Deferred feature |
| Notification delivery | No notification system in MVP |

### Test-per-Sprint Plan

| Sprint | Unit Tests Added | Integration Tests Added | E2E Tests Added | Total |
|--------|-----------------|------------------------|-----------------|-------|
| Sprint 0 | 0 | 0 | 0 | 0 |
| Sprint 1 | 25 (validation, stores, utils) | 15 (auth, workspace, channel, message routers) | 4 (#1-4: signup, login, messaging, real-time) | 44 |
| Sprint 2 | 20 (agent context, mention parsing) | 10 (thread, agent, task routers) | 3 (#4-5, plus thread E2E) | 77 |
| Sprint 3 | 25 (fork logic, resolution prompt, progressive disclosure) | 10 (fork router, resolution flow) | 5 (#6-8, #11-12: fork flows) | 117 |
| Sprint 4 | 10 (search, config) | 5 (search, config routers) | 3 (#9-10, #13: search, admin) | 135 |

---

## 5. Incremental Delivery

### Deployment after Each Sprint

Every sprint produces a deployable version on the production URL.

| Sprint | Deployed Version | What Users Can Do | Internal Testing? |
|--------|-----------------|-------------------|-------------------|
| Sprint 0 | v0.0.1 | Nothing (empty shell) | Dev-only |
| Sprint 1 | v0.1.0 | Sign up, create channels, post messages, see real-time updates | **Yes -- basic chat.** Invite 2-3 team members for early feedback. |
| Sprint 2 | v0.2.0 | + Threads, agent @mentions, AI responses | **Yes -- threaded chat + AI.** This is where it gets interesting. Invite 5-8 team members. |
| Sprint 3 | v0.3.0 | + Forks, resolve with AI summary, fork sidebar | **Yes -- the differentiator.** This is the product thesis being tested. Expand to full 20-person team. |
| Sprint 4 | v1.0.0 | + Search, admin config, polish | **Full dogfood launch.** Replace Slack for internal use. |

### When Is It Usable Enough for Internal Testing?

**Sprint 1 (Week 2):** Usable as a basic chat tool for 2-3 early adopters. Not a Slack replacement yet, but validates auth, channels, and messaging.

**Sprint 2 (Week 4):** Usable as a team chat tool with AI. This is the minimum viable product that is meaningfully different from Slack. Threads + agent responses make it compelling for technical discussions.

**Sprint 3 (Week 6):** The product thesis is testable. Fork/Resolve is the differentiator. If the Vibe team uses forks and finds the resolution summaries useful, the product works. If they don't fork, the thesis needs revision.

**Sprint 4 (Week 8):** Dogfood-ready. The full 20-person team can use it as their primary collaboration tool for at least some use cases. Slack may still be needed for DMs, notifications, and external integrations.

### Rollback Strategy

Each sprint is a tagged release. If a sprint introduces a breaking issue:
1. Revert to the previous sprint's tag: `git checkout v0.x.0`
2. Redeploy: Vercel auto-deploys from the tag
3. Fix forward in the next sprint

No database rollback mechanism in MVP (append-only data model makes this less risky). If a migration breaks, manual SQL fix via Supabase dashboard.

---

## 6. Technical Milestones

### Milestone 0: Infrastructure Ready (Sprint 0, Days 1-3)

**Criteria:**
- [ ] Nx monorepo with Next.js app compiles and deploys
- [ ] Supabase project created with all tables, RLS, and Realtime
- [ ] tRPC router scaffold exists (empty procedures)
- [ ] Vercel deployment works (preview + production)
- [ ] GitHub Actions CI passes (lint + typecheck + build)
- [ ] Environment variables configured in Vercel
- [ ] Local development setup documented (README)

**How to verify:** Visit the Vercel URL. See a blank page (or placeholder). Check Supabase dashboard: tables exist, Realtime is enabled.

### Milestone 1: First Message Stored and Displayed in Real-Time (Sprint 1, Week 2)

**Criteria:**
- [ ] User can sign up, log in, and see channels
- [ ] User can post a message in a channel
- [ ] Message is stored in Supabase `messages` table
- [ ] Message appears in the UI without page refresh (Supabase Realtime)
- [ ] Second user in a different browser tab sees the message appear

**How to verify:**
```
1. Open two browser tabs
2. Log in as alice in tab 1, bob in tab 2
3. Both navigate to #general
4. Alice types "Hello Bob" -> message appears in Alice's view
5. Bob's view updates to show "Hello Bob" within 1 second
```

**This is the single most important milestone.** Everything else builds on top of real-time messaging.

### Milestone 2: First Agent Response (Sprint 2, Week 4)

**Criteria:**
- [ ] User types `@assistant hello` in a thread
- [ ] A task is created in the `tasks` table with status "queued"
- [ ] The agent worker picks up the task, calls Claude API
- [ ] A response message appears in the thread with agent styling
- [ ] The task status is updated to "completed" with token usage recorded

**How to verify:**
```
1. In a thread, type "@assistant what is the capital of France?"
2. See "Agent is thinking..." indicator
3. See response: "The capital of France is Paris."
4. Response has agent avatar and distinct styling
5. Check tasks table: status = 'completed', token_usage populated
```

### Milestone 3: First Fork Created and Resolved (Sprint 3, Week 6)

**Criteria:**
- [ ] User clicks "Fork" on a message -> fork is created
- [ ] Fork appears in the sidebar with name and status
- [ ] User posts messages in the fork
- [ ] User @mentions agent in fork -> agent responds with fork + parent context
- [ ] User clicks "Resolve" -> AI generates summary
- [ ] User edits summary -> posts to parent thread
- [ ] Resolution message appears in main thread for all participants
- [ ] Fork status changes to "resolved"

**How to verify:**
```
1. In a thread, click Fork on a message about "API design"
2. Fork created: "API Design Research" appears in sidebar
3. In fork: "@researcher compare REST vs GraphQL"
4. Agent responds with analysis (using fork + thread context)
5. Click "Resolve" -> see AI summary
6. Edit headline -> click "Post to Thread"
7. Summary appears in main thread: "REST recommended for our use case..."
8. Fork sidebar shows "Resolved"
```

**This milestone validates the core product thesis.** If the resolution summary is useful and the fork flow is natural, the product works.

### Milestone 4: Dogfood Launch (Sprint 4, Week 8)

**Criteria:**
- [ ] All 7 Epics have their core scenarios passing
- [ ] Search returns relevant results
- [ ] Admin can configure agents
- [ ] No blank/broken UI states
- [ ] App deployed to production URL
- [ ] All 20 Vibe team members have accounts
- [ ] Default channels exist: #general, #engineering, #product, #random
- [ ] 3 agents configured: @assistant, @coder, @researcher
- [ ] Brief onboarding guide shared with team
- [ ] Token usage monitoring in place (SQL query)

**How to verify:** The Vibe team uses OpenVibe for at least one real discussion topic per day for a week. Track: messages sent, threads created, forks created, forks resolved, agent invocations. If fork usage is zero after 1 week, the product thesis needs revisiting.

---

## Open Questions

### 1. Playwright-BDD vs Plain Playwright for E2E

Should E2E tests use the Gherkin specs directly (via `playwright-bdd` library) or keep Playwright tests as plain TypeScript that mirrors the Gherkin scenarios?

**Recommendation:** Plain Playwright for MVP. The `playwright-bdd` library adds a layer of indirection (step definitions, feature file parsing) that slows down a 1-2 person team. Write Playwright tests that follow the Gherkin structure (use scenario names as test names) but don't require the Cucumber runtime. Revisit when the team grows and non-developers need to read test specs.

### 2. Supabase Local Dev vs Cloud for Integration Tests

Should integration tests run against Supabase local (Docker) or a dedicated cloud test project?

**Recommendation:** Supabase local for CI (deterministic, fast, free). Supabase cloud test project for manual testing. Use `supabase start` in CI to spin up a local instance. Seed it with test data before each test run.

### 3. AI Summary Quality Testing

How do we test that resolution summaries are "good enough"?

**Recommendation:** Do not automate summary quality testing for MVP. Instead:
- Manually test the resolution prompt with 5 real Vibe team Slack conversations.
- Iterate the prompt until summaries are consistently useful.
- During dogfood, collect thumbs-up/thumbs-down on summaries.
- Build a small set of "golden" test conversations with expected summaries for regression testing (Sprint 3+).

### 4. Test Data Management

How to manage test data across unit, integration, and E2E tests?

**Recommendation:**
- **Unit tests:** No external data. Use factories/fixtures inline.
- **Integration tests:** Seed database in `beforeEach`, truncate in `afterEach`. Use a `createTestData()` helper.
- **E2E tests:** Seed via API calls in `beforeAll` (use tRPC caller or Supabase admin client). Clean up in `afterAll`.

### 5. When to Start Writing Tests

**Recommendation:** Write tests starting in Sprint 1, not retroactively. For each feature:
1. Write the Gherkin spec (already done in this document)
2. Implement the feature
3. Write unit + integration tests for the backend (tRPC procedures)
4. Write E2E test for the critical flow
5. Move to next feature

This is not strict TDD (tests before code) because the specs already define behavior. It is "BDD-guided development" -- the specs exist before implementation, tests are written alongside or immediately after.

### 6. Progressive Disclosure Complexity

Feature 5.4 (Progressive Disclosure) requires the agent to generate structured output (headline + summary + full). Should this be:
- (A) Agent generates structured JSON, frontend renders layers
- (B) Agent generates markdown, frontend parses sections
- (C) Separate post-processing step generates summary from full output

**Recommendation:** (C) for MVP. The agent generates a full response. A separate Haiku call generates the headline and summary from the full response. This decouples agent output from presentation. The cost is one extra Haiku call per agent response (~$0.001), negligible.

---

*Plan completed: 2026-02-07*
*Researcher: implementation-planner*
*This document provides the full BDD specification, critical path, sprint plan, and testing strategy for the OpenVibe MVP.*
