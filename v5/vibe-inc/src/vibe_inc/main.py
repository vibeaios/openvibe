"""Vibe Inc runtime — wires roles, operators, and workflows."""
from openvibe_sdk import RoleRuntime

from vibe_inc.roles.d2c_growth import D2CGrowth
from vibe_inc.roles.d2c_growth.workflows import (
    create_amazon_campaign_create_graph,
    create_amazon_competitive_analysis_graph,
    create_amazon_daily_optimize_graph,
    create_amazon_search_term_harvest_graph,
    create_amazon_weekly_report_graph,
    create_experiment_analyze_graph,
    create_funnel_diagnose_graph,
    create_google_campaign_create_graph,
    create_google_daily_optimize_graph,
    create_google_recommendations_review_graph,
    create_google_search_term_mining_graph,
    create_google_weekly_report_graph,
    create_linkedin_campaign_create_graph,
    create_linkedin_daily_optimize_graph,
    create_linkedin_lead_quality_review_graph,
    create_linkedin_weekly_report_graph,
    create_meta_audience_refresh_graph,
    create_meta_campaign_create_graph,
    create_meta_daily_optimize_graph,
    create_meta_weekly_report_graph,
    create_page_optimize_graph,
    create_product_optimize_graph,
    create_discount_strategy_graph,
    create_conversion_report_graph,
    create_pinterest_daily_optimize_graph,
    create_pinterest_campaign_create_graph,
    create_pinterest_creative_refresh_graph,
    create_pinterest_weekly_report_graph,
    create_tiktok_campaign_create_graph,
    create_tiktok_creative_refresh_graph,
    create_tiktok_daily_optimize_graph,
    create_tiktok_weekly_report_graph,
)
from vibe_inc.roles.d2c_growth.crm_workflows import (
    create_deal_progression_graph,
    create_enrichment_audit_graph,
    create_pipeline_health_graph,
    create_workflow_enrollment_graph,
)
from vibe_inc.roles.d2c_growth.cross_platform_workflows import (
    create_unified_cac_report_graph,
    create_budget_rebalance_graph,
    create_platform_health_check_graph,
)
from vibe_inc.roles.d2c_growth.email_workflows import (
    create_email_campaign_create_graph,
    create_email_flow_optimize_graph,
    create_email_segment_refresh_graph,
    create_email_lifecycle_report_graph,
)
from vibe_inc.roles.d2c_strategy import D2CStrategy
from vibe_inc.roles.d2c_strategy.workflows import (
    create_define_framework_graph,
    create_refine_icp_graph,
    create_threat_assess_graph,
    create_validate_story_graph,
    create_weekly_scan_graph,
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
    runtime = RoleRuntime(roles=[D2CGrowth, D2CStrategy, DataOps], llm=llm)

    # MetaAdOps workflows
    runtime.register_workflow("meta_ad_ops", "campaign_create", create_meta_campaign_create_graph)
    runtime.register_workflow("meta_ad_ops", "daily_optimize", create_meta_daily_optimize_graph)
    runtime.register_workflow("meta_ad_ops", "weekly_report", create_meta_weekly_report_graph)
    runtime.register_workflow("meta_ad_ops", "audience_refresh", create_meta_audience_refresh_graph)

    # GoogleAdOps workflows
    runtime.register_workflow("google_ad_ops", "campaign_create", create_google_campaign_create_graph)
    runtime.register_workflow("google_ad_ops", "daily_optimize", create_google_daily_optimize_graph)
    runtime.register_workflow("google_ad_ops", "search_term_mining", create_google_search_term_mining_graph)
    runtime.register_workflow("google_ad_ops", "weekly_report", create_google_weekly_report_graph)
    runtime.register_workflow("google_ad_ops", "recommendations_review", create_google_recommendations_review_graph)

    # AmazonAdOps workflows
    runtime.register_workflow("amazon_ad_ops", "campaign_create", create_amazon_campaign_create_graph)
    runtime.register_workflow("amazon_ad_ops", "daily_optimize", create_amazon_daily_optimize_graph)
    runtime.register_workflow("amazon_ad_ops", "search_term_harvesting", create_amazon_search_term_harvest_graph)
    runtime.register_workflow("amazon_ad_ops", "weekly_report", create_amazon_weekly_report_graph)
    runtime.register_workflow("amazon_ad_ops", "competitive_analysis", create_amazon_competitive_analysis_graph)

    # TikTokAdOps workflows
    runtime.register_workflow("tiktok_ad_ops", "campaign_create", create_tiktok_campaign_create_graph)
    runtime.register_workflow("tiktok_ad_ops", "daily_optimize", create_tiktok_daily_optimize_graph)
    runtime.register_workflow("tiktok_ad_ops", "creative_refresh", create_tiktok_creative_refresh_graph)
    runtime.register_workflow("tiktok_ad_ops", "weekly_report", create_tiktok_weekly_report_graph)

    # LinkedInAdOps workflows
    runtime.register_workflow("linkedin_ad_ops", "campaign_create", create_linkedin_campaign_create_graph)
    runtime.register_workflow("linkedin_ad_ops", "daily_optimize", create_linkedin_daily_optimize_graph)
    runtime.register_workflow("linkedin_ad_ops", "weekly_report", create_linkedin_weekly_report_graph)
    runtime.register_workflow("linkedin_ad_ops", "lead_quality_review", create_linkedin_lead_quality_review_graph)

    # PinterestAdOps workflows
    runtime.register_workflow("pinterest_ad_ops", "campaign_create", create_pinterest_campaign_create_graph)
    runtime.register_workflow("pinterest_ad_ops", "daily_optimize", create_pinterest_daily_optimize_graph)
    runtime.register_workflow("pinterest_ad_ops", "creative_refresh", create_pinterest_creative_refresh_graph)
    runtime.register_workflow("pinterest_ad_ops", "weekly_report", create_pinterest_weekly_report_graph)

    # EmailOps workflows
    runtime.register_workflow("email_ops", "campaign_create", create_email_campaign_create_graph)
    runtime.register_workflow("email_ops", "flow_optimize", create_email_flow_optimize_graph)
    runtime.register_workflow("email_ops", "segment_refresh", create_email_segment_refresh_graph)
    runtime.register_workflow("email_ops", "lifecycle_report", create_email_lifecycle_report_graph)

    # CROps workflows
    runtime.register_workflow("cro_ops", "experiment_analyze", create_experiment_analyze_graph)
    runtime.register_workflow("cro_ops", "funnel_diagnose", create_funnel_diagnose_graph)
    runtime.register_workflow("cro_ops", "page_optimize", create_page_optimize_graph)
    runtime.register_workflow("cro_ops", "product_optimize", create_product_optimize_graph)
    runtime.register_workflow("cro_ops", "discount_strategy", create_discount_strategy_graph)
    runtime.register_workflow("cro_ops", "conversion_report", create_conversion_report_graph)

    # CrossPlatformOps workflows
    runtime.register_workflow("cross_platform_ops", "unified_cac_report", create_unified_cac_report_graph)
    runtime.register_workflow("cross_platform_ops", "budget_rebalance", create_budget_rebalance_graph)
    runtime.register_workflow("cross_platform_ops", "platform_health_check", create_platform_health_check_graph)

    # CRMOps workflows
    runtime.register_workflow("crm_ops", "workflow_enrollment", create_workflow_enrollment_graph)
    runtime.register_workflow("crm_ops", "deal_progression", create_deal_progression_graph)
    runtime.register_workflow("crm_ops", "enrichment_audit", create_enrichment_audit_graph)
    runtime.register_workflow("crm_ops", "pipeline_health", create_pipeline_health_graph)

    # PositioningEngine workflows
    runtime.register_workflow("positioning_engine", "define_framework", create_define_framework_graph)
    runtime.register_workflow("positioning_engine", "validate_story", create_validate_story_graph)
    runtime.register_workflow("positioning_engine", "refine_icp", create_refine_icp_graph)

    # CompetitiveIntel workflows
    runtime.register_workflow("competitive_intel", "weekly_scan", create_weekly_scan_graph)
    runtime.register_workflow("competitive_intel", "threat_assess", create_threat_assess_graph)

    # CatalogOps workflows
    runtime.register_workflow("catalog_ops", "catalog_audit", create_catalog_audit_graph)

    # QualityOps workflows
    runtime.register_workflow("quality_ops", "freshness_check", create_freshness_check_graph)

    # AccessOps workflows
    runtime.register_workflow("access_ops", "data_query", create_data_query_graph)
    runtime.register_workflow("access_ops", "build_report", create_build_report_graph)

    return runtime
