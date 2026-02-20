"""LangGraph workflow factories for D2C Strategy operators."""
from typing import TypedDict

from langgraph.graph import StateGraph


# --- PositioningEngine states ---


class DefineFrameworkState(TypedDict, total=False):
    product: str
    framework_result: str


class ValidateStoryState(TypedDict, total=False):
    product: str
    experiment_id: str
    validation_result: str


class RefineICPState(TypedDict, total=False):
    product: str
    icp_result: str


# --- CompetitiveIntel states ---


class WeeklyScanState(TypedDict, total=False):
    period: str
    scan_result: str


class ThreatAssessState(TypedDict, total=False):
    competitor: str
    move: str
    threat_result: str


# --- PositioningEngine workflows ---


def create_define_framework_graph(operator):
    """Positioning: product specs → messaging framework."""
    graph = StateGraph(DefineFrameworkState)
    graph.add_node("define", operator.define_framework)
    graph.set_entry_point("define")
    graph.set_finish_point("define")
    return graph.compile()


def create_validate_story_graph(operator):
    """Positioning: experiment data → winner analysis."""
    graph = StateGraph(ValidateStoryState)
    graph.add_node("validate", operator.validate_story)
    graph.set_entry_point("validate")
    graph.set_finish_point("validate")
    return graph.compile()


def create_refine_icp_graph(operator):
    """Positioning: purchase + CRM data → updated ICP definitions."""
    graph = StateGraph(RefineICPState)
    graph.add_node("refine", operator.refine_icp)
    graph.set_entry_point("refine")
    graph.set_finish_point("refine")
    return graph.compile()


# --- CompetitiveIntel workflows ---


def create_weekly_scan_graph(operator):
    """Competitive: scan competitors → digest + battlecard updates."""
    graph = StateGraph(WeeklyScanState)
    graph.add_node("scan", operator.weekly_scan)
    graph.set_entry_point("scan")
    graph.set_finish_point("scan")
    return graph.compile()


def create_threat_assess_graph(operator):
    """Competitive: specific move → impact analysis + response options."""
    graph = StateGraph(ThreatAssessState)
    graph.add_node("assess", operator.threat_assess)
    graph.set_entry_point("assess")
    graph.set_finish_point("assess")
    return graph.compile()
