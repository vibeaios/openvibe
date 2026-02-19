"""CatalogOps operator — manages the dbt data catalog, field mappings, and coverage."""
from openvibe_sdk import Operator, agent_node

from vibe_inc.tools.shared_memory import read_memory, write_memory


class CatalogOps(Operator):
    operator_id = "catalog_ops"

    @agent_node(
        tools=[read_memory, write_memory],
        output_key="audit_result",
    )
    def schema_audit(self, state):
        """You are a data catalog auditor for Vibe's CDP (dbt-cdp on Redshift).

        Audit the current data catalog for completeness and accuracy:
        1. Read the catalog from shared memory (data/catalog.yaml).
        2. Check each table definition: are all key columns documented?
        3. Verify foreign key references (dim_*_sk) are consistent across tables.
        4. Flag any tables missing description, grain, or column definitions.
        5. Compare against known dbt models — identify gaps.

        Return: audit summary with coverage %, issues found, recommendations."""
        scope = state.get("scope", "all")
        return f"Audit the data catalog. Scope: {scope}."

    @agent_node(
        tools=[read_memory, write_memory],
        output_key="mapping_result",
    )
    def field_mapping(self, state):
        """You are a data field mapping specialist for Vibe's CDP.

        Review and update the field mapping definitions:
        1. Read current field_mapping.yaml from shared memory.
        2. Check that all unified conversion names match dbt macro definitions.
        3. Verify revenue metric definitions are accurate.
        4. Validate funnel stage ordering matches actual data flow.
        5. Update mappings if discrepancies found.

        Return: mapping status, any changes made, consistency report."""
        focus = state.get("focus", "conversions")
        return f"Review field mappings. Focus area: {focus}."

    @agent_node(
        tools=[read_memory],
        output_key="coverage_result",
    )
    def coverage_report(self, state):
        """You are a data coverage analyst for Vibe's CDP.

        Generate a coverage report showing what data is available:
        1. Read the catalog and field mappings.
        2. For each domain (ads, orders, website, email), list available tables.
        3. Calculate coverage: how many key business questions can be answered?
        4. Identify blind spots — what data is missing or not in the warehouse?
        5. Recommend priorities for catalog expansion.

        Return: coverage % by domain, blind spots, expansion priorities."""
        domain = state.get("domain", "all")
        return f"Generate data coverage report. Domain: {domain}."
