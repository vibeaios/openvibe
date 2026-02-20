# OpenVibe Progress

> Read this first at session start, then follow Session Resume Protocol in CLAUDE.md.

---

## Current State

**Version:** V5 — Platform Prototype
**Phase:** D2C Growth + D2C Strategy complete (12 operators, 53 workflows, ~64 tools)

| Package | Path | Version | Tests |
|---------|------|---------|-------|
| openvibe-sdk | `v5/openvibe-sdk/` | v1.0.0 | 279 |
| openvibe-runtime | `v5/openvibe-runtime/` | v1.0.0 | 28 |
| openvibe-platform | `v5/openvibe-platform/` | v1.0.0 | 60 |
| openvibe-cli | `v5/openvibe-cli/` | v1.0.0 | 15 |
| vibe-inc | `v5/vibe-inc/` | v0.1.0 | 367 |

**Total: 749 tests passing, 2 skipped (real API)**

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

**D2CGrowth role** — 10 operators, 48 workflows, ~62 API tools:
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
- `v5/vibe-inc/` — src layout, hatchling build, full test suite (367 tests)
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

## Not Yet Done

- **No real API calls yet** — tools implemented with mock tests only, no live credentials tested
- **D2C Content** — D2C design has 3 roles; Growth + Strategy built, Content remaining
- **HubSpot CRMOps built** — 6 tools, 4 workflows, but no live API credentials tested yet
- **Phase 3 gate not passed** — needs 3 Vibe Inc roles live + 1 end-to-end workflow with real APIs
- **Known debt** (documented in DESIGN.md §6-7):
  - Model duality: V3 RoleTemplate/RoleSpec coexists with V5 TemplateConfig/RoleInstance
  - YAML templates not connected to TemplateRegistry
  - System roles not injected into workspaces

## Rules

- Important milestone complete → pause for user confirmation
- No external calls without confirmation
- UI direction unclear → pause for user sketch

---

*Updated: 2026-02-20 — D2C Strategy complete: 12 operators, 53 workflows, 367 vibe-inc tests (749 total)*
