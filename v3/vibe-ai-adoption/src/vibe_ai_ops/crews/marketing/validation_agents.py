from __future__ import annotations

from crewai import Crew

from vibe_ai_ops.crews.base import create_validation_crew
from vibe_ai_ops.shared.models import AgentConfig


def create_m1_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """M1 Segment Research — single agent validation crew."""
    return create_validation_crew(
        config=config,
        role="Market Research Specialist",
        goal="Generate comprehensive micro-segment buyer profiles through deep market research",
        backstory=system_prompt,
        task_description=(
            "Research the {segment} micro-segment. Produce a detailed profile covering: "
            "firmographics, pain points (ranked by severity), language patterns, "
            "channel preferences, competitive landscape, buying triggers, "
            "and 3-5 messaging hypotheses."
        ),
        expected_output="Detailed segment profile JSON with all sections populated",
    )


def create_m2_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """M2 Message Testing — single agent validation crew."""
    return create_validation_crew(
        config=config,
        role="Message Testing Specialist",
        goal="Generate and rank messaging variants for each segment and channel",
        backstory=system_prompt,
        task_description=(
            "Given segment profile and messaging hypotheses, generate 10 messaging "
            "variants with headlines, value props, and CTAs. Adapt for email, LinkedIn, "
            "ads, landing pages, and social. Score each variant by predicted performance."
        ),
        expected_output="JSON with ranked messaging variants per channel",
    )


def create_m4_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """M4 Content Repurposing — single agent validation crew."""
    return create_validation_crew(
        config=config,
        role="Content Repurposing Specialist",
        goal="Convert a single content piece into 10 format variants for different channels",
        backstory=system_prompt,
        task_description=(
            "Take this content piece and create 10 format variants: email nurture, "
            "5 LinkedIn posts, Twitter thread, video script, podcast talking points, "
            "slide deck outline, infographic outline, sales one-pager, internal enablement doc, "
            "and community post. Each must stand alone."
        ),
        expected_output="JSON array with 10 format variants, each with content and CTA",
    )


def create_m5_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """M5 Distribution — single agent validation crew."""
    return create_validation_crew(
        config=config,
        role="Distribution Specialist",
        goal="Plan and optimize content distribution across channels for each segment",
        backstory=system_prompt,
        task_description=(
            "Given content assets and segment channel preferences, create a distribution plan. "
            "Include: channel selection, scheduling, budget allocation, and expected metrics. "
            "Optimize for highest-ROI channels."
        ),
        expected_output="JSON distribution plan with channels, schedules, budgets, and expected metrics",
    )


def create_m6_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """M6 Journey Optimization — single agent validation crew."""
    return create_validation_crew(
        config=config,
        role="Journey Optimization Specialist",
        goal="Analyze full-funnel performance and generate optimization decisions",
        backstory=system_prompt,
        task_description=(
            "Analyze funnel data across all segments: impression → click → lead → MQL → SQL → deal → won. "
            "Benchmark segments, identify top/bottom performers. Generate kill/double-down/test decisions. "
            "Produce feedback for M1 (segment updates), M2 (messaging hypotheses), and M5 (budget shifts)."
        ),
        expected_output="JSON weekly optimization report with actions, feedback, and KPIs",
    )


# Registry for easy lookup by agent ID
MARKETING_CREW_REGISTRY = {
    "m1": create_m1_crew,
    "m2": create_m2_crew,
    "m4": create_m4_crew,
    "m5": create_m5_crew,
    "m6": create_m6_crew,
}
