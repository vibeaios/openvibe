"""LangGraph workflow factories for CRMOps."""
from typing import TypedDict

from langgraph.graph import StateGraph


class WorkflowEnrollmentState(TypedDict, total=False):
    contact_email: str
    signal: str
    enrollment_result: str


class DealProgressionState(TypedDict, total=False):
    contact_id: str
    deal_data: dict
    deal_result: str


class EnrichmentAuditState(TypedDict, total=False):
    contact_email: str
    enrichment_result: str


class PipelineHealthState(TypedDict, total=False):
    pipeline_id: str
    pipeline_result: str


def create_workflow_enrollment_graph(operator):
    """CRM workflow enrollment: signal → contact lookup → workflow enroll."""
    graph = StateGraph(WorkflowEnrollmentState)
    graph.add_node("trigger", operator.workflow_trigger)
    graph.set_entry_point("trigger")
    graph.set_finish_point("trigger")
    return graph.compile()


def create_deal_progression_graph(operator):
    """CRM deal progression: contact → enrichment check → deal create/update."""
    graph = StateGraph(DealProgressionState)
    graph.add_node("manage", operator.deal_manage)
    graph.set_entry_point("manage")
    graph.set_finish_point("manage")
    return graph.compile()


def create_enrichment_audit_graph(operator):
    """CRM enrichment audit: contact → enrichment status → recommendation."""
    graph = StateGraph(EnrichmentAuditState)
    graph.add_node("check", operator.contact_enrich_check)
    graph.set_entry_point("check")
    graph.set_finish_point("check")
    return graph.compile()


def create_pipeline_health_graph(operator):
    """CRM pipeline health: deals → stage counts → stale alerts → KPIs."""
    graph = StateGraph(PipelineHealthState)
    graph.add_node("review", operator.pipeline_review)
    graph.set_entry_point("review")
    graph.set_finish_point("review")
    return graph.compile()
