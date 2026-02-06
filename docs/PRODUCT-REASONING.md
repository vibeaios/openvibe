# Vibe AI Workspace - Product Reasoning

> The thought process from vision to product design

---

## Starting Point: What I Want

### The Initial Vision

```
The scenario I imagined:

A group of Agents and humans working together in one space.

Not the "ask ChatGPT a question" model,
but Agents that are truly members of the team,
with their own responsibilities, persistent context,
able to act proactively and collaborate with humans.

Like Slack where there are people and bots,
but the bots don't just passively respond --
they participate like colleagues.
```

### This raises the first question

**Q: If Agents and humans need to collaborate, what should the experience look like?**

---

## Derivation 1: Thread Experience

### Thought Process

```
Existing experiences:
  - Slack/Discord: Channels are message streams, linear
  - ChatGPT: Solo conversations, no other participants
  - Notion: Documents, not conversations

What I want:
  - Multiple humans + multiple Agents in the same conversation
  - Conversations centered around a topic
  - Conversations that can branch for exploration, then merge
  - Conclusions from conversations that persist

Isn't this just a Thread?
And a Git-like Thread at that.
```

### Design Decision

```
Thread = The fundamental unit of collaboration

Characteristics:
  1. Threads have a clear topic/purpose
  2. Both humans and Agents can participate in Threads
  3. Threads can branch -- explore different directions
  4. Branches can merge -- consolidate conclusions
  5. Important Thread content distills into Memory

Analogy: Git repo for conversations
```

### To Be Validated

```
? Will Branch/Merge be too complex for average users?
   -> Need user testing
   -> May need simplified UI that hides complexity

? When should Threads be created? Automatically or manually?
   -> Initial decision: Hybrid
   -> Some scenarios automatic (e.g. device-captured meetings)
   -> Some manual (user-initiated)
```

---

## Derivation 2: Agent as Team Member

### Thought Process

```
If Agents should act like colleagues:

What makes a colleague:
  - Has a name and identity
  - Has specific responsibilities
  - Has persistent memory (knows what happened before)
  - Can be @-mentioned
  - Sometimes speaks up proactively

This means Agents need:
  - Persistent identity (not ephemeral)
  - Clearly defined responsibilities
  - Access to organizational Memory
  - Ability to be mentioned
  - Ability to act proactively
```

### Design Decision

```
Agent types:

1. Role Agent
   - Represents an organizational role
   - e.g. @CRO, @Scheduler, @PMM
   - Exists permanently
   - Can be @-invoked by anyone

2. Personal Agent
   - One per user
   - Like "my assistant"
   - Serves only the individual
   - Can access personal + public Memory

3. Worker Agent
   - Executes one-off tasks
   - Destroyed on completion
   - e.g. running a long-duration research task in the background
```

### This raises the next question

**Q: Everyone should have an Agent -- how do we implement this?**

---

## Derivation 3: One OpenClaw Per Person

### Thought Process

```
I've been using OpenClaw, and the experience is great.

OpenClaw's characteristics:
  - One Agent per user
  - Agent has persistent Memory
  - Agent has Skills
  - Agent has personality (SOUL.md)

If every Workspace member had an OpenClaw-like Agent:
  - Personal assistant
  - Understands my preferences
  - Can handle tasks for me
  - Can also collaborate with other Agents

The question is: How do we implement "one OpenClaw per person" in the cloud?
```

### Design Decision

```
Agent Runtime = Containerized OpenClaw

Implementation:
  1. Each Agent runs in an isolated container
  2. Container runs the OpenClaw architecture internally
  3. Has its own SOUL.md
  4. Has its own Skills
  5. Mounts shared Team Memory (read-only)
  6. Has its own Private Memory (read-write)

Benefits:
  - Isolation: One Agent crashing doesn't affect others
  - Security: Resources and permissions are controllable
  - Scaling: Can scale horizontally
```

### To Be Validated

```
? Will one container per user be too expensive?
   -> May need "lazy startup"
   -> Only start when user is active
   -> Hibernate when idle

? How do Agents collaborate with each other?
   -> Route through Orchestrator
   -> Pass information via shared Memory
   -> Direct invocation (like function calls) might be too complex
```

---

## Derivation 4: Memory Needs Granular Permissions

### Thought Process

```
If multiple Agents and humans share Memory,
permissions become critical.

Scenario 1: CEO vs. regular employee
  - CEO should see everything
  - Regular employees should only see their department's data

Scenario 2: Sensitive information
  - Salary and HR info shouldn't be visible to everyone
  - But Threads discussing these topics may need to exist

Scenario 3: Information density
  - CEO doesn't need to read every word of a 2-hour meeting
  - Only needs key decisions
  - But participants may need the details

This means:
  1. Memory needs hierarchy (Workspace -> Space -> Thread)
  2. Memory needs role-based permissions
  3. Memory needs multiple "detail levels"
```

### Design Decision

```
Memory permission design:

1. Hierarchical permissions
   +-------------------------------------------+
   | Workspace Memory (Visible to all members) |
   |   +-- Space Memory (Visible to Space members) |
   |       +-- Thread Memory (Visible to participants) |
   |           +-- Personal Memory (Only self)  |
   +-------------------------------------------+

2. Zoom Level (Detail level)
   - L1: Executive (one sentence)
   - L2: Manager (structured summary)
   - L3: Full (complete content)

   Role determines which level you can see

3. Auto-extraction
   - Memory is automatically extracted from conversations
   - No manual confirmation needed
   - Users can edit after the fact
```

### To Be Validated

```
? Are 3 Zoom Levels enough?
   -> Start with 3
   -> Add more if needed

? Will auto-extraction accuracy be acceptable?
   -> Need testing
   -> May need to train Agents on "what's worth extracting"
```

---

## Derivation 5: Threads Without Channels

### Thought Process

```
Initially I thought of the Slack model:
  Workspace -> Channel -> Message

But on further thought:

Channel problems:
  - A Channel is a container, not a topic
  - Multiple topics get mixed in one Channel
  - Historical messages are hard to trace
  - No concept of branching

If using Threads:
  - Thread = one topic
  - More focused
  - Can branch
  - Can merge
  - Can have status (open/resolved)

Do we still need Channels?
  -> No
  -> Spaces for area segmentation (departments/projects)
  -> Threads for topic segmentation
```

### Design Decision

```
Hierarchy becomes:

Workspace -> Space -> Thread -> Feed

- Space: A work area (e.g. #sales, #product)
- Thread: A topic/task
- Feed: Message stream within a Thread

No Channel layer.

Benefits:
  - Simpler concepts
  - Every conversation has a clear topic
  - Enforces better organizational habits
```

---

## Derivation 6: Adapting Across Industries

### Thought Process

```
Vibe needs to sell to different industries:
  - Medical clinics
  - Construction companies
  - SaaS companies
  - Law firms
  - ...

Each industry needs:
  - Different Agents
  - Different workflows
  - Different compliance requirements
  - Different external system integrations

But the underlying capabilities are the same:
  - Thread/Memory/Agent architecture stays the same
  - Only the configuration differs

Conclusion: Configuration over Code
  - Don't change code
  - Adapt to different industries through configuration packages
```

### Design Decision

```
4-layer configuration system:

Layer 1: Platform (We define)
  -> Base constraints, e.g. max token count
  -> Cannot be changed

Layer 2: Template (Industry template)
  -> e.g. medical-clinic, construction
  -> Defines industry-specific Agents, Workflows
  -> Some parts can be locked (e.g. HIPAA compliance)

Layer 3: Workspace (Admin configuration)
  -> Customer Admin configuration
  -> Customizable within Template-allowed range

Layer 4: User (Personal preferences)
  -> User personal settings
  -> Within Admin-allowed range

This way:
  - New industry = new Template, no code changes
  - Compliance requirements can be locked
  - Customers can customize
```

---

## Derivation 7: Devices Are More Than Data Sources

### Thought Process

```
Vibe has hardware: Bot, Dot, Board

Traditional approach:
  Device records -> Data enters system -> Done

But if devices were smarter:
  - Devices have identity
  - Devices can be assigned to a room/person
  - Devices have status (online/offline/recording)
  - Devices can receive commands

This is Device as Entity

Devices aren't just data sources,
they're participants in the system.
```

### Design Decision

```
Device = First-class Entity

Properties:
  - id, name, serial
  - type (bot/dot/board)
  - capabilities (what it can do)
  - status (online/offline/healthy)
  - assignedTo (who it's assigned to)
  - location (where it is)

Benefits:
  - Devices can be managed
  - Data sources can be tracked
  - Remote control is possible
  - Lays the foundation for more complex device interactions in the future
```

---

## Derivation 8: Hardware Is Not Required

### Thought Process

```
Vibe's hardware is an advantage, but shouldn't be a barrier.

If a customer doesn't have Vibe hardware:
  - Can they still use it? -> They should be able to
  - Will the experience be worse? -> Slightly reduced, but core value remains

What is the core value?
  - Human-Agent collaboration
  - Organizational Memory
  - Git-like Threads

None of these depend on hardware.

Hardware provides:
  - Additional data entry points
  - Richer capture (meeting recordings)
  - Enhancement, not requirement
```

### Design Decision

```
Hardware = Optional Enhancement

Without hardware:
  - Use via Web UI
  - Use via Slack integration
  - Manual content input
  - All core features work

With hardware:
  - Automatic meeting capture
  - More passive data collection
  - Richer context
```

---

## Derivation 9: Dogfood Is Most Important

### Thought Process

```
How do we validate these design decisions?

The best way: Use it ourselves

Vibe the company is itself a customer:
  - 155 people
  - Has Sales, Marketing, Product, Engineering, Support
  - Has real cross-departmental collaboration needs
  - Can provide the most authentic feedback

Dogfood benefits:
  - Fast iteration
  - Real scenarios
  - Team understands the product
  - Problems discovered earlier
```

### Design Decision

```
Vibe (Dogfood) is the P0 Vertical

Priority:
  1. Vibe internal use (Dogfood)
  2. 1-2 external customers (Alpha)
  3. More customers (Beta)

Why dogfood first:
  - We understand our own needs best
  - Fastest iteration
  - Can polish the product before giving it to external users
```

---

## Summary: Product Design

From the above derivations, the product design is as follows:

### Core Concepts

```
+---------------------------------------------------------------------------+
| Workspace (Organization)                                                   |
|                                                                            |
|   +-- Space (Work area)                                                    |
|   |       +-- Thread (Topic) <- Git-like                                   |
|   |               +-- Feed (Message stream)                                |
|   |               +-- Branches                                             |
|   |               +-- Memory Items (Distilled knowledge)                   |
|   |                                                                        |
|   +-- Agents                                                               |
|   |       +-- Role Agents (@CRO, @Scheduler)                              |
|   |       +-- Personal Agents (One per person)                             |
|   |       +-- Worker Agents (Temporary)                                    |
|   |                                                                        |
|   +-- Members (Humans)                                                     |
|   |                                                                        |
|   +-- Devices (Optional)                                                   |
|   |       +-- Bot                                                          |
|   |       +-- Dot                                                          |
|   |                                                                        |
|   +-- Memory                                                               |
|           +-- Workspace Memory                                             |
|           +-- Space Memory                                                 |
|           +-- Thread Memory                                                |
|           +-- Personal Memory                                              |
+---------------------------------------------------------------------------+
```

### Key Design Decisions

| Decision | Choice | Rationale |
|------|------|------|
| Collaboration unit | Thread (not Channel) | More focused, supports branching |
| Thread model | Git-like | Supports exploration and merging |
| Agent implementation | Containerized OpenClaw | Isolation, scalable |
| Memory permissions | Hierarchical + Zoom Level | Granular control |
| Industry adaptation | 4-layer configuration | No code changes needed |
| Device positioning | First-class Entity | Manageable |
| Hardware dependency | Optional enhancement | Lowers the barrier to entry |

### Assumptions To Be Validated

| Assumption | Validation Method | Risk |
|------|----------|------|
| Users can understand Branch/Merge | User testing | May need simplification |
| One Agent per person is cost-viable | Technical testing | May need lazy loading |
| 3 Zoom Levels are sufficient | Dogfood | May need adjustment |
| Auto-extracting Memory is accurate | Dogfood | May need iteration |
| Users can accept no Channels | User testing | May need explanation |

---

## From Product to System

Based on the product design above, the system architecture is as follows:

```
+---------------------------------------------------------------------------+
| Product Requirements      |  System Design                                |
+---------------------------+-----------------------------------------------+
| Multi-entry (Web/Slack/   |  -> Capture Layer                             |
| Bot/Dot)                  |     Unified data entry                        |
+---------------------------+-----------------------------------------------+
| Human-Agent routing       |  -> Coordination Layer                        |
|                           |     Orchestrator                              |
+---------------------------+-----------------------------------------------+
| Git-like Thread           |  -> Thread Engine                             |
|                           |     Branch/Merge/Feed                         |
+---------------------------+-----------------------------------------------+
| One Agent per person      |  -> Agent Runtime                             |
| Containerized OpenClaw    |     Container Pool                            |
+---------------------------+-----------------------------------------------+
| Device as Entity          |  -> Device Service                            |
|                           |     Registration/Status/Capture               |
+---------------------------+-----------------------------------------------+
| Memory + Permissions      |  -> Memory Layer                              |
| + Zoom Level              |     Storage/Vector/Permission                 |
+---------------------------+-----------------------------------------------+
| 4-layer configuration     |  -> Config Service                            |
|                           |     Template/Workspace/User                   |
+---------------------------+-----------------------------------------------+
| External integrations     |  -> Integration Service                       |
|                           |     EHR/CRM/PM adapters                       |
+---------------------------+-----------------------------------------------+
```

---

## Derivation 10: How Admins Configure Workspaces

### Thought Process

```
Traditional configuration approach:
  - Give Admin a bunch of forms
  - Check features
  - Fill in parameters
  - Tedious and error-prone

But what the Admin is thinking is:
  "We're a clinic,
   the front desk needs to check in patients,
   doctors need auto-generated notes,
   I need to see daily appointment stats..."

This is a natural language description of workflows.

What if:
  Admin describes via prompt -> AI generates Workspace configuration

Isn't this Generative UI?
```

### Design Decision

```
Admin Console = Prompt -> Workspace Experience

Flow:
  1. Admin describes needs in natural language
     "We're a clinic, 5 doctors, 3 front desk staff..."
     "Front desk needs to check in patients"
     "Auto-generate notes after doctor consultations"

  2. AI understands needs and generates configuration proposal
     - Recommended Agents: @Scheduler, @NoteWriter
     - Recommended Spaces: #front-desk, #providers
     - Recommended workflows: check-in flow
     - Permission recommendations: Front desk L2, Doctors L3

  3. Admin previews and adjusts
     - Visual preview of the experience
     - Manual fine-tuning available
     - Can continue iterating via prompt

  4. Apply configuration
     - Generate final configuration
     - Deploy to Workspace
```

### Going Further

```
Not just initial configuration, but continuous iteration:

Admin: "Patients have been complaining about long wait times recently"
AI: "Analysis shows the check-in flow can be optimized. Recommendation..."
     -> Generate optimization proposal
     -> Admin confirms and applies

Admin: "Add an insurance pre-authorization feature"
AI: "Recommend adding @Insurance Agent with the following configuration..."
     -> Generate new Agent configuration
     -> Preview the effect
     -> Deploy

This way:
  - Admin doesn't need to understand technical details
  - Describes needs in business language
  - AI translates into system configuration
```

### To Be Validated

```
? How accurate is AI-generated configuration?
   -> Need extensive testing
   -> May need Admin confirmation for critical settings

? How to handle complex customizations?
   -> Provide "advanced mode" for manual editing
   -> Prompt + manual hybrid

? How to assess the impact of configuration changes?
   -> Need preview/sandbox
   -> May need gradual rollout
```

### Console Interface Concept

```
+---------------------------------------------------------------------------+
|  Admin Console                                              [Preview]      |
+---------------------------------------------------------------------------+
|                                                                            |
|  +--------------------------------------------------------------+        |
|  | Describe your workspace needs...                              |        |
|  |                                                               |        |
|  | "We're a clinic with 5 doctors and 3 front desk staff.        |        |
|  |  Patients need to check in and have insurance verified.       |        |
|  |  Doctors need auto-generated notes after consultations.       |        |
|  |  Every morning I want to see today's appointment overview."   |        |
|  |                                                          [->] |        |
|  +--------------------------------------------------------------+        |
|                                                                            |
|  +--------------------------------------------------------------+        |
|  | AI Generated Configuration:                                    |        |
|  |                                                               |        |
|  | Spaces:                                                       |        |
|  |   #front-desk (Front desk operations)                         |        |
|  |   #providers (Doctors)                                        |        |
|  |   #daily-briefing (Daily briefing)                            |        |
|  |                                                               |        |
|  | Agents:                                                       |        |
|  |   @Scheduler (Appointment management)                         |        |
|  |   @Insurance (Insurance verification)                         |        |
|  |   @NoteWriter (Note generation)                               |        |
|  |   @DailyBrief (Daily briefing)                                |        |
|  |                                                               |        |
|  | Workflows:                                                    |        |
|  |   Patient Check-in                                            |        |
|  |   Post-visit Note                                             |        |
|  |                                                               |        |
|  | Roles:                                                        |        |
|  |   Physician (L3, all agents)                                  |        |
|  |   Front-desk (L2, @Scheduler, @Insurance)                    |        |
|  |                                                               |        |
|  |                          [Edit Details] [Apply Config]         |        |
|  +--------------------------------------------------------------+        |
|                                                                            |
+---------------------------------------------------------------------------+
```

---

## Derivation 11: Relationship Between Templates and Generative UI

### Thought Process

```
Two configuration approaches:

1. Template (Predefined)
   - We predefine a medical-clinic template
   - Admin selects template, makes tweaks
   - Standardized, stable

2. Generative UI
   - Admin describes via prompt
   - AI generates configuration
   - Flexible, personalized

These two are not mutually exclusive:

Template = Starting point
Generative UI = Iterate from the starting point

Flow:
  1. Admin selects "Medical Clinic" template
  2. Template provides base configuration
  3. Admin describes special needs via prompt
  4. AI generates adjustments on top of template
  5. Final configuration = Template + Customization
```

### Design Decision

```
Template + Generative UI combined

+---------------------------------------------------------------------------+
| 1. Select Template                                                         |
|    "Medical Clinic"                                                        |
|                                                                            |
|    -> Get standard configuration:                                          |
|      Agents: @Scheduler, @Insurance, @FollowUp                            |
|      Workflows: check-in, prescription                                     |
|      Compliance: HIPAA                                                     |
+---------------------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------------------+
| 2. Prompt customization                                                    |
|    "We specialize in pediatrics, we need..."                               |
|                                                                            |
|    -> AI adjusts on top of template:                                       |
|      + @PediatricsHelper                                                   |
|      + Kid-friendly check-in flow                                          |
|      + Vaccine reminder workflow                                           |
+---------------------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------------------+
| 3. Final configuration                                                     |
|    = Medical Clinic Template                                               |
|    + Pediatrics Customization                                              |
|    + Admin manual fine-tuning                                              |
+---------------------------------------------------------------------------+
```

---

## Complete Derivation Summary

### Path From Vision to Design

```
+---------------------------------------------------------------------------+
|                                                                            |
|  Starting point: "A group of Agents and humans working together"           |
|                                                                            |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 1: What should the experience be? -> Thread (Git-like)         |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 2: Agent as colleague -> Identity, responsibilities, Memory    |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 3: One Agent per person -> Containerized OpenClaw              |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 4: Multi-user shared Memory -> Hierarchical permissions        |
|         |                                + Zoom Level                       |
|         v                                                                  |
|                                                                            |
|  Derivation 5: Do we need Channels? -> No, Space + Thread is enough       |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 6: Multi-industry adaptation? -> 4-layer config system         |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 7: What are devices? -> First-class Entity                     |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 8: Is hardware required? -> No, hardware is an enhancement     |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 9: How to validate? -> Dogfood first                           |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 10: How do Admins configure? -> Generative UI (Prompt)         |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  Derivation 11: Template vs generated? -> Template + AI customization      |
|                                                                            |
|         |                                                                  |
|         v                                                                  |
|                                                                            |
|  End point: Complete product design                                        |
|                                                                            |
+---------------------------------------------------------------------------+
```

### 11 Design Decisions at a Glance

| # | Question | Decision | Rationale |
|---|------|------|------|
| 1 | Collaboration experience | Git-like Thread | Branch to explore, merge conclusions |
| 2 | Agent positioning | Team Member | Has identity, responsibilities, persistent context |
| 3 | Agent implementation | Containerized OpenClaw | Isolation, security, scalable |
| 4 | Memory permissions | Hierarchical + Zoom Level | Granular control, present as needed |
| 5 | Hierarchy structure | Space -> Thread -> Feed | Simplified concepts, no Channel needed |
| 6 | Industry adaptation | 4-layer configuration | Adapt to new industries without code changes |
| 7 | Device positioning | First-class Entity | Manageable, trackable, controllable |
| 8 | Hardware dependency | Optional enhancement | Lowers barrier, expands market |
| 9 | Validation approach | Dogfood first | Fastest feedback, most authentic scenarios |
| 10 | Admin configuration | Generative UI | Prompt description -> AI generates |
| 11 | Configuration model | Template + AI | Standard starting point + personalized customization |

### Assumptions To Be Validated

| Assumption | Risk Level | Validation Method |
|------|----------|----------|
| Users can understand Branch/Merge | High | User testing |
| One Agent per person is cost-viable | High | Technical prototype |
| Users can accept no Channels | Medium | Dogfood |
| 3 Zoom Levels are sufficient | Low | Dogfood |
| Auto Memory extraction is accurate | Medium | Dogfood |
| Generative UI configuration is accurate | Medium | Admin testing |

---

## Next Steps

1. **Dogfood first** -- Vibe internal use
2. **Validate assumptions** -- Especially Branch/Merge and Agent cost
3. **Iterate and adjust** -- Based on feedback
4. **External Alpha** -- 1-2 customers
5. **Polish Templates** -- Refine industry templates

---

*Last updated: 2026-02-07*
*Status: Complete - Product Reasoning Document*
