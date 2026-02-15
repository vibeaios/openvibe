# Vibe AI Ops: Design Document

> Date: 2026-02-15
> Status: Approved
> Goal: Deploy 20 AI agents across Marketing, Sales, CS, and Revenue Intelligence to transform Vibe's GTM from human-limited to agent-powered

---

## 1. What This Is

An internal ops tool that deploys 20 AI agents in parallel across Vibe's GTM operations. Three engines (Marketing, Sales, CS) plus a Revenue Intelligence layer, all running simultaneously from day one.

**What this is NOT:**
- Not an OSS platform (that's a future conversation)
- Not a product for external sale (yet)
- Not incremental optimization of existing processes

**The test:** Can one person + AI stand up an agent-powered GTM organization in 4 weeks?

---

## 2. The "Previously Impossible" Thesis

The dividing line between optimization and transformation:

| | Optimization | Transformation |
|---|---|---|
| **Definition** | Same work, faster | Work that was impossible before |
| **Marketing** | Write content faster | Run 50 parallel micro-segment buyer journeys simultaneously |
| **Sales** | Better CRM dashboards | Every lead gets a dedicated team (research + personalization + follow-up) regardless of deal size |
| **CS** | Automated health alerts | Every customer gets enterprise-grade success regardless of account size |
| **Common pattern** | Help existing team | **Collapse tiering** — everyone gets the best experience |

Today, only the biggest accounts get attention. AI means every lead, every customer, every segment gets the full treatment.

---

## 3. Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Human Layer                            │
│   CMO          Sales Lead       CS Lead        CEO/RevOps    │
│   (strategy)   (close deals)    (escalations)  (decisions)   │
└─────┬──────────────┬────────────────┬──────────────┬─────────┘
      │              │                │              │
      ▼              ▼                ▼              ▼
┌──────────┐  ┌───────────┐  ┌────────────┐  ┌────────────────┐
│ Engine 1 │  │ Engine 2  │  │  Engine 3  │  │   Revenue      │
│Marketing │→ │  Sales    │→ │  CS/Growth │→ │ Intelligence   │
│ 6 agents │  │ 5 agents  │  │  5 agents  │  │  4 agents      │
└──────────┘  └───────────┘  └────────────┘  └────────────────┘
      │              │                │              │
      └──────────────┴────────────────┴──────────────┘
                             │
                   ┌─────────┴──────────┐
                   │  Shared Services    │
                   │  Claude API         │
                   │  HubSpot / CRM      │
                   │  Email / Slack      │
                   │  Web Research       │
                   │  Analytics APIs     │
                   │  LangSmith          │
                   └────────────────────┘
```

### The Loop

```
Engine 1 (Marketing) generates qualified leads
  → Engine 2 (Sales) converts to customers
    → Engine 3 (CS) retains + expands
      → success stories feed back to Engine 1
      → expansion pipeline feeds back to Engine 2
      → all data feeds Revenue Intelligence
        → Intelligence optimizes all 3 engines
```

### Two-Tier Implementation

| Tier | Count | Implementation | Purpose |
|------|-------|----------------|---------|
| **Deep Dive** | 3 agents | Multi-step logic, full integrations, error handling, baseline metrics | Prove value rigorously |
| **Validation** | 17 agents | Single Claude API call, real inputs, output to Slack, human rates output | Prove concept works at all |

All 20 agents run with real triggers and produce real output from day one. Deep-dive agents just get more sophisticated implementations.

---

## 4. Engine 1: Marketing — Micro-Segment Buyer Journey Machine

**The transformation:** From "1 campaign for 1 broad audience" to "50 independent buyer journeys running simultaneously, each optimized for its micro-segment."

**Why previously impossible:** One complete buyer journey (research → messaging → content → distribution → optimization → iteration) requires a full marketing team. Running 10-50 of these in parallel would require 50-200 marketers. With agents: 1 CMO + 6 agents.

### M1. Segment Research Agent

**Trigger:** Weekly refresh
**Input:** ICP definition + market data + competitor landscape
**Output:** Per-segment profile document

For each micro-segment, produces:
- Firmographic profile (size, industry, geo, tech stack)
- Pain points (ranked by severity, with evidence)
- Language patterns (how they talk about the problem)
- Channel preferences (where they spend attention)
- Competitive landscape (what they use today, why they'd switch)
- Buying triggers (events that cause them to buy)
- Messaging angles (3-5 hypotheses to test)

Uses web research, job postings, G2 reviews, LinkedIn data, support tickets, competitor content.

**Previously impossible:** A human analyst produces 1-2 segment profiles per week. This produces 10-50 simultaneously, refreshed weekly.

### M2. Message Testing Agent

**Trigger:** Continuous loop (test → measure → iterate)
**Input:** Segment profile + messaging hypotheses from M1
**Output:** Tested, ranked messaging per segment

For each segment:
- Generate 10 messaging variants (headlines, value props, CTAs)
- Deploy across channels (email subject lines, ad copy, social posts, landing pages)
- Track: open rate, click rate, reply rate, conversion rate
- After 48-72h: kill bottom 50%, generate new variants from top performers
- After 2 weeks: declare winners per segment per channel

**Previously impossible:** Manual A/B testing = 2-3 variants, one channel, weeks to conclude. This runs 10 variants across 5 channels for 50 segments simultaneously, iterating every 48h.

### M3. Content Generation Agent [DEEP DIVE]

**Trigger:** Daily + on winning message declared by M2
**Input:** Winning messages from M2 + segment profile from M1
**Output:** Full content pieces per segment

For each segment's winning message:
- Long-form: blog post, whitepaper, case study
- Short-form: email sequence (3-5 touches), social posts
- Visual brief: slide deck outline, infographic spec
- SEO: keyword-optimized versions
- Tone/voice: matched to segment's language patterns

Quality gate: Human CMO reviews first 5 pieces per segment, then agent self-scores against approved examples.

**Volume:** 2-5 pieces per segment per week x 50 segments = 100-250 pieces/week

**Deep dive specifics:**
- Multi-step generation pipeline (outline → draft → edit → format)
- Style consistency scoring against brand guide
- SEO integration (keyword density, structure, meta)
- Segment-specific tone calibration
- Performance feedback loop (which content converts → adjust generation)

### M4. Content Repurposing Agent

**Trigger:** On new content from M3
**Input:** 1 content piece
**Output:** 10 format variants

For each piece: blog → email nurture → 5 LinkedIn posts → Twitter thread → video script → podcast talking points → slide deck → infographic outline → sales one-pager → internal enablement doc.

**Volume:** 100 pieces x 10 formats = 1000 assets/week

### M5. Distribution Agent

**Trigger:** On content assets ready
**Input:** Content from M3/M4 + segment channel preferences
**Output:** Published content across channels

Per segment: deploy email sequences, LinkedIn posts, targeted ads, organic blog, partner co-marketing. Track impressions, clicks, leads per channel per segment. Shift budget to highest-performing channels.

### M6. Journey Optimization Agent

**Trigger:** Weekly + on significant data thresholds
**Input:** Full funnel data across all segments
**Output:** Optimization decisions + learnings

Tracks: impression → click → lead → MQL → SQL → deal → won (per segment, per channel, per message). Benchmarks segments against each other. Kills underperformers, doubles down on winners. Feeds learnings back to M1 and M2. Weekly optimization report to CMO.

### The Full Marketing Loop

```
M1 (Research) → M2 (Test Messages) → M3 (Create Content)
→ M4 (Repurpose) → M5 (Distribute) → M6 (Optimize)
→ back to M1 (with learnings)

Running for 10-50 segments simultaneously.
Weekly iteration cycle per segment.
```

---

## 5. Engine 2: Sales — 1:1 Buyer Experience at Scale

**The transformation:** From "top 10 deals get attention, rest fall through" to "every lead gets a dedicated team — research, personalized engagement, custom proposals — previously reserved for $100K+ enterprise deals."

**Why previously impossible:** A truly personalized sales experience (deep research + custom messaging + behavior-responsive follow-up + tailored proposals + competitive positioning) requires a senior AE handling 10-15 deals. With agents, every lead gets this treatment.

### S1. Lead Qualification Agent [DEEP DIVE]

**Trigger:** Real-time (on new lead event in HubSpot)
**SLA:** < 5 minutes from lead creation to qualification
**Input:** New lead from any source
**Output:** Qualified, scored, routed lead in CRM

For each incoming lead:
- **Enrich:** company (size, industry, funding, tech stack, growth signals, news) + person (role, seniority, LinkedIn, past companies, content engagement)
- **Score:**
  - Fit (0-100): Does this match ICP?
  - Intent (0-100): Buying signals? (pricing page, demo request, downloads)
  - Urgency (0-100): Trigger event? (funding, hiring, competitor switch, renewal)
  - Composite: weighted score
- **Route:**
  - 80+ → Engine 2 immediately, human AE engages
  - 50-79 → Nurture sequence (S5)
  - <50 → Educational content, stay in Engine 1
  - ICP mismatch → Tag + archive
- **CRM:** Score, segment, source, enrichment data tagged in HubSpot
- **Alert:** Slack notification to Sales Lead for 80+ leads

**Deep dive specifics:**
- Multi-step enrichment pipeline (HubSpot → web research → LinkedIn → news)
- Scoring model with configurable weights per segment
- HubSpot read/write integration (tags, properties, lifecycle stage)
- Qualification accuracy tracking (predicted score vs actual outcome)
- Feedback loop: deals that closed → retrain scoring weights

### S2. Buyer Intelligence Agent

**Trigger:** On qualification + pre-meeting + every 48h while deal active
**Input:** Qualified lead or upcoming meeting
**Output:** Living buyer profile (continuously updated)

Company deep dive: business model, revenue, growth, tech stack, competitors, news, hiring. Person deep dive: career, interests, communication style, content they publish, mutual connections, decision-making role. Competitive positioning: what they use, why they'd switch, objections they'll raise, counter-positioning. Auto-generates pre-call brief 5 minutes before scheduled meetings.

**Previously impossible:** AEs spend 1 hour per prospect on research. This runs continuously for every prospect simultaneously.

### S3. Engagement Agent [DEEP DIVE]

**Trigger:** On qualified lead + behavior events
**Input:** Buyer profile (S2) + segment messaging (from Engine 1)
**Output:** Personalized multi-touch sequences

For each qualified lead:
- **Initial outreach:** Personalized email (references their specific situation, pain, trigger event) + LinkedIn connection
- **Behavior-responsive follow-up:**
  - Opened email → send case study from their industry
  - Clicked pricing → send ROI calculator
  - Visited competitor page → send comparison guide
  - Downloaded whitepaper → send meeting invite
  - No response → try different channel, different angle
  - Replied → hand to human AE immediately
- **Multi-touch cadence:** Day 1, 3, 7, 14 — always value-add, never "just checking in"
- **Human handoff:** Full context package (buyer profile + engagement history + recommended talking points)

**Deep dive specifics:**
- Behavior event tracking (email opens, clicks, website visits)
- Dynamic sequence adjustment based on signals
- Personalization engine (segment data + buyer profile → unique message)
- Human review queue for all outbound (until trust established)
- A/B testing of outreach approaches per segment
- Performance tracking: response rate, meeting rate, conversion by approach

### S4. Deal Support Agent

**Trigger:** Continuous while deal active
**Input:** Active deal + call transcripts + emails
**Output:** Everything the AE needs to close

Pre-call prep (auto-generated before every meeting): updated buyer profile, deal history summary, suggested agenda, anticipated objections, competitive intel. Post-call actions: meeting summary, action items, follow-up email draft, CRM update, risk assessment. Proposal generation: custom (not template), tailored to their pain, use case, ROI projection. Stall intervention: no activity 7 days → re-engagement approach, champion quiet → multi-thread strategy, new stakeholder → research + positioning.

### S5. Nurture Agent

**Trigger:** On lead routed to nurture (score 50-79) + ongoing behavior events
**Input:** Lead profile + segment content from Engine 1
**Output:** Long-term relationship building until buying signal

Segment-aware content sequence: educational → solution-aware → product-aware → decision-ready. Behavior monitoring: re-visits website → bump score, company trigger event → re-qualify immediately, score crosses 80 → hand to S3 (Engagement). Duration up to 12 months. Always value-add, never "just checking in."

---

## 6. Engine 3: Customer Success — Dedicated Success Team per Customer

**The transformation:** From "tiered CS (enterprise gets CSM, mid-market gets emails, SMB gets nothing)" to "every customer gets enterprise-grade success regardless of account size."

**Why previously impossible:** Enterprise-grade CS = dedicated CSM who knows the account, monitors proactively, provides personalized guidance, identifies expansion, and intervenes before problems. At 1 CSM : 20 accounts, this costs ~$7K/account/year. With agents, every customer gets it.

| Tier | Today | With Engine 3 |
|------|-------|---------------|
| Enterprise ($100K+) | Dedicated CSM | Same + AI augmentation |
| Mid-market ($10-50K) | Shared CSM, reactive | Dedicated AI team + human escalation |
| SMB ($1-5K) | Self-serve, high churn | Dedicated AI team (same quality as enterprise) |

**Business impact:** Most SaaS revenue loss is mid-market and SMB churn. Enterprise-grade success for every account collapses the churn curve.

### C1. Onboarding Agent

**Trigger:** On deal closed-won in CRM
**Input:** New customer + context from Engine 2 (why they bought, who's involved, what was promised)
**Output:** Personalized onboarding journey

Custom plan based on their specific use case:
- Day 1: Welcome + setup guide (tailored, not generic)
- Day 3: Feature walkthrough (only features relevant to THEIR use case)
- Day 7: First success milestone check ("Did you achieve X?")
- Day 14: Advanced features (based on what they've actually used)
- Day 21: Integration setup + workflow optimization
- Day 30: Success review with impact metrics

Stuck detection: Haven't logged in 3 days → proactive outreach. Setup incomplete after 7 days → guided session. Key feature not adopted → tailored tutorial. Multiple users not activated → manager outreach.

Adaptive pacing: Fast adopters → accelerate. Slow adopters → more hand-holding. Stuck → escalate to human CS.

Day 30 graduation → hand to C2 (Success Advisor).

**Previously impossible:** Today onboarding is the same email sequence for everyone. This builds a unique journey per customer based on why they bought and how they're actually using the product.

### C2. Success Advisor Agent

**Trigger:** Weekly scheduled + on significant usage events
**Input:** Customer usage data + support history + account context
**Output:** Proactive, personalized guidance

Usage intelligence: which features used vs available, frequency, workflow patterns, feature discovery gaps, power user vs casual segmentation.

Proactive recommendations:
- "You're using X manually — Y automates this"
- "Companies like yours in [industry] get 3x value from [feature]"
- "Your team added 3 users — here's how to set up permissions for growing teams"

Cross-customer intelligence: pattern matching from similar companies, best practices, workflow templates from successful customers.

Milestone celebrations with impact metrics ("You've saved X hours this quarter").

Cadence: weekly insights + 1 recommendation, monthly success summary, quarterly strategic review prep for human CS.

### C3. Health Intelligence Agent

**Trigger:** Daily compute + real-time on critical signals
**Input:** Usage data + support tickets + engagement + payment + market context
**Output:** Health score + predictions + intervention triggers

Health score (0-100, computed daily):
- Usage (40%): login frequency, feature breadth, time in product, trend
- Engagement (20%): email opens, support interactions, community
- Support (20%): ticket volume, severity, satisfaction, repeat issues
- Business (20%): payment on time, user growth/decline, renewal proximity

Predictive signals:
- Usage declining 3 weeks → 70% churn risk in 60 days
- Champion left company → 50% churn risk
- Support tickets spiking → frustration building
- Competitor content engagement → evaluating alternatives
- Renewal in 60 days + no engagement → at risk

Intervention triggers:
- Score drop >10 → increase touchpoints
- Score drop >20 → human CS alert + intervention plan
- Score <50 → escalate to CS Lead
- Score <30 → executive intervention

Cohort intelligence: compare vs segment average, flag outliers, identify systemic issues.

**Previously impossible:** Human CSMs check accounts reactively or quarterly. This monitors every customer every day, predicts problems 30-60 days out.

### C4. Expansion Agent

**Trigger:** Weekly scan + on expansion signals
**Input:** Usage data + health score + account context + product catalog
**Output:** Expansion opportunities + custom proposals

Signal detection: usage hitting limits, team growing, new use cases emerging, department expansion, success milestone reached, renewal approaching.

Custom expansion proposal: specific to their usage, ROI projection from their actual data, peer comparison, pricing recommendation. Timing intelligence: propose after success milestone, during planning cycle, before renewal — not during active issues.

Qualified expansion opportunities feed back to Engine 2 (Sales) for human close.

**Previously impossible:** Expansion today is opportunistic. This systematically identifies every opportunity across every account with proposals ready.

### C5. Customer Voice Agent

**Trigger:** Continuous aggregation + weekly synthesis
**Input:** Support tickets + NPS + call transcripts + usage data + social + community
**Output:** Synthesized customer intelligence

Aggregates all customer signals into:
- Top 10 pain points this week (ranked by revenue impact)
- Feature requests by segment
- Competitive mentions
- Success patterns (what makes customers succeed)
- Failure patterns (what causes churn)

Product intelligence: "Feature X requested by $500K ARR customers — here's the business case." "Bug Y affecting 15% of enterprise — estimated churn risk $200K."

Feeds to Engine 1: success stories as content fuel, customer language for messaging, testimonial candidates, reference customers by segment.

Weekly report for product + CS + marketing. Monthly customer voice report for leadership.

---

## 7. Revenue Intelligence Layer

The monitoring and optimization layer across all three engines. This is where the sales team's operational priorities (funnel monitoring, deal risk, forecasting, coaching) live — important, but the intelligence layer, not the transformation engine.

### R1. Funnel & Pipeline Monitor

**Trigger:** Real-time + daily summary
**Coverage:** Full journey across all 3 engines

- Engine 1: impressions → clicks → leads per segment
- Engine 1→2 handoff: lead quality, qualification accuracy
- Engine 2: leads → meetings → proposals → closed
- Engine 2→3 handoff: promise vs reality
- Engine 3: onboarding success, health, expansion, churn, NRR
- Anomaly detection: any metric deviating from baseline
- Attribution: segments, channels, messages → revenue
- Output: real-time dashboard + Slack alerts on anomalies

### R2. Deal Risk & Forecast

**Trigger:** Daily risk scan + weekly forecast
**Coverage:** Every active deal + pipeline aggregate

Deal risk scoring: activity gaps, stage SLA breach, missing elements (champion, budget, timeline), buyer behavior signals, historical pattern matching.

Forecast: system forecast (bottom-up), rep forecast (weekly submission), delta analysis, accuracy scoring per rep.

Big deal intelligence: narrative summary + risk + recommended action for deals above threshold.

### R3. Conversation Analysis

**Trigger:** Weekly
**Coverage:** All rep calls and SDR interactions

Call scoring against training framework. Pattern detection across team. Per-rep weekly coaching packs (3 clips to improve, 3 done well). Message discipline monitoring. SDR quality: ICP fit, qualification judgment, value proposition delivery. Training feedback loop: gaps → content updates.

### R4. Natural Language Revenue Interface

**Trigger:** On-demand (Slack command or dashboard)
**Coverage:** All data across all 3 engines

- "Show red-flag deals over $25K"
- "Which segments are converting best?"
- "Why is pipeline down vs last week?"
- "Which customers are at churn risk?"
- "What's our NRR trend by segment?"

Outputs: tables, charts, summaries, alerts.

---

## 8. Complete Agent Map

| # | Agent | Engine | Tier | Trigger | Primary Output |
|---|-------|--------|------|---------|----------------|
| M1 | Segment Research | Marketing | Validation | Weekly | Segment profiles |
| M2 | Message Testing | Marketing | Validation | Continuous | Ranked messaging |
| M3 | **Content Generation** | Marketing | **Deep Dive** | Daily | Content pieces |
| M4 | Content Repurposing | Marketing | Validation | On content | 10 format variants |
| M5 | Distribution | Marketing | Validation | On content | Published assets |
| M6 | Journey Optimization | Marketing | Validation | Weekly | Optimization decisions |
| S1 | **Lead Qualification** | Sales | **Deep Dive** | Real-time | Scored + routed leads |
| S2 | Buyer Intelligence | Sales | Validation | On qual + 48h | Living buyer profiles |
| S3 | **Engagement** | Sales | **Deep Dive** | On qual + events | Personalized sequences |
| S4 | Deal Support | Sales | Validation | Continuous | Pre/post-call support |
| S5 | Nurture | Sales | Validation | On route | Long-term sequences |
| C1 | Onboarding | CS | Validation | On deal won | Personalized journey |
| C2 | Success Advisor | CS | Validation | Weekly | Proactive guidance |
| C3 | Health Intelligence | CS | Validation | Daily | Health scores + alerts |
| C4 | Expansion | CS | Validation | Weekly | Upsell proposals |
| C5 | Customer Voice | CS | Validation | Continuous | Customer insights |
| R1 | Funnel Monitor | Intelligence | Validation | Real-time | Dashboard + alerts |
| R2 | Deal Risk & Forecast | Intelligence | Validation | Daily | Forecast + risk |
| R3 | Conversation Analysis | Intelligence | Validation | Weekly | Coaching packs |
| R4 | NL Revenue Interface | Intelligence | Validation | On-demand | Query responses |

**Total: 20 agents. 3 deep-dive, 17 validation.**

---

## 9. Tech Stack

No Temporal. No CrewAI. Minimal infrastructure.

| Component | Purpose | Why This |
|-----------|---------|----------|
| **Python** | All agent code | Simple, Claude SDK native |
| **Claude API** | Agent intelligence | Best reasoning, long context |
| **HubSpot API** | CRM read/write | Where lead/customer data lives |
| **Slack API** | Output + alerts + commands | Where humans already work |
| **Email API** | Outbound drafts | For engagement + nurture sequences |
| **SQLite → Postgres** | Run logs, agent config, state | Start simple, migrate when needed |
| **LangSmith** | Observability | See every Claude call, debug quality |
| **Cron (system)** | Scheduling | Simple. No Temporal needed for cron |
| **Webhooks** | Event triggers | HubSpot → agent on new lead |

LangGraph considered for Lead Qualification if multi-step state management with checkpoints needed. Start without it — add when simple approach breaks.

### Why Not Temporal + LangGraph + CrewAI

The original plan specified a 3-layer stack. For this project:
- **Temporal:** Overkill for cron jobs and webhooks. Add if we need durable multi-day workflows with retry.
- **CrewAI:** Unnecessary abstraction layer. Claude API with system prompts achieves the same for single-agent tasks.
- **LangGraph:** Valuable for complex state machines. Reserve for Lead Qualification upgrade if simple scoring breaks.

Principle: add infrastructure when simple approach hits limits, not before.

---

## 10. Implementation Approach

### Agent Runner Framework

A shared framework all 20 agents use:

```
agent-runner/
├── config/
│   ├── agents.yaml          # All 20 agents: name, trigger, tier, enabled
│   └── integrations.yaml    # API keys, endpoints
├── agents/
│   ├── marketing/
│   │   ├── m1_segment_research.py
│   │   ├── m2_message_testing.py
│   │   ├── m3_content_generation.py   # [DEEP DIVE]
│   │   ├── m4_content_repurposing.py
│   │   ├── m5_distribution.py
│   │   └── m6_journey_optimization.py
│   ├── sales/
│   │   ├── s1_lead_qualification.py    # [DEEP DIVE]
│   │   ├── s2_buyer_intelligence.py
│   │   ├── s3_engagement.py            # [DEEP DIVE]
│   │   ├── s4_deal_support.py
│   │   └── s5_nurture.py
│   ├── cs/
│   │   ├── c1_onboarding.py
│   │   ├── c2_success_advisor.py
│   │   ├── c3_health_intelligence.py
│   │   ├── c4_expansion.py
│   │   └── c5_customer_voice.py
│   └── intelligence/
│       ├── r1_funnel_monitor.py
│       ├── r2_deal_risk_forecast.py
│       ├── r3_conversation_analysis.py
│       └── r4_nl_revenue_interface.py
├── shared/
│   ├── claude_client.py      # Claude API wrapper
│   ├── hubspot_client.py     # HubSpot API wrapper
│   ├── slack_client.py       # Slack output
│   ├── email_client.py       # Email drafting
│   ├── web_research.py       # Web scraping/research
│   └── logger.py             # Run logging + metrics
├── runner.py                 # Agent execution engine
├── scheduler.py              # Cron-based trigger manager
└── dashboard.py              # Agent health + output quality
```

### Standard Agent Interface

Every agent implements the same interface:

```python
class Agent:
    name: str
    tier: str          # "deep_dive" | "validation"
    trigger: str       # "cron:daily" | "cron:weekly" | "webhook:new_lead" | "on_demand"

    def run(self, input_data: dict) -> AgentOutput:
        """Execute the agent's core logic."""
        ...

    def get_system_prompt(self) -> str:
        """Return the Claude system prompt for this agent."""
        ...

class AgentOutput:
    content: str       # The agent's output
    destination: str   # "slack:#channel" | "hubspot:lead_tag" | "email:draft"
    cost: float        # Claude API cost for this run
    duration: float    # Execution time
    metadata: dict     # Agent-specific data
```

### Validation Tier Pattern

Every validation-tier agent follows the same simple pattern:

```python
def run(self, input_data):
    prompt = self.get_system_prompt()
    response = claude.messages.create(
        model="claude-sonnet-4-5-20250929",
        system=prompt,
        messages=[{"role": "user", "content": format_input(input_data)}]
    )
    output = AgentOutput(
        content=response.content,
        destination=self.output_channel,
        cost=calculate_cost(response.usage)
    )
    log_run(self.name, input_data, output)
    route_output(output)
    return output
```

### Deep Dive Tier Pattern

Deep-dive agents add:
- Multi-step pipelines (e.g., enrich → score → route)
- Real integrations (HubSpot read/write, email API)
- Error handling and retry logic
- Baseline metrics tracking
- Human-in-the-loop approval for external actions
- Performance feedback loops

---

## 11. Timeline

| Week | Focus | Deliverables |
|------|-------|-------------|
| **Week 1** | Framework + shared services | Agent runner, Claude wrapper, HubSpot wrapper, Slack output, logging, config system |
| **Week 1-2** | All 20 agents defined | System prompts, input sources, output destinations, trigger configs for all 20 |
| **Week 2** | Deep dive: Content Generation (M3) | Multi-step pipeline, style scoring, SEO, segment calibration |
| **Week 2-3** | Deep dive: Lead Qualification (S1) | Enrichment pipeline, scoring model, HubSpot integration, routing |
| **Week 3** | Deep dive: Engagement Agent (S3) | Behavior tracking, dynamic sequences, personalization, review queue |
| **Week 3** | All 17 validation agents running | Real triggers, real inputs, output to Slack, logging |
| **Week 4** | Full system live | All 20 agents running. Measure everything. First data on what works. |

### What We Know at Week 4

- Which of the 20 agents produce useful output
- Which should graduate from validation → deep dive next
- Which should be killed or redesigned
- Whether the full-funnel thesis (Marketing → Sales → CS loop) moves the needle
- Whether "one person + AI deploys 20 agents in parallel" actually works
- Data to decide where to invest next

---

## 12. Success Metrics

### Per-Engine Metrics

| Engine | Metric | Baseline | Target (Month 2) | "Previously Impossible" Signal |
|--------|--------|----------|-------------------|-------------------------------|
| **Marketing** | Micro-segments with active buyer journeys | 1 | 10+ | Running simultaneously |
| **Marketing** | Content pieces per week | 2 | 20+ | 10x with same headcount |
| **Marketing** | Message variants being tested | 2-3 | 50+ | Per segment, per channel |
| **Sales** | Lead follow-up rate | 20% | 100% | Every lead, personalized |
| **Sales** | Time from lead → qualification | Hours/days | < 5 minutes | Real-time |
| **Sales** | Personalized outreach coverage | Top 10 deals | Every qualified lead | Enterprise-grade for all |
| **CS** | Customers with proactive monitoring | Enterprise only | All customers | Tiering collapsed |
| **CS** | Churn prediction lead time | 0 (reactive) | 30 days | Predictive |
| **CS** | Expansion opportunities identified | Ad hoc | Systematic, weekly | Every account scanned |

### System Metrics

| Metric | Target |
|--------|--------|
| Agents running in production | 20/20 |
| Agent uptime (scheduled runs complete) | > 95% |
| Human rating of validation-tier output | > 70% useful |
| Deep-dive agent accuracy (qual, content, engagement) | Baselined and improving weekly |
| Monthly Claude API cost | < $5,000 |
| Time from concept to running agent | < 1 day (validation tier) |

### Kill Signals

| Signal | Threshold | Action |
|--------|-----------|--------|
| Agent output consistently useless | < 30% useful after 2 weeks | Kill or redesign |
| No measurable funnel improvement | Month 2, no movement | Re-evaluate entire approach |
| Cost per useful output too high | > $50/useful output | Optimize prompts or kill |
| Human review bottleneck | Humans can't keep up with output | Reduce agent volume or automate review |

---

## 13. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent output quality too low | High — wastes human review time | Start with human review on all output. Invest in prompt engineering for deep-dive agents. Kill agents that don't improve. |
| 20 agents = too much noise | Medium — alert fatigue | Dedicated Slack channels per engine. Daily digest, not real-time for validation tier. Human can mute agents. |
| HubSpot integration complexity | Medium — blocks Sales agents | Start with read-only. Add write when confident. |
| Claude API cost spiral | Medium — budget risk | Per-agent cost tracking. Budget alerts. Use Haiku for simple tasks, Sonnet for deep dive. |
| No one reviews validation-tier output | High — running but not learning | Weekly review ritual: 30 min, rate each agent's best/worst output. |
| Scope creep to 30+ agents | Medium — diluted focus | Freeze at 20 for Month 1. Add agents only by replacing killed ones. |

---

## 14. Open Decisions

| Decision | Options | When to Decide |
|----------|---------|----------------|
| Hosting | Local machine vs cloud (AWS/GCP) | Week 1 — start local, move to cloud when always-on needed |
| LangGraph for Lead Qual | Simple scoring vs LangGraph state machine | Week 3 — after simple version hits limits |
| Email sending | Draft-only vs auto-send | Week 4 — after trust established on quality |
| Agent-to-agent communication | Independent vs shared context | Week 4 — based on whether engines need cross-talk |
| Additional deep-dive agents | Which 3 next? | Week 4 — based on validation tier results |

---

*Last updated: 2026-02-15*
