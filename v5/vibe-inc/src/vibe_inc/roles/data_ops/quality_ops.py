"""QualityOps operator — data freshness, discrepancy detection, and credibility scoring."""
from openvibe_sdk import Operator, agent_node

from vibe_inc.tools.analytics_tools import analytics_query_metrics, analytics_query_sql
from vibe_inc.tools.shared_memory import read_memory, write_memory


class QualityOps(Operator):
    operator_id = "quality_ops"

    @agent_node(
        tools=[analytics_query_sql, read_memory, write_memory],
        output_key="freshness_result",
    )
    def freshness_monitor(self, state):
        """You are a data freshness monitor for Vibe's CDP (Redshift + dbt).

        Check data freshness across all key tables:
        1. Query MAX(date) or MAX(updated_at) for each fact table:
           - fct_ads_ad_metrics, fct_order, fct_website_session,
             fct_website_visitor_conversion, fct_email_event
        2. Compare against expected freshness SLA:
           - Ads: ≤24h stale
           - Orders: ≤6h stale
           - Website: ≤12h stale
           - Email: ≤24h stale
        3. Flag any tables exceeding SLA.
        4. Write freshness status to shared memory for other roles to read.

        Return: table-by-table freshness status, SLA compliance, alerts."""
        tables = state.get("tables", "all")
        return f"Check data freshness. Tables: {tables}."

    @agent_node(
        tools=[analytics_query_metrics, analytics_query_sql, read_memory],
        output_key="discrepancy_result",
    )
    def discrepancy_report(self, state):
        """You are a data discrepancy analyst for Vibe's CDP.

        Compare data between Redshift and source platforms to find mismatches:
        1. For a given platform and date range, query Redshift spend/impressions/clicks.
        2. Compare against known platform dashboard values (from shared memory).
        3. Calculate discrepancy % for each metric.
        4. Flag anything >5% discrepancy.
        5. Common causes: attribution windows, timezone mismatches, late data.

        Return: platform-by-platform comparison, discrepancy %, likely causes."""
        platform = state.get("platform", "all")
        date_range = state.get("date_range", "last_7d")
        return f"Check data discrepancies for {platform} over {date_range}."

    @agent_node(
        tools=[analytics_query_sql, read_memory],
        output_key="credibility_result",
    )
    def credibility_assessment(self, state):
        """You are a data credibility assessor for Vibe's CDP.

        Assess the trustworthiness of data for decision-making:
        1. Check row counts — are there unexpected drops or spikes?
        2. Check NULL rates for key columns (spend, conversions, order amounts).
        3. Check for duplicate primary keys.
        4. Verify referential integrity (fact FK → dimension PK).
        5. Score credibility: High (>95% clean), Medium (85-95%), Low (<85%).

        Return: credibility score by domain, specific issues, remediation steps."""
        domain = state.get("domain", "ads")
        return f"Assess data credibility for {domain} domain."
