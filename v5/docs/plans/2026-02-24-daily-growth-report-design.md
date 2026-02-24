# Daily Growth Report — Design

> D2C Growth role produces a daily ops report from Redshift data, interpreted by Claude using Ricky's 3-layer framework.

## Context

The D2C Growth role has 10 operators and 48 workflows but no unified daily output. Growth team has no feedback loop — tests pass but nobody reads real output. Ricky's Growth Systems Diagnostic (Q1 2026) defines a 3-layer performance framework that this report implements.

**Ricky's 3-Layer Framework:**
- L1: Business Outcomes — pipeline, marginal CAC, revenue
- L2: Channel Efficiency — per-channel ROI, decay analysis
- L3: Learning & Signal — funnel friction, conversion rates, contamination

**Core principle:** Net New vs Known separation is prerequisite for all measurement.

## Approach

**Redshift SQL → Claude Interpreter.** Pre-written SQL queries hit Redshift for each layer. Raw data goes to Claude with soul context and benchmarks. Claude produces the layered report with anomaly detection and recommended actions.

Why not LLM-generated SQL: SQL generation is unreliable, harder to debug, security risk on production warehouse. The queries are well-defined by Ricky's framework — deterministic data in, intelligent analysis out.

## Architecture

### New Operator: DailyReportOps

```
daily_growth_report workflow:

  [query_l1]  →  [query_l2]  →  [query_l3]  →  [interpret_and_report]
   Business       Channel        Funnel          Claude reads all 3 layers
   Outcomes       Efficiency     Signal          + benchmarks + soul
                                                 → formatted report
```

One operator, not three — the layers are sequential context. L2 only matters when L1 flags an issue, L3 only matters when L2 identifies a channel. One agent needs all three for coherent recommendations.

### File Layout

```
vibe-inc/src/vibe_inc/roles/d2c_growth/
  operators/daily_report_ops.py     # DailyReportOps operator
  sql/                              # SQL templates per layer
    l1_business_outcomes.sql
    l2_channel_efficiency.sql
    l3_funnel_signal.sql
```

### Data Flow

```
Redshift (dbt tables)
  ├── fct_ads_ad_metrics          ─┐
  ├── fct_ads_amazon_ad_group_metrics ─┤── L2: Channel Efficiency
  ├── dim_ads_campaign            ─┘
  ├── fct_order                   ──── L1: Business Outcomes (+ spend from ads)
  ├── fct_website_session         ─┐
  └── fct_website_visitor_conversion ─┘── L3: Funnel Signal
```

### Tools Used

Existing tools — no new tools needed:
- `analytics_query_sql` — executes raw SQL against Redshift
- `read_memory` — reads benchmarks from shared_memory

## Layer Definitions

### L1: Business Outcomes

**Questions:** Did we make money? Is Net New CAC on track? Growing or shrinking?

**Queries:**

1. Revenue by product (yesterday vs 7d avg vs 28d avg):
```sql
-- Yesterday
SELECT
  DATE(created_at) as date,
  SUM(board_net_sales) as board_revenue,
  SUM(bot_net_sales) as bot_revenue,
  SUM(net_sales) as total_revenue,
  COUNT(*) as order_count
FROM common.fct_order
WHERE DATE(created_at) = CURRENT_DATE - 1
GROUP BY 1;

-- 7d average
SELECT
  SUM(board_net_sales) / 7.0 as board_revenue_7d_avg,
  SUM(bot_net_sales) / 7.0 as bot_revenue_7d_avg,
  SUM(net_sales) / 7.0 as total_revenue_7d_avg,
  COUNT(*) / 7.0 as order_count_7d_avg
FROM common.fct_order
WHERE DATE(created_at) BETWEEN CURRENT_DATE - 8 AND CURRENT_DATE - 2;

-- 28d average
SELECT
  SUM(board_net_sales) / 28.0 as board_revenue_28d_avg,
  SUM(bot_net_sales) / 28.0 as bot_revenue_28d_avg,
  SUM(net_sales) / 28.0 as total_revenue_28d_avg,
  COUNT(*) / 28.0 as order_count_28d_avg
FROM common.fct_order
WHERE DATE(created_at) BETWEEN CURRENT_DATE - 29 AND CURRENT_DATE - 2;
```

2. Total ad spend yesterday (for CAC calculation):
```sql
SELECT
  SUM(spend_in_usd) as total_spend
FROM common.fct_ads_ad_metrics
WHERE date = CURRENT_DATE - 1;
```

**Derived metrics:**
- Blended CAC = total_spend / order_count
- Per-product CAC approximated from product-attributed spend (campaign naming convention)

**Benchmarks:** Bot CAC ≤$400, Dot CAC ≤$300, Board ACOS ≤20%.

### L2: Channel Efficiency

**Questions:** Which platform is off? Spend pacing, CPA spike, or creative fatigue?

**Queries:**

1. Per-platform daily metrics (yesterday + 7d avg):
```sql
-- Yesterday per platform
SELECT
  platform,
  SUM(spend_in_usd) as spend,
  SUM(impressions) as impressions,
  SUM(clicks) as clicks,
  SUM(purchase_count) as purchases,
  CASE WHEN SUM(purchase_count) > 0
    THEN SUM(spend_in_usd) / SUM(purchase_count)
    ELSE NULL END as cpa
FROM common.fct_ads_ad_metrics
WHERE date = CURRENT_DATE - 1
GROUP BY platform;

-- 7d average per platform
SELECT
  platform,
  SUM(spend_in_usd) / 7.0 as spend_7d_avg,
  SUM(impressions) / 7.0 as impressions_7d_avg,
  SUM(clicks) / 7.0 as clicks_7d_avg,
  SUM(purchase_count) / 7.0 as purchases_7d_avg,
  CASE WHEN SUM(purchase_count) > 0
    THEN SUM(spend_in_usd) / SUM(purchase_count)
    ELSE NULL END as cpa_7d_avg
FROM common.fct_ads_ad_metrics
WHERE date BETWEEN CURRENT_DATE - 8 AND CURRENT_DATE - 2
GROUP BY platform;
```

2. Amazon separately (different table):
```sql
SELECT
  channel,
  SUM(spend_in_usd) as spend,
  SUM(impressions) as impressions,
  SUM(clicks) as clicks,
  SUM(conversions14d) as conversions,
  SUM(sales14d) as sales,
  CASE WHEN SUM(sales14d) > 0
    THEN SUM(spend_in_usd) / SUM(sales14d)
    ELSE NULL END as acos
FROM common.fct_ads_amazon_ad_group_metrics
WHERE date = CURRENT_DATE - 1
GROUP BY channel;
```

3. Top/bottom campaigns by CPA (for action specificity):
```sql
SELECT
  c.campaign_name,
  f.platform,
  SUM(f.spend_in_usd) as spend,
  SUM(f.purchase_count) as purchases,
  CASE WHEN SUM(f.purchase_count) > 0
    THEN SUM(f.spend_in_usd) / SUM(f.purchase_count)
    ELSE NULL END as cpa
FROM common.fct_ads_ad_metrics f
JOIN common.dim_ads_campaign c ON f.dim_ads_campaign_sk = c.dim_ads_campaign_sk
WHERE f.date = CURRENT_DATE - 1
  AND f.spend_in_usd > 0
GROUP BY c.campaign_name, f.platform
ORDER BY cpa DESC
LIMIT 10;
```

**Anomaly triggers:** CPA >1.2x target, spend pacing >20% off budget, CTR drop >15% WoW.

### L3: Funnel Signal

**Questions:** Are people reaching the site? Converting? Where's the drop-off?

**Queries:**

1. Website sessions by traffic channel:
```sql
-- Yesterday
SELECT
  session_traffic_channel,
  COUNT(*) as sessions,
  AVG(session_page_viewed) as avg_pages,
  AVG(session_time_engaged_in_s) as avg_time_s
FROM common.fct_website_session
WHERE DATE(session_first_page_tstamp) = CURRENT_DATE - 1
GROUP BY session_traffic_channel;

-- 7d average
SELECT
  session_traffic_channel,
  COUNT(*) / 7.0 as sessions_7d_avg
FROM common.fct_website_session
WHERE DATE(session_first_page_tstamp) BETWEEN CURRENT_DATE - 8 AND CURRENT_DATE - 2
GROUP BY session_traffic_channel;
```

2. Funnel conversion counts:
```sql
-- Yesterday
SELECT
  conversion,
  COUNT(*) as count,
  SUM(conversion_value) as value
FROM common.fct_website_visitor_conversion
WHERE DATE(original_tstamp) = CURRENT_DATE - 1
GROUP BY conversion;

-- 7d average
SELECT
  conversion,
  COUNT(*) / 7.0 as count_7d_avg,
  SUM(conversion_value) / 7.0 as value_7d_avg
FROM common.fct_website_visitor_conversion
WHERE DATE(original_tstamp) BETWEEN CURRENT_DATE - 8 AND CURRENT_DATE - 2
GROUP BY conversion;
```

**Funnel steps tracked:** `visitor_add_to_cart`, `visitor_init_checkout`, `visitor_close_won`.

## Output Format

Progressive disclosure — scannable in 10 seconds, actionable in 2 minutes.

```
═══════════════════════════════════════════════
DAILY GROWTH REPORT — {date} ({day_of_week})
═══════════════════════════════════════════════

{🔴|⚠️|✅} HEADLINE
{One sentence: single most important thing today.}
{One sentence: root cause hypothesis if red/yellow.}

───────────────────────────────────────────────
L1: BUSINESS OUTCOMES
───────────────────────────────────────────────

              Yesterday    7d Avg    28d Avg    Target
Revenue       ${X}         ${X}      ${X}       —
  Board       ${X}         ${X}      ${X}       —
  Bot         ${X}         ${X}      ${X}       —
  Dot         ${X}         ${X}      ${X}       —

Orders        {N}          {N}       {N}        —
Blended CAC   ${X}         ${X}      ${X}       —
Bot CAC       ${X}         ${X}      ${X}       ≤$400 {flag}
Dot CAC       ${X}         ${X}      ${X}       ≤$300 {flag}

Ad Spend      ${X}         ${X}      ${X}       —

───────────────────────────────────────────────
L2: CHANNEL EFFICIENCY
───────────────────────────────────────────────

Platform    Spend     CPA      vs Target   vs 7d Avg   Flag
{platform}  ${X}      ${X}     {+/-}%      {+/-}%      {flag}
...

───────────────────────────────────────────────
L3: FUNNEL SIGNAL
───────────────────────────────────────────────

Traffic       Yesterday    7d Avg    Δ
{channel}     {N}          {N}       {arrow}{%}
...

Funnel        Count    Rate     vs 7d Avg
Sessions      {N}      —        {Δ}
Add to Cart   {N}      {%}      {Δ}pp
Checkout      {N}      {%}      {Δ}pp
Purchase      {N}      {%}      {Δ}pp

{anomaly commentary if any funnel step deviates >2pp from baseline}

───────────────────────────────────────────────
RECOMMENDED ACTIONS
───────────────────────────────────────────────

1. [{PLATFORM}] {verb} + {specific target}
   — {reason with data}
   — Expected impact: {quantified}

2. ...
```

### Flag System

| Flag | Meaning | Trigger |
|------|---------|---------|
| 🔴 | Action needed now | CPA >1.5x target, revenue drop >20%, funnel break >5pp |
| ⚠️ | Watch / investigate | CPA >1.2x target, revenue drop >10%, funnel drop >2pp |
| ✅ | Healthy | Within targets |
| ⬚ | Inactive / no data | Platform paused or no data |

### Headline Color Logic

- **🔴 Red:** Any L1 metric >20% off target OR any platform CPA >1.5x target
- **⚠️ Yellow:** Any L1 metric >10% off OR trending wrong direction for 3+ days
- **✅ Green:** All within targets and stable/improving

## Agent Prompt

The `interpret_and_report` node receives all three layers as structured dicts and uses this prompt:

```
You are a D2C growth analyst for Vibe hardware products (Board, Bot, Dot).

You receive three layers of data from Redshift:
- L1: business outcomes (revenue, orders, CAC by product)
- L2: channel efficiency (per-platform spend, CPA, trends)
- L3: funnel signal (traffic, conversion rates, drop-offs)

Your job:
1. HEADLINE — one sentence: what's the single most important thing today?
   Red (action needed), Yellow (watch), Green (all clear).
2. L1 TABLE — revenue + CAC by product vs 7d/28d avg and targets.
3. L2 TABLE — per-platform spend, CPA, flags.
4. L3 TABLE — traffic + funnel with conversion rates.
5. RECOMMENDED ACTIONS — numbered, specific, with expected impact.
   Each action: [PLATFORM] verb + specific target + reason + expected impact.

Rules:
- Net New CAC is the only CAC that matters. If data doesn't separate
  Net New vs Known, flag this as a measurement gap.
- Never say "optimize" without saying what specifically to do.
- Flag anomalies as: structural (trend over 3+ days) vs noise (single day spike).
- If data is missing or stale (>24h), say so — don't guess.
- Benchmarks: Bot CAC ≤$400, Dot CAC ≤$300, Board ACOS ≤20%.
- Every number needs context: vs target, vs 7d avg, vs 28d avg.
- Actions must be specific enough to execute without further research.
```

## Scope

### In Scope (v1)
- DailyReportOps operator with `daily_growth_report` workflow
- SQL templates for L1, L2, L3 (reading from existing dbt tables)
- Agent interpretation node with soul-aligned prompt
- CLI trigger: `vibe report daily` (or similar)
- Tests with mock Redshift data

### Out of Scope (future)
- Scheduled execution (cron/scheduler)
- Slack/email delivery of report
- Net New vs Known cohort separation in SQL (depends on campaign naming or audience tagging — Ricky's Phase 1 deliverable)
- Interactive follow-up ("tell me more about Meta")
- Historical trend charts (text-only for now)
- Email (Klaviyo) layer in the report

## Known Limitations

1. **Net New vs Known split not in data yet.** Ricky's Phase 1 is implementing this. Until then, the report shows blended CAC and flags this as a measurement gap. The SQL and prompt are designed to separate them once the data supports it.

2. **Per-product CAC is approximate.** Requires campaign naming convention to attribute spend to Board/Bot/Dot. If naming is inconsistent, the agent will flag it.

3. **Amazon data is separate.** `fct_ads_amazon_ad_group_metrics` has different columns (conversions14d, sales14d, ACOS) vs the unified `fct_ads_ad_metrics`. The L2 queries handle this but the agent prompt must account for the difference.

## Dependencies

- Redshift credentials (`REDSHIFT_HOST`, `REDSHIFT_PORT`, `REDSHIFT_DATABASE`, `REDSHIFT_USER`, `REDSHIFT_PASSWORD`)
- Existing `RedshiftProvider` in `vibe_inc/tools/analytics/redshift.py`
- Existing `analytics_query_sql` tool
- dbt tables populated and fresh (daily refresh assumed)
