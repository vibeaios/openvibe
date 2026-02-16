"""Lead Qualification workflow — enrich → score → route → update_crm.

Migrated from graphs/sales/s1_lead_qualification.py.
Replaces CrewAI crew_kickoff() with call_claude().
"""

from __future__ import annotations

import json
import os
from typing import Any

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.revenue_ops.state import RevenueOpsState
from vibe_ai_ops.shared.config import load_prompt
from vibe_ai_ops.shared.hubspot_client import HubSpotClient

# Module-level client — lazy init, mockable in tests
hubspot_client: HubSpotClient | None = None


def _get_hubspot() -> HubSpotClient:
    global hubspot_client
    if hubspot_client is None:
        hubspot_client = HubSpotClient(api_key=os.environ.get("HUBSPOT_API_KEY"))
    return hubspot_client


def _enrich_lead(state: RevenueOpsState) -> RevenueOpsState:
    """Node 1 (logic): Enrich lead from HubSpot."""
    hs = _get_hubspot()
    contact_id = state.get("contact_id", "")
    if contact_id:
        state["enriched_data"] = hs.get_contact(contact_id)
    return state


def _score_lead(state: RevenueOpsState) -> RevenueOpsState:
    """Node 2 (LLM): Score lead using Claude — replaces CrewAI crew."""
    try:
        prompt = load_prompt("config/prompts/sales/s1_lead_qualification.md")
    except FileNotFoundError:
        prompt = "You are a lead qualification specialist."

    lead_data = state.get("enriched_data", {})
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Score this lead and return ONLY valid JSON:\n\n"
            f"Lead data: {json.dumps(lead_data)}\n\n"
            f"Return: {{\"fit_score\": 0-100, \"intent_score\": 0-100, "
            f"\"urgency_score\": 0-100, \"reasoning\": \"...\", "
            f"\"route\": \"sales|nurture|education|disqualify\"}}"
        ),
        model="claude-sonnet-4-5-20250929",
        temperature=0.3,
    )

    try:
        score = json.loads(response.content)
        state["score"] = score
    except (json.JSONDecodeError, TypeError):
        state["score"] = {
            "fit_score": 0,
            "intent_score": 0,
            "urgency_score": 0,
            "reasoning": f"Failed to parse output: {response.content[:200]}",
            "route": "education",
        }
    return state


def _route_lead(state: RevenueOpsState) -> RevenueOpsState:
    """Node 3 (logic): Route based on composite score."""
    score = state.get("score") or {}
    composite = (
        0.4 * score.get("fit_score", 0)
        + 0.35 * score.get("intent_score", 0)
        + 0.25 * score.get("urgency_score", 0)
    )

    if score.get("fit_score", 0) < 20:
        state["route"] = "disqualify"
    elif composite >= 80:
        state["route"] = "sales"
    elif composite >= 50:
        state["route"] = "nurture"
    else:
        state["route"] = "education"
    return state


def _update_crm(state: RevenueOpsState) -> RevenueOpsState:
    """Node 4 (logic): Update HubSpot with scores and route."""
    hs = _get_hubspot()
    contact_id = state.get("contact_id", "")
    score = state.get("score") or {}
    route = state.get("route", "")

    if contact_id:
        hs.update_contact(contact_id, {
            "hs_lead_status": route.upper(),
            "lead_score": str(int(
                0.4 * score.get("fit_score", 0)
                + 0.35 * score.get("intent_score", 0)
                + 0.25 * score.get("urgency_score", 0)
            )),
        })
    state["crm_updated"] = True
    return state


def create_lead_qual_graph(checkpointer=None):
    """Create the Lead Qualification LangGraph workflow."""
    workflow = StateGraph(RevenueOpsState)

    workflow.add_node("enrich", _enrich_lead)
    workflow.add_node("score", _score_lead)
    workflow.add_node("route", _route_lead)
    workflow.add_node("update_crm", _update_crm)

    workflow.set_entry_point("enrich")
    workflow.add_edge("enrich", "score")
    workflow.add_edge("score", "route")
    workflow.add_edge("route", "update_crm")
    workflow.add_edge("update_crm", END)

    return workflow.compile(checkpointer=checkpointer)
