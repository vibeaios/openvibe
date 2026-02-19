"""Vibe Inc runtime — wires roles, operators, and workflows."""
from openvibe_sdk import RoleRuntime

from vibe_inc.roles.d2c_growth import D2CGrowth
from vibe_inc.roles.d2c_growth.workflows import (
    create_campaign_create_graph,
    create_daily_optimize_graph,
    create_experiment_analyze_graph,
    create_funnel_diagnose_graph,
    create_page_optimize_graph,
    create_weekly_report_graph,
)
from vibe_inc.roles.data_ops import DataOps
from vibe_inc.roles.data_ops.workflows import (
    create_build_report_graph,
    create_catalog_audit_graph,
    create_data_query_graph,
    create_freshness_check_graph,
)


def create_runtime(llm) -> RoleRuntime:
    """Create and configure the Vibe Inc RoleRuntime.

    Registers all roles and workflow factories.
    """
    runtime = RoleRuntime(roles=[D2CGrowth, DataOps], llm=llm)

    # MetaAdOps workflows
    runtime.register_workflow("meta_ad_ops", "campaign_create", create_campaign_create_graph)
    runtime.register_workflow("meta_ad_ops", "daily_optimize", create_daily_optimize_graph)
    runtime.register_workflow("meta_ad_ops", "weekly_report", create_weekly_report_graph)

    # CROps workflows
    runtime.register_workflow("cro_ops", "experiment_analyze", create_experiment_analyze_graph)
    runtime.register_workflow("cro_ops", "funnel_diagnose", create_funnel_diagnose_graph)
    runtime.register_workflow("cro_ops", "page_optimize", create_page_optimize_graph)

    # CatalogOps workflows
    runtime.register_workflow("catalog_ops", "catalog_audit", create_catalog_audit_graph)

    # QualityOps workflows
    runtime.register_workflow("quality_ops", "freshness_check", create_freshness_check_graph)

    # AccessOps workflows
    runtime.register_workflow("access_ops", "data_query", create_data_query_graph)
    runtime.register_workflow("access_ops", "build_report", create_build_report_graph)

    return runtime
