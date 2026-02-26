# OpenVibe Progress

> Read this first at session start, then follow Session Resume Protocol in CLAUDE.md.

---

## Current State

**Version:** V5 — Platform Prototype
**Phase:** D2C Growth + D2C Strategy + Daily Report complete (13 operators, 54 workflows, ~64 tools)

| Package | Path | Version | Tests |
|---------|------|---------|-------|
| openvibe-sdk | `v5/openvibe-sdk/` | v1.0.0 | 279 |
| openvibe-runtime | `v5/openvibe-runtime/` | v1.0.0 | 28 |
| openvibe-platform | `v5/openvibe-platform/` | v1.0.0 | 60 |
| openvibe-cli | `v5/openvibe-cli/` | v1.0.0 | 15 |
| vibe-inc | `v5/vibe-inc/` | v0.1.0 | 387 |

**Total: 769 tests passing, 6 skipped (real API)**

## What's Built

### Infrastructure (Phases 0-2)

**SDK v1.0.0:**
- `TenantContext`, `TemplateConfig`, `RoleInstance` models
- `TemplateRegistry` — register + instantiate role templates
- System roles: `Coordinator`, `Archivist`, `Auditor`
- 13 role templates as YAML (GTM × 4, Product Dev × 3, Astrocrest × 6)

**Platform v1.0.0:**
- `TenantStore` + `tenants.yaml` (vibe-inc, astrocrest)
- `/tenants` routes: list, get
- Tenant-scoped routes with isolation: workspaces, roles, approvals, deliverables
- Per-tenant service instances in `app.state`

**CLI v1.0.0:**
- `--tenant` / `-t` flag (default: vibe-inc)

### D2C Growth — Full Toolmap (complete)

**D2CGrowth role** — 12 operators, 49 workflows, ~62 API tools:
- Soul with Net New CAC principles + escalation rules
- All operators use `@agent_node` pattern with tool injection

**Ad Platform Operators (6):**

| Operator | Workflows | Tools | Platform |
|----------|-----------|-------|----------|
| MetaAdOps | campaign_create, daily_optimize, weekly_report, audience_refresh | meta_ads (8 tools) | Meta Ads API |
| GoogleAdOps | campaign_create, daily_optimize, search_term_mining, weekly_report, recommendations_review | google_ads (6 tools) | Google Ads API |
| AmazonAdOps | campaign_create, daily_optimize, search_term_harvesting, weekly_report, competitive_analysis | amazon_ads (6 tools) | Amazon Ads API |
| TikTokAdOps | campaign_create, daily_optimize, creative_refresh, weekly_report | tiktok_ads (5 tools) | TikTok Ads API |
| LinkedInAdOps | campaign_create, daily_optimize, weekly_report, lead_quality_review | linkedin_ads (5 tools) | LinkedIn Marketing API |
| PinterestAdOps | campaign_create, daily_optimize, creative_refresh, weekly_report | pinterest_ads (5 tools) | Pinterest API v5 |

**Commerce + Email Operators (1):**

| Operator | Workflows | Tools | Platform |
|----------|-----------|-------|----------|
| EmailOps | campaign_create, flow_optimize, segment_refresh, lifecycle_report | klaviyo (6 tools) | Klaviyo API |

**Optimization Operators (2):**

| Operator | Workflows | Tools | Platform |
|----------|-----------|-------|----------|
| CROps | experiment_analyze, funnel_diagnose, page_optimize, product_optimize, discount_strategy, conversion_report | shopify (4), analytics (2), ab_testing (2) | Shopify, GA4/Redshift, Convert.com |
| CrossPlatformOps | unified_cac_report, budget_rebalance, platform_health_check | unified_metrics (3) | shared_memory aggregation |

**CRM Operator (1):**

| Operator | Workflows | Tools | Platform |
|----------|-----------|-------|----------|
| CRMOps | workflow_enrollment, deal_progression, enrichment_audit, pipeline_health | hubspot (6 tools) | HubSpot API v3 |

**Daily Report Operator (1):**

| Operator | Workflows | Tools | Platform |
|----------|-----------|-------|----------|
| DailyReportOps | daily_growth_report (fetch_data → interpret) | analytics_query_sql, read_memory | Redshift (SQL) + Claude interpreter |

Two-node workflow: deterministic SQL queries for L1 (Business Outcomes), L2 (Channel Efficiency), L3 (Funnel Signal) → Claude interprets with Ricky's 3-layer framework. Includes date validation, funnel benchmarks from shared_memory, Net New CAC flagging.

**Shared memory added:**
- `data/intent_stage_classification.sql` — 4-level campaign intent CASE expression
- `performance/funnel_benchmarks.yaml` — real funnel rates by intent stage (Oct 2025–Feb 2026)
- `data/catalog.yaml` — expanded with dbt_analytics tables, raw website events, CRM dims, Redshift gotchas

**Ops docs:**
- `v5/docs/ops/redshift-connection.md` — SSH tunnel setup, schema overview

### D2C Strategy (complete)

**D2CStrategy role** — 2 operators, 5 workflows, 2 new tools:
- Soul with positioning/ICP/competitive principles + escalation rules
- Web tools: `web_search` (Brave Search API), `web_fetch` (HTTP GET, truncated)

| Operator | Workflows | Tools | Purpose |
|----------|-----------|-------|---------|
| PositioningEngine | define_framework, validate_story, refine_icp | read_memory, write_memory, ga4_read | Messaging frameworks + ICP definitions |
| CompetitiveIntel | weekly_scan, threat_assess | web_search, web_fetch, read_memory, write_memory | Competitive monitoring + threat analysis |

**Shared memory added:**
- `competitive/competitor_registry.yaml` — Bot/Dot/Board competitor tracking
- `competitive/market-signals.yaml` — weekly scan output template

**DataOps role** — 3 operators, 4 workflows:
- CatalogOps: catalog_audit
- QualityOps: freshness_check
- AccessOps: data_query, build_report

**Shared memory YAML:**
- Messaging frameworks: Bot, Dot, Board
- ICP definitions: Bot (SMB managers), Dot (knowledge workers), Board (K-12 admins)
- CAC benchmarks: Bot $400, Dot $300, Board N/A
- Email benchmarks: campaign targets, flow targets, list health
- CRO benchmarks: funnel targets, experiment standards, product CVR targets
- CRM config: routing rules (3 signals), pipeline config (B2B stages, product targets)

**Applications scaffolded:**
- `v5/vibe-inc/` — src layout, hatchling build, full test suite (387 tests)
- `v5/astrocrest/` — soul.yaml + roles.yaml + scoring.yaml (6 roles, not yet implemented)

## Key Docs

- `v5/docs/THESIS.md` — two-customer cognition OS thesis
- `v5/docs/DESIGN.md` — multi-tenant Role SDK architecture
- `v5/docs/ROADMAP.md` — phased execution plan
- `v5/docs/strategy/ASTROCREST.md` — Astrocrest principles
- `v5/docs/plans/2026-02-18-v5-implementation.md` — V5 platform implementation (complete)
- `v5/docs/plans/2026-02-19-d2c-marketing-adoption.md` — D2C marketing design (3-role architecture)
- `v5/docs/plans/2026-02-19-d2c-phase1-implementation.md` — D2C Phase 1 plan (17 tasks, complete)
- `v5/docs/plans/2026-02-19-d2c-growth-toolmap-implementation.md` — D2C Growth toolmap plan (37 tasks, complete)
- `v5/docs/plans/2026-02-20-hubspot-crm-ops-design.md` — HubSpot CRMOps design (10th operator)
- `v5/docs/plans/2026-02-20-hubspot-crm-ops-implementation.md` — HubSpot CRMOps implementation (11 tasks, complete)
- `v5/docs/plans/2026-02-20-d2c-strategy-implementation.md` — D2C Strategy implementation (10 tasks, complete)
- `v5/docs/plans/2026-02-24-daily-growth-report-design.md` — Daily Growth Report design (Redshift SQL + Claude interpreter)
- `v5/docs/plans/2026-02-24-daily-growth-report-implementation.md` — Daily Growth Report implementation (7 tasks, complete)

## Live API Testing (2026-02-20)

First real API calls validated. Credentials configured for Meta Ads + HubSpot.

| Test | Layer | Status | Time |
|------|-------|--------|------|
| HubSpot `contact_get` | Tool smoke | **PASSED** | 0.5s |
| Meta `meta_ads_read` | Tool smoke | **PASSED** | 118s |
| Meta `weekly_report` (Claude + Meta API) | Agent loop | **PASSED** | 148s |

**Issues discovered:** see `vibe-inc/shared_memory/performance/live_testing_insights.yaml`
- Meta N+1 query pattern triggers rate limit — needs account-level insights refactor
- LLM string-to-list coercion — fixed for meta_ads_read, audit needed for others

## Strategic Note: Open Source as Competitive Moat (2026-02-24)

**Trigger:** Notion 3.3 Custom Agents launched — 24/7 autonomous agents with Slack/Mail/Calendar/MCP integrations, natural language config, credit-based pricing. 21,000+ agents built in beta.

**Key insight:** Notion agents = platform-locked automation. Your data lives on their platform, workflows run in their sandbox, you pay credits for their compute. 80% of teams will find this "good enough."

**OpenVibe's differentiator is ownership:**
- Data on your infra (per-tenant data_dir)
- Workflows you define (operator/workflow/tool YAML)
- Model choice (direct SDK, not platform-wrapped)
- Agent logic transparent (LangGraph state machine, not black box)

**Open source is a must.** The 20% who need full control over data + workflows won't trust another SaaS platform — they need to self-host, fork, and audit. Open source is the only credible way to offer that. It also:
- Creates distribution without sales team
- Builds trust with technical buyers
- Lets the community extend operators/tools for platforms we don't cover
- Makes "feedback is the moat" real — contributions compound

**Notion validates the market, OpenVibe serves the segment they can't.**

### Why Open Source Wins When Code Is Easy to Write

When AI makes code trivial to produce, closed-source protects nothing — anyone can replicate your SaaS in a day. Moats shift from code to:
1. **Data** — accumulated domain knowledge, user feedback, training data
2. **Operations** — who runs it better, responds faster
3. **Community** — ecosystem richness, integrations, contributions
4. **Brand trust** — "just use theirs" in a specific domain

Closed source survives only where data network effects (Bloomberg), liability requirements (healthcare/finance), or hardware integration (Apple) justify it. For everything else, open source becomes the rational default: trust via auditability, distribution via zero-friction adoption, compounding via community.

This aligns with OpenVibe's thesis: code is open, domain knowledge + feedback loops are the moat. Notion charges credits for platform-locked compute. OpenVibe earns trust through transparency + data ownership.

### The Data Substrate Insight

The agent itself is commodity. What matters is the data substrate agents operate on. Notion's moat isn't Custom Agents — it's that they already have your docs. Slack's moat is your conversations. The agent is just a feature on top of the data.

OpenVibe's play isn't "better agent framework" (that's LangChain territory). It's:
1. **Memory as core product** — Episode/Insight/Reflect triple-layer is your data substrate. Agents are features on top.
2. **Cross-silo unification** — Notion has docs, Slack has convos, HubSpot has CRM, Meta has ads. Each SaaS does agents within its silo. OpenVibe is the unified data layer + agents that reason across all of it.
3. **Open source = open data ownership layer** — not "open source agent framework" but "own your data substrate, run your own agents on it."

### Notion as Gateway Drug — The Graduation Path

Notion agents educate the market: "agents can do things for you." But they're trigger-based automation (Level 1-2). Enterprises will graduate to wanting real autonomous decision-making.

| Level | Capability | Who |
|-------|-----------|-----|
| 1 | Trigger → summarize | Notion Custom Agents |
| 2 | Monitor → alert | Most SaaS agents |
| 3 | Analyze → recommend → human approves → execute | OpenVibe (human-in-the-loop) |
| 4 | Autonomous within guardrails | OpenVibe (target state) |

The gap between "set a trigger" and "manage a $50K budget autonomously" is where the next wave gets built. OpenVibe's architecture is already here: HumanLoopService approval chain, escalation_rules in soul.yaml, daily_optimize workflows that reallocate spend within CAC guardrails.

### Agent-Native vs Agent-Augmented

The more interesting future isn't old companies adding agents as features — it's fully agentic companies built from scratch around agent workflows. Notion adding agents to docs is agent-augmented. A company where agents ARE the workforce (with humans as supervisors/escalation) is agent-native. OpenVibe is infrastructure for agent-native companies — not "add AI to your existing workflow" but "build your company around human+agent collaboration from day one."

## Open Source Launch Plan (2026-02-24)

### Product Roadmap

**Phase 0 — Packaging (2 weeks)**
- v5 → clean open source repo, strip Vibe Inc business data
- `pip install openvibe` works
- 3 example role templates (extracted from vibe-inc, sanitized)
- Quickstart: clone → install → run demo agent → 5 minutes
- README: one sentence what + why + how

**Phase 1 — Developer Experience (month 1-2)**
- `vibe init --template <name>` one-command role creation
- Contributing guide: how to add operators, tools, role templates
- GitHub Actions CI
- 3-5 building-in-public articles (Vibe Inc real case studies)

**Phase 2 — Community (month 2-4)**
- Template contribution mechanism
- Discord / GitHub Discussions
- First external contributors submit operators (Stripe, Zendesk, QuickBooks...)
- "Vibe your first role" tutorial series

**Phase 3 — Hosted Platform (month 4-6)**
- vibe.us hosted version
- Select template → connect API keys → run
- Free tier (1 role, limited hours) → paid tier
- Vibe Inc dashboard as reference customer

### GTM Path

GitHub launch → HN "Show HN" post → building-in-public content → developer adoption → community templates → hosted platform conversion

### Business Model

| Layer | Price | Who |
|-------|-------|-----|
| Open source (self-host) | Free | Developers, technical teams |
| Hosted platform | $/agent-hour | Teams without devops |
| Enterprise (self-host + support) | Contract | Regulated industries |

### Core Metrics

- Phase 0-1: GitHub stars, clones, quickstart completion rate
- Phase 2: Contributors, templates submitted, companies using
- Phase 3: Hosted signups, conversion rate, revenue

## Strategic Deep Dive (2026-02-25)

Five parallel research agents investigated core strategic assumptions. Results saved in `memory/strategy.md`.

**Key assumption corrections:**
- Model companies ARE moving into orchestration (OpenAI Frontier, Anthropic Cowork). The "separate orchestration layer" thesis needs reframing.
- Big tech CAN connect cross-platform (1,400+ connectors). They WON'T go deep on cross-vendor domain intelligence. Moat = domain depth, not connection.
- "OS for X" winners all started with a narrow wedge (Stripe = 7 lines, Shopify = snowboard shop). None declared "OS" on day one.

**Framework: Bet Sequence (not destination picking)**
- In Perez Frenzy phase, design a sequence of bets: each affordable, valuable standalone, informative, compounding.
- Bet 1: Dogfood daily report (30 days) → Bet 2: 3-5 workflows live → Bet 3: Package for others (3 paths: open source / hardware upsell / education vertical) → Bet 4: Revenue → Bet 5: Platform ecosystem
- ~2 years to credible platform (consistent with Stripe/Twilio/Shopify historical data)

**Hardware+AI vertical analysis:**
- K-12 Private Schools = strongest sub-vertical for hardware+AI structural change (AI co-teacher that sees Board + hears classroom)
- Healthcare = pass for now (HIPAA burden, AI scribe market already crowded)
- Hardware advantage: gives AI agents physical presence (eyes/ears/canvas) that pure-software competitors can't match

**Production gap assessment:**
- Architecture is solid. Production-hardening needed: auth, database, error handling, logging, deployment infra, async.
- Estimates: dogfood 1 workflow = 2-3 weeks, open source = 4-6 weeks, hosted platform = 3-5 months
- "Building agent = 20% effort. Production-ready = 80%." (AWS DevOps Agent team)

## Not Yet Done

- **D2C Content** — D2C design has 3 roles; Growth + Strategy built, Content remaining
- **Google Ads** — credentials pending, not yet tested
- **Meta API optimization** — N+1 query pattern needs refactor (DESIGN.md §8)
- **Phase 3 gate not passed** — needs 3 Vibe Inc roles live + 1 end-to-end workflow; agent loop validated but Meta rate limit blocks repeat runs
- **Known debt** (documented in DESIGN.md §6-8):
  - Model duality: V3 RoleTemplate/RoleSpec coexists with V5 TemplateConfig/RoleInstance
  - YAML templates not connected to TemplateRegistry
  - System roles not injected into workspaces
  - Meta N+1 query pattern (§8)

## Future: Multi-Developer Readiness

When ready to onboard the team (each person/group owns a role), need to address:

1. **Role Developer Guide** — onboarding doc covering Role/Operator/Tool contract, soul writing, test patterns
2. **Tool ownership** — shared `tools/` needs per-domain ownership; shared tools (e.g. GA4) need frozen interfaces
3. **Test reorg** — flat `tests/` → per-role subdirectories
4. **CI pipeline** — GitHub Actions running pytest on PRs
5. **Shared memory write protocol** — per-role namespace or ownership rules for `shared_memory/` YAML
6. **Example role template** — empty role + operator + test skeleton for new developers

## Rules

- Important milestone complete → pause for user confirmation
- No external calls without confirmation
- UI direction unclear → pause for user sketch

---

*Updated: 2026-02-25 — Strategic deep dive: 5 research agents, bet sequence framework, assumption corrections, industry analysis. See memory/strategy.md.*
