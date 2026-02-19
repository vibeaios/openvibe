"""LangGraph workflow factories for DataOps."""
from typing import TypedDict

from langgraph.graph import StateGraph


class AuditState(TypedDict, total=False):
    scope: str
    audit_result: str


class FreshnessState(TypedDict, total=False):
    tables: str
    freshness_result: str


class QueryState(TypedDict, total=False):
    question: str
    query_result: str


class ReportState(TypedDict, total=False):
    report_type: str
    report_result: str


def create_catalog_audit_graph(operator):
    """Catalog audit: read catalog → check completeness → report gaps."""
    graph = StateGraph(AuditState)
    graph.add_node("audit", operator.schema_audit)
    graph.set_entry_point("audit")
    graph.set_finish_point("audit")
    return graph.compile()


def create_freshness_check_graph(operator):
    """Freshness check: query max dates → compare SLAs → alert if stale."""
    graph = StateGraph(FreshnessState)
    graph.add_node("check", operator.freshness_monitor)
    graph.set_entry_point("check")
    graph.set_finish_point("check")
    return graph.compile()


def create_data_query_graph(operator):
    """Data query: parse question → route to table → execute → return."""
    graph = StateGraph(QueryState)
    graph.add_node("query", operator.route_query)
    graph.set_entry_point("query")
    graph.set_finish_point("query")
    return graph.compile()


def create_build_report_graph(operator):
    """Build report: gather data → structure → write to shared memory."""
    graph = StateGraph(ReportState)
    graph.add_node("report", operator.build_report)
    graph.set_entry_point("report")
    graph.set_finish_point("report")
    return graph.compile()
