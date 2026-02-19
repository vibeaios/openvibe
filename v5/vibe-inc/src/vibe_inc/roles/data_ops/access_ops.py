"""AccessOps operator — query routing, report building, and cache management."""
from openvibe_sdk import Operator, agent_node

from vibe_inc.tools.analytics_tools import (
    analytics_query_cohort,
    analytics_query_events,
    analytics_query_funnel,
    analytics_query_metrics,
    analytics_query_sql,
)
from vibe_inc.tools.shared_memory import read_memory, write_memory


class AccessOps(Operator):
    operator_id = "access_ops"

    @agent_node(
        tools=[analytics_query_metrics, analytics_query_funnel, analytics_query_sql, read_memory],
        output_key="query_result",
    )
    def route_query(self, state):
        """You are a data query router for Vibe's CDP (Redshift + dbt).

        Given a natural language question, route it to the right data:
        1. Read the data catalog to understand available tables and columns.
        2. Determine which table(s) can answer the question.
        3. Choose the right tool:
           - analytics_query_metrics for aggregated KPIs (spend, impressions, CAC)
           - analytics_query_funnel for conversion funnel analysis
           - analytics_query_sql for complex joins or custom queries
        4. Execute the query and format the result.
        5. Always include the SQL that was executed for transparency.

        Return: query result with data, SQL used, and source table."""
        question = state.get("question", "")
        return f"Answer this data question: {question}"

    @agent_node(
        tools=[analytics_query_metrics, analytics_query_funnel, analytics_query_cohort,
               analytics_query_events, analytics_query_sql, read_memory, write_memory],
        output_key="report_result",
    )
    def build_report(self, state):
        """You are a report builder for Vibe's CDP.

        Build a structured report from multiple data queries:
        1. Read the report template from shared memory (if exists).
        2. Execute multiple queries to gather all needed data.
        3. Structure the report in progressive disclosure format:
           - Headline: one-line verdict
           - Summary: 3-5 key metrics with trends
           - Detail: full breakdown tables
        4. Write the report to shared memory for other roles to access.

        Return: formatted report with headline, summary, and detail sections."""
        report_type = state.get("report_type", "weekly_performance")
        return f"Build {report_type} report."

    @agent_node(
        tools=[analytics_query_sql, read_memory, write_memory],
        output_key="cache_result",
    )
    def cache_refresh(self, state):
        """You are a data cache manager for Vibe's CDP.

        Refresh cached aggregations in shared memory:
        1. Query latest metrics from Redshift for commonly-used views:
           - Daily platform spend totals
           - Weekly CAC by product
           - Funnel conversion rates
        2. Write the results to shared memory performance/ directory.
        3. Include timestamps so consumers know data freshness.
        4. This runs on a schedule — keep it fast and focused.

        Return: what was refreshed, row counts, timestamps."""
        scope = state.get("scope", "daily")
        return f"Refresh data cache. Scope: {scope}."
