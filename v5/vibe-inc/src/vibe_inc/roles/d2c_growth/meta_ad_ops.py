"""MetaAdOps operator — manages Meta (Facebook/Instagram) ad campaigns."""
from openvibe_sdk import Operator, agent_node

from vibe_inc.tools.ads.meta_ads import (
    meta_ads_create,
    meta_ads_read,
    meta_ads_update,
    meta_ads_rules,
    meta_audiences,
)


class MetaAdOps(Operator):
    operator_id = "meta_ad_ops"

    @agent_node(
        tools=[meta_ads_read, meta_ads_create, meta_ads_update],
        output_key="campaign_result",
    )
    def campaign_create(self, state):
        """You are a Meta Ads performance marketing specialist for Vibe hardware products.

        Given a campaign brief, create a complete Meta Ads campaign structure:
        1. Review the brief (product, narrative, audience, budget).
        2. Read the messaging framework from shared memory for the product.
        3. Create a campaign with appropriate objective and naming convention:
           [Product] - [Narrative] - [Audience] - [Date]
        4. Use PAUSED status so human can review before activating.
        5. Always separate Net New audiences from Known (exclude site visitors, video viewers, prior clickers).

        Return a summary of what was created with IDs and configuration."""
        brief = state.get("brief", {})
        return f"Create campaign from brief: {brief}"

    @agent_node(
        tools=[meta_ads_read, meta_ads_update, meta_ads_rules],
        output_key="optimization_result",
    )
    def daily_optimize(self, state):
        """You are a Meta Ads performance marketing optimizer for Vibe hardware products.

        Review all active campaign performance from the last 24 hours:
        1. Read campaign-level and adset-level performance data.
        2. Compare CPA against target benchmarks (Bot: $400, Dot: $300).
        3. Check automated rules — ensure they're firing correctly.
        4. Apply these rules:
           - Bid adjustment ≤20%: execute autonomously.
           - Pause any ad with CPA >2x target: execute autonomously.
           - Budget change >$500/day: flag for approval (do not execute).
        5. Always calculate and report Net New CAC separately from Known.
        6. Summarize: what changed, what needs approval, overall health.

        Return a structured optimization report."""
        date = state.get("date", "today")
        return f"Review and optimize all active Meta campaigns for {date}."

    @agent_node(
        tools=[meta_ads_read],
        output_key="report",
    )
    def weekly_report(self, state):
        """You are a Meta Ads performance marketing analyst for Vibe.

        Generate a weekly performance report covering:
        1. Read all campaign data for the past 7 days.
        2. Calculate Net New CAC vs Known CAC by product (Bot, Dot, Board).
        3. Calculate ROAS by campaign.
        4. Report spend efficiency: revenue per visitor, cost per click.
        5. Highlight top 3 performers and bottom 3 underperformers.
        6. Compare against targets: Bot CAC ≤$400, Dot CAC ≤$300, CVR ≥2%.

        Format as progressive disclosure: headline → summary → detailed breakdown."""
        week = state.get("week", "current")
        return f"Generate weekly Meta Ads performance report for {week}."

    @agent_node(
        tools=[meta_audiences, meta_ads_read],
        output_key="audience_result",
    )
    def audience_refresh(self, state):
        """You are a Meta Ads audience management specialist for Vibe.

        Review and refresh custom and lookalike audiences:
        1. List all custom audiences and their sizes.
        2. Check last refresh dates — flag stale audiences (>30 days).
        3. Compare audience performance: which audiences drive lowest Net New CAC?
        4. Recommend audience consolidation or expansion.
        5. Ensure Net New exclusions are current (exclude purchasers, site visitors >180d).

        Return: audience inventory, staleness status, performance ranking, recommendations."""
        action = state.get("action", "review")
        return f"Review Meta audiences. Action: {action}."

    @agent_node(
        tools=[meta_ads_read],
        output_key="fatigue_result",
    )
    def creative_fatigue_check(self, state):
        """You are a Meta Ads creative performance analyst for Vibe.

        Detect creative fatigue across active campaigns:
        1. Read ad-level performance for last 14 days.
        2. Calculate trend: is CTR declining? Is CPC rising?
        3. Fatigue signals: CTR drop >20% week-over-week, frequency >3.0.
        4. For each fatigued creative, recommend: pause, refresh copy, or new creative.
        5. Cross-reference with best-performing creatives to suggest replacements.

        Return: creative health status, fatigue alerts, recommended actions."""
        lookback = state.get("lookback_days", 14)
        return f"Check creative fatigue over last {lookback} days."
