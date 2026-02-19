# Vibe Inc D2C Marketing Adoption — Design Document

> V5 SDK Phase 3: Three AI roles that decide, create, and distribute Vibe's D2C stories.

Created: 2026-02-19T04:34:27Z

---

## 1. Context

Vibe Inc is a hardware company ($30-35M annual revenue) launching two new AI products:
- **Vibe Bot** (~$1,599-$2,000) — AI meeting device, shipping Feb 2026
- **Vibe Dot** ($249-$279) — AI memory assistant, shipping June 2026
- **Vibe Board / Smartboard** ($3,699-$7,299) — Interactive whiteboard, mature (~600 units/month)

2026 revenue target: $80M (per CRO framework). D2C is the primary growth engine.

### Out of Scope
- **Lifecycle/retention marketing:** Cart recovery, post-purchase sequences, churn prevention (separate effort)
- **B2B and Channel motions:** Covered by separate roles (@SalesOps, @ChannelMarketing)
- **Amazon Ads:** Deferred to Phase 2+ (Meta + Google first)

### Current Pain Points
- **Story not validated:** Bot testing 3 narratives, Dot testing 2 paths. No winner yet.
- **Measurement broken:** Net New vs Known CAC not separated. True CAC likely 40-60% higher than reported.
- **Content gap:** Need 10+/month, have no content machine. Copywriter missing.
- **Organic weak:** 27% of traffic (target 50%+). Over-dependent on paid.
- **Google Ads suspended.** Recovery in progress.

### What the SDK Must Deliver
AI roles that autonomously execute D2C marketing work — not dashboards, not assistants. Roles that produce real output (campaigns, landing pages, content) with human approval gates.

---

## 2. Architecture: Three Roles, One Story

The fundamental insight: D2C marketing is storytelling at scale. Every activity maps to one of three functions:

| Role | Function | Core Question | Cadence |
|------|----------|---------------|---------|
| **Story Strategist** | Decide the story | What to say, to whom, why | Monthly |
| **Story Creator** | Birth the story | How to say it, in what form | Weekly |
| **Story Distributor** | Spread the story | Where to say it, how much to spend, what works | Daily |

### Dependency Flow

```
Story Strategist ──→ Story Creator ──→ Story Distributor
  (what)               (how)             (where)
                                              │
                                              └──→ performance data
                                                   flows back to
                                                   all three roles
```

### Shared Memory

All three roles read from and write to a shared memory layer, implemented as a `WorkspaceMemory` instance (SDK V2 memory system). Each role gets its own `AgentMemory` for private state; shared memory is the cross-role coordination surface.

In Phase 1, shared memory is bootstrapped as YAML files on disk (simple, debuggable). Phase 2+ migrates to `MemoryFilesystem` with `.directory` index files for structured navigation.

```
shared_memory/
├── messaging/
│   ├── bot-framework.yaml      # Bot positioning + messaging hierarchy
│   ├── dot-framework.yaml      # Dot positioning + messaging hierarchy
│   └── board-framework.yaml    # Board positioning + messaging hierarchy
├── audiences/
│   ├── icp-definitions.yaml    # Ideal customer profiles per product
│   └── winning-segments.yaml   # Validated audience segments (from Distributor)
├── competitive/
│   ├── battlecards/            # Per-competitor analysis
│   └── market-signals.yaml     # Recent competitive moves
├── performance/
│   ├── cac-benchmarks.yaml     # Net New CAC by product/channel
│   ├── cvr-benchmarks.yaml     # Conversion rates by variant
│   └── story-validation.yaml   # Experiment results + winner status
└── content/
    ├── keyword-research.yaml   # SEO opportunities
    └── content-calendar.yaml   # Planned + published content
```

---

## 3. Role 1: Story Distributor (Phase 1)

> "投放 + CRO — 花多少钱, 投给谁, 转化率怎么提"

### SOUL

```yaml
name: Story Distributor
soul:
  identity:
    name: Story Distributor
    role: Performance marketing and conversion optimization engine
    description: >
      Manages the full paid acquisition → landing page → conversion loop
      for Vibe's hardware products. Operates on daily data cycles.
      Optimizes for Net New CAC, not blended metrics.
  philosophy:
    principles:
      - Net New CAC is the only CAC that matters
      - Separate Net New vs Known in every analysis
      - Story validation before scale — don't pour money into unvalidated narrative
      - Small bets, fast reads — $500 tests before $5K campaigns
      - Revenue per visitor > raw traffic volume
    values: [Measurability, Speed-to-learn, Capital-efficiency]
  behavior:
    response_style: progressive_disclosure
    proactive: true
  constraints:
    trust_level: L2
    escalation_rules:
      - "New campaign creation: require approval"
      - "Budget change >$500/day: require approval"
      - "Bid adjustment ≤20%: autonomous"
      - "Pause ad with CPA >2x target: autonomous"
      - "LP content change: require approval"
      - "A/B test setup: require approval"
```

### Operator: AdOps (投放全链路)

| Workflow | Trigger | Input | Output | Approval |
|----------|---------|-------|--------|----------|
| `campaign_create` | Manual | product, audience, budget, creative brief | Campaign structure + ad copy | Required |
| `daily_optimize` | Daily 6am UTC | Active campaign performance (24h + 7d) | Bid adjustments, pause/enable, budget shifts | Auto ≤20%, else Required |
| `weekly_report` | Monday 8am UTC | All campaign data (7d) | Net New vs Known CAC, ROAS, spend efficiency | None |
| `audience_expand` | Manual | Winning segment, expansion criteria | Lookalike specs + test campaign proposals | Required |

**Tools:**

| Tool | External API | Access | Purpose |
|------|-------------|--------|---------|
| `meta_ads_read` | Meta Marketing API | Read | Campaign, adset, ad performance |
| `meta_ads_create` | Meta Marketing API | Write | Create campaign/adset/ad |
| `meta_ads_update` | Meta Marketing API | Write | Modify bids, budgets, status |
| `google_ads_read` | Google Ads API | Read | Campaign performance |
| `google_ads_create` | Google Ads API | Write | Create campaigns |
| `google_ads_update` | Google Ads API | Write | Modify bids, budgets, status |

### Operator: CROps (转化优化)

| Workflow | Trigger | Input | Output | Approval |
|----------|---------|-------|--------|----------|
| `experiment_analyze` | Daily (when experiments active) | GA4 events per variant | Performance table + significance + winner rec | None |
| `funnel_diagnose` | Weekly or on-demand | Full funnel data by product | Drop-off analysis + fix recommendations | None |
| `page_optimize` | Manual | Page ID, optimization spec | Modified LP content | Required |
| `experiment_setup` | On request from Strategist | Variants, traffic %, metrics, duration | A/B test configuration | Required |

**Note:** Story Strategist *requests* experiments (defines what to test and why). Story Distributor *executes* them (sets up tracking, allocates traffic, collects data). Strategist then *interprets* results via `validate_story` workflow.

**Tools:**

| Tool | External API | Access | Purpose |
|------|-------------|--------|---------|
| `ga4_read` | GA4 Data API | Read | Events, funnels, segments |
| `shopify_page_read` | Shopify Admin API | Read | Current LP content |
| `shopify_page_update` | Shopify Admin API | Write | Modify LP content |

### Cross-Operator Flow

```
Daily Loop:
  6am: AdOps.daily_optimize
    → reads campaign performance
    → reads CROps memory (CVR per variant, funnel health)
    → adjusts bids (higher for high-CVR variants, lower for poor ones)
    → writes performance data to shared memory

  8am: CROps.experiment_analyze
    → reads GA4 events (scroll, click, checkout by variant)
    → reads AdOps memory (traffic quality per source)
    → computes statistical significance
    → recommends winner or "keep testing"
    → writes experiment results to shared memory
```

### Success Metrics

| Metric | Current | Phase 1 Target |
|--------|---------|----------------|
| Net New CAC (Bot) | Unknown (blended) | ≤$400, separately tracked |
| Net New CAC (Dot) | Unknown | ≤$300, separately tracked |
| Website CVR (Bot PDP) | ~1.5% | ≥2% |
| Revenue per visitor (Bot) | Unknown | >$15 |
| Story validation decision | Manual, slow | Automated analysis, weekly reports |

---

## 4. Role 2: Story Strategist (Phase 2)

> "PMM + positioning — 讲什么故事, 讲给谁, 为什么这么讲"

### SOUL

```yaml
name: Story Strategist
soul:
  identity:
    name: Story Strategist
    role: Product marketing strategist and competitive intelligence analyst
    description: >
      Defines positioning, messaging frameworks, and ICP for each product.
      Validates stories through data. Maintains competitive battlecards.
      Outputs are the source of truth for what Creator creates and
      Distributor distributes.
  philosophy:
    principles:
      - Positioning is a bet — validate fast, commit hard
      - One message per product, ruthlessly simple
      - Know the enemy better than they know themselves
      - ICP clarity > broad reach
    values: [Clarity, Conviction, Market-awareness]
  behavior:
    response_style: progressive_disclosure
    proactive: true
  constraints:
    trust_level: L3
    escalation_rules:
      - "Positioning change: require approval"
      - "ICP redefinition: require approval"
      - "Battlecard update: autonomous"
      - "Competitive alert: autonomous notification"
```

### Operator: PositioningEngine

| Workflow | Trigger | Input | Output | Approval |
|----------|---------|-------|--------|----------|
| `define_framework` | Manual / quarterly | Product specs, market research, ICP data | Messaging framework (primary → supporting → proof) | Required |
| `validate_story` | Weekly (during test) | Story validation experiment data (from Distributor) | Winner analysis + positioning lock recommendation | Required for lock |
| `refine_icp` | Monthly | Purchase data, survey data, CRM signals | Updated ICP definitions | Required |

### Operator: CompetitiveIntel

| Workflow | Trigger | Input | Output | Approval |
|----------|---------|-------|--------|----------|
| `weekly_scan` | Weekly | Competitor websites, pricing pages, product updates | Competitive digest + battlecard updates | Auto for updates, alert for major changes |
| `threat_assess` | On alert | Specific competitive move | Impact analysis + response recommendations | None (analysis only) |

**Tools:**

| Tool | External API | Access | Purpose |
|------|-------------|--------|---------|
| `web_search` | Search API | Read | Competitor news, product launches |
| `web_fetch` | HTTP | Read | Competitor pricing pages, feature pages |
| `ga4_read` | GA4 Data API | Read | Story validation experiment data |

### Outputs → Shared Memory

```yaml
# messaging/bot-framework.yaml (example)
product: Vibe Bot
status: validating  # validating | locked | revising
positioning:
  primary: "The room that remembers for you"  # Narrative B (Foundation) — currently in validation
  supporting:
    - "Every meeting outcome captured, every action tracked"
    - "Cross-platform: works with Zoom, Teams, Meet, in-person"
  proof_points:
    - "360° audio capture"
    - "AI action extraction, not just transcription"
    - "Integrates with Vibe Workspace for team memory"
target_icp:
  primary: "SMB managers (50-200 employees) running 10+ meetings/week"
  secondary: "Sales teams tracking client conversations"
competitors:
  vs_owl: "Meeting Owl has no AI — Vibebot extracts actions, not just video"
  vs_otter: "Otter is software you activate — Vibebot is hardware always ready"
narrative_test:
  status: in_progress
  variants: [control, pain, foundation, future]
  current_leader: foundation
  confidence: 0.72
  decision_date: 2026-03-07
```

---

## 5. Role 3: Story Creator (Phase 3)

> "内容生产 + 素材工厂 — 怎么讲故事, 用什么形式"

### SOUL

```yaml
name: Story Creator
soul:
  identity:
    name: Story Creator
    role: Content strategist, writer, and creative producer
    description: >
      Produces all content assets for D2C: SEO articles, product pages,
      comparison pieces, ad creatives, video briefs. Every piece aligns
      with the messaging framework from Story Strategist.
  philosophy:
    principles:
      - Segment-first — every piece targets a specific ICP
      - Quality over quantity, but quantity matters at 10+/month
      - Reuse aggressively — one insight becomes blog + ad + LP copy
      - SEO is compounding — organic traffic is the long game
    values: [Clarity, Relevance, Consistency, Velocity]
  behavior:
    response_style: progressive_disclosure
    proactive: true
  constraints:
    trust_level: L2
    escalation_rules:
      - "External publish: require approval"
      - "Ad creative deployment: require approval"
      - "Internal draft: autonomous"
      - "Keyword research: autonomous"
```

### Operator: ContentEngine

| Workflow | Trigger | Input | Output | Approval |
|----------|---------|-------|--------|----------|
| `research_topics` | Weekly | Keyword data, messaging framework, competitor content | Topic recommendations + SEO brief | None |
| `write_article` | On assignment | Topic brief, messaging framework, ICP | Full article draft (headline, body, CTA) | Required |
| `write_product_page` | On assignment | Product specs, messaging, competitor comparison | PDP copy (headline, features, social proof) | Required |
| `write_comparison` | On assignment | Product + competitor battlecard | "Vibe vs X" article | Required |

### Operator: CreativeFactory

| Workflow | Trigger | Input | Output | Approval |
|----------|---------|-------|--------|----------|
| `generate_ad_copy` | On assignment | Messaging framework, audience, channel (Meta/Google) | Ad copy variants (headline, body, CTA) × 3-5 | Required |
| `generate_video_brief` | On assignment | Messaging, product, target platform | Video script + shot list + hook options | Required |
| `analyze_creative_performance` | Weekly | Ad creative performance data | Top/bottom performers + insights | None |

**Tools:**

| Tool | External API | Access | Purpose |
|------|-------------|--------|---------|
| `seo_keywords` | SEO API (Ahrefs/SEMrush) | Read | Keyword research, difficulty, volume |
| `web_search` | Search API | Read | Competitor content analysis |
| `web_fetch` | HTTP | Read | Reference content for research |
| `cms_publish` | Shopify/CMS API | Write | Publish content |
| `meta_ads_read` | Meta Marketing API | Read | Creative performance data |

---

## 6. Technical Implementation (V5 SDK)

### Package Structure

```
v5/vibe-inc/
├── config/
│   ├── soul.yaml                    # Company-level SOUL (exists)
│   ├── roles.yaml                   # Role definitions (exists, extend)
│   └── secrets.env                  # API credentials (gitignored)
│
├── roles/
│   ├── story_distributor/
│   │   ├── __init__.py              # Role class
│   │   ├── ad_ops.py                # AdOps operator
│   │   ├── cro_ops.py               # CROps operator
│   │   └── workflows.py             # LangGraph workflow factories
│   │
│   ├── story_strategist/
│   │   ├── __init__.py
│   │   ├── positioning.py           # PositioningEngine operator
│   │   ├── competitive.py           # CompetitiveIntel operator
│   │   └── workflows.py
│   │
│   └── story_creator/
│       ├── __init__.py
│       ├── content_engine.py        # ContentEngine operator
│       ├── creative_factory.py      # CreativeFactory operator
│       └── workflows.py
│
├── tools/
│   ├── meta_ads.py                  # Meta Marketing API wrapper
│   ├── google_ads.py                # Google Ads API wrapper
│   ├── ga4.py                       # GA4 Data API wrapper
│   ├── shopify.py                   # Shopify Admin API wrapper
│   └── seo.py                       # SEO tool wrapper
│
└── shared_memory/
    ├── messaging/                   # Populated by Strategist
    ├── audiences/                   # Populated by Strategist + Distributor
    ├── competitive/                 # Populated by Strategist
    ├── performance/                 # Populated by Distributor
    └── content/                     # Populated by Creator
```

### SDK Integration Pattern

**Key SDK conventions:**
- `@agent_node` decorator: the method's **docstring** becomes the LLM system prompt, the **return value** becomes the user message sent to the LLM. The LLM then decides which tools to call.
- `Role.__init__()` takes `llm`, `agent_memory`, `config`, `lifecycle`, `trust`, `goals`.
- `operators` is a **class variable** (list of Operator classes), not an init argument.
- `RoleRuntime` instantiates roles and dispatches activations.

```python
# v5/vibe-inc/roles/story_distributor/__init__.py
from openvibe_sdk import Role
from .ad_ops import AdOps
from .cro_ops import CROps

class StoryDistributor(Role):
    role_id = "story_distributor"
    operators = [AdOps, CROps]
```

```python
# v5/vibe-inc/roles/story_distributor/ad_ops.py
from openvibe_sdk import Operator, agent_node
from ...tools.meta_ads import meta_ads_read, meta_ads_create, meta_ads_update
from ...tools.google_ads import google_ads_read, google_ads_create, google_ads_update

class AdOps(Operator):
    operator_id = "ad_ops"

    @agent_node(
        tools=[meta_ads_read, meta_ads_create, meta_ads_update,
               google_ads_read, google_ads_create, google_ads_update],
        output_key="campaign_result"
    )
    def campaign_create(self, state):
        """You are a performance marketing specialist for Vibe.
        Create a campaign structure based on the provided brief.
        Use the messaging framework from shared memory.
        Always separate Net New vs Known audiences."""
        # Return value = user message to LLM. LLM decides which tools to invoke.
        return f"Create campaign: {state['brief']}"

    @agent_node(
        tools=[meta_ads_read, meta_ads_update,
               google_ads_read, google_ads_update],
        output_key="optimization_result"
    )
    def daily_optimize(self, state):
        """Review campaign performance from the last 24 hours.
        Adjust bids within 20% threshold autonomously.
        Flag anything requiring budget changes >$500/day.
        Always report Net New CAC separately from Known."""
        return f"Optimize campaigns for {state['date']}"
```

```python
# v5/vibe-inc/roles/story_distributor/workflows.py
from typing import TypedDict
from langgraph.graph import StateGraph

class OptimizeState(TypedDict):
    date: str
    optimization_result: str

class CampaignState(TypedDict):
    brief: dict
    campaign_result: dict

def create_daily_optimize_graph(operator):
    """Daily optimization workflow: read → analyze → adjust → report."""
    graph = StateGraph(OptimizeState)
    graph.add_node("optimize", operator.daily_optimize)
    graph.set_entry_point("optimize")
    graph.set_finish_point("optimize")
    return graph.compile()

def create_campaign_create_graph(operator):
    """Campaign creation workflow with approval gate."""
    graph = StateGraph(CampaignState)
    graph.add_node("create", operator.campaign_create)
    # Approval gate wired via HumanLoopService (see platform layer)
    graph.set_entry_point("create")
    graph.set_finish_point("create")
    return graph.compile()
```

```python
# v5/vibe-inc/main.py — Runtime wiring
from openvibe_runtime import RoleRuntime
from openvibe_sdk.llm import AnthropicProvider
from roles.story_distributor import StoryDistributor
from roles.story_distributor.workflows import (
    create_daily_optimize_graph, create_campaign_create_graph
)

# Initialize runtime with role classes
llm = AnthropicProvider()
runtime = RoleRuntime(roles=[StoryDistributor], llm=llm)

# Register workflow factories
runtime.register_workflow("ad_ops", "daily_optimize", create_daily_optimize_graph)
runtime.register_workflow("ad_ops", "campaign_create", create_campaign_create_graph)

# Activate a workflow
result = runtime.activate(
    role_id="story_distributor",
    operator_id="ad_ops",
    workflow_id="daily_optimize",
    input_data={"date": "2026-02-19"}
)
```

### Scheduling

The SDK runtime (`RoleRuntime.activate()`) is synchronous — it has no built-in scheduler. Daily/weekly triggers require an external scheduler:

- **Phase 1:** Simple cron jobs calling `runtime.activate()` via CLI or script
- **Phase 2+:** Temporal workflows (already in V4 stack) for durable scheduling with retry/observability

### Tool Implementation Pattern

```python
# v5/vibe-inc/tools/meta_ads.py
import os
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

def _get_client():
    """Initialize Meta Ads API client from environment."""
    FacebookAdsApi.init(
        app_id=os.environ["META_APP_ID"],
        app_secret=os.environ["META_APP_SECRET"],
        access_token=os.environ["META_ACCESS_TOKEN"],
    )
    return AdAccount(f'act_{os.environ["META_AD_ACCOUNT_ID"]}')

def meta_ads_read(level: str = "campaign", date_range: str = "last_7d",
                  fields: list[str] | None = None) -> dict:
    """Read Meta Ads performance data.

    Args:
        level: Reporting level — campaign, adset, or ad
        date_range: Date range — last_24h, last_7d, last_30d, or YYYY-MM-DD,YYYY-MM-DD
        fields: Metrics to retrieve (default: spend, impressions, clicks, conversions, cpa, roas)

    Returns:
        Performance data as dict with rows per campaign/adset/ad
    """
    account = _get_client()
    # ... implementation
    return {"level": level, "rows": [...]}

def meta_ads_create(campaign_name: str, objective: str, budget_daily: float,
                    targeting: dict, creative: dict) -> dict:
    """Create a new Meta Ads campaign with adset and ad.

    Args:
        campaign_name: Name for the campaign
        objective: Campaign objective (CONVERSIONS, TRAFFIC, etc.)
        budget_daily: Daily budget in USD
        targeting: Audience targeting spec
        creative: Ad creative (headline, body, image_url, link)

    Returns:
        Created campaign, adset, and ad IDs
    """
    account = _get_client()
    # ... implementation
    return {"campaign_id": "...", "adset_id": "...", "ad_id": "..."}

def meta_ads_update(object_type: str, object_id: str, updates: dict) -> dict:
    """Update a Meta Ads object (campaign, adset, or ad).

    Args:
        object_type: Type — campaign, adset, or ad
        object_id: ID of the object to update
        updates: Fields to update (status, budget, bid_amount, etc.)

    Returns:
        Updated object confirmation
    """
    # ... implementation
    return {"updated": True, "object_id": object_id}
```

### Secrets Management

```bash
# v5/vibe-inc/config/secrets.env (gitignored)
META_APP_ID=...
META_APP_SECRET=...
META_ACCESS_TOKEN=...
META_AD_ACCOUNT_ID=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_CUSTOMER_ID=...
GA4_PROPERTY_ID=...
GA4_SERVICE_ACCOUNT_JSON=...
SHOPIFY_STORE=...
SHOPIFY_API_KEY=...
SHOPIFY_API_SECRET=...
```

Loaded via `python-dotenv` in role initialization. Never committed to git.

---

## 7. Phased Rollout

### Phase 1: Story Distributor (Weeks 1-8)

**Goal:** Ads + CRO running with daily optimization and weekly reporting.

**Strategy:** Meta Ads + GA4 first (core pair). Google Ads deferred until account recovery confirmed. Shopify LP integration added in weeks 5-6.

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-2 | Core tool layer | Meta Ads API + GA4 Data API wrappers, tested against real APIs. Secrets management (dotenv). |
| 3 | AdOps operator (Meta) | campaign_create + daily_optimize workflows with Meta tools, unit tested |
| 4 | CROps operator | experiment_analyze + funnel_diagnose workflows with GA4, unit tested |
| 5 | Shopify + Google Ads | Shopify page read/write tools. Google Ads tools (if account recovered). |
| 6 | CROps page_optimize | LP modification workflow with Shopify, approval gate wired |
| 7 | Integration | End-to-end: create Meta campaign → run → GA4 analyze → optimize loop |
| 8 | Validation | Run on real Bot story validation data, validate against human decisions |

**Phase 1 Bootstrap:** Hardcode current messaging context (Bot 3 narratives, Dot 2 paths) from CEO docs into shared memory YAML files. Strategy role will replace this in Phase 2.

**Fallback:** If Google Ads account is not recoverable by week 5, defer Google Ads integration entirely. Meta + GA4 alone deliver the core value.

**Gate → Phase 2:**
- Daily optimize workflow running for 2+ weeks
- Weekly report matches human-generated reports
- At least 1 autonomous bid adjustment validated

### Phase 2: Story Strategist (Weeks 7-10)

**Goal:** PMM decisions formalized, competitive intel automated.

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 7 | PositioningEngine | define_framework + validate_story workflows |
| 8 | CompetitiveIntel | weekly_scan + threat_assess workflows |
| 9 | Shared memory | Replace hardcoded messaging with dynamic Strategist output |
| 10 | Validation | Strategist analysis matches Tara's positioning decisions |

**Gate → Phase 3:**
- Messaging frameworks generated for all 3 products
- Weekly competitive scan running
- Story validation analysis automated

### Phase 3: Story Creator (Weeks 11-16)

**Goal:** Content machine producing 10+/month, creative variants feeding Distributor.

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 11-12 | ContentEngine | research_topics + write_article workflows |
| 13 | CreativeFactory | generate_ad_copy + analyze_creative_performance |
| 14-15 | Integration | Full loop: Strategist → Creator → Distributor |
| 16 | Validation | Published content matches quality bar, creative variants tested |

**Gate → Scale:**
- 10+ content pieces published in a month
- At least 3 ad creative variants generated and tested
- Full three-role loop validated end-to-end

---

## 8. Success Criteria

### Phase 1 (Distributor)
- Net New CAC tracked separately from Known (currently not possible)
- Daily optimization running without manual intervention
- Story validation experiments analyzed automatically
- CVR improvement on at least 1 product PDP

### Phase 2 (Strategist)
- Messaging frameworks exist for Bot, Dot, Board
- Competitive battlecards updated weekly
- Story validation winner identified with data backing

### Phase 3 (Creator)
- Content machine: 10+/month published
- Ad creative: 3-5 variants per campaign tested
- Organic traffic share: 27% → 32%+

### Overall (by end of Phase 3)
- Full D2C story loop: Strategist decides → Creator produces → Distributor spreads
- Human role shifts from execution to review/approve
- Foundation for replicating to Astrocrest brands

---

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Meta/Google API rate limits or policy changes | Medium | High | Rate limiting in tool layer (exponential backoff), fallback to manual |
| Ad platform bans automated management | Low | High | Start with read-heavy, write-light |
| Content quality below human bar | Medium | Medium | Approval gates on all published content |
| Story validation data insufficient for AI analysis | Medium | Medium | Minimum sample size checks before recommending |
| Secrets management breach | Low | Critical | Environment-only, never in code or memory |
| Google Ads account not recoverable | Medium | Medium | Phase 1 ships Meta-only. Google Ads deferred or new account. |
| Phase 1 takes longer than 8 weeks | Medium | Medium | Ship AdOps (Meta) first, CROps second (split Phase 1) |

---

## 10. Open Questions

1. **Hotjar integration:** API available? Or manual data export?
2. **CMS specifics:** Is the website pure Shopify, or Shopify + custom frontend?
3. **Google Ads recovery:** Is the suspended account recoverable, or new account needed?
4. **Budget for AI API costs:** Anthropic API calls for role execution — what's the budget ceiling?
5. **Approval workflow UX:** CLI review (existing), Slack notification, or web UI?
