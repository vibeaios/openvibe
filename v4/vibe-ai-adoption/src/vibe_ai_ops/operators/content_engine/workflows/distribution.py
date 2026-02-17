"""Distribution workflow — select_channels → schedule_posts → report.

3 nodes: 2 logic (select_channels, schedule_posts) + 1 LLM (report).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from langgraph.graph import END, StateGraph

from vibe_ai_ops.operators.base import call_claude
from vibe_ai_ops.operators.content_engine.state import ContentEngineState
from vibe_ai_ops.shared.config import load_prompt


def _select_channels(state: ContentEngineState) -> ContentEngineState:
    """Node 1 (logic): Select distribution channels based on content formats."""
    channels = state.get("channels", [])
    adapted = state.get("adapted_content", {})

    if not channels:
        # Auto-select channels from available adapted content
        format_to_channel = {
            "social_post": "linkedin",
            "email_snippet": "email",
            "blog_summary": "blog",
            "newsletter_section": "newsletter",
        }
        channels = []
        for fmt in adapted:
            channel = format_to_channel.get(fmt, fmt)
            if channel not in channels:
                channels.append(channel)
        if not channels:
            channels = ["linkedin", "email"]
        state["channels"] = channels

    return state


def _schedule_posts(state: ContentEngineState) -> ContentEngineState:
    """Node 2 (logic): Create a posting schedule for selected channels."""
    channels = state.get("channels", [])
    adapted = state.get("adapted_content", {})

    now = datetime.now(tz=timezone.utc)
    schedule = []
    for i, channel in enumerate(channels):
        # Stagger posts across channels
        post_time = now + timedelta(hours=i * 4 + 8)
        # Find matching content
        content_key = next(
            (k for k in adapted if channel in k or k in channel), None
        )
        schedule.append({
            "channel": channel,
            "scheduled_at": post_time.isoformat(),
            "content_key": content_key,
            "status": "scheduled",
        })
    state["schedule"] = schedule
    return state


def _report(state: ContentEngineState) -> ContentEngineState:
    """Node 3 (LLM): Generate distribution report summary."""
    try:
        prompt = load_prompt("config/prompts/marketing/m5_distribution.md")
    except FileNotFoundError:
        prompt = (
            "You create concise distribution reports. Summarize the plan "
            "with channel, timing, and expected impact."
        )

    schedule = state.get("schedule", [])
    channels = state.get("channels", [])
    response = call_claude(
        system_prompt=prompt,
        user_message=(
            f"Create a distribution report:\n\n"
            f"Channels: {', '.join(channels)}\n"
            f"Schedule: {json.dumps(schedule, default=str)}\n\n"
            f"Include: summary, per-channel timing, and next steps."
        ),
        model="claude-haiku-4-5-20251001",
    )
    state["distribution_report"] = response.content
    return state


def create_distribution_graph(checkpointer=None):
    """Create the Distribution LangGraph workflow."""
    workflow = StateGraph(ContentEngineState)

    workflow.add_node("select_channels", _select_channels)
    workflow.add_node("schedule_posts", _schedule_posts)
    workflow.add_node("report", _report)

    workflow.set_entry_point("select_channels")
    workflow.add_edge("select_channels", "schedule_posts")
    workflow.add_edge("schedule_posts", "report")
    workflow.add_edge("report", END)

    return workflow.compile(checkpointer=checkpointer)
