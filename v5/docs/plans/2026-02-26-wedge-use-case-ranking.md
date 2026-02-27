---
name: wedge-use-case-ranking
status: draft
audience: internal team
created: 2026-02-26T23:15:00Z
updated: 2026-02-26T23:15:00Z
---

# Vibe Workspace: "7 Lines of Code" Wedge Use Case Ranking

> 8 domains, 24 use cases, 6 scoring dimensions. Which use case do we build first?

---

## Scoring Framework

| Dimension | Question | Scale |
|-----------|----------|-------|
| Pain | How much does it hurt without this? | 1-10 |
| Lightness | Can you set it up in 5 minutes? | 1-10 |
| Frequency | How often do you use it? (daily=10) | 1-10 |
| Workspace Pull | Does it naturally lead to wanting more agents? | 1-10 |
| Hardware Synergy | Does Vibe hardware make this meaningfully better? | 1-10 |
| Uniqueness | Is this poorly served by existing tools? | 1-10 |

Composite = average of all 6 dimensions.

---

## Full Ranking (24 use cases)

| Rank | Use Case | Domain | Pain | Light | Freq | Pull | HW | Unique | **Score** |
|------|----------|--------|------|-------|------|------|----|--------|-----------|
| **1** | **Decision Ghost** | Meetings | 9 | 9 | 8 | 9 | 8 | 8 | **8.5** |
| **2** | **Board Buddy (Daily Warm-Up)** | Education | 7 | 9 | 10 | 8 | 10 | 6 | **8.3** |
| **3** | **Morning Marketing Briefing** | Marketing | 8 | 9 | 9 | 9 | 7 | 7 | **8.2** |
| 4 | Deal Prep Brief | Sales | 8 | 9 | 9 | 8 | 7 | 6 | 7.8 |
| 5 | Escalation Briefer | CS/Support | 9 | 8 | 8 | 8 | 7 | 7 | 7.8 |
| 6 | Account Pulse Digest | CS/Support | 7 | 9 | 7 | 9 | 6 | 8 | 7.7 |
| 7 | Decision Log Agent | Product/Eng | 9 | 7 | 5 | 9 | 8 | 8 | 7.7 |
| 8 | Sprint Changelog | Product/Eng | 7 | 9 | 8 | 7 | 6 | 7 | 7.3 |
| 9 | Expense Policy Oracle | Finance/Ops | 8 | 9 | 9 | 7 | 4 | 7 | 7.3 |
| 10 | Cross-Team Catch-Up | Meetings | 8 | 9 | 8 | 7 | 5 | 6 | 7.2 |
| 11 | Meeting-to-Action Tracker | HR/People | 6 | 7 | 8 | 7 | 8 | 7 | 7.2 |
| 12 | Vendor Payment Status | Finance/Ops | 9 | 7 | 8 | 7 | 3 | 8 | 7.0 |
| 13 | Policy Q&A Agent | HR/People | 8 | 9 | 9 | 7 | 4 | 5 | 7.0 |
| 14 | Emergency Sub Autopilot | Education | 9 | 5 | 3 | 6 | 9 | 8 | 6.7 |
| 15 | Meeting Debt Killer | Meetings | 7 | 7 | 5 | 8 | 6 | 7 | 6.7 |
| 16 | Pipeline Narcolepsy Alert | Sales | 9 | 7 | 6 | 8 | 4 | 5 | 6.5 |
| 17 | Cash Position Brief | Finance/Ops | 7 | 6 | 5 | 8 | 7 | 6 | 6.5 |
| 18 | Competitive Move Alert | Marketing | 7 | 7 | 4 | 8 | 4 | 8 | 6.3 |
| 19 | Knowledge Surfacer | CS/Support | 8 | 6 | 9 | 6 | 4 | 5 | 6.3 |
| 20 | "Why Is This Broken?" | Product/Eng | 8 | 6 | 6 | 8 | 4 | 6 | 6.3 |
| 21 | New Hire Onboarding Buddy | HR/People | 7 | 6 | 4 | 9 | 6 | 6 | 6.3 |
| 22 | Class Digest (Parent Update) | Education | 8 | 8 | 6 | 7 | 4 | 5 | 6.3 |
| 23 | Lost Deal Autopsy | Sales | 7 | 8 | 4 | 7 | 3 | 7 | 6.0 |
| 24 | Campaign Post-Mortem | Marketing | 7 | 6 | 3 | 7 | 6 | 6 | 5.8 |

---

## Top 3 Analysis

### #1: Decision Ghost (Meetings) — 8.5

**What:** After every meeting (captured by Bot/Dot), agent extracts decisions (not just action items) and posts to Workspace. Tracks decisions across meetings. Flags when a decision gets silently reversed.

**Why it wins:**
- Requires agent **memory** — the exact differentiator of Workspace vs every meeting AI tool
- Hardware gives structural advantage (always-on capture via Bot/Dot, no "invite the bot" friction)
- The "contradiction detection" feature is genuinely new — nobody does cross-meeting decision tracking
- Strongest workspace pull: once you have a decision ledger, you want agents to check proposals against past decisions

**Risk:** Decision extraction from natural conversation is hard. "We should probably go with A" vs "We've decided on A" — the agent will get this wrong. Mitigation: human confirm/reject in Workspace.

**Audience:** Every team, every company. Universal pain.

---

### #2: Board Buddy — Daily Warm-Up (Education) — 8.3

**What:** Agent on the Vibe Board generates context-aware warm-up activities for every class period. Displayed automatically when students walk in. Teacher does zero prep.

**Why it scores high:**
- Perfect 10 on hardware synergy — this use case is MEANINGLESS without the Board
- Perfect 10 on frequency — 5-6 times per day, every school day
- The "walk-in moment" is the most powerful sales demo: principal walks into classrooms, every Board is already running
- Teacher-by-teacher adoption, no IT required

**Risk:** Content quality must be high. One bad warm-up and the teacher turns it off. Also, uniqueness is only 6 — bell ringer generators exist (SchoolGPT, EasyClass), the differentiation is the hardware delivery.

**Audience:** K-12 private/charter schools with Vibe Boards already installed.

---

### #3: Morning Marketing Briefing — 8.2

**What:** Agent runs at 7am, pulls yesterday's metrics from ad platforms + analytics, posts structured narrative briefing to Workspace. Three layers: headline → summary → full data.

**Why it's strong:**
- Solves a daily 30-45 min ritual every marketer does
- Highest workspace pull (9) — reading leads to asking → requesting → automating
- The progressive disclosure format (headline/summary/detail) IS the Workspace UX vision
- Board in the marketing area showing the briefing = "marketing war room"

**Risk:** Requires API connections to ad platforms (Meta, Google, etc.) — not quite "5 minutes." If data connections break (OAuth expiring), trust collapses fast.

**Audience:** D2C / performance marketing teams at SMBs.

---

## Dimension-Specific Rankings

### Top 5 by Hardware Synergy (Vibe's structural moat)

| Rank | Use Case | HW Score |
|------|----------|----------|
| 1 | Board Buddy (Education) | 10 |
| 2 | Emergency Sub Autopilot (Education) | 9 |
| 3 | Decision Ghost (Meetings) | 8 |
| 3 | Decision Log Agent (Product/Eng) | 8 |
| 3 | Meeting-to-Action Tracker (HR) | 8 |

Education and Meetings are the hardware-native domains.

### Top 5 by Workspace Pull (leads to more agent adoption)

| Rank | Use Case | Pull Score |
|------|----------|------------|
| 1 | Decision Ghost (Meetings) | 9 |
| 1 | Morning Marketing Briefing (Marketing) | 9 |
| 1 | Account Pulse Digest (CS) | 9 |
| 1 | Decision Log Agent (Product/Eng) | 9 |
| 1 | New Hire Onboarding Buddy (HR) | 9 |

### Top 5 by Lightness (5-minute setup)

| Rank | Use Case | Light Score |
|------|----------|-------------|
| 1 | Decision Ghost (Meetings) | 9 |
| 1 | Board Buddy (Education) | 9 |
| 1 | Morning Marketing Briefing (Marketing) | 9 |
| 1 | Deal Prep Brief (Sales) | 9 |
| 1 | Sprint Changelog (Product/Eng) | 9 |
| 1 | Account Pulse Digest (CS) | 9 |
| 1 | Expense Policy Oracle (Finance) | 9 |
| 1 | Cross-Team Catch-Up (Meetings) | 9 |
| 1 | Policy Q&A Agent (HR) | 9 |

---

## Strategic Lens: Which wedge for which business leg?

### Hardware Leg (vibe.us) — sell more devices

Best wedges are ones where **hardware is essential**, not optional:

1. **Board Buddy** (Education) — Board IS the product
2. **Emergency Sub Autopilot** (Education) — Board IS the substitute's lifeline
3. **Decision Ghost** (Meetings) — Bot/Dot always-on capture is the enabler

These make the hardware sale story: "Your Board/Bot/Dot isn't just a display — it's an AI agent with physical presence."

### Software Leg (vibe.dev) — prove Workspace value

Best wedges are ones where **agent memory and workspace UX** are the differentiator:

1. **Decision Ghost** (Meetings) — cross-meeting memory is the killer feature
2. **Morning Marketing Briefing** (Marketing) — progressive disclosure IS the Workspace UX
3. **Account Pulse Digest** (CS) — daily agent → "can it do more?" pull

These prove the Workspace thesis: "Agents that remember, reason across sessions, and collaborate with humans."

### The Intersection (both legs)

**Decision Ghost** is the only use case that scores top-3 for BOTH legs:
- Hardware: Bot/Dot always-on capture makes it reliable
- Software: Cross-meeting memory makes it unique
- Universal: every team has meetings

---

## Recommendation

### Primary Wedge: Decision Ghost

It's the highest-scoring use case (8.5), leverages both hardware and software, and serves every team in every company. The "decision reversal detection" feature is genuinely novel — it requires agent memory (Workspace differentiator) AND always-on capture (hardware differentiator).

### Secondary Wedge by Vertical:

| If targeting... | Build this next | Why |
|----------------|----------------|-----|
| K-12 Education | Board Buddy | Perfect hardware synergy, teacher-by-teacher adoption |
| D2C / Marketing teams | Morning Marketing Briefing | Already half-built (Daily Report operator in v5) |
| Sales-led orgs | Deal Prep Brief | Highest frequency, CRM integration |
| CS-heavy orgs | Account Pulse Digest | Strongest pull toward more agents |

### The Bet 1 Question

For internal dogfooding (Bet 1), the Morning Marketing Briefing is the most practical starting point — it maps directly to the Daily Growth Report already built in v5. Decision Ghost requires meeting capture infrastructure that may not be set up internally yet.

**Suggested Bet 1 sequence:**
1. Morning Marketing Briefing (already have the operator) — prove daily agent value
2. Decision Ghost (add meeting capture) — prove cross-session memory value
3. Pick vertical wedge based on signal

---

## Appendix: All 24 Use Cases by Domain

### Sales
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Deal Prep Brief | 7.8 | 15 min before every call, agent posts deal context + suggested talking points |
| Pipeline Narcolepsy Alert | 6.5 | Daily scan of deals going cold, with drafted follow-up messages |
| Lost Deal Autopsy | 6.0 | Auto-generated post-mortem when deals close-lost, with pattern matching |

### Marketing
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Morning Marketing Briefing | 8.2 | Daily narrative report of yesterday's metrics with interpretation |
| Competitive Move Alert | 6.3 | Monitor competitor websites/pricing, alert on changes with analysis |
| Campaign Post-Mortem | 5.8 | Auto-generated campaign retrospective when campaigns end |

### Customer Success
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Escalation Briefer | 7.8 | Structured summary when tickets escalate, replacing 40-message thread reading |
| Account Pulse Digest | 7.7 | Morning digest of which accounts need attention, with signals and context |
| Knowledge Surfacer | 6.3 | Answer support team questions from internal docs and past tickets |

### Product / Engineering
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Decision Log Agent | 7.7 | Extract and track decisions from meetings, flag reversals |
| Sprint Changelog | 7.3 | Auto-generated weekly changelog from GitHub + project tracker |
| "Why Is This Broken?" | 6.3 | Incident context aggregation across GitHub, Slack, error tracker |

### Finance / Operations
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Expense Policy Oracle | 7.3 | Answer employee policy questions from uploaded handbook |
| Vendor Payment Status | 7.0 | Auto-draft replies to vendor payment inquiries |
| Cash Position Brief | 6.5 | Daily cash position + 7-day forecast from accounting system |

### HR / People
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Meeting-to-Action Tracker | 7.2 | Capture action items from meetings, follow up before next meeting |
| Policy Q&A Agent | 7.0 | Answer HR policy questions from employee handbook |
| New Hire Onboarding Buddy | 6.3 | Proactive onboarding agent for new hires with checklist + Q&A |

### Education / K-12
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Board Buddy (Warm-Up) | 8.3 | Auto-generated, context-aware warm-up activities on the Board every period |
| Emergency Sub Autopilot | 6.7 | Board activates "Sub Mode" with full lesson plans when teacher is absent |
| Class Digest (Parents) | 6.3 | Auto-generated weekly parent newsletter from classroom activity |

### Meetings / Collaboration
| Use Case | Score | One-liner |
|----------|-------|-----------|
| Decision Ghost | 8.5 | Extract decisions from meetings, track across sessions, flag reversals |
| Cross-Team Catch-Up | 7.2 | Personalized daily digest of meetings you missed but are relevant to you |
| Meeting Debt Killer | 6.7 | Pre-meeting brief showing what was already decided in past meetings |

---

*Generated 2026-02-26 from 8 parallel research agents scanning Sales, Marketing, CS, Product/Eng, Finance/Ops, HR, Education, and Meetings domains.*
