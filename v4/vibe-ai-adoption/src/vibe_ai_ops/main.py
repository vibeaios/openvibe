"""Build the operator-based system.

Loads operators.yaml, creates the OperatorRuntime, and registers all
workflow graph factories. This is the central wiring point.
"""

from __future__ import annotations

from typing import Any

from vibe_ai_ops.operators.base import OperatorRuntime
from vibe_ai_ops.shared.tracing import init_tracing
from vibe_ai_ops.temporal.schedules import build_schedule_specs
from vibe_ai_ops.shared.config import load_agent_configs

# --- Workflow graph factories ---
from vibe_ai_ops.operators.company_intel.workflows.research import (
    create_company_intel_graph,
)
from vibe_ai_ops.operators.revenue_ops.workflows.lead_qualification import (
    create_lead_qual_graph,
)
from vibe_ai_ops.operators.revenue_ops.workflows.engagement import (
    create_engagement_graph,
)
from vibe_ai_ops.operators.revenue_ops.workflows.nurture_sequence import (
    create_nurture_graph,
)
from vibe_ai_ops.operators.revenue_ops.workflows.buyer_intelligence import (
    create_buyer_intel_graph,
)
from vibe_ai_ops.operators.revenue_ops.workflows.deal_support import (
    create_deal_support_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.segment_research import (
    create_segment_research_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.message_testing import (
    create_message_testing_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.content_generation import (
    create_content_generation_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.repurposing import (
    create_repurposing_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.distribution import (
    create_distribution_graph,
)
from vibe_ai_ops.operators.content_engine.workflows.journey_optimization import (
    create_journey_optimization_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.onboarding import (
    create_onboarding_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.success_advisory import (
    create_success_advisory_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.health_monitoring import (
    create_health_monitoring_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.expansion_scan import (
    create_expansion_scan_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.customer_voice import (
    create_customer_voice_graph,
)
from vibe_ai_ops.operators.customer_success.workflows.urgent_review import (
    create_urgent_review_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.funnel_monitor import (
    create_funnel_monitor_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.deal_risk_forecast import (
    create_deal_risk_forecast_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.conversation_analysis import (
    create_conversation_analysis_graph,
)
from vibe_ai_ops.operators.market_intel.workflows.nl_query import (
    create_nl_query_graph,
)

# Map: (operator_id, workflow_id) → graph factory
_WORKFLOW_REGISTRY: dict[tuple[str, str], Any] = {
    # Company Intel
    ("company_intel", "research"): create_company_intel_graph,
    # Revenue Ops
    ("revenue_ops", "lead_qualification"): create_lead_qual_graph,
    ("revenue_ops", "engagement"): create_engagement_graph,
    ("revenue_ops", "nurture_sequence"): create_nurture_graph,
    ("revenue_ops", "buyer_intelligence"): create_buyer_intel_graph,
    ("revenue_ops", "deal_support"): create_deal_support_graph,
    # Content Engine
    ("content_engine", "segment_research"): create_segment_research_graph,
    ("content_engine", "message_testing"): create_message_testing_graph,
    ("content_engine", "content_generation"): create_content_generation_graph,
    ("content_engine", "repurposing"): create_repurposing_graph,
    ("content_engine", "distribution"): create_distribution_graph,
    ("content_engine", "journey_optimization"): create_journey_optimization_graph,
    # Customer Success
    ("customer_success", "onboarding"): create_onboarding_graph,
    ("customer_success", "success_advisory"): create_success_advisory_graph,
    ("customer_success", "health_monitoring"): create_health_monitoring_graph,
    ("customer_success", "expansion_scan"): create_expansion_scan_graph,
    ("customer_success", "customer_voice"): create_customer_voice_graph,
    ("customer_success", "urgent_review"): create_urgent_review_graph,
    # Market Intelligence
    ("market_intel", "funnel_monitor"): create_funnel_monitor_graph,
    ("market_intel", "deal_risk_forecast"): create_deal_risk_forecast_graph,
    ("market_intel", "conversation_analysis"): create_conversation_analysis_graph,
    ("market_intel", "nl_query"): create_nl_query_graph,
}


def build_system(
    config_path: str = "config/operators.yaml",
) -> dict[str, Any]:
    """Build the complete operator system.

    Loads operators.yaml, creates the runtime, registers all workflow
    factories, and returns system state for inspection.
    """
    runtime = OperatorRuntime(config_path=config_path)
    runtime.load(enabled_only=True)

    # Register all workflow graph factories
    for (op_id, wf_id), factory in _WORKFLOW_REGISTRY.items():
        if op_id in runtime.operators:
            runtime.register_workflow(op_id, wf_id, factory)

    tracing = init_tracing()

    # Build Temporal schedule specs from old agent configs (backward compat)
    try:
        agent_configs = load_agent_configs("config/agents.yaml", enabled_only=True)
        schedules = build_schedule_specs(agent_configs)
    except FileNotFoundError:
        schedules = []

    return {
        "runtime": runtime,
        "operator_count": len(runtime.operators),
        "operators": runtime.list_operators(),
        "summary": runtime.summary(),
        "schedules": schedules,
        "tracing": tracing,
    }
