# Vibe AI Workspace - Project Overview

> Product & System Design Overview
>
> **Current Status**: Phase 2 - Implementation
> **Implementation Guide**: [`INTENT.md`](INTENT.md) | [`BDD-IMPLEMENTATION-PLAN.md`](research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md)

---

## 1. Product Positioning

### 1.1 The Core Problem

**What problem are we solving?**

```
Traditional organizations:
  - Human <-> Human collaboration
  - Tools are passive (Slack, Notion, Excel)
  - Knowledge lives in people's heads, lost when they leave
  - Processes depend on human memory, often missed

The AI era changes this:
  - Human <-> Agent <-> Human collaboration
  - Agents can act proactively
  - Knowledge needs to be persisted for Agent use
  - Processes can be executed by Agents

Core question:
  How exactly do Humans + Agents collaborate together?
```

### 1.2 Our Answer

**Vibe AI Workspace = A new way for organizations to collaborate**

Not "adding AI to existing tools," but "redesigning how humans and Agents work together."

```
Traditional model:
  Slack (communication) + Notion (docs) + CRM (data) + Human brain (decisions)
  -> Fragmented, AI can only be an assistant

Vibe AI model:
  Unified Workspace
  -> Humans and Agents in the same space
  -> Shared Memory (knowledge base)
  -> Agents are team members, not just tools
  -> Conversation is the workflow
```

### 1.3 Core Principles

1. **Agents are Team Members, not tools**
   - Agents have persistent identities (@Scheduler, @CRO)
   - Agents have their own responsibilities and knowledge scope
   - Agents can proactively initiate conversations

2. **Memory is the organization's knowledge asset**
   - All conversations, decisions, and documents flow into Memory
   - Agents can retrieve and use Memory
   - The more Memory accumulates, the smarter the organization becomes

3. **Thread is the unit of collaboration**
   - One Thread = one topic / task / project
   - Humans and Agents collaborate within Threads
   - Threads can branch for exploration and merge conclusions

4. **Configuration as adaptation**
   - Different industries adapt through configuration, not code changes
   - Admins define boundaries, Users operate freely within them

---

## 2. Entity Model

### 2.1 Core Hierarchy

```
Workspace (Organization)
    |
    +-- Space (Work area)
    |       |
    |       +-- Thread (Collaboration topic)
    |       |       |
    |       |       +-- Feed (Message stream)
    |       |       +-- Branches
    |       |       +-- Memory Items (Distilled knowledge)
    |       |
    |       +-- Thread ...
    |       +-- Thread ...
    |
    +-- Space ...
    |
    +-- Agents (AI members)
    |       +-- @Scheduler
    |       +-- @CRO
    |       +-- @...
    |
    +-- Members (Human members)
    |       +-- Charles
    |       +-- Tara
    |       +-- ...
    |
    +-- Devices (Hardware devices)
    |       +-- Bot-FrontDesk
    |       +-- Dot-DrSmith
    |       +-- ...
    |
    +-- Memory (Knowledge base)
            +-- Workspace Memory (Global)
            +-- Space Memory (Scoped)
            +-- Personal Memory (Private)
```

### 2.2 Entity Definitions

| Entity | Definition | Key Properties |
|------|------|----------|
| **Workspace** | Top-level container for an organization | name, template, members, config |
| **Space** | Functional area / team / project | name, purpose, members, agents |
| **Thread** | A collaboration topic | topic, participants, status, branches |
| **Feed** | Message stream within a Thread | messages, real-time sync |
| **Memory** | Persisted knowledge unit | content, zoom levels, permissions, embeddings |
| **Agent** | AI team member | identity, capabilities, knowledge scope |
| **Device** | Vibe hardware device | type, location, capabilities, status |

### 2.3 Thread Deep Dive

Thread is the core unit of collaboration:

```
Thread: "Q1 Pricing Strategy Discussion"
|
+-- Feed (Main message stream)
|   +-- [Charles] We need to decide Q1 pricing
|   +-- [@CRO] Based on historical data, I recommend Option A...
|   +-- [Tara] I'm concerned about market reaction to Option A
|   +-- [Charles] @CRO can you analyze Option B?
|   +-- [@CRO] Here's the Option B analysis...
|
+-- Branches
|   +-- main (Main branch)
|   +-- explore-option-c (Exploration branch)
|       +-- [Charles] What if we consider Option C...
|       +-- [@CRO] The risks of Option C are...
|
+-- Memory Items (Distilled from conversation)
|   +-- Decision: "Chose Option A because..."
|   +-- Context: "Reasons Option B was rejected..."
|   +-- Action: "Tara to execute pricing update"
|
+-- Metadata
    +-- status: resolved
    +-- decision: "Option A"
    +-- participants: [Charles, Tara, @CRO]
```

### 2.4 Feed Deep Dive

Feed is the real-time message stream within a Thread:

```typescript
interface Feed {
  threadId: string;
  branchId: string;  // Which branch it belongs to

  messages: Message[];

  // Real-time state
  typingUsers: string[];
  onlineParticipants: string[];

  // Sync
  lastSyncAt: Date;
  unreadCount: number;
}

interface Message {
  id: string;
  author: Author;  // Human or Agent
  content: Content;
  timestamp: Date;

  // Associations
  replyTo?: string;
  mentions?: string[];

  // Metadata
  reactions?: Reaction[];
  memoryItems?: string[];  // Memory extracted from this message
}
```

---

## 3. Use Cases (Concrete Scenarios)

### 3.1 Scenario 1: A Sales Team's Daily Workflow

**Background:** A B2B sales team with 5 reps + 1 sales manager

**Pain points with the traditional approach:**
```
- CRM data is incomplete; reps are too lazy to update it
- Sales manager doesn't know the real status of each deal
- Customer information lives in reps' heads, lost when they leave
- Weekly reports are manually written and quickly forgotten
```

**The Vibe AI approach:**

```
Workspace: "Acme Sales Team"

Spaces:
+-- #deals (All deals)
+-- #accounts (Account management)
+-- #pipeline-review (Weekly review)
+-- #wins (Closed deal celebrations)

Agents:
+-- @CRO (Sales data analysis)
+-- @DealHelper (Individual deal support)
+-- @Researcher (Customer research)

Typical Thread: "Acme Corp Deal"
+-- [Sales] Had a meeting with Acme's VP today, they're interested
+-- [@DealHelper] Recorded: Acme Corp, VP of Ops, interested. Need to fill in: Budget? Timeline?
+-- [Sales] Budget is about $50K, want to go live in Q2
+-- [@DealHelper] Deal updated: $50K, Q2 close. Suggested next step: send proposal
+-- ... (follow-ups automatically recorded)
|
+-- Memory automatically distilled:
    +-- Deal: Acme Corp, $50K, Q2
    +-- Contact: John Smith, VP of Ops
    +-- Meeting Notes: 2024-02-07...
    +-- Next Steps: Send proposal by 02/10

Sales manager's view:
+-- @CRO reports daily pipeline changes
+-- Weekly review Thread auto-generates deal status summary
+-- Ask "@CRO how is the Acme deal going?" anytime and get an accurate answer
+-- When a rep leaves, all deal context remains in Memory
```

**Value:**
- Reps don't need to deliberately "update CRM" -- conversation is the record
- Manager has real-time pipeline visibility
- Knowledge doesn't leave with people

---

### 3.2 Scenario 2: A Day at a Medical Clinic

**Background:** A small clinic with 2 doctors + 3 front desk staff + 1 billing specialist

**Pain points with the traditional approach:**
```
- Front desk uses 5 systems: EHR, calendar, phone, insurance verification, payments
- Patients wait a long time to check in
- Doctors delay writing notes, still catching up after hours
- Follow-ups rely on memory, often missed
- Insurance verification is slow, patients complain
```

**The Vibe AI approach:**

```
Workspace: "Downtown Medical Clinic"

Spaces:
+-- #front-desk (Front desk)
+-- #providers (Doctors)
+-- #billing (Billing)
+-- #patients (Patient-related)

Agents:
+-- @Scheduler (Appointment management)
+-- @Insurance (Insurance verification)
+-- @FollowUp (Follow-up management)
+-- @Concierge (Patient services)

Devices:
+-- Bot-FrontDesk (Front desk, Check-in)
+-- Dot-DrSmith (Dr. Smith's office)
+-- Dot-DrJones (Dr. Jones's office)

Scenario A: Patient arrival
+-- [Bot-FrontDesk captures] Patient John Doe arrived
+-- [@Concierge] Welcome John, verifying your information...
+-- [@Insurance] Insurance verified: Blue Cross, copay $25
+-- [@Concierge] Please pay $25 copay. Your appointment is at 10:30 with Dr. Smith
+-- [System] Check-in complete, notifying Dr. Smith
|
+-- Memory automatically distilled:
    +-- Visit: John Doe, 2024-02-07 10:30
    +-- Insurance: Blue Cross verified
    +-- Payment: $25 copay collected

Scenario B: Doctor consultation
+-- [Dot-DrSmith recording starts]
+-- [Dr. Smith converses with patient...]
+-- [Dot-DrSmith recording ends]
+-- [@NoteWriter] Generated visit note draft:
|   Chief Complaint: ...
|   Assessment: ...
|   Plan: ...
+-- [Dr. Smith] Revise the Plan section...
+-- [@NoteWriter] Updated, signature confirmation needed
|
+-- Memory automatically distilled:
    +-- Encounter Note: John Doe, 2024-02-07
    +-- Diagnosis: ...
    +-- Treatment Plan: ...

Scenario C: Follow-up management
+-- [@FollowUp] Patients needing follow-up today (3):
|   1. Jane Smith - Blood pressure recheck (last reading 140/90)
|   2. Bob Johnson - 2 weeks post-surgery
|   3. Mary Wilson - Diabetes follow-up
+-- [Front desk] I'll call Jane Smith
+-- [@FollowUp] Jane Smith call outcome?
+-- [Front desk] Scheduled for next Wednesday 2pm
+-- [@FollowUp] Calendar updated, Dr. Jones notified
```

**Value:**
- Patient check-in from 10 minutes to 2 minutes
- Doctors don't need to manually write notes
- Zero missed follow-ups
- Front desk doesn't need to switch between multiple systems

---

### 3.3 Scenario 3: A Day at a Construction Site

**Background:** A commercial construction project with PM + superintendent + subcontractors

**Pain points with the traditional approach:**
```
- RFI emails everywhere, can't find who responded
- Daily reports are handwritten and incomplete
- Subcontractor coordination relies on phone calls with no records
- Drawings get updated but the field doesn't know
```

**The Vibe AI approach:**

```
Workspace: "Project-CenterPoint-Tower"

Spaces:
+-- #general (Overall project)
+-- #rfis (RFI management)
+-- #daily-logs (Daily reports)
+-- #safety (Safety)
+-- #subs (Subcontractor coordination)

Agents:
+-- @RFI (RFI management)
+-- @DailyLog (Daily reports)
+-- @DocSearch (Document search)
+-- @Safety (Safety management)

Devices:
+-- Bot-Trailer (Site trailer)
+-- Dot-Superintendent (Superintendent)

Scenario A: RFI handling
+-- [Superintendent] Steel beam connection details on the 5th floor are unclear on the drawings
+-- [@RFI] Created RFI-2024-0207: 5F Steel Beam Connection Details
|   Automatically:
|   - Attached relevant drawing excerpts
|   - Sent to structural engineer
|   - Set 72-hour deadline
+-- [Structural engineer] (24 hours later) Response: Use Detail A-5...
+-- [@RFI] RFI-2024-0207 closed, response archived
|   Notified: Superintendent, subcontractor
|
+-- Memory automatically distilled:
    +-- RFI: 5F Steel Connection
    +-- Resolution: Use Detail A-5
    +-- Affected Areas: 5F structural

Scenario B: Daily report
+-- [Bot-Trailer captures throughout the day]
|   7:30 - 45 workers on site
|   8:00 - Started 5F steel structure
|   12:00 - Lunch break
|   15:30 - Concrete pour completed
|   16:00 - Weather turning cloudy, early dismissal
+-- [@DailyLog] Today's report draft:
|   Weather: Cloudy, 45 F
|   Manpower: 45 workers
|   Work Completed:
|   - 5F steel structure 80%
|   - 4F concrete pour completed
|   Issues: Early dismissal due to weather
+-- [PM] Confirmed, send it
+-- [@DailyLog] Sent to owner and archived
|
+-- Memory automatically distilled:
    +-- Daily Log: 2024-02-07
    +-- Progress: 5F steel 80%, 4F concrete done
    +-- Weather Impact: 2 hours lost

Scenario C: Subcontractor coordination
+-- [PM] Can the electrical sub mobilize next week?
+-- [@SubCoordinator] Checking schedule...
|   Issue: 5F walls not yet complete, electrical can't start
|   Recommendation: Delay electrical mobilization to 02/15
+-- [PM] @Electrical-sub please confirm 02/15 mobilization
+-- [Electrical sub] Confirmed, mobilizing 02/15
+-- [@SubCoordinator] Schedule updated, relevant parties notified
```

**Value:**
- RFIs never get lost, automatically tracked
- Daily reports auto-generated
- Subcontractor coordination is recorded
- Ask "@DocSearch what spec for 5F steel beams?" anytime and get an instant answer

---

### 3.4 Scenario 4: Vibe Company (Dogfood)

**Background:** Vibe itself -- a 155-person hardware + software company making AI meeting devices

**Why dogfood matters most:**
```
- We use it ourselves, so we get the most authentic feedback
- The team understands the product and can provide better suggestions
- We have Sales, Marketing, Product, Engineering, and Support functions
- Real cross-departmental collaboration needs
```

**The Vibe AI approach:**

```
Workspace: "Vibe"

Spaces:
+-- #leadership (Leadership)
+-- #sales (Sales)
+-- #marketing (Marketing)
+-- #product (Product)
+-- #engineering (Engineering)
+-- #support (Support)
+-- #deals (Key deals)
+-- #releases (Product releases)

Agents:
+-- @CEO-Assistant (CEO assistant, cross-department view)
+-- @CRO (Sales data, pipeline)
+-- @PMM (Product marketing, competitive intel, positioning)
+-- @ProductBot (Product requirements, roadmap)
+-- @SupportBot (Customer issues, FAQ)
+-- @Researcher (Market research, competitive analysis)

Scenario A: Sales needs product information
+-- [Sales: Richard] Customer asking if Vibe Bot supports real-time translation?
+-- [@ProductBot] Checking roadmap...
|   Real-time translation is on the Q2 roadmap, expected April release
|   Currently supported: Post-meeting translation (15 languages)
|   Suggested talking points: Post-meeting translation currently available, real-time translation coming in Q2
+-- [Sales: Richard] Got it, I'll respond to the customer this way
|
+-- Memory automatically distilled:
    +-- Customer Question: Real-time translation
    +-- Current Status: Post-meeting translation available
    +-- Roadmap: Q2 for real-time
    +-- Sales Response: ...

Scenario B: Leadership weekly meeting
+-- [Thread: Leadership Weekly 02/07]
+-- [@CEO-Assistant] This week's summary:
|   Sales: Pipeline +$2M, 3 deals closed
|   Product: Bot v2.1 shipped, 12 bugs fixed
|   Marketing: CES recap published, 50K views
|   Support: Ticket volume -15%, CSAT 4.5
|   Key Issues:
|   - Enterprise deal stuck on security review
|   - Dot supply chain delay (2 weeks)
+-- [Charles] @CRO What's going on with the enterprise deal?
+-- [@CRO] Acme Corp ($500K) is in security review
|   Blocker: SOC2 certification issue
|   Action: Security team to provide docs by Wednesday
+-- [Charles] @Susie please follow up on Dot supply chain
|
+-- Memory automatically distilled:
    +-- Weekly Summary: 2024-02-07
    +-- Key Decisions: ...
    +-- Action Items: Security docs, Supply chain follow-up
    +-- Blockers: SOC2, Dot supply

Scenario C: Product <-> Support collaboration
+-- [Support: Jenny] Lots of customers recently asking about Bot connecting to Zoom
+-- [@SupportBot] Stats: 23 related tickets in the past 7 days
|   Main issue: Zoom connection drops
|   Affected version: v2.0.3
|   Known workaround: Restart Bot
+-- [Product: Sean] This is a bug, already fixed in v2.1
+-- [@SupportBot] FAQ updated, support team notified
|   Recommendation: Proactively reach out to affected customers about the upgrade
|
+-- Memory automatically distilled:
    +-- Issue: Zoom connection drops
    +-- Root Cause: Bug in v2.0.3
    +-- Fix: v2.1
    +-- Customer Communication: Proactive outreach planned
```

**Value:**
- Smooth cross-departmental information flow
- Leadership doesn't need to wait for weekly reports; ask an Agent anytime
- Tighter collaboration between support and product
- Knowledge isn't trapped in individuals' heads

---

### 3.5 Scenario 5: E-commerce Company

**Background:** A DTC e-commerce brand with a 20-person team

**Pain points with the traditional approach:**
```
- Customer service answers the same questions every day
- Inventory info is in the ERP; customer service doesn't have access
- Refund/return processes rely on memory
- Marketing doesn't know about customer feedback
```

**The Vibe AI approach:**

```
Workspace: "BrandX Store"

Spaces:
+-- #customer-service (Customer service)
+-- #orders (Orders)
+-- #inventory (Inventory)
+-- #marketing (Marketing)
+-- #product-feedback (Product feedback)

Agents:
+-- @CustomerBot (Customer issue handling)
+-- @OrderHelper (Order inquiries)
+-- @InventoryBot (Inventory queries)
+-- @FeedbackCollector (Customer feedback collection)
+-- @MarketingInsight (Marketing insights)

Scenario A: Customer inquiry
+-- [Customer via chat] When will my order arrive?
+-- [@OrderHelper] Looking up order #12345...
|   Status: Shipped
|   Carrier: FedEx
|   ETA: 2024-02-09
|   Reply to customer: Your order has shipped, estimated delivery February 9
+-- [Customer] Can I change the address?
+-- [@OrderHelper] Order has shipped, address cannot be changed
|   Suggestion: Contact FedEx to change delivery address
|   Provided FedEx tracking link
|
+-- Memory automatically distilled:
    +-- Customer Inquiry: Order tracking, address change
    +-- Resolution: Provided FedEx info
    +-- Feedback: Address change after shipment (common issue)

Scenario B: Inventory alert
+-- [@InventoryBot] Low inventory alert:
|   - Product A: 15 units left (avg. 10/day)
|   - Product B: 8 units left (avg. 5/day)
|   Recommendation: Restock within 3 days
+-- [Ops: Mike] Product A reorder placed, arriving next week
+-- [@InventoryBot] Recorded. Product B?
+-- [Ops: Mike] Product B sales paused, supplier issue
+-- [@InventoryBot] Product B marked as paused, customer service notified
|
+-- Memory automatically distilled:
    +-- Inventory Alert: 2024-02-07
    +-- Actions: Product A reordered, Product B paused
    +-- Supply Chain Issue: Product B supplier

Scenario C: Marketing insights
+-- [Marketing: Lisa] How's the customer feedback this week?
+-- [@FeedbackCollector] Customer feedback for the past 7 days:
|   Positive (65%):
|   - Fast shipping (23 mentions)
|   - Good product quality (18 mentions)
|   Negative (35%):
|   - Packaging too plain (12 mentions)
|   - Sizes run small (8 mentions)
|   Recommendation: Consider upgrading packaging, update sizing guide
+-- [Marketing: Lisa] Send the sizing feedback to product
+-- [@FeedbackCollector] Thread created in #product-feedback
```

**Value:**
- 3x improvement in customer service efficiency
- Early inventory issue warnings
- Automatic customer feedback summaries
- Cross-departmental information flow

---

### 3.6 Scenario 6: SaaS Company

**Background:** A B2B SaaS company, 50 people, selling project management software

**Pain points with the traditional approach:**
```
- Sales and CS information is siloed; customers repeat their issues
- Product doesn't know customers' real pain points
- Churn warnings rely on CS gut feelings
- New feature release notifications don't reach customers
```

**The Vibe AI approach:**

```
Workspace: "ProjectPro SaaS"

Spaces:
+-- #sales (Sales)
+-- #customer-success (Customer success)
+-- #product (Product)
+-- #engineering (Engineering)
+-- #accounts (Customer accounts, one Thread per key account)
+-- #releases (Releases)

Agents:
+-- @CRO (Sales data)
+-- @CSBot (Customer health)
+-- @FeatureRequest (Feature request collection)
+-- @ChurnAlert (Churn alerts)
+-- @ReleaseBot (Release notifications)

Scenario A: Customer health monitoring
+-- [@ChurnAlert] Churn risk alert:
|   Account: Acme Corp ($50K ARR)
|   Signals:
|   - Logins down 60% (past 30 days)
|   - 2 support tickets last week (feature dissatisfaction)
|   - Contract expires in 45 days
|   Recommendation: CSM should reach out immediately
+-- [CS: Sarah] I'll reach out. What's the prior communication history?
+-- [@CSBot] Acme Corp history:
|   - Signed last Q3, $50K/year
|   - Primary users: PM team (15 people)
|   - Last QBR: December, mentioned wanting Gantt charts
|   - Recent tickets: Export too slow, Gantt chart request
+-- [CS: Sarah] I've scheduled a call with them next week
+-- [@CSBot] Recorded. Reminder: Gantt chart is on Q1 roadmap
|
+-- Memory automatically distilled:
    +-- Churn Risk: Acme Corp
    +-- Intervention: CSM outreach scheduled
    +-- Key Issue: Gantt chart feature request

Scenario B: Feature request summary
+-- [Product: PM] What features do customers want most this quarter?
+-- [@FeatureRequest] Q1 feature request rankings:
|   1. Gantt chart (32 requests, 15 accounts)
|   2. Time tracking (28 requests, 12 accounts)
|   3. Resource management (20 requests, 8 accounts)
|
|   Weighted by ARR:
|   1. Gantt chart ($850K ARR related)
|   2. Resource management ($620K ARR related)
|   3. Time tracking ($450K ARR related)
+-- [Product: PM] Give me the list of customers related to Gantt chart
+-- [@FeatureRequest] Gantt chart related customers (15):
|   Top 5 by ARR:
|   - Acme Corp: $50K, at-risk
|   - BigTech Inc: $80K, healthy
|   - ...
|
+-- Memory automatically distilled:
    +-- Feature Requests Q1 Summary
    +-- Priority: Gantt chart
    +-- Related Accounts: ...

Scenario C: Release notification
+-- [Engineering] v3.2 released, includes Gantt chart
+-- [@ReleaseBot] New release detected, checking related customers...
|   Gantt chart related: 15 customers
|   Recommended notifications:
|   - Send release email
|   - CS individually contacts at-risk accounts
|   - Update changelog
+-- [CS Lead] Approved, execute
+-- [@ReleaseBot]
|   Release email sent (template + personalized)
|   Threads created for 3 at-risk accounts' CSMs
|   Changelog updated
```

**Value:**
- Churn warnings 30 days in advance
- Feature requests backed by data
- Sales/CS information sharing
- Releases automatically notify relevant customers

---

### 3.7 Scenario 7: Agency (Marketing/Design)

**Background:** A 15-person digital marketing agency serving 8 clients simultaneously

**Pain points with the traditional approach:**
```
- Client information scattered everywhere
- Project status requires asking the PM
- Deliverables are hard to find
- New hires take too long to ramp up
```

**The Vibe AI approach:**

```
Workspace: "Creative Agency"

Spaces:
+-- #client-acme (Client A)
+-- #client-bigcorp (Client B)
+-- #client-... (Other clients)
+-- #internal (Internal)
+-- #resources (Resource library)
+-- #new-business (New business development)

Agents:
+-- @PMBot (Project status)
+-- @ClientHelper (Client background)
+-- @AssetFinder (Find deliverables)
+-- @TimeTracker (Time tracking)
+-- @BrandGuide (Brand guidelines lookup)

Scenario A: Quick client background lookup
+-- [Designer: Amy] I'm taking over the Acme project, what are their brand colors?
+-- [@BrandGuide] Acme Corp brand guidelines:
|   Primary: #2563EB (Blue)
|   Secondary: #10B981 (Green)
|   Font: Inter
|   Logo: [link]
|   Brand Guidelines PDF: [link]
+-- [Designer: Amy] What projects have they done before?
+-- [@ClientHelper] Acme Corp project history:
|   - 2023 Q4: Website redesign (delivered)
|   - 2024 Q1: Social campaign (in progress)
|   - 2024 Q1: Video ads (planning)
|   Key contacts: John (Marketing Dir), Sarah (Brand)
|   Preferences: Clean and minimal style, minimal animations
|
+-- Memory automatically distilled:
    +-- Onboarding: Amy on Acme account
    +-- Context Shared: Brand guide, project history

Scenario B: Project status report
+-- [Account Manager] How's the Acme project going?
+-- [@PMBot] Acme project status:
|
|   Social Campaign:
|   +-- Creative: 90% (pending client review)
|   +-- Copy: 100%
|   +-- Media Plan: 100%
|   +-- Timeline: On track for 02/15 launch
|
|   Video Ads:
|   +-- Script: 60%
|   +-- Storyboard: 30%
|   +-- Timeline: 2 days behind (script revision)
|
|   Blockers:
|   - Video script needs client direction confirmation
+-- [Account Manager] I'll confirm with the client on the script
+-- [@PMBot] Recorded, follow-up reminder created
```

**Value:**
- Client context is never lost
- Project status at a glance
- New hires ramp up faster
- Assets are easy to find

---

### Scenario Comparison Summary

| Vertical | Core Value | Key Agents | Hardware Fit |
|----------|----------|-------------|----------|
| **Vibe (Dogfood)** | Cross-department collaboration, leadership visibility | @CEO-Assistant, @CRO, @PMM | Bot (meetings), Dot (notes) |
| **Sales Team** | Conversation as CRM, knowledge doesn't leave with people | @CRO, @DealHelper | Dot (client meetings) |
| **Medical Clinic** | Efficiency gains, compliance automation | @Scheduler, @Insurance | Bot (front desk), Dot (exam room) |
| **Construction** | Document management, coordination records | @RFI, @DailyLog, @Safety | Bot (job site) |
| **E-commerce** | Customer service efficiency, inventory alerts | @CustomerBot, @InventoryBot | -- |
| **SaaS** | Churn alerts, requirement aggregation | @ChurnAlert, @FeatureRequest | -- |
| **Agency** | Client context, project tracking | @PMBot, @ClientHelper | -- |

---

## 4. System Design

### 4.1 High-Level Architecture

```
+---------------------------------------------------------------------------+
|                              CAPTURE LAYER                                 |
|                          (Data capture entry points)                       |
|                                                                            |
|  +---------+  +---------+  +---------+  +---------+  +---------+          |
|  |Vibe Bot |  |Vibe Dot |  |  Slack  |  |  Web UI |  |  API    |          |
|  +----+----+  +----+----+  +----+----+  +----+----+  +----+----+          |
+-------+------------+------------+------------+------------+----------------+
                                |
                                v
+---------------------------------------------------------------------------+
|                              API LAYER                                     |
|                          (Unified entry point)                             |
|                                                                            |
|  +-------------+  +-------------+  +-------------+  +-------------+       |
|  |    Auth     |  |   Routing   |  | Rate Limit  |  |  Validation |       |
|  +-------------+  +-------------+  +-------------+  +-------------+       |
+--------------------------------------+------------------------------------+
                                |
                                v
+---------------------------------------------------------------------------+
|                           COORDINATION LAYER                               |
|                        (Coordination and scheduling)                       |
|                                                                            |
|  +------------------------------------------------------------------+    |
|  |                         Orchestrator                               |    |
|  |                                                                    |    |
|  |  +-------------+  +-------------+  +-------------+                |    |
|  |  |  Message    |  |   Agent     |  |   Event     |                |    |
|  |  |  Router     |  |  Scheduler  |  |  Dispatcher |                |    |
|  |  +-------------+  +-------------+  +-------------+                |    |
|  +------------------------------------------------------------------+    |
+--------------------------------------+------------------------------------+
                                |
         +---------------------+---------------------+
         v                     v                     v
+-----------------+  +-----------------+  +-----------------+
|  THREAD ENGINE  |  |  AGENT RUNTIME  |  |  DEVICE SERVICE |
|                 |  |                 |  |                 |
| - Space mgmt   |  | - Agent         |  | - Device        |
| - Thread mgmt  |  |   containers    |  |   registration  |
| - Feed sync    |  | - Task exec     |  | - Status        |
| - Branch/Merge |  | - Concurrency   |  |   monitoring    |
|                 |  | - Tool calls    |  | - Data capture  |
|                 |  |                 |  | - Capability    |
|                 |  |                 |  |   management    |
+--------+-------+  +--------+-------+  +--------+--------+
         |                    |                    |
         +--------------------+--------------------+
                              |
                              v
+---------------------------------------------------------------------------+
|                            MEMORY LAYER                                    |
|                         (Core data layer)                                  |
|                                                                            |
|  +------------------------------------------------------------------+    |
|  |                         Memory System                              |    |
|  |                                                                    |    |
|  |  +-------------+  +-------------+  +-------------+  +-----------+ |    |
|  |  |  Storage    |  |   Vector    |  |   Search    |  | Permission| |    |
|  |  |  Engine     |  |   Index     |  |   Engine    |  |  Control  | |    |
|  |  +-------------+  +-------------+  +-------------+  +-----------+ |    |
|  |                                                                    |    |
|  |  Memory Hierarchy:                                                 |    |
|  |  +---------------------------------------------------------------+|    |
|  |  | Workspace Memory (Global)                                      ||    |
|  |  |   +-- Space Memory (Scoped)                                    ||    |
|  |  |       +-- Thread Memory (Conversation-level)                   ||    |
|  |  |           +-- Personal Memory (Private)                        ||    |
|  |  +---------------------------------------------------------------+|    |
|  +------------------------------------------------------------------+    |
+--------------------------------------+------------------------------------+
                                |
         +---------------------+---------------------+
         v                     v                     v
+-----------------+  +-----------------+  +-----------------+
|   CONFIG SVC    |  |     IAM SVC     |  |   INTEGRATION   |
|                 |  |                 |  |                 |
| - 4-layer       |  | - Auth          |  | - EHR           |
|   config        |  | - Permissions   |  |   integration   |
| - Templates     |  | - Workspace     |  | - CRM           |
| - Admin Console |  |                 |  |   integration   |
|                 |  |                 |  | - PM             |
|                 |  |                 |  |   integration   |
+-----------------+  +-----------------+  +-----------------+
```

### 4.2 Data Flow Details

#### Flow 1: Sending a Message

```
User sends message "I need to schedule a meeting"
    |
    v
+-------------------------------------------------------------+
| 1. API Gateway                                               |
|    - Validate token                                          |
|    - Confirm workspace/space/thread permissions              |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 2. Thread Engine                                             |
|    - Write message to Feed                                   |
|    - Broadcast to Thread participants (Realtime)             |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 3. Orchestrator                                              |
|    - Detect whether Agent response is needed                 |
|    - Detect @mention or intent                               |
|    - If needed -> route to appropriate Agent                 |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 4. Agent Runtime (@Scheduler)                                |
|    - Load Agent context (SOUL, Memory access)                |
|    - Query Memory: user's calendar, preferences              |
|    - Call LLM to generate response                           |
|    - May call tools: check calendar availability             |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 5. Thread Engine                                             |
|    - Write Agent response to Feed                            |
|    - Broadcast to participants                               |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 6. Memory System (Async)                                     |
|    - Analyze conversation, extract Memory Items              |
|    - Generate embeddings                                     |
|    - Store and index                                         |
+-------------------------------------------------------------+
```

#### Flow 2: Device Data Capture

```
Vibe Bot starts recording a meeting
    |
    v
+-------------------------------------------------------------+
| 1. Device Service                                            |
|    - Receive audio stream                                    |
|    - Update device status: recording                         |
|    - Create capture session                                  |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 2. Processing Pipeline (Async)                               |
|    - Transcription: audio -> text                            |
|    - Speaker Diarization: identify who said what             |
|    - Entity Extraction: extract names, companies, topics     |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 3. Thread Engine                                             |
|    - Create or associate with Thread                         |
|    - Write transcript to Feed (optional)                     |
|    - Generate meeting summary                                |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 4. Memory System                                             |
|    - Store full transcript (L3)                              |
|    - Generate structured summary (L2)                        |
|    - Generate one-line summary (L1)                          |
|    - Extract decisions, action items                         |
|    - Generate embeddings, index                              |
+-------------------------------------------------------------+
```

#### Flow 3: Memory Query

```
User asks "@CRO what was discussed in last week's meeting with Acme"
    |
    v
+-------------------------------------------------------------+
| 1. Orchestrator                                              |
|    - Detect @CRO mention                                     |
|    - Route to @CRO Agent                                     |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 2. Agent Runtime (@CRO)                                      |
|    - Parse query: company=Acme, time=last week, type=meeting |
|    - Call Memory Search                                      |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 3. Memory System                                             |
|    - Permission check: what Memory the user can access       |
|    - Zoom Level: how much detail the user can see            |
|    - Semantic search: query embedding -> similar Memory      |
|    - Filter: time=last week, entity contains "Acme"         |
|    - Return matching Memory Items                            |
+-------------------------------------------------------------+
    |
    v
+-------------------------------------------------------------+
| 4. Agent Runtime (@CRO)                                      |
|    - Synthesize answer from Memory                           |
|    - Format output                                           |
|    - Return to user                                          |
+-------------------------------------------------------------+
```

### 4.3 Module Responsibilities

| Module | Core Responsibility | Key Interface |
|------|----------|----------|
| **API Gateway** | Unified entry, authentication, routing | REST/WebSocket |
| **Orchestrator** | Message routing, Agent scheduling | Internal RPC |
| **Thread Engine** | Space/Thread/Feed management | Thread CRUD, Feed Sync |
| **Agent Runtime** | Agent lifecycle, task execution | Task API |
| **Device Service** | Device registration, status, data capture | Device API, Stream |
| **Memory System** | Storage, indexing, retrieval, permissions | Memory API |
| **Config Service** | Configuration management, template system | Config API |
| **IAM Service** | Authentication, authorization, multi-tenancy | Auth API |
| **Integration Hub** | External system connections | System Adapters |

---

## 5. Memory System Deep Dive

### 5.1 Why Memory is the Core

```
+---------------------------------------------------------------------------+
| Memory is the organization's knowledge asset                               |
|                                                                            |
| Unlike other assets that depreciate, Memory becomes more valuable          |
| over time:                                                                 |
|                                                                            |
|   Day 1: Empty                                                             |
|   Month 1: 100 Memory Items                                               |
|   Month 6: 1000 Memory Items -> Agents become smarter                     |
|   Year 1: 5000 Memory Items -> Organizational knowledge base              |
|   Year 2: 10000+ -> Historical context for almost any question            |
|                                                                            |
| This is the data flywheel:                                                 |
|                                                                            |
|   More usage -> More Memory -> More useful Agents -> More usage -> ...     |
|                                                                            |
+---------------------------------------------------------------------------+
```

### 5.2 Memory Item Structure

```typescript
interface MemoryItem {
  id: string;
  workspaceId: string;
  spaceId?: string;
  threadId?: string;

  // Content (multi-level zoom)
  content: {
    l1: string;  // Executive: one sentence
    l2: string;  // Manager: structured summary
    l3: string;  // Full: complete content
  };

  // Type
  type: MemoryType;

  // Source
  source: {
    type: "message" | "device" | "import" | "agent";
    ref: string;  // Source ID
    capturedAt: Date;
  };

  // Entities (for search)
  entities: {
    people: string[];
    companies: string[];
    topics: string[];
    dates: string[];
  };

  // Vectors (semantic search)
  embeddings: {
    l1: number[];
    l2: number[];
    l3: number[];
  };

  // Permissions
  permissions: {
    visibility: "workspace" | "space" | "thread" | "personal";
    allowedRoles?: string[];
  };

  // Metadata
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

type MemoryType =
  | "decision"      // Decision
  | "action_item"   // Action item
  | "meeting_note"  // Meeting note
  | "context"       // Background information
  | "document"      // Document
  | "contact"       // Contact
  | "deal"          // Deal
  | "custom";       // Custom
```

### 5.3 Zoom Level Details

```
Original data: 2-hour meeting recording

+---------------------------------------------------------------------------+
| L3 (Full) - IC / Direct participants                                       |
|                                                                            |
| Full transcript (~10,000 words)                                            |
| Includes every utterance, speaker, timestamps                              |
| Suitable for: People who need specific details                             |
+---------------------------------------------------------------------------+
                              |
                              v (compressed)
+---------------------------------------------------------------------------+
| L2 (Manager) - Managers                                                    |
|                                                                            |
| Structured summary (~500 words)                                            |
| - Participants: Alice, Bob, Charlie                                        |
| - Topic: Q1 pricing strategy                                              |
| - Key discussion points:                                                   |
|   - Option A: 10% price increase, risk is...                              |
|   - Option B: Keep current pricing, benefit is...                          |
| - Decision: Chose Option A                                                 |
| - Action Items:                                                            |
|   - Alice: Update price sheet by 02/10                                     |
|   - Bob: Notify key customers by 02/12                                     |
|                                                                            |
| Suitable for: Managers who need context without details                    |
+---------------------------------------------------------------------------+
                              |
                              v (compressed)
+---------------------------------------------------------------------------+
| L1 (Executive) - Executives                                                |
|                                                                            |
| One paragraph (~100 words)                                                 |
| "Q1 pricing strategy meeting decided on a 10% price increase,             |
|  primarily due to rising costs. Alice is responsible for execution,        |
|  expected completion in 2 weeks. 2 key accounts need individual outreach." |
|                                                                            |
| Suitable for: Executives who only need conclusions and impact              |
+---------------------------------------------------------------------------+
```

---

## 6. Agent System Deep Dive

### 6.1 What is an Agent

An Agent is not a chatbot; it is an **AI Team Member**:

```
+---------------------------------------------------------------------------+
| Chatbot (Traditional)        |  Agent (Vibe AI)                            |
+------------------------------+--------------------------------------------+
| Passive response             |  Can proactively initiate                   |
| Stateless                    |  Has persistent identity and memory         |
| General capabilities         |  Specialized responsibilities               |
| Tool                         |  Team member                                |
| Use and discard              |  Ongoing participation                      |
+------------------------------+--------------------------------------------+
```

### 6.2 Agent Types

```
+---------------------------------------------------------------------------+
|                      Agent Types                                           |
|                                                                            |
|  +-----------------+                                                       |
|  |  Personal Agent |  One per user                                         |
|  |                 |  Private Memory                                       |
|  |  "My assistant" |  Personalized                                         |
|  +-----------------+                                                       |
|                                                                            |
|  +-----------------+                                                       |
|  |   Role Agent    |  Organizational role                                  |
|  |                 |  e.g. @CRO, @Scheduler                               |
|  |  "Company role" |  Shared Memory                                        |
|  +-----------------+                                                       |
|                                                                            |
|  +-----------------+                                                       |
|  |  Worker Agent   |  Temporary task-based                                 |
|  |                 |  Destroyed on completion                              |
|  |  "Temp worker"  |  e.g. long-running research tasks                    |
|  +-----------------+                                                       |
|                                                                            |
+---------------------------------------------------------------------------+
```

### 6.3 Agent Definition (SOUL.md)

```markdown
# @Scheduler Agent

## Identity
You are the clinic's appointment assistant. You help patients and staff manage appointments.

## Responsibilities
- Schedule new appointments
- Modify/cancel appointments
- Send reminders
- Check doctor availability
- Handle conflicts

## Knowledge Scope
You can access:
- Doctor schedules (read/write)
- Patient appointment history (read)
- Clinic policies (appointment duration, cancellation rules, etc.)

You cannot access:
- Patient medical records
- Financial information

## Constraints
- No double-booking
- Respect doctor preference settings
- Maintain buffer time between appointments
- Follow HIPAA guidelines

## Communication Style
- Professional but friendly
- Offer options rather than demands
- Confirm key information

## Tools Available
- calendar.check_availability
- calendar.create_appointment
- calendar.cancel_appointment
- notification.send_reminder
```

---

## 7. Configuration System Deep Dive

### 7.1 4-Layer Configuration

```
+---------------------------------------------------------------------------+
| Layer 1: Platform                                                          |
| Defined by Vibe, immutable                                                 |
| e.g. Maximum token count, security constraints                             |
+------------------------------------------------------------------------- -+
| Layer 2: Template                                                          |
| Industry template, e.g. medical-clinic                                     |
| Can lock certain configurations                                            |
+---------------------------------------------------------------------------+
| Layer 3: Workspace                                                         |
| Admin configuration, e.g. Downtown Clinic                                  |
| Customizable within Template-allowed range                                 |
+---------------------------------------------------------------------------+
| Layer 4: User                                                              |
| Personal preferences                                                       |
| Customizable within Admin-allowed range                                    |
+---------------------------------------------------------------------------+
```

### 7.2 Configuration Example

```yaml
# Template: medical-clinic
vertical:
  name: medical-clinic

agents:
  available: ["@Scheduler", "@Insurance", "@FollowUp"]

compliance:
  hipaa: true  # Locked, cannot be disabled

workflows:
  check_in:
    locked: true  # Cannot be modified

# Workspace: Downtown Clinic
workspace:
  template: medical-clinic

agents:
  enabled: ["@Scheduler", "@Insurance"]  # Which ones to enable
  config:
    "@Scheduler":
      working_hours: "08:00-18:00"

# User: Dr. Smith
user:
  role: physician
  preferences:
    theme: dark
    notifications: email
```

---

## 8. Design Decisions (Confirmed)

| Question | Decision | Notes |
|------|------|------|
| **Feed vs Channel** | No Channel concept | Feed is a component within Thread |
| **Thread creation** | Hybrid | Partially automatic, partially manual |
| **Agent proactivity** | Depends | Determined by configuration and scenario |
| **Memory auto-extraction** | No manual confirmation required | Auto-extracted, users can edit afterward |
| **Branch/Merge** | Required for V1 | Core differentiating feature |
| **Device requirement** | Hardware not required | Pure software works, hardware is an enhancement |
| **Pricing model** | To be discussed later | -- |

---

## 9. Areas Requiring Further Design

1. Specific logic for hybrid Thread creation
2. Trigger conditions and configuration for Agent proactivity
3. Rules and types for automatic Memory extraction
4. UI/UX design for Branch/Merge
5. Detailed Agent definitions per vertical

---

*Last updated: 2026-02-07*
*Status: Draft v2 - decisions confirmed*
