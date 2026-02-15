from __future__ import annotations

from pydantic import BaseModel
from crewai import Crew, Task, Process

from vibe_ai_ops.crews.base import create_crew_agent
from vibe_ai_ops.shared.models import AgentConfig


class LeadScore(BaseModel):
    fit_score: int  # 0-100
    intent_score: int  # 0-100
    urgency_score: int  # 0-100
    reasoning: str
    route: str  # "sales" | "nurture" | "education" | "disqualify"

    @property
    def composite(self) -> float:
        return 0.4 * self.fit_score + 0.35 * self.intent_score + 0.25 * self.urgency_score


def create_lead_qual_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """Create the Lead Qualification crew — single agent, single task."""
    agent = create_crew_agent(
        config=config,
        role="Lead Qualification Specialist",
        goal="Score and route incoming leads based on fit, intent, and urgency",
        backstory=system_prompt,
    )

    task = Task(
        description=(
            "Score this lead. Evaluate:\n"
            "- Fit (0-100): Does this match our ICP?\n"
            "- Intent (0-100): Are there buying signals?\n"
            "- Urgency (0-100): Is there a trigger event?\n\n"
            "Route: 80+ → sales, 50-79 → nurture, <50 → education, ICP mismatch → disqualify\n\n"
            "Lead data: {lead_data}\n\n"
            "Return ONLY valid JSON with: fit_score, intent_score, urgency_score, reasoning, route"
        ),
        expected_output="JSON with fit_score, intent_score, urgency_score, reasoning, route",
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
