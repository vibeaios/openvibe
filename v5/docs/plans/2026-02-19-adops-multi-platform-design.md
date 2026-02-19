# Multi-Platform AdOps Architecture Design

> D2C Growth role refactor: platform-specific operators for Meta, Google, Amazon, TikTok, LinkedIn + cross-platform orchestration.

**Date:** 2026-02-19
**Status:** Design
**Depends on:** D2C Phase 1 (complete), V5 SDK v1.0.0

---

## 1. Problem Statement

Current `AdOps` operator has 3 generic workflows (`campaign_create`, `daily_optimize`, `weekly_report`) that only reference Meta Ads tools. In reality, Vibe operates across **5 ad platforms** with fundamentally different:

- **Campaign structures** (Meta: Campaign→AdSet→Ad, Google: Campaign→AdGroup→Ad+Keywords, Amazon: profile-per-marketplace with ASIN-centric ads)
- **Bidding strategies** (Meta: Lowest Cost/Cost Cap/Bid Cap/Min ROAS, Google: Smart Bidding tCPA/tROAS/Max Conv, Amazon: Dynamic Down/Up-Down/Fixed + ACOS-based manual)
- **Optimization logic** (Meta: audience+creative, Google: keywords+Quality Score, Amazon: search term harvesting, TikTok: creative-first with fast fatigue, LinkedIn: B2B audience refinement)
- **API patterns** (Meta: Graph API sync, Google: gRPC+GAQL, Amazon: async 3-step reporting, TikTok: REST v1.3, LinkedIn: Rest.li with version headers)

A single operator cannot capture these differences. We need platform-specific operators with a cross-platform orchestration layer.

---

## 2. Target Architecture

```
D2CGrowth (Role)
├── MetaAdOps          # refactored from current AdOps
├── GoogleAdOps        # new
├── AmazonAdOps        # new
├── TikTokAdOps        # new
├── LinkedInAdOps      # new
├── CrossPlatformOps   # new — budget allocation, unified CAC, reporting
└── CROps              # unchanged
```

Each platform operator owns:
- **Platform-specific tool functions** (API wrappers)
- **Platform-specific agent_nodes** (LLM-powered workflows)
- **Platform-specific LangGraph workflows** (orchestration graphs)

`CrossPlatformOps` aggregates data from all platform operators for unified reporting and budget allocation decisions.

### 2.1 File Layout

```
v5/vibe-inc/src/vibe_inc/
├── roles/d2c_growth/
│   ├── __init__.py              # D2CGrowth role class
│   ├── meta_ad_ops.py           # MetaAdOps operator
│   ├── google_ad_ops.py         # GoogleAdOps operator
│   ├── amazon_ad_ops.py         # AmazonAdOps operator
│   ├── tiktok_ad_ops.py         # TikTokAdOps operator
│   ├── linkedin_ad_ops.py       # LinkedInAdOps operator
│   ├── cross_platform_ops.py    # CrossPlatformOps operator
│   ├── cro_ops.py               # CROps (unchanged)
│   └── workflows.py             # all LangGraph workflow factories
├── tools/
│   ├── meta_ads.py              # refactored (exists)
│   ├── google_ads.py            # new
│   ├── amazon_ads.py            # new
│   ├── tiktok_ads.py            # new
│   ├── linkedin_ads.py          # new
│   ├── ga4.py                   # exists (unchanged)
│   ├── shopify.py               # exists (unchanged)
│   └── shared_memory.py         # exists (unchanged)
└── data/
    └── shared_memory/           # exists — messaging, ICP, CAC benchmarks
```

---

## 3. Platform Comparison Matrix

### 3.1 API & SDK

| Aspect | Meta | Google | Amazon | TikTok | LinkedIn |
|--------|------|--------|--------|--------|----------|
| **Python SDK** | `facebook-business` (official) | `google-ads` (official) | `python-amazon-ad-api` (community) | `tiktok-business-api-sdk-official` / direct HTTP | `linkedin-api-client` (beta) / direct HTTP |
| **API style** | REST (Graph API) | gRPC + GAQL | REST | REST (v1.3) | REST (Rest.li) |
| **Auth** | System User token (no expiry) | OAuth2 + Developer Token | LWA OAuth2 (refresh token) | OAuth2 (24h access, 1yr refresh) | OAuth2 (60-day access, 365-day refresh) |
| **Rate limits** | 9000 pts/5min (Standard), 4x/hr budget change per adset | Standard = unlimited ops; token bucket QPS | Dynamic (undocumented), 429 + Retry-After | ~600/min sliding window | Not publicly documented; 45M metric values/5min for analytics |
| **Reporting** | Sync (Insights API) | Sync (GAQL SearchStream) | **Async only** (3-step poll) | Sync (page_size=1000), async on allowlist | Sync (max 15,000 elements, no pagination) |
| **Versioning** | ~3x/year (v24/v25), 2yr lifecycle | Monthly (v23+), ~4 major/year | Frequent (SP v3, SB v4, Reporting v3) | v1.3 stable | Monthly YYYYMM, 1yr support window |

### 3.2 Campaign Structure

| Aspect | Meta | Google | Amazon | TikTok | LinkedIn |
|--------|------|--------|--------|--------|----------|
| **Hierarchy** | Campaign→AdSet→Ad | Campaign→AdGroup→Ad(+Keywords) | Campaign→AdGroup→ProductAd(+Keywords/Targets) | Campaign→AdGroup→Ad | CampaignGroup→Campaign→Creative |
| **Creative** | Advertiser-created (image/video+copy) | Text ads (RSA), feed products (Shopping), assets (PMax) | **Auto-generated from product listing** (SP) | Advertiser-created video/image | Advertiser-created (image/video+copy) |
| **Budget model** | CBO (campaign) or ABO (adset) | Campaign budget | Campaign daily budget + Portfolio caps | Campaign or AdGroup budget | Campaign daily/total budget |
| **Automation tier** | Advantage+ (audience, creative, budget, placement) | Performance Max (all-in-one AI) | Dynamic Bids + Budget Rules | Smart+ (modular control) | Maximum Delivery (auto bid) |

### 3.3 Bidding Strategies

| Strategy Type | Meta | Google | Amazon | TikTok | LinkedIn |
|---------------|------|--------|--------|--------|----------|
| **Auto/lowest cost** | Lowest Cost | Maximize Conversions / Maximize Clicks | Dynamic Bids - Down Only | Lowest Cost | Maximum Delivery |
| **Target CPA** | Cost Cap | Max Conv + Target CPA | N/A (use ACOS-based manual) | Cost Cap | Cost Cap |
| **Target ROAS** | Minimum ROAS | Max Conv Value + Target ROAS | Rule-Based ROAS Guardrails | Target ROAS | N/A |
| **Hard ceiling** | Bid Cap | Manual CPC | Fixed Bids | Bid Cap | Manual Bidding |
| **Placement boost** | N/A | N/A | Top-of-Search 0-900%, Product Pages 0-900% | N/A | N/A |

### 3.4 Optimization Primary Levers

| Platform | Primary Lever | Secondary Lever | Tertiary |
|----------|--------------|-----------------|----------|
| **Meta** | Audience targeting + creative testing | Bid strategy | Budget pacing |
| **Google** | Keywords + Quality Score | Smart Bidding signals | Ad copy (RSA headlines) |
| **Amazon** | Search term harvesting (auto→manual) | Bid by keyword/target | Negative keyword management |
| **TikTok** | Creative freshness (7-10 day fatigue) | Broad targeting + learning phase | Spark Ads (boost organic) |
| **LinkedIn** | B2B audience refinement (title, company, seniority) | Frequency management | Lead Gen Form optimization |

### 3.5 Key Metrics by Platform

| Metric | Meta | Google | Amazon | TikTok | LinkedIn |
|--------|------|--------|--------|--------|----------|
| **Efficiency** | CPA, ROAS | CPA, ROAS, Quality Score | ACOS, TACoS, ROAS | CPA, ROAS | CPL, Cost per MQL |
| **Volume** | Impressions, Reach, Frequency | Impressions, Search Impression Share | Impressions, Clicks, Orders | Impressions, Video Views | Impressions, Reach |
| **Engagement** | CTR (1.4-1.8%), Frequency (<3) | CTR (3-5% Search), Ad Rank | CTR, CVR | CTR (0.84%), Engagement Rate (4%) | CTR (0.44%), Social Actions |
| **Cost bench** | CPC $0.70-2, CPM $7-15 | CPC $1-5 (Search) | CPC varies, ACOS 15-25% | CPC $0.25-4, CPM $3-15 | CPC $5-15+, CPM $33-65 |

### 3.6 D2C Hardware Budget Allocation (typical)

| Platform | % of Budget | Role | Why |
|----------|-------------|------|-----|
| Google (Search+Shopping+YouTube) | 35-40% | Bottom-funnel conversion | High-intent product search |
| Meta (Facebook+Instagram) | 25-30% | Mid-funnel + retargeting | DPA, video education, Advantage+ |
| Amazon | 15-20% | Bottom-funnel + organic flywheel | If selling on Amazon; drives organic rank |
| TikTok | 8-12% | Top-funnel awareness | Viral potential, low CPM, sub-$200 products |
| LinkedIn | 1-3% | B2B niche (if applicable) | High CPL but highest lead quality |

---

## 4. Per-Platform Operator Design

### 4.1 MetaAdOps (refactored from current AdOps)

**SDK:** `facebook-business` (`pip install facebook_business`)
**Auth:** System User token (non-expiring), stored in env `META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `meta_ads_read` | Read insights at campaign/adset/ad level | Existing, needs refactor for batch + date preset mapping |
| `meta_ads_create` | Create campaign+adset+ad (PAUSED) | Existing, needs Advantage+ migration for v25.0 |
| `meta_ads_update` | Update status/budget/bid on any object | Existing |
| `meta_ads_rules` | Create/read automated rules | New — `POST /act_{id}/adrules_library` |
| `meta_audiences` | Create/manage Custom + Lookalike audiences | New — for Net New vs Known separation |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create campaign for Vibe product with Net New audience exclusions, PAUSED status, naming convention `[Product]-[Narrative]-[Audience]-[Date]` | meta_ads_read, meta_ads_create, meta_audiences | `campaign_result` | Human required |
| `daily_optimize` | Review 24h performance. Bid adjust ≤20% autonomous. CPA >2x target auto-pause. Budget >$500 escalate. Track frequency (<3). | meta_ads_read, meta_ads_update | `optimization_result` | Autonomous within rules |
| `weekly_report` | Net New CAC vs Known CAC by product. ROAS by objective. Creative fatigue check (CTR trend). Progressive disclosure format. | meta_ads_read | `report` | None (read-only) |
| `audience_refresh` | Refresh lookalikes, update Custom Audiences with recent converters, exclude site visitors from Net New campaigns. | meta_audiences, meta_ads_read | `audience_result` | Autonomous |
| `creative_fatigue_check` | Monitor frequency >3, CTR decline >20% over 7 days. Flag fatigued creatives. | meta_ads_read | `fatigue_report` | None (read-only) |

#### Workflows (LangGraph)

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `meta_campaign_create` | campaign_create | Manual (from brief) | On demand |
| `meta_daily_optimize` | daily_optimize | Scheduled | Daily |
| `meta_weekly_report` | weekly_report + creative_fatigue_check | Scheduled | Weekly |
| `meta_audience_refresh` | audience_refresh | Scheduled | Weekly |

#### Platform-Specific Rules

- **Budget adjustment:** Max 4x/hour per adset (API hard limit)
- **Advantage+ migration:** v25.0 (Q1 2026) deprecates legacy ASC. New unified campaign creation with automation levers.
- **Attribution:** Default 7-day click + 1-day view. 7-day view deprecated Jan 2026.
- **CAPI required:** Server-side event tracking (Conversions API) mandatory for accurate data.

---

### 4.2 GoogleAdOps

**SDK:** `google-ads` (`pip install google-ads`)
**Auth:** Developer Token + OAuth2 (refresh_token or service account with Workspace delegation). Config via `google-ads.yaml`.

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `google_ads_query` | Execute GAQL query via SearchStream | Core read tool. Returns rows with fields. Cost in micros (÷1,000,000). |
| `google_ads_mutate` | Create/update campaigns, ad groups, keywords, ads | Batch mutations via `GoogleAdsService.Mutate`. |
| `google_ads_budget` | Create/update campaign budgets | Separate service: `CampaignBudgetService`. |
| `google_ads_recommendations` | Retrieve + apply/dismiss Google recommendations | `RecommendationService`. Auto-apply subscriptions available. |
| `google_ads_conversions` | Upload offline conversions (GCLID + enhanced) | `ConversionUploadService`. For offline/CRM data. |

#### GAQL Query Examples (embedded in tool)

```sql
-- Campaign performance
SELECT campaign.id, campaign.name, campaign.status,
       metrics.impressions, metrics.clicks, metrics.cost_micros,
       metrics.conversions, metrics.conversions_value
FROM campaign
WHERE segments.date DURING LAST_7_DAYS AND campaign.status = 'ENABLED'

-- Keyword quality scores
SELECT ad_group_criterion.keyword.text,
       ad_group_criterion.quality_info.quality_score
FROM keyword_view WHERE ad_group_criterion.status = 'ENABLED'

-- Search terms report
SELECT search_term_view.search_term,
       metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros
FROM search_term_view WHERE segments.date DURING LAST_7_DAYS
ORDER BY metrics.cost_micros DESC
```

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create Search/Shopping/PMax campaign. Set Smart Bidding (tCPA or tROAS). Structure ad groups by product line. RSA with 15 headlines + 4 descriptions. | google_ads_mutate, google_ads_budget | `campaign_result` | Human required |
| `daily_optimize` | Review Quality Scores, Search Impression Share, budget pacing. Add negative keywords from search terms report. Adjust tCPA/tROAS targets within ±15%. Flag Search Lost IS (Budget) > 20%. | google_ads_query, google_ads_mutate | `optimization_result` | Autonomous within rules |
| `search_term_mining` | Pull search terms report. Identify converting terms → add as exact match. Identify waste → add as negative exact. Weekly harvest cycle. | google_ads_query, google_ads_mutate | `mining_result` | Autonomous |
| `weekly_report` | CPA/ROAS by campaign type (Search, Shopping, PMax). Quality Score distribution. Budget utilization. Search impression share trend. Progressive disclosure. | google_ads_query | `report` | None |
| `recommendations_review` | Retrieve Google Recommendations. Filter by type (budget, keyword, bid). Auto-apply safe recommendations (keyword suggestions with >80% relevance). Flag risky ones (budget increases >30%). | google_ads_recommendations | `recommendations_result` | Mixed |

#### Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `google_campaign_create` | campaign_create | Manual | On demand |
| `google_daily_optimize` | daily_optimize | Scheduled | Daily |
| `google_search_term_mining` | search_term_mining | Scheduled | Weekly |
| `google_weekly_report` | weekly_report + recommendations_review | Scheduled | Weekly |

#### Platform-Specific Rules

- **Cost in micros:** All monetary values ÷ 1,000,000 for USD display.
- **Smart Bidding:** When active, manual bid adjustments mostly ignored. Optimize inputs (conversion data quality, audience signals) instead of bids.
- **Performance Max opacity:** Limited granular control. Focus on asset management, signal tuning, budget allocation between PMax and standard campaigns.
- **Monthly API releases (2026+):** Pin to specific version, test before upgrade. Budget migration time every 3-6 months.

---

### 4.3 AmazonAdOps

**SDK:** `python-amazon-ad-api` (`pip install python-amazon-ad-api`) — community library, de facto standard
**Auth:** LWA OAuth2 (Login with Amazon). Client ID + Secret + Refresh Token. Profile ID per marketplace.

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `amazon_ads_campaigns` | CRUD on SP/SB/SD campaigns | POST for create/list, PUT for update. Profile-scoped. |
| `amazon_ads_keywords` | CRUD on keywords, negative keywords | Includes match type (broad/phrase/exact), bid override. |
| `amazon_ads_targets` | CRUD on product targets (ASIN/category) | For product targeting campaigns. |
| `amazon_ads_report` | **Async 3-step**: request → poll → download | Returns GZIP JSON. Report types: campaigns, search terms, targeting, purchased products. |
| `amazon_ads_bid_recs` | Get ML-driven bid recommendations | Per-keyword suggested bids (low/median/high range). |
| `amazon_ads_budget_rules` | CRUD on budget rules | Schedule-based (events) and performance-based (ROAS threshold). |

#### Async Reporting Pattern (critical)

```python
# Step 1: Request report
report_id = amazon_ads_report(
    ad_product="SPONSORED_PRODUCTS",
    report_type="spSearchTerm",
    columns=["impressions", "clicks", "spend", "sales7d", "acos7d"],
    date_range="2026-02-12,2026-02-18",
)

# Step 2: Poll until COMPLETED (up to 15 min)
status = amazon_ads_report_status(report_id)  # IN_PROGRESS → COMPLETED

# Step 3: Download and decompress
data = amazon_ads_report_download(report_id)  # GZIP JSON → list of dicts
```

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create SP campaign (auto or manual). Set Dynamic Bids - Down Only (safest). Associate product ASINs. Name: `[Product]-[Type]-[Target]-[Date]`. | amazon_ads_campaigns, amazon_ads_keywords, amazon_ads_targets | `campaign_result` | Human required |
| `daily_optimize` | Review ACOS by keyword/target (use 7-day attribution, min 3-day lookback). Lower bid if ACOS >target. Raise bid if ACOS <target with volume. Pause keywords with clicks >20 and 0 orders. | amazon_ads_report, amazon_ads_keywords, amazon_ads_targets | `optimization_result` | Autonomous within rules |
| `search_term_harvest` | **Core Amazon loop.** Pull search term report. Converting terms (ACOS < target, ≥2 orders) → add as exact match in manual campaign. Waste terms (clicks >threshold, 0 orders) → add as negative exact. Add harvested terms as negative in auto campaign (prevent double-serving). | amazon_ads_report, amazon_ads_keywords | `harvest_result` | Autonomous |
| `weekly_report` | ACOS by campaign. TACoS trend (ad spend / total revenue). New-to-brand %. Top/bottom keywords. Budget utilization. Progressive disclosure. | amazon_ads_report | `report` | None |
| `budget_rules_manage` | Set schedule-based budget increases for events (Prime Day, BFCM). Performance-based rules (increase budget if ROAS > threshold). | amazon_ads_budget_rules | `rules_result` | Human required |

#### Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `amazon_campaign_create` | campaign_create | Manual | On demand |
| `amazon_daily_optimize` | daily_optimize | Scheduled | Daily |
| `amazon_search_term_harvest` | search_term_harvest | Scheduled | Weekly |
| `amazon_weekly_report` | weekly_report | Scheduled | Weekly |

#### Platform-Specific Rules

- **Async-first architecture:** All reporting is async. Must build data pipeline: request report → poll → store → analyze → act.
- **Profile-per-marketplace:** Multi-market support requires iterating over profiles. Each marketplace is separate.
- **No shared negative keyword lists:** Each campaign/ad group managed individually. Makes automation high-value.
- **No native dayparting:** Must implement via API + scheduler if needed.
- **Data restates:** Don't optimize on data <3 days old. Use 7-day attribution window for decisions.
- **TACoS > ACOS:** ACOS = campaign efficiency. TACoS = business health (includes organic flywheel).
- **Amazon MCP Server (Feb 2026 open beta):** Potential future integration path for AI-agent based automation.

---

### 4.4 TikTokAdOps

**SDK:** Direct HTTP via `httpx` (recommended) or `tiktok-business-api-sdk-official` (official but verbose)
**Auth:** OAuth2. Access token expires 24h, refresh token 1yr. Must schedule daily refresh.
**Base URL:** `https://business-api.tiktok.com/open_api/v1.3/`

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `tiktok_ads_campaigns` | CRUD on campaigns | POST `/campaign/create/`, GET `/campaign/get/`, POST `/campaign/update/` |
| `tiktok_ads_adgroups` | CRUD on ad groups | Includes targeting, placement, schedule, bid strategy |
| `tiktok_ads_ads` | CRUD on ads | Creative: video/image + text + CTA + landing URL |
| `tiktok_ads_report` | Sync reporting (integrated) | `GET /report/integrated/get/`, page_size=1000 |
| `tiktok_ads_audiences` | DMP custom/lookalike audience management | File upload, rule-based, lookalike creation |
| `tiktok_ads_rules` | Automated rules CRUD | `optimizer/rule/*` endpoints, up to 5 conditions |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create campaign with Sales or Traffic objective. Set Cost Cap or Lowest Cost bid. 3-5 creatives per ad group. Daily budget ≥ 30x target CPA for learning phase. | tiktok_ads_campaigns, tiktok_ads_adgroups, tiktok_ads_ads | `campaign_result` | Human required |
| `daily_optimize` | **DO NOT modify campaigns in learning phase** (first 50 conversions or 7 days). Post-learning: adjust bids, pause underperformers. Monitor video completion rates for fatigue. | tiktok_ads_report, tiktok_ads_adgroups, tiktok_ads_ads | `optimization_result` | Autonomous with learning phase guard |
| `creative_rotation` | Check creative fatigue (CTR decline, engagement drop over 7-10 days). Pause fatigued creatives. Queue replacements. Flag need for new creative production. | tiktok_ads_report, tiktok_ads_ads | `rotation_result` | Autonomous |
| `weekly_report` | CPA/ROAS by campaign. Video view metrics (2s, 6s, completion rates). Creative performance ranking. Learning phase status. Spark Ads performance vs standard. Progressive disclosure. | tiktok_ads_report | `report` | None |
| `audience_manage` | Create Custom Audiences (website pixel, customer file). Create Lookalikes (min 1000 matched). Recommend Saved Audience presets. | tiktok_ads_audiences | `audience_result` | Autonomous |

#### Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `tiktok_campaign_create` | campaign_create | Manual | On demand |
| `tiktok_daily_optimize` | daily_optimize + creative_rotation | Scheduled | Daily |
| `tiktok_weekly_report` | weekly_report | Scheduled | Weekly |

#### Platform-Specific Rules

- **Creative-first platform:** Creative quality and freshness are THE primary levers. Budget 20-50 new variations/month.
- **Learning phase protection:** Automation MUST NOT make changes during first 50 conversions or 7 days. This is the #1 rule.
- **Creative fatigue:** Top performers fatigue in 7-10 days. Monitor 6-second focused view rate and engagement rate decline.
- **Spark Ads:** Boost high-performing organic TikTok posts as ads. 30% higher completion rate, 142% engagement boost vs standard.
- **Events API (CAPI):** Server-side conversion tracking mandatory. Pixel alone misses ~40% of conversions.
- **Token refresh:** Access token expires every 24h. Must automate daily refresh via `/oauth2/access_token/`.

---

### 4.5 LinkedInAdOps

**SDK:** Direct HTTP via `httpx` with Rest.li headers, or `linkedin-api-client` (beta)
**Auth:** OAuth2 (3-legged). Access token 60 days, refresh token 365 days (partner-only).
**Base URL:** `https://api.linkedin.com/rest/`
**Required headers:** `Authorization: Bearer {token}`, `Linkedin-Version: YYYYMM`, `X-Restli-Protocol-Version: 2.0.0`

#### Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `linkedin_ads_campaigns` | CRUD on campaigns (within ad accounts) | Create/update/pause campaigns, set objectives, targeting, budget |
| `linkedin_ads_creatives` | CRUD on ad creatives | Single image, video, carousel, document, Lead Gen |
| `linkedin_ads_analytics` | Read performance data (adAnalytics) | 3 finders: analytics (single pivot), statistics (multi-pivot), attributedRevenueMetrics (CRM) |
| `linkedin_ads_audiences` | Matched Audiences management | Company list upload (ABM), contact list, retargeting audiences, Predictive Audiences |
| `linkedin_ads_forms` | Lead Gen Forms CRUD + response retrieval | Form create/manage, read submissions, webhook registration |
| `linkedin_ads_targeting` | Discover targeting facets and entities | Job titles, functions, seniority, companies, industries, skills |

#### Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `campaign_create` | Create campaign with Lead Generation or Website Visits objective. B2B targeting: job title + seniority + company size + industry. Audience size 50K-400K. Min $10/day budget. | linkedin_ads_campaigns, linkedin_ads_creatives, linkedin_ads_targeting | `campaign_result` | Human required |
| `daily_optimize` | Monitor CPL (target <$X). Frequency check (target 5-9/month). Pause creatives at frequency >9. Budget pacing (high CPCs burn fast). Allow 2-3 weeks before major changes (longer learning). | linkedin_ads_analytics, linkedin_ads_campaigns | `optimization_result` | Autonomous within rules |
| `abm_audience_sync` | Upload/refresh company lists for ABM targeting. Sync CRM account lists to Matched Audiences. Ensure min 300 matched members. | linkedin_ads_audiences | `abm_result` | Autonomous |
| `weekly_report` | CPL by campaign. Lead quality (if CRM connected: MQL rate, pipeline attributed). Demographic breakdown (job title, company size). Frequency distribution. Budget utilization. Progressive disclosure. | linkedin_ads_analytics | `report` | None |
| `lead_form_manage` | Create/update Lead Gen Forms. Monitor submission rate. Sync form responses to CRM. Recommend form field optimization. | linkedin_ads_forms | `form_result` | Human for form changes |

#### Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `linkedin_campaign_create` | campaign_create | Manual | On demand |
| `linkedin_daily_optimize` | daily_optimize | Scheduled | Daily |
| `linkedin_abm_sync` | abm_audience_sync | Scheduled | Weekly |
| `linkedin_weekly_report` | weekly_report + lead_form_manage | Scheduled | Weekly |

#### Platform-Specific Rules

- **High CPCs:** $5-15+ per click. Budget monitoring must be aggressive (daily, not weekly).
- **Longer optimization windows:** Need 2-3 weeks of data before meaningful bid/targeting changes (vs 3-7 days on Meta).
- **Audience management is the core lever:** Layering job title + seniority + company + industry is the primary optimization surface, not creative or bidding.
- **Lead Gen Forms > landing pages:** Native Lead Gen Forms convert significantly better. Prioritize form optimization.
- **ABM is first-class:** Company-level targeting is LinkedIn's unique capability. Matched Audience sync should be automated.
- **Rest.li protocol:** Version header required on every request. Missing version = error (no default). Must update version quarterly.
- **Revenue attribution:** If CRM connected (Salesforce/Dynamics/HubSpot), use `attributedRevenueMetrics` for true ROI measurement.

---

## 5. CrossPlatformOps

**Purpose:** Aggregate data across all 5 platforms for unified reporting, budget allocation, and cross-platform optimization decisions.

### 5.1 Tools

| Tool Function | Operations | Notes |
|---------------|-----------|-------|
| `unified_metrics_read` | Aggregate spend, conversions, revenue from all platforms | Pulls from each platform's tool, normalizes to common schema |
| `budget_allocator` | Recommend budget shifts based on marginal CPA/ROAS | Rules-based + portfolio theory signals |
| `shared_memory` | Read/write cross-platform benchmarks, ICP data | Existing tool (unchanged) |

### 5.2 Unified Schema

```python
@dataclass
class UnifiedCampaignMetric:
    platform: str          # meta, google, amazon, tiktok, linkedin
    campaign_id: str       # platform-native ID
    campaign_name: str
    date: str              # YYYY-MM-DD
    spend: float           # USD (normalized from micros, cents, etc.)
    impressions: int
    clicks: int
    conversions: float     # platform-reported
    revenue: float         # platform-reported (0 if not available)
    cpc: float
    cpm: float
    cpa: float             # spend / conversions
    roas: float            # revenue / spend (0 if no revenue data)
    platform_specific: dict # ACOS, Quality Score, frequency, etc.
```

### 5.3 Agent Nodes

| Node | System Prompt Focus | Tools | Output Key | Approval |
|------|-------------------|-------|------------|----------|
| `unified_cac_report` | Calculate **Unified CAC** = Total Ad Spend / Total New Customers (from Shopify, not platform data). Calculate **Blended ROAS** = Total Revenue / Total Spend. Break down by platform contribution. Compare platform-reported vs Shopify-attributed. Progressive disclosure. | unified_metrics_read, shared_memory | `unified_report` | None |
| `budget_rebalance` | Weekly budget rebalancing recommendation. Rules: if platform CPA >target by >20% for 3+ days → reduce 15-25%. If ROAS >target by >30% → increase 10-20%. Min floor per platform. Max ceiling 40%. Flag cross-platform cannibalization signals. | unified_metrics_read, budget_allocator | `rebalance_recommendation` | Human required |
| `platform_health_check` | Daily check: is any platform overspending? Underspending? API errors? Token expiring? Auth issues? Rate limit warnings? | unified_metrics_read | `health_report` | None |

### 5.4 Workflows

| Workflow | Nodes | Trigger | Cadence |
|----------|-------|---------|---------|
| `cross_platform_daily_health` | platform_health_check | Scheduled | Daily |
| `cross_platform_unified_report` | unified_cac_report | Scheduled | Weekly |
| `cross_platform_budget_rebalance` | budget_rebalance | Scheduled | Weekly (with human approval) |

### 5.5 Budget Allocation Logic

```
Exploit/Explore split:
  - 70-80% to proven channels (exploit)
  - 20-30% to testing (explore)

Reallocation rules:
  - IF platform CPA > target × 1.2 for 3+ consecutive days → reduce budget 15-25%
  - IF platform ROAS > target × 1.3 → increase budget 10-20% (with diminishing returns cap)
  - Minimum floor per platform: never below $X/day (maintain learnings)
  - Maximum ceiling: no platform exceeds 45% of total ad budget

Cadence:
  - Daily: per-platform automated micro-adjustments (within operator)
  - Weekly: cross-platform budget shifts (CrossPlatformOps, human approval)
  - Monthly: strategic review + new platform testing decisions (manual)
  - Quarterly: portfolio review (manual)
```

### 5.6 Unified CAC Calculation

```
Platform-Reported CPA (directional, NOT cross-comparable):
  Each platform's own CPA = Platform Spend / Platform-Reported Conversions
  → Useful for trend analysis WITHIN a platform
  → NOT comparable across platforms (different attribution windows/methods)

True Unified CAC (source of truth):
  Unified CAC = Total Ad Spend (all platforms) / Total New Customers (from Shopify/CRM)
  → Uses business system as truth, not platform data
  → Platforms collectively over-report conversions by 40-80%

Blended ROAS (MER):
  MER = Total Revenue / Total Ad Spend
  → Most honest efficiency metric
  → Doesn't try to attribute revenue to specific platforms
```

---

## 6. Soul & Escalation Rules (Updated)

The D2CGrowth role soul remains mostly the same but with cross-platform awareness:

```python
_SOUL = """You are D2C Growth for Vibe Inc.

Your mission: manage paid acquisition across Meta, Google, Amazon, TikTok, and LinkedIn
for Vibe's hardware products (Bot, Dot, Board).

Core principles:
- Net New CAC is the only CAC that matters. Never report blended platform metrics as truth.
- Use Shopify/CRM data as source of truth for customer counts, not platform-reported conversions.
- Each platform has different strengths: Google captures intent, Meta educates, Amazon converts
  on-platform, TikTok generates awareness, LinkedIn reaches B2B decision-makers.
- Story validation before scale — $500 tests before $5K campaigns.
- Revenue per visitor > raw traffic volume.

Escalation rules:
- New campaign creation (any platform): require human approval.
- Budget change >$500/day (any platform): require human approval.
- Cross-platform budget rebalancing: require human approval.
- Bid adjustment ≤20% (any platform): autonomous.
- Pause ad with CPA >2x target (any platform): autonomous.
- LP content change: require human approval.
- TikTok learning phase: DO NOT modify (automated guard).
"""
```

---

## 7. Shared Memory Extensions

Current `v5/vibe-inc/data/shared_memory/` contains messaging frameworks, ICP definitions, and CAC benchmarks. Extend with:

```yaml
# platform_benchmarks.yaml
meta:
  bot_target_cpa: 400
  dot_target_cpa: 300
  board_target_cpa: null  # not yet advertising
  frequency_cap: 3
  attribution_window: "7d_click_1d_view"

google:
  bot_target_cpa: 300
  dot_target_cpa: 250
  min_quality_score: 5
  search_impression_share_target: 0.7

amazon:
  bot_target_acos: 0.20
  dot_target_acos: 0.18
  tacos_target: 0.10
  harvest_threshold_clicks: 20
  harvest_min_orders: 2

tiktok:
  bot_target_cpa: 500
  dot_target_cpa: 400
  learning_phase_budget_multiplier: 30  # daily budget = 30x target CPA
  creative_fatigue_days: 10
  min_creatives_per_adgroup: 3

linkedin:
  target_cpl: 150
  min_audience_size: 50000
  max_audience_size: 400000
  frequency_target_monthly: 7
  min_data_days_before_optimize: 14

cross_platform:
  total_monthly_budget: null  # set by finance
  budget_split:
    google: 0.37
    meta: 0.28
    amazon: 0.18
    tiktok: 0.10
    linkedin: 0.02
    testing: 0.05
  rebalance_threshold_cpa: 1.2   # 20% above target triggers reduction
  rebalance_threshold_roas: 1.3  # 30% above target triggers increase
  min_platform_budget_pct: 0.05  # never below 5% of total
  max_platform_budget_pct: 0.45  # never above 45% of total
```

---

## 8. Implementation Dependencies

### 8.1 Python Packages (add to vibe-inc)

```toml
# pyproject.toml [project.dependencies]
facebook-business = ">=22.0"       # Meta Ads SDK
google-ads = ">=25.0.0"            # Google Ads API v23
python-amazon-ad-api = ">=0.4.3"   # Amazon Ads API (community)
httpx = ">=0.27"                   # For TikTok + LinkedIn direct HTTP
tenacity = ">=8.0"                 # Retry with exponential backoff (all platforms)
```

### 8.2 Environment Variables

```bash
# Meta
META_APP_ID, META_APP_SECRET, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

# Google
GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET,
GOOGLE_ADS_REFRESH_TOKEN, GOOGLE_ADS_LOGIN_CUSTOMER_ID

# Amazon
AMAZON_ADS_CLIENT_ID, AMAZON_ADS_CLIENT_SECRET, AMAZON_ADS_REFRESH_TOKEN,
AMAZON_ADS_PROFILE_ID  # per marketplace

# TikTok
TIKTOK_APP_ID, TIKTOK_APP_SECRET, TIKTOK_ACCESS_TOKEN, TIKTOK_ADVERTISER_ID

# LinkedIn
LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN,
LINKEDIN_AD_ACCOUNT_ID
```

### 8.3 Test Strategy

Each platform operator gets its own test module with:
- **Unit tests:** Mock API responses, verify tool function logic
- **Workflow tests:** Compile LangGraph graphs, verify node wiring
- **Integration tests (skipped by default):** Real API calls with test accounts/sandboxes, marked `@pytest.mark.skip(reason="real API")`

Estimated test count: ~30-40 per platform operator × 5 = 150-200 new tests, plus ~20 for CrossPlatformOps.

---

## 9. Implementation Order

**Phase 1: Infrastructure** (shared foundations)
1. Extend shared_memory with `platform_benchmarks.yaml`
2. Create `UnifiedCampaignMetric` schema in SDK
3. Refactor existing `meta_ads.py` tools (add rules, audiences)
4. Refactor existing `AdOps` → `MetaAdOps` with new agent_nodes

**Phase 2: High-Impact Platforms** (Google + Amazon)
5. `google_ads.py` tools (GAQL query, mutate, budget, recommendations)
6. `GoogleAdOps` operator (5 agent_nodes, 4 workflows)
7. `amazon_ads.py` tools (campaigns, keywords, async report, bid recs)
8. `AmazonAdOps` operator (5 agent_nodes, 4 workflows)

**Phase 3: Growth Platforms** (TikTok + LinkedIn)
9. `tiktok_ads.py` tools (campaigns, adgroups, ads, report, audiences, rules)
10. `TikTokAdOps` operator (5 agent_nodes, 3 workflows)
11. `linkedin_ads.py` tools (campaigns, creatives, analytics, audiences, forms, targeting)
12. `LinkedInAdOps` operator (5 agent_nodes, 4 workflows)

**Phase 4: Cross-Platform Orchestration**
13. `CrossPlatformOps` operator (3 agent_nodes, 3 workflows)
14. Update `D2CGrowth.__init__` with all 7 operators
15. Update `roles.yaml` and docs

**Phase 5: Validation**
16. Full test suite (target: 200+ new tests)
17. End-to-end workflow validation with mock data
18. Update PROGRESS.md and DESIGN.md

---

## 10. Open Questions

1. **Amazon marketplace scope:** Which marketplaces is Vibe active in? US only or multi-market? (Affects profile management complexity)
2. **TikTok Shop:** Is Vibe selling on TikTok Shop or website-only? (Affects campaign types and metrics)
3. **LinkedIn B2B angle:** Does Vibe have B2B hardware applications? If not, LinkedIn allocation should be minimal or zero.
4. **CRM integration:** Is there a CRM (Salesforce, HubSpot) for LinkedIn revenue attribution and cross-platform CAC calculation?
5. **Creative production pipeline:** Who produces ad creatives? Especially for TikTok (20-50 variations/month needed). Does this need automation?
6. **Live API credentials:** When will test/sandbox credentials be available for each platform?

---

## Appendix A: Platform SDK Quick Reference

### Meta

```python
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

FacebookAdsApi.init(app_id, app_secret, access_token)
account = AdAccount(f'act_{account_id}')
campaigns = account.get_campaigns(fields=["name", "status"])
insights = campaign.get_insights(fields=["spend", "cpc"], params={"date_preset": "last_7d"})
```

### Google

```python
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_storage("google-ads.yaml")
ga_service = client.get_service("GoogleAdsService")
query = "SELECT campaign.name, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_7_DAYS"
stream = ga_service.search_stream(customer_id=customer_id, query=query)
for batch in stream:
    for row in batch.results:
        print(row.campaign.name, row.metrics.cost_micros / 1_000_000)
```

### Amazon

```python
from ad_api.api.sp import Campaigns
from ad_api.base import Credentials

creds = Credentials(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, profile_id=profile_id)

# List campaigns
response = Campaigns(credentials=creds).list_campaigns(body={"stateFilter": {"include": ["ENABLED"]}})

# Request async report
from ad_api.api import Reports
report = Reports(credentials=creds).post_report(body={...})
# Poll: Reports(credentials=creds).get_report(reportId=report["reportId"])
# Download: GET report["url"]
```

### TikTok

```python
import httpx

BASE = "https://business-api.tiktok.com/open_api/v1.3"
headers = {"Access-Token": access_token, "Content-Type": "application/json"}

# List campaigns
resp = httpx.get(f"{BASE}/campaign/get/", headers=headers,
                 params={"advertiser_id": adv_id, "page_size": 100})
campaigns = resp.json()["data"]["list"]

# Create campaign
resp = httpx.post(f"{BASE}/campaign/create/", headers=headers,
                  json={"advertiser_id": adv_id, "campaign_name": "Test", "objective_type": "TRAFFIC"})
```

### LinkedIn

```python
import httpx

BASE = "https://api.linkedin.com/rest"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Linkedin-Version": "202602",
    "X-Restli-Protocol-Version": "2.0.0",
}

# List campaigns
resp = httpx.get(f"{BASE}/adAccounts/{account_id}/adCampaigns", headers=headers,
                 params={"q": "search", "search.status.values[0]": "ACTIVE"})
campaigns = resp.json()["elements"]

# Get analytics
resp = httpx.get(f"{BASE}/adAnalytics", headers=headers,
                 params={"q": "analytics", "pivot": "CAMPAIGN", "timeGranularity": "DAILY",
                         "dateRange": "(start:(year:2026,month:2,day:12))",
                         "campaigns": f"List(urn%3Ali%3AsponsoredCampaign%3A{campaign_id})",
                         "fields": "impressions,clicks,costInLocalCurrency"})
```
