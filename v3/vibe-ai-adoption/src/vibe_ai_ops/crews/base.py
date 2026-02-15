from __future__ import annotations

from crewai import Agent, Crew, Task, Process

from vibe_ai_ops.shared.models import AgentConfig


def create_crew_agent(
    config: AgentConfig,
    role: str,
    goal: str,
    backstory: str,
    tools: list | None = None,
) -> Agent:
    """Create a single CrewAI Agent from config."""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=f"anthropic/{config.model}",
        tools=tools or [],
        verbose=False,
    )


def create_validation_crew(
    config: AgentConfig,
    role: str,
    goal: str,
    backstory: str,
    task_description: str,
    expected_output: str,
    tools: list | None = None,
) -> Crew:
    """Create a single-agent, single-task Crew for validation-tier agents."""
    agent = create_crew_agent(config, role, goal, backstory, tools)

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
