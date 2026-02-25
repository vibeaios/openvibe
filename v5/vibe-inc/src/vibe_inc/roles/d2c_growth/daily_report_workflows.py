"""LangGraph workflow factory for DailyReportOps."""

from typing import TypedDict

from langgraph.graph import StateGraph


class DailyReportState(TypedDict, total=False):
    date: str
    l1_data: dict
    l2_data: dict
    l3_data: dict
    report: str


def create_daily_growth_report_graph(operator):
    """Daily growth report: fetch Redshift data -> interpret with Claude.

    Two nodes:
    - fetch_data: deterministic SQL execution for L1/L2/L3
    - interpret: Claude analyzes data and produces formatted report
    """
    graph = StateGraph(DailyReportState)
    graph.add_node("fetch_data", operator.fetch_data)
    graph.add_node("interpret", operator.interpret)
    graph.add_edge("fetch_data", "interpret")
    graph.set_entry_point("fetch_data")
    graph.set_finish_point("interpret")
    return graph.compile()
