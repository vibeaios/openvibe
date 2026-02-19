# D2C Growth Complete Tool Map + DataOps Role

> Two-role design: D2C Growth (10 operators, ~58 tools) + DataOps (3 operators, ~8 tools).
> Replaces and extends `2026-02-19-adops-multi-platform-design.md`.

**Date:** 2026-02-19
**Status:** Design
**Depends on:** D2C Phase 1 (complete), V5 SDK v1.0.0

---

## 1. Problem Statement

D2C Phase 1 built a D2C Growth skeleton: 2 operators (AdOps + CROps), 4 external tools (Meta Ads, GA4, Shopify pages, shared memory), 6 workflows. This is insufficient for production:

**AdOps is too narrow.** Only Meta Ads. Vibe operates across 7 ad platforms (Meta, Google, Amazon, TikTok, LinkedIn, Pinterest) with fundamentally different campaign structures, bidding strategies, optimization logic, and API patterns. A single `AdOps` operator cannot capture these differences.

**CROps lacks depth.** Only GA4 read + Shopify page read/update. No product management, order analysis, heatmaps, A/B testing, or discount optimization. Cannot diagnose conversion problems or run experiments.

**Email is missing.** D2C without email lifecycle automation (welcome flows, cart abandonment, post-purchase, winback) is leaving money on the table. Email is the highest-ROI channel for retention.

**No data governance.** Every operator directly queries external APIs and interprets results in isolation. No shared understanding of:
- What data exists vs what doesn't
- Which fields map across systems (Mixpanel "purchase_completed" = Shopify "order" = Meta "conversion")
- Data freshness and credibility (GA4 has 24-48h lag, platform conversions over-report by 40-80%)
- What queries to run against which source

**Solution:** Two roles — **DataOps** as the data truth layer, **D2C Growth** with 10 specialized operators that query data through DataOps.

---

## 2. Target Architecture

```
Vibe Inc Tenant
│
├── DataOps (Role) — system-level, shared by all roles
│   ├── CatalogOps          # schema registry, coverage audit, field mapping
│   ├── QualityOps          # freshness, discrepancy detection, credibility scoring
│   └── AccessOps           # unified query interface (Mixpanel, GA4, Redshift)
│
├── D2C Growth (Role)
│   ├── MetaAdOps           # refactored from current AdOps
│   ├── GoogleAdOps         # new
│   ├── AmazonAdOps         # new
│   ├── TikTokAdOps         # new
│   ├── LinkedInAdOps       # new
│   ├── PinterestAdOps      # new
│   ├── CrossPlatformOps    # new — unified CAC, budget allocation
│   ├── EmailOps            # new — Klaviyo lifecycle + campaigns
│   └── CROps              # expanded — Shopify full, heatmaps, A/B testing
│
└── (future: D2C Strategy, D2C Content, Astrocrest — all use DataOps)
```

### 2.1 Data Flow

```
External APIs (Meta, Google, Amazon, TikTok, LinkedIn, Pinterest, Klaviyo, Shopify)
        │
        ▼
DataOps.AccessOps ← unified analytics query interface
        │              (Mixpanel, GA4, Redshift providers)
        ▼
DataOps.QualityOps ← credibility scoring, discrepancy detection
        │
        ▼
DataOps.CatalogOps ← schema registry, field mapping
        │
        ▼
D2C Growth operators query data through DataOps tools
        │
        ▼
D2C Growth operators write actions through platform-specific tools
        │
        ▼
Shared Memory (YAML) ← cross-operator context, benchmarks, results
```

**Key principle:** Operators READ data through DataOps, WRITE actions through their own platform tools. DataOps never modifies external platforms — it's read-only + metadata.

### 2.2 File Layout

```
v5/vibe-inc/src/vibe_inc/
├── roles/
│   ├── data_ops/
│   │   ├── __init__.py              # DataOps role class
│   │   ├── catalog_ops.py           # CatalogOps operator
│   │   ├── quality_ops.py           # QualityOps operator
│   │   ├── access_ops.py            # AccessOps operator
│   │   └── workflows.py             # DataOps workflow factories
│   │
│   └── d2c_growth/
│       ├── __init__.py              # D2CGrowth role class
│       ├── meta_ad_ops.py           # MetaAdOps operator
│       ├── google_ad_ops.py         # GoogleAdOps operator
│       ├── amazon_ad_ops.py         # AmazonAdOps operator
│       ├── tiktok_ad_ops.py         # TikTokAdOps operator
│       ├── linkedin_ad_ops.py       # LinkedInAdOps operator
│       ├── pinterest_ad_ops.py      # PinterestAdOps operator
│       ├── cross_platform_ops.py    # CrossPlatformOps operator
│       ├── email_ops.py             # EmailOps operator (Klaviyo)
│       ├── cro_ops.py               # CROps operator (expanded)
│       └── workflows.py             # D2C Growth workflow factories
│
├── tools/
│   ├── analytics/                   # DataOps analytics abstraction
│   │   ├── __init__.py              # AnalyticsProvider protocol
│   │   ├── mixpanel.py              # MixpanelProvider
│   │   ├── ga4.py                   # GA4Provider (refactored from tools/ga4.py)
│   │   └── redshift.py              # RedshiftProvider
│   │
│   ├── ads/                         # Ad platform tools
│   │   ├── meta_ads.py              # refactored (exists)
│   │   ├── google_ads.py            # new
│   │   ├── amazon_ads.py            # new
│   │   ├── tiktok_ads.py            # new
│   │   ├── linkedin_ads.py          # new
│   │   └── pinterest_ads.py         # new
│   │
│   ├── commerce/                    # Commerce tools
│   │   ├── shopify.py               # expanded (products, orders, collections, discounts)
│   │   └── klaviyo.py               # new — email marketing
│   │
│   ├── optimization/                # CRO tools
│   │   ├── heatmap.py               # Hotjar or Microsoft Clarity
│   │   └── ab_testing.py            # VWO or equivalent
│   │
│   └── shared_memory.py             # exists (unchanged)
│
└── data/
    └── shared_memory/               # exists + extensions
```

---

## 3. DataOps Role

**SOUL:**
```
You are DataOps for Vibe Inc.

Your mission: be the single source of truth about what data exists, how reliable it is,
and how to access it correctly.

Core principles:
- Never let operators query data without understanding its limitations.
- Platform-reported metrics are directional, not factual. Shopify/Redshift = truth.
- Every metric has a freshness lag. Know it. Communicate it.
- Same concept, different names across systems. Map them explicitly.
- When data contradicts, flag it — don't silently pick one.

You do NOT modify external platforms. You are read-only + metadata.
```

### 3.1 CatalogOps — "What data do we have?"

**Purpose:** Maintain a live understanding of all data sources, schemas, field meanings, and coverage gaps.

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `catalog_read` | Read schema registry from shared memory | Returns source definitions, field mappings, coverage |
| `catalog_update` | Update schema registry when new fields/sources discovered | Write to shared_memory/data/ |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key |
|------|-------------------|-------|------------|
| `schema_audit` | Enumerate all connected data sources. For each: list available fields, data types, freshness, coverage. Flag fields that exist in one source but not another. Update catalog. | catalog_read, catalog_update, analytics_query | `audit_result` |
| `field_mapping` | Map equivalent concepts across systems. "conversion" in Meta vs Google vs Shopify vs Mixpanel. Document discrepancies in counting methodology. Maintain mapping in shared memory. | catalog_read, catalog_update | `mapping_result` |
| `coverage_report` | What data do we have? What's missing? What would we need to answer common questions (e.g., "What's our Net New CAC by channel?")? Progressive disclosure format. | catalog_read | `coverage_report` |

#### Workflows

| Workflow | Nodes | Cadence |
|----------|-------|---------|
| `data_catalog_audit` | schema_audit + field_mapping | Weekly |
| `data_coverage_report` | coverage_report | On demand |

#### Shared Memory Output

```yaml
# shared_memory/data/catalog.yaml
sources:
  mixpanel:
    type: event_tracking
    freshness: real-time
    covers: [user_events, funnels, cohorts, retention, user_profiles]
    missing: [ad_spend, impression_data, server-side_only_events]
    credibility: high
    notes: "Primary event tracker. All client-side + server-side events flow here."

  ga4:
    type: web_analytics
    freshness: 24-48h_lag
    covers: [sessions, traffic_source, acquisition_channel, basic_ecommerce]
    missing: [server-side_events, offline_conversions, detailed_user_profiles]
    credibility: medium
    notes: "Sampling on high-volume properties. Cookie limitations reduce accuracy. Good for traffic source analysis."

  redshift:
    type: data_warehouse
    freshness: depends_on_etl  # typically 1-6h
    covers: [everything]
    missing: [real-time]
    credibility: highest
    notes: "Single source of truth. All sources ETL here. Use for final reporting and cross-source validation."

  shopify:
    type: commerce_platform
    freshness: real-time
    covers: [orders, revenue, products, customers, inventory, discounts]
    missing: [pre-purchase_behavior, ad_attribution]
    credibility: high
    notes: "Source of truth for transactions. Customer.orders_count = 1 → Net New."

  meta_ads:
    type: ad_platform
    freshness: near_real-time
    covers: [campaign_performance, audience_insights, creative_metrics]
    missing: [post-click_behavior, true_conversions]
    credibility: low_for_conversions
    notes: "Over-reports conversions by 30-60%. Use for within-platform trend analysis only."

  google_ads:
    type: ad_platform
    freshness: near_real-time
    covers: [campaign_performance, keyword_data, quality_scores, search_terms]
    missing: [post-click_behavior_detail]
    credibility: low_for_conversions
    notes: "Cost in micros (÷1M). Over-reports conversions. Good for keyword/search intent data."

  amazon_ads:
    type: ad_platform
    freshness: 3-day_lag_recommended
    covers: [campaign_performance, search_terms, keyword_bids, ASIN_targeting]
    missing: [off-amazon_behavior]
    credibility: medium
    notes: "7-day attribution window. Data restates for 3 days. Don't optimize on <3 day data."

  tiktok_ads:
    type: ad_platform
    freshness: near_real-time
    covers: [campaign_performance, video_metrics, audience_data]
    missing: [post-click_behavior_detail]
    credibility: low_for_conversions
    notes: "Pixel misses ~40% conversions without Events API (CAPI)."

  linkedin_ads:
    type: ad_platform
    freshness: near_real-time
    covers: [campaign_performance, demographic_breakdown, lead_gen_forms]
    missing: [revenue_attribution_without_crm]
    credibility: medium
    notes: "Longer attribution. Best for B2B lead quality metrics."

  pinterest_ads:
    type: ad_platform
    freshness: near_real-time
    covers: [campaign_performance, pin_metrics, shopping_data]
    missing: [post-click_behavior_detail]
    credibility: low_for_conversions
    notes: "Long consideration window. View-through attribution inflates conversions."

  klaviyo:
    type: email_marketing
    freshness: real-time
    covers: [email_performance, flow_metrics, subscriber_profiles, revenue_attribution]
    missing: [pre-email_behavior]
    credibility: high_for_email_metrics
    notes: "Revenue attribution uses last-click with 5-day window by default."

# shared_memory/data/field_mapping.yaml
conversion:
  mixpanel: "purchase_completed"
  ga4: "purchase"
  shopify: "orders.created"
  meta_ads: "offsite_conversion.fb_pixel_purchase"
  google_ads: "conversions"
  amazon_ads: "attributedSales7d"  # 7-day attributed sales
  tiktok_ads: "complete_payment"
  linkedin_ads: "externalWebsiteConversions"
  pinterest_ads: "checkout"
  klaviyo: "Placed Order"
  redshift: "fact_orders.order_id COUNT"
  note: "Platform-reported conversions ALWAYS over-count vs Shopify orders. Use Shopify/Redshift as truth."

revenue:
  mixpanel: "purchase_completed.properties.revenue"
  ga4: "purchaseRevenue"
  shopify: "orders.total_price"
  klaviyo: "Placed Order.$value"
  redshift: "fact_orders.gross_revenue"
  note: "Shopify = gross. Redshift can compute net (after refunds, discounts). Klaviyo attributes based on email click."

new_customer:
  shopify: "customer.orders_count == 1"
  redshift: "dim_customers.first_order_date = order_date"
  mixpanel: "NOT available natively — needs custom property or Redshift lookup"
  ga4: "newUsers (session-level, NOT customer-level)"
  note: "Critical for Net New CAC. Only Shopify/Redshift can reliably identify first-time buyers."

ad_spend:
  meta_ads: "spend (USD)"
  google_ads: "metrics.cost_micros / 1000000 (USD)"
  amazon_ads: "cost (USD)"
  tiktok_ads: "spend (USD)"
  linkedin_ads: "costInLocalCurrency (USD)"
  pinterest_ads: "spend (USD, in micros ÷ 1M)"
  klaviyo: "N/A — no ad spend"
  redshift: "fact_ad_spend (aggregated from all platforms)"
  note: "Google and Pinterest report in micros. Normalize to USD float."
```

### 3.2 QualityOps — "Can we trust this data?"

**Purpose:** Monitor data freshness, detect cross-source discrepancies, score metric credibility.

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `quality_check` | Run freshness + completeness check on a data source | Returns lag, missing fields, row counts |
| `discrepancy_detect` | Compare same metric across 2+ sources | Returns delta, % difference, recommendation |
| `credibility_score` | Score a metric's trustworthiness (0-1) | Based on source, freshness, cross-validation |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key |
|------|-------------------|-------|------------|
| `freshness_monitor` | For each connected source, check: when was data last updated? Is it within expected SLA? Flag stale data. Alert if Redshift ETL is >6h behind or Mixpanel events stop flowing. | quality_check, analytics_query | `freshness_report` |
| `discrepancy_report` | Compare platform-reported conversions vs Shopify orders for each ad platform. Calculate over-reporting ratio. Flag if any platform's ratio changed significantly (drift detection). Compare Mixpanel events vs GA4 sessions for consistency. | discrepancy_detect, analytics_query | `discrepancy_report` |
| `credibility_assessment` | For a requested metric (e.g., "Net New CAC for Bot via Meta"), assess: which sources contribute, what's the freshness, what's the cross-validation status, what's the confidence level. Return credibility score + caveats. | credibility_score, catalog_read | `credibility_result` |

#### Workflows

| Workflow | Nodes | Cadence |
|----------|-------|---------|
| `data_quality_daily` | freshness_monitor | Daily (6am, before operator runs) |
| `data_discrepancy_weekly` | discrepancy_report | Weekly |
| `data_credibility_check` | credibility_assessment | On demand (called by other operators) |

### 3.3 AccessOps — "How do I get the data?"

**Purpose:** Provide a unified query interface. Operators call AccessOps tools instead of directly querying Mixpanel/GA4/Redshift.

#### Analytics Provider Protocol

```python
class AnalyticsProvider(Protocol):
    """Unified analytics interface. Each provider implements this."""

    def query_metrics(
        self,
        metrics: list[str],
        dimensions: list[str] | None = None,
        date_range: str = "last_7d",
        filters: dict | None = None,
    ) -> dict:
        """Aggregated metrics. e.g. sessions, conversions, revenue by channel."""

    def query_funnel(
        self,
        steps: list[str],
        date_range: str = "last_7d",
        filters: dict | None = None,
    ) -> dict:
        """Funnel drop-off analysis."""

    def query_events(
        self,
        event_name: str,
        date_range: str = "last_7d",
        properties: list[str] | None = None,
        filters: dict | None = None,
    ) -> dict:
        """Raw event stream with property breakdowns."""

    def query_cohort(
        self,
        cohort_property: str,
        metric: str,
        date_range: str = "last_90d",
    ) -> dict:
        """Cohort analysis. e.g. retention by signup week."""

    def query_sql(self, sql: str) -> dict:
        """Raw SQL. Redshift only. Errors on other providers."""
```

#### Provider Routing

| Query Type | Default Provider | Fallback | Why |
|-----------|-----------------|----------|-----|
| Event tracking, funnels, cohorts | Mixpanel | Redshift | Mixpanel is primary event tracker |
| Traffic source, acquisition | GA4 | Mixpanel | GA4 excels at channel attribution |
| Raw / custom joins / reporting | Redshift | - | Only source with all data |
| Real-time active users | Mixpanel | GA4 | Mixpanel Live View |
| Transaction truth | Shopify API | Redshift | Source of truth for orders |

#### Tools (exposed to all operators)

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `analytics_query_metrics` | Aggregated metrics via default provider | Routes to Mixpanel/GA4/Redshift based on query type |
| `analytics_query_funnel` | Funnel analysis | Defaults to Mixpanel |
| `analytics_query_events` | Event-level data | Defaults to Mixpanel |
| `analytics_query_cohort` | Cohort retention/LTV | Defaults to Mixpanel |
| `analytics_query_sql` | Raw Redshift SQL | Redshift only |
| `analytics_cross_validate` | Same query against 2 providers, return comparison | For discrepancy detection |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key |
|------|-------------------|-------|------------|
| `route_query` | Receive analytics request from another operator. Determine best provider based on query type, freshness requirements, and data availability. Execute query. Attach credibility metadata to response. | All analytics tools | `query_result` |
| `build_report` | Compose a multi-source report. Pull metrics from appropriate providers. Cross-validate key numbers. Format with progressive disclosure. Include data caveats. | All analytics tools, credibility_score | `report` |
| `cache_refresh` | Refresh cached query results for common queries (daily CAC by platform, weekly funnel, monthly cohort). Store in shared memory for fast operator access. | All analytics tools, shared_memory | `cache_result` |

#### Workflows

| Workflow | Nodes | Cadence |
|----------|-------|---------|
| `analytics_query` | route_query | On demand (called by operators) |
| `analytics_report` | build_report | On demand |
| `analytics_cache_refresh` | cache_refresh | Daily (5am, before quality checks) |

#### Provider Implementations

**MixpanelProvider:**
```python
# SDK: mixpanel-utils or direct HTTP (Mixpanel Data Export API + Query API)
# Auth: Service Account (project_id + service_account_username + service_account_secret)
# Endpoints:
#   - /api/2.0/export — raw event export
#   - /api/2.0/insights — JQL queries
#   - /api/2.0/funnels — funnel analysis
#   - /api/2.0/retention — cohort retention
#   - /api/2.0/segmentation — event segmentation
# Env: MIXPANEL_PROJECT_ID, MIXPANEL_SERVICE_ACCOUNT, MIXPANEL_SERVICE_SECRET
```

**GA4Provider:**
```python
# SDK: google-analytics-data (exists, refactored into provider pattern)
# Auth: Service Account JSON
# Env: GA4_PROPERTY_ID, GA4_SERVICE_ACCOUNT_JSON
```

**RedshiftProvider:**
```python
# SDK: psycopg2 or redshift_connector
# Auth: IAM or username/password
# Env: REDSHIFT_HOST, REDSHIFT_PORT, REDSHIFT_DB, REDSHIFT_USER, REDSHIFT_PASSWORD
#      or REDSHIFT_IAM_ROLE for IAM auth
# Notes: Connection pooling required. Query timeout 30s default. UNLOAD for large results.
```

---

## 4. D2C Growth — Ad Platform Operators

> Sections 4.1-4.5 (Meta, Google, Amazon, TikTok, LinkedIn) are fully designed in
> `2026-02-19-adops-multi-platform-design.md` §4.1-4.5. Refer to that document for:
> - Per-platform tools, agent nodes, workflows, platform-specific rules
> - Platform comparison matrix (API/SDK, campaign structure, bidding, metrics)
> - SDK quick reference code samples
>
> Section 4.6 (Pinterest) and beyond are new.

### Summary of Existing Platform Operators

| Operator | Tools | Nodes | Workflows | SDK |
|----------|-------|-------|-----------|-----|
| MetaAdOps | 5 (read, create, update, rules, audiences) | 5 | 4 | `facebook-business` |
| GoogleAdOps | 5 (query, mutate, budget, recommendations, conversions) | 5 | 4 | `google-ads` |
| AmazonAdOps | 6 (campaigns, keywords, targets, report, bid_recs, budget_rules) | 5 | 4 | `python-amazon-ad-api` |
| TikTokAdOps | 6 (campaigns, adgroups, ads, report, audiences, rules) | 5 | 3 | `httpx` (direct) |
| LinkedInAdOps | 6 (campaigns, creatives, analytics, audiences, forms, targeting) | 5 | 4 | `httpx` (direct) |

### Key change: All ad operators now query conversion/attribution data through DataOps

Before: `daily_optimize` calls `meta_ads_read` and trusts platform conversions.
After: `daily_optimize` calls `meta_ads_read` for platform metrics AND `analytics_query_metrics` (via DataOps) for Shopify/Redshift-verified conversions. Compares both. Reports discrepancy.

### 4.6 PinterestAdOps

**SDK:** Direct HTTP via `httpx` (Pinterest Marketing API v5)
**Auth:** OAuth2. Access token + refresh token. Sandbox available for testing.
**Base URL:** `https://api.pinterest.com/v5/`

#### Platform Comparison (extends §3 matrix)

| Aspect | Pinterest |
|--------|-----------|
| **Python SDK** | `pinterest-api-sdk` (official) or direct HTTP |
| **API style** | REST (v5) |
| **Auth** | OAuth2, access + refresh tokens |
| **Rate limits** | 1000/min per user token, 200/min for write ops |
| **Reporting** | Async (create report → poll → download) |
| **Hierarchy** | Campaign → Ad Group → Ad (promoted Pin) |
| **Creative** | Image Pin, Video Pin, Carousel, Shopping (from catalog), Idea Pin |
| **Budget model** | Campaign daily/lifetime budget |
| **Automation** | Performance+ campaigns (auto-targeting, auto-bidding) |
| **Bidding** | Automatic, Custom (max CPC/CPM), Target ROAS |
| **Primary lever** | Pin quality + keyword/interest targeting + shopping catalog |
| **Key metric** | Outbound Click Rate (vs total clicks — many clicks stay on Pinterest) |
| **Unique** | Long consideration window (users save Pins for weeks). View-through attribution inflates. |
| **Cost bench** | CPC $0.10-1.50, CPM $2-5 (cheapest among major platforms) |

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `pinterest_ads_campaigns` | CRUD campaigns | `POST/GET/PATCH /ad_accounts/{id}/campaigns` |
| `pinterest_ads_adgroups` | CRUD ad groups + targeting | Keywords, interests, demographics, audiences, auto-targeting |
| `pinterest_ads_pins` | Promote Pins as ads | Image, video, carousel, shopping. Link to Pin ID or create new. |
| `pinterest_ads_report` | Async analytics reporting | `POST /ad_accounts/{id}/reports`, poll, download CSV/JSON |
| `pinterest_ads_audiences` | Customer list, actalike, website visitors | `POST /ad_accounts/{id}/audiences`. Actalike = Pinterest's lookalike. |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create Consideration or Conversion campaign. Set automatic bidding initially. Keyword + interest targeting for discovery. Shopping campaigns from product catalog. Min 4 Pins per ad group for creative testing. Name: `[Product]-[Objective]-[Targeting]-[Date]`. | pinterest_ads_campaigns, pinterest_ads_adgroups, pinterest_ads_pins | `campaign_result` | Human required |
| `daily_optimize` | Review Outbound Click Rate (not total clicks — most "clicks" stay on Pinterest). Adjust bids on ad groups with CTR below 0.5%. Pause ad groups spending >2x target CPA with <0.3% outbound CTR. Watch for seasonal trends (Pinterest users plan ahead). | pinterest_ads_report, pinterest_ads_adgroups | `optimization_result` | Autonomous within rules |
| `weekly_report` | CPA by campaign. Outbound vs total click ratio. Top performing Pins. Shopping performance (if catalog connected). Audience overlap check. Progressive disclosure. | pinterest_ads_report | `report` | None |
| `audience_manage` | Create Actalike audiences (Pinterest's lookalike) from converters. Upload customer lists. Create website visitor audiences from tag. Refresh monthly. | pinterest_ads_audiences | `audience_result` | Autonomous |

#### Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `pinterest_campaign_create` | campaign_create | Manual | On demand |
| `pinterest_daily_optimize` | daily_optimize | Scheduled | Daily |
| `pinterest_weekly_report` | weekly_report + audience_manage | Scheduled | Weekly |

#### Platform-Specific Rules

- **Outbound clicks matter, total clicks don't.** Pinterest inflates "click" numbers because users click to expand Pins (closeup), not to visit your site. Always filter for "outbound click" metrics.
- **Long consideration cycle.** Users save Pins and convert days/weeks later. Don't over-optimize on short attribution windows. Use 30-day click + 30-day view cautiously.
- **Shopping catalog integration.** If Shopify product feed is connected, Shopping campaigns auto-generate Pins from product catalog. High-intent, low effort.
- **Seasonal planning.** Pinterest users search 2-3 months ahead of events. Start campaigns early for seasonal products.
- **Performance+ campaigns.** Pinterest's automated campaign type. Less control but often lower CPA. Test alongside manual campaigns.

#### SDK Quick Reference

```python
import httpx

BASE = "https://api.pinterest.com/v5"
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

# List campaigns
resp = httpx.get(f"{BASE}/ad_accounts/{ad_account_id}/campaigns", headers=headers)
campaigns = resp.json()["items"]

# Create campaign
resp = httpx.post(f"{BASE}/ad_accounts/{ad_account_id}/campaigns", headers=headers,
                  json={"name": "Bot-Awareness-Q1", "objective_type": "TRAFFIC",
                        "daily_spend_cap": 5000,  # in micros ($5.00)
                        "status": "PAUSED"})

# Request async report
resp = httpx.post(f"{BASE}/ad_accounts/{ad_account_id}/reports", headers=headers,
                  json={"start_date": "2026-02-01", "end_date": "2026-02-18",
                        "columns": ["SPEND_IN_DOLLAR", "OUTBOUND_CLICK", "CPC_IN_DOLLAR"],
                        "level": "CAMPAIGN", "granularity": "DAY"})
report_token = resp.json()["token"]

# Poll report
resp = httpx.get(f"{BASE}/ad_accounts/{ad_account_id}/reports?token={report_token}", headers=headers)
# status: "IN_PROGRESS" or "FINISHED" with download URL
```

---

## 5. CrossPlatformOps

> Fully designed in `2026-02-19-adops-multi-platform-design.md` §5.
> Updated here: now aggregates 7 platforms (added Pinterest) and queries truth data through DataOps.

### Updates from original design

**Tools:** `unified_metrics_read` now pulls Pinterest data alongside the other 6 platforms.

**Unified CAC calculation updated:**
```
True Unified CAC = Total Ad Spend (7 platforms + Klaviyo) / Total New Customers (from Shopify via DataOps)
                    ↑ DataOps.analytics_query_sql("SELECT ...") for Shopify truth
                    ↑ Each platform's spend via platform-specific tools

Blended ROAS (MER) = Total Revenue (Shopify via DataOps) / Total Ad Spend (all platforms)
```

**Budget allocation updated (7 platforms):**

| Platform | % of Budget | Role |
|----------|-------------|------|
| Google (Search+Shopping+YouTube) | 33-38% | Bottom-funnel conversion |
| Meta (Facebook+Instagram) | 23-28% | Mid-funnel + retargeting |
| Amazon | 15-18% | Bottom-funnel + organic flywheel |
| TikTok | 8-12% | Top-funnel awareness |
| Pinterest | 3-5% | Visual discovery + shopping |
| LinkedIn | 1-3% | B2B niche |
| Testing (new channels) | 3-5% | Exploration budget |

---

## 6. EmailOps (Klaviyo)

**SDK:** `klaviyo-api` (`pip install klaviyo-api`) — official Python SDK
**Auth:** Private API key (simple, non-expiring)
**Base URL:** `https://a.]klaviyo.com/api/` (v2024-10-15+)

### 6.1 Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `klaviyo_campaigns` | Create, schedule, send, cancel email campaigns | `POST /campaigns`, includes A/B test configuration |
| `klaviyo_flows` | CRUD automated flows (triggers, actions, timing, splits) | `POST /flows`. Flows = automated sequences (welcome, cart abandon, etc.) |
| `klaviyo_segments` | Create/update segments by behavior, properties, engagement | `POST /segments`. Dynamic segments update automatically. |
| `klaviyo_metrics` | Read email performance: opens, clicks, revenue, unsubscribes | `GET /metrics/`. Aggregate + timeline views. |
| `klaviyo_profiles` | Read/update subscriber profiles, suppress/unsuppress | `GET/PATCH /profiles/`. Subscriber management. |
| `klaviyo_catalogs` | Sync product catalog for dynamic email content | `POST /catalog-items/`. Used in product recommendation blocks. |

### 6.2 Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create promotional email campaign. A/B test subject lines (min 1000 recipients per variant). Use product-specific messaging from shared memory. Segment by engagement level (engaged = opened in 90 days). Send time optimization on. | klaviyo_campaigns, klaviyo_segments, shared_memory | `campaign_result` | Human required |
| `flow_optimize` | Analyze automated flow performance. Check: welcome series completion rate, cart abandonment recovery rate (target >5%), post-purchase repeat rate, winback re-engagement rate. Adjust timing between emails. Identify underperforming steps. | klaviyo_flows, klaviyo_metrics | `flow_result` | Autonomous for timing, Human for content |
| `segment_refresh` | Update key segments: VIPs (3+ orders), At-Risk (no open in 60 days), Cart Abandoners (active cart, no purchase in 24h), New Subscribers (<30 days). Ensure segments don't overlap for campaign exclusions. | klaviyo_segments, klaviyo_profiles, analytics_query_events | `segment_result` | Autonomous |
| `lifecycle_report` | Revenue per flow. Revenue per campaign. Subscriber growth vs churn. List health (engaged %, unsubscribe rate). Compare email-attributed revenue vs Shopify-attributed (via DataOps). Progressive disclosure. | klaviyo_metrics, analytics_query_metrics | `lifecycle_report` | None |
| `list_hygiene` | Identify unengaged subscribers (no open in 120+ days). Run sunset flow (re-engagement attempt → suppress if no response). Monitor deliverability (bounce rate, spam complaints). Keep list health >95% engaged. | klaviyo_profiles, klaviyo_segments, klaviyo_flows | `hygiene_result` | Human for suppression >1000 profiles |

### 6.3 Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `email_campaign_create` | campaign_create | Manual | On demand |
| `email_flow_optimize` | flow_optimize | Scheduled | Weekly |
| `email_lifecycle_report` | lifecycle_report + segment_refresh | Scheduled | Weekly |
| `email_list_hygiene` | list_hygiene | Scheduled | Monthly |

### 6.4 Core Email Flows (pre-configured in Klaviyo)

| Flow | Trigger | Emails | Key Metric |
|------|---------|--------|-----------|
| **Welcome Series** | New subscriber | 3-5 over 7 days | Completion rate, first purchase rate |
| **Cart Abandonment** | Added to cart, no purchase in 1h | 2-3 over 48h | Recovery rate (target >5%) |
| **Browse Abandonment** | Viewed product, no cart in 24h | 1-2 over 48h | Add-to-cart rate |
| **Post-Purchase** | Order confirmed | 2-3 over 14 days | Review rate, repeat purchase rate |
| **Winback** | No purchase in 60 days | 2-3 over 14 days | Re-engagement rate |
| **VIP** | 3+ orders | Ongoing exclusives | LTV growth |

### 6.5 Platform-Specific Rules

- **Revenue attribution is last-click with 5-day window.** Klaviyo will claim revenue from email clicks within 5 days. Compare vs Shopify total to avoid double-counting with ad platforms.
- **Deliverability is everything.** Suppress unengaged subscribers aggressively. Gmail/Yahoo 2024+ rules: keep spam complaint rate <0.1%, provide one-click unsubscribe.
- **A/B test sample size.** Need 1000+ recipients per variant for statistical significance on open rate. Smaller lists → skip A/B, test sequentially.
- **Flow vs Campaign.** Flows are automated (set and optimize). Campaigns are one-time sends. Revenue should shift toward flows over time (target: 40-60% from flows).
- **Catalog sync.** If Shopify-Klaviyo integration active, catalog syncs automatically. Dynamic product blocks in emails pull real-time inventory/pricing.

### 6.6 SDK Quick Reference

```python
from klaviyo_api import KlaviyoAPI

klaviyo = KlaviyoAPI(api_key=private_api_key)

# List flows
flows = klaviyo.Flows.get_flows()

# Get flow performance
flow_metrics = klaviyo.Metrics.query_metric_aggregates(body={
    "data": {
        "type": "metric-aggregate",
        "attributes": {
            "metric_id": "PLACED_ORDER_METRIC_ID",
            "measurements": ["count", "sum_value"],
            "filter": ["greater-or-equal(datetime,2026-02-01)"],
            "by": ["$flow"],
        }
    }
})

# Create segment
segment = klaviyo.Segments.create_segment(body={
    "data": {
        "type": "segment",
        "attributes": {
            "name": "Cart Abandoners - 24h",
            "definition": {
                "condition_groups": [{
                    "conditions": [{
                        "type": "profile-metric",
                        "metric": {"id": "ADDED_TO_CART_METRIC_ID"},
                        "filter": {"type": "date", "operator": "after", "value": "-1d"}
                    }]
                }]
            }
        }
    }
})

# Send campaign
campaign = klaviyo.Campaigns.create_campaign(body={
    "data": {
        "type": "campaign",
        "attributes": {
            "name": "Bot Spring Promo",
            "audiences": {"included": [segment_id], "excluded": [suppressed_id]},
            "send_strategy": {"method": "smart_send_time"},
        }
    }
})
```

---

## 7. CROps (Expanded)

**Current state:** GA4 read + Shopify page read/update, 3 agent nodes.
**Expanded:** Shopify full + Heatmaps + A/B Testing, 6 agent nodes. All analytics via DataOps.

### 7.1 Tools

| Tool Function | Source | Operations | Notes |
|---------------|--------|-----------|-------|
| `shopify_products` | Shopify Admin API | CRUD products, variants, inventory levels | `GET/POST/PUT /admin/api/2024-01/products.json` |
| `shopify_orders` | Shopify Admin API | Read orders, refunds, fulfillments | `GET /admin/api/2024-01/orders.json`. Read-only for analysis. |
| `shopify_collections` | Shopify Admin API | Manage collections, sort rules | Smart collections (rule-based) + custom collections |
| `shopify_discounts` | Shopify Admin API | Create/manage price rules + discount codes | Automatic + code-based. Amount/percentage/BXGY/free shipping. |
| `shopify_page_read` | Shopify Admin API | Read page content | Existing |
| `shopify_page_update` | Shopify Admin API | Update page content | Existing. Human approval required. |
| `heatmap_read` | Microsoft Clarity | Read heatmap data, scroll depth, dead clicks, rage clicks | Clarity API: `GET /export/{projectId}/` |
| `heatmap_recordings` | Microsoft Clarity | Get session recording summaries | Filter by page, device, user segment |
| `ab_test_read` | VWO | Read experiment status, variant performance, significance | `GET /experiments/{id}` |
| `ab_test_manage` | VWO | Create/start/stop/archive experiments | `POST /experiments`. Human approval for start. |

Note: `ga4_read` is removed from CROps tools. All analytics queries go through DataOps `analytics_*` tools.

### 7.2 Agent Nodes

| Node | System Prompt Focus | Tools + DataOps | Output Key | Approval |
|------|-------------------|----------------|------------|----------|
| `experiment_analyze` | Read A/B test results from VWO. Cross-validate with DataOps analytics (Mixpanel funnel for test variants). Require statistical significance (p<0.05, min 1000 visitors/variant). Compare conversion uplift vs revenue uplift (they can diverge). Recommend: declare winner, extend test, or kill. | ab_test_read, analytics_query_funnel | `analysis` | None |
| `funnel_diagnose` | Full funnel: sessions → PDP view → scroll → add to cart → checkout → purchase. Pull from DataOps (Mixpanel funnel). Overlay with heatmap data (Clarity) — where do users actually look? Where do they rage-click? Identify top 3 bottlenecks. Compare traffic quality by source (organic vs paid vs email). | analytics_query_funnel, heatmap_read, heatmap_recordings | `diagnosis` | None |
| `page_optimize` | Read current page from Shopify. Read heatmap for that page (scroll depth, click patterns). Read winning narrative from shared memory. Propose specific changes (headline, CTA, body). Show before/after. If A/B testing available, recommend test instead of direct change. | shopify_page_read, shopify_page_update, heatmap_read, ab_test_manage, shared_memory | `optimization_result` | Human required |
| `product_optimize` | Analyze product performance: views → add-to-cart → purchase rate by product. Identify underperformers. Compare product page scroll depth and click patterns via heatmaps. Recommend: title/description changes, image reorder, pricing adjustments, collection placement. | shopify_products, analytics_query_metrics, heatmap_read | `product_result` | Human for price changes |
| `discount_strategy` | Analyze past discount performance: incremental revenue vs margin erosion. Create targeted discounts for specific segments (cart abandoners, first-time buyers, winback). Set automatic discounts for collection-level promotions. Measure lift vs baseline. | shopify_discounts, shopify_orders, analytics_query_metrics | `discount_result` | Human required |
| `conversion_report` | Weekly CRO report. Overall CVR trend. Funnel metrics. Active experiment results. Top heatmap insights. Page performance ranking. Revenue impact of changes. Progressive disclosure. | analytics_query_metrics, analytics_query_funnel, ab_test_read, heatmap_read | `conversion_report` | None |

### 7.3 Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `cro_experiment_analyze` | experiment_analyze | Scheduled / On demand | Daily (for active tests) |
| `cro_funnel_diagnose` | funnel_diagnose | Scheduled | Weekly |
| `cro_page_optimize` | page_optimize | Manual | On demand |
| `cro_conversion_report` | conversion_report + product_optimize | Scheduled | Weekly |
| `cro_discount_strategy` | discount_strategy | Manual / Scheduled | Monthly or event-driven |

### 7.4 Heatmap + A/B Testing Details

**Microsoft Clarity** (chosen over Hotjar):
- Free, unlimited traffic
- API for data export (heatmaps, recordings, metrics)
- Integrates with GA4
- Session recordings with rage click / dead click / quick back detection
- Env: `CLARITY_PROJECT_ID`, `CLARITY_API_KEY`

**VWO** (Visual Website Optimizer):
- Server-side + client-side testing
- API for experiment management
- Bayesian statistics (faster decisions than frequentist)
- Env: `VWO_ACCOUNT_ID`, `VWO_API_KEY`

---

## 8. Soul & Escalation Rules

### D2C Growth Soul (updated for 10 operators)

```python
_SOUL = """You are D2C Growth for Vibe Inc.

Your mission: manage paid acquisition, email lifecycle, and conversion optimization
across Meta, Google, Amazon, TikTok, LinkedIn, Pinterest, and Klaviyo
for Vibe's hardware products (Bot, Dot, Board).

Core principles:
- Net New CAC is the only CAC that matters. Never report blended platform metrics as truth.
- Use Shopify/Redshift data (via DataOps) as source of truth for customer counts.
- Each platform has different strengths: Google captures intent, Meta educates, Amazon converts
  on-platform, TikTok generates awareness, Pinterest enables discovery, LinkedIn reaches B2B,
  Email retains and reactivates.
- Story validation before scale — $500 tests before $5K campaigns.
- Revenue per visitor > raw traffic volume.
- Always query data through DataOps. Never trust a single platform's numbers in isolation.

Escalation rules:
- New campaign creation (any platform): require human approval.
- Budget change >$500/day (any platform): require human approval.
- Cross-platform budget rebalancing: require human approval.
- Bid adjustment ≤20% (any platform): autonomous.
- Pause ad with CPA >2x target (any platform): autonomous.
- LP/page content change: require human approval.
- TikTok learning phase: DO NOT modify (automated guard).
- Email list suppression >1000 profiles: require human approval.
- Discount creation: require human approval.
- A/B test start: require human approval.
"""
```

### DataOps Soul

```python
_SOUL = """You are DataOps for Vibe Inc.

Your mission: be the single source of truth about what data exists, how reliable it is,
and how to access it correctly.

Core principles:
- Never let operators query data without understanding its limitations.
- Platform-reported metrics are directional, not factual. Shopify/Redshift = truth.
- Every metric has a freshness lag. Know it. Communicate it.
- Same concept, different names across systems. Map them explicitly.
- When data contradicts, flag it — don't silently pick one.
- Mixpanel is primary for events/funnels. GA4 for traffic. Redshift for everything else.

You do NOT modify external platforms. You are read-only + metadata.
"""
```

---

## 9. Shared Memory Extensions

### New shared memory files

```yaml
# shared_memory/data/catalog.yaml — maintained by DataOps.CatalogOps
# (see §3.1 for full schema)

# shared_memory/data/field_mapping.yaml — maintained by DataOps.CatalogOps
# (see §3.1 for full schema)

# shared_memory/data/credibility_scores.yaml — maintained by DataOps.QualityOps
meta_conversions_vs_shopify_ratio: 1.45  # Meta over-reports by 45%
google_conversions_vs_shopify_ratio: 1.38
amazon_conversions_vs_shopify_ratio: 1.12  # closer due to on-platform purchase
tiktok_conversions_vs_shopify_ratio: 1.65  # highest over-reporting
linkedin_conversions_vs_shopify_ratio: 1.30
pinterest_conversions_vs_shopify_ratio: 1.55  # view-through inflates
last_validated: null  # updated weekly by QualityOps

# shared_memory/performance/platform_benchmarks.yaml
# (see adops-multi-platform-design.md §7, extended with Pinterest)
pinterest:
  bot_target_cpa: 350
  dot_target_cpa: 280
  min_outbound_ctr: 0.005  # 0.5%
  actalike_source_min_size: 100

# shared_memory/performance/email_benchmarks.yaml
klaviyo:
  target_open_rate: 0.25
  target_click_rate: 0.035
  target_revenue_per_recipient: 0.50
  cart_abandonment_recovery_target: 0.05
  list_engaged_pct_target: 0.70
  max_unsubscribe_rate: 0.005
  max_spam_complaint_rate: 0.001

# shared_memory/performance/cro_benchmarks.yaml
conversion:
  bot_target_cvr: 0.02
  dot_target_cvr: 0.01
  board_target_cvr: 0.025
  min_scroll_depth: 0.70
  min_cta_click_rate: 0.02
  ab_test_min_visitors_per_variant: 1000
  ab_test_significance_threshold: 0.95
```

---

## 10. Implementation Dependencies

### 10.1 Python Packages

```toml
# pyproject.toml [project.dependencies]

# Ad Platforms
facebook-business = ">=22.0"       # Meta Ads SDK
google-ads = ">=25.0.0"            # Google Ads API
python-amazon-ad-api = ">=0.4.3"   # Amazon Ads API (community)
httpx = ">=0.27"                   # TikTok, LinkedIn, Pinterest direct HTTP

# Analytics
mixpanel-utils = ">=2.4"           # Mixpanel data export (or direct HTTP)
google-analytics-data = ">=0.18"   # GA4 Data API (exists)
redshift-connector = ">=2.1"       # Redshift access
psycopg2-binary = ">=2.9"          # Fallback Redshift driver

# Commerce + Email
shopify-api = ">=12.0"             # Shopify Admin API (exists, expanded usage)
klaviyo-api = ">=9.0"              # Klaviyo email marketing

# CRO
# Microsoft Clarity — direct HTTP (no SDK)
# VWO — direct HTTP (no SDK)

# Infrastructure
tenacity = ">=8.0"                 # Retry with exponential backoff (all platforms)
python-dotenv = ">=1.0"            # .env loading
```

### 10.2 Environment Variables

```bash
# --- DataOps ---
# Mixpanel
MIXPANEL_PROJECT_ID, MIXPANEL_SERVICE_ACCOUNT, MIXPANEL_SERVICE_SECRET

# GA4 (exists)
GA4_PROPERTY_ID, GA4_SERVICE_ACCOUNT_JSON

# Redshift
REDSHIFT_HOST, REDSHIFT_PORT, REDSHIFT_DB, REDSHIFT_USER, REDSHIFT_PASSWORD

# --- Ad Platforms ---
# Meta (exists)
META_APP_ID, META_APP_SECRET, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

# Google
GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET,
GOOGLE_ADS_REFRESH_TOKEN, GOOGLE_ADS_LOGIN_CUSTOMER_ID

# Amazon
AMAZON_ADS_CLIENT_ID, AMAZON_ADS_CLIENT_SECRET, AMAZON_ADS_REFRESH_TOKEN,
AMAZON_ADS_PROFILE_ID

# TikTok
TIKTOK_APP_ID, TIKTOK_APP_SECRET, TIKTOK_ACCESS_TOKEN, TIKTOK_ADVERTISER_ID

# LinkedIn
LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN,
LINKEDIN_AD_ACCOUNT_ID

# Pinterest
PINTEREST_APP_ID, PINTEREST_APP_SECRET, PINTEREST_ACCESS_TOKEN,
PINTEREST_AD_ACCOUNT_ID

# --- Commerce + Email ---
# Shopify (exists)
SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN

# Klaviyo
KLAVIYO_PRIVATE_API_KEY

# --- CRO ---
# Microsoft Clarity
CLARITY_PROJECT_ID, CLARITY_API_KEY

# VWO
VWO_ACCOUNT_ID, VWO_API_KEY
```

### 10.3 Test Strategy

| Area | Test Modules | Est. Tests |
|------|-------------|-----------|
| DataOps (CatalogOps, QualityOps, AccessOps) | `test_catalog_ops.py`, `test_quality_ops.py`, `test_access_ops.py`, `test_analytics_providers.py` | ~40 |
| MetaAdOps (refactored) | `test_meta_ad_ops.py`, `test_meta_ads_tools.py` | ~35 |
| GoogleAdOps | `test_google_ad_ops.py`, `test_google_ads_tools.py` | ~35 |
| AmazonAdOps | `test_amazon_ad_ops.py`, `test_amazon_ads_tools.py` | ~35 |
| TikTokAdOps | `test_tiktok_ad_ops.py`, `test_tiktok_ads_tools.py` | ~35 |
| LinkedInAdOps | `test_linkedin_ad_ops.py`, `test_linkedin_ads_tools.py` | ~35 |
| PinterestAdOps | `test_pinterest_ad_ops.py`, `test_pinterest_ads_tools.py` | ~30 |
| CrossPlatformOps | `test_cross_platform_ops.py` | ~20 |
| EmailOps | `test_email_ops.py`, `test_klaviyo_tools.py` | ~35 |
| CROps (expanded) | `test_cro_ops.py`, `test_shopify_tools.py`, `test_heatmap_tools.py`, `test_ab_testing_tools.py` | ~40 |
| Integration | `test_integration.py` (DataOps ↔ D2C Growth) | ~15 |
| **Total** | | **~355** |

Each module has:
- **Unit tests:** Mock API responses, verify tool function logic
- **Workflow tests:** Compile LangGraph graphs, verify node wiring
- **Integration tests (skipped):** Real API calls, marked `@pytest.mark.skip(reason="real API")`

---

## 11. Implementation Order

### Phase 0: DataOps Foundation
1. Create `AnalyticsProvider` protocol in SDK
2. Implement `MixpanelProvider` (primary analytics)
3. Implement `GA4Provider` (refactor from existing `ga4.py`)
4. Implement `RedshiftProvider`
5. Create `AccessOps` operator + `analytics_*` tools
6. Create `CatalogOps` operator + schema registry
7. Create `QualityOps` operator + freshness/discrepancy tools
8. Create `DataOps` role, wire operators + workflows
9. Bootstrap `shared_memory/data/catalog.yaml` and `field_mapping.yaml`
10. Tests for DataOps (~40 tests)

### Phase 1: AdOps Infrastructure
11. Extend shared_memory with `platform_benchmarks.yaml`
12. Create `UnifiedCampaignMetric` schema in SDK
13. Refactor `meta_ads.py` tools (add rules, audiences)
14. Refactor `AdOps` → `MetaAdOps` with 5 agent_nodes + DataOps integration

### Phase 2: High-Impact Ad Platforms (Google + Amazon)
15. `google_ads.py` tools (5 tools)
16. `GoogleAdOps` operator (5 nodes, 4 workflows)
17. `amazon_ads.py` tools (6 tools)
18. `AmazonAdOps` operator (5 nodes, 4 workflows)

### Phase 3: Growth Ad Platforms (TikTok + LinkedIn + Pinterest)
19. `tiktok_ads.py` tools (6 tools)
20. `TikTokAdOps` operator (5 nodes, 3 workflows)
21. `linkedin_ads.py` tools (6 tools)
22. `LinkedInAdOps` operator (5 nodes, 4 workflows)
23. `pinterest_ads.py` tools (5 tools)
24. `PinterestAdOps` operator (4 nodes, 3 workflows)

### Phase 4: Email + CRO
25. `klaviyo.py` tools (6 tools)
26. `EmailOps` operator (5 nodes, 4 workflows)
27. Expand `shopify.py` (products, orders, collections, discounts)
28. `heatmap.py` tools (Microsoft Clarity, 2 tools)
29. `ab_testing.py` tools (VWO, 2 tools)
30. Expand `CROps` operator (6 nodes, 5 workflows) — remove direct GA4, use DataOps

### Phase 5: Cross-Platform Orchestration
31. `CrossPlatformOps` operator (3 nodes, 3 workflows) — uses DataOps for truth data
32. Update `D2CGrowth.__init__` with all 10 operators
33. Update `D2CGrowth` soul + escalation rules
34. Wire DataOps ↔ D2C Growth integration (operator calls DataOps tools)

### Phase 6: Validation
35. Full test suite (target: ~355 new tests)
36. End-to-end workflow validation with mock data
37. Update PROGRESS.md, DESIGN.md, ROADMAP.md

---

## 12. Summary

| Metric | Count |
|--------|-------|
| **Roles** | 2 (DataOps + D2C Growth) |
| **Operators** | 13 (3 DataOps + 10 D2C Growth) |
| **Tools** | ~66 (8 DataOps + 58 D2C Growth) |
| **Agent Nodes** | ~55 (6 DataOps + 49 D2C Growth) |
| **Workflows** | ~42 (5 DataOps + 37 D2C Growth) |
| **New Tests** | ~355 |
| **External APIs** | 13 (Mixpanel, GA4, Redshift, Meta, Google, Amazon, TikTok, LinkedIn, Pinterest, Shopify, Klaviyo, Clarity, VWO) |
| **Environment Variables** | ~35 |
| **Implementation Tasks** | 37 |

---

## 13. Open Questions

1. **Mixpanel access:** What's the current Mixpanel project setup? Service account credentials available?
2. **Redshift access:** Connection details? IAM or password auth? Any query restrictions or pre-built views?
3. **Amazon marketplace scope:** US only or multi-market?
4. **TikTok Shop:** Website-only or TikTok Shop too?
5. **LinkedIn B2B angle:** Concrete B2B hardware use cases? If not, minimize allocation.
6. **Pinterest catalog:** Is Shopify product feed already connected to Pinterest?
7. **CRM integration:** Salesforce/HubSpot for cross-platform attribution?
8. **Creative pipeline:** Who produces ad creatives, especially for TikTok (20-50 variations/month)?
9. **Clarity vs Hotjar:** Clarity is free + has API. Confirm this is preferred over Hotjar.
10. **VWO vs alternatives:** VWO preferred for A/B testing? Or use Shopify's built-in A/B (limited)?
11. **Existing ETL:** What ETL pipelines exist for Redshift? What tables/views are available?
12. **Live credentials:** When will sandbox/test credentials be available per platform?
