from __future__ import annotations

from crewai import Agent, Crew, Task, Process

from vibe_ai_ops.crews.base import create_crew_agent
from vibe_ai_ops.shared.models import AgentConfig


def create_content_gen_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """Create the M3 Content Generation crew — 3 agents, 3 sequential tasks."""
    researcher = create_crew_agent(
        config=config,
        role="Content Researcher",
        goal="Gather data, statistics, and examples relevant to the content topic",
        backstory=(
            "You are a meticulous researcher who finds compelling data points, "
            "real-world examples, and statistics to support content creation. "
            "You focus on accuracy and relevance to the target segment."
        ),
    )

    writer = create_crew_agent(
        config=config,
        role="Content Writer",
        goal="Produce high-quality content using segment-specific tone and winning messages",
        backstory=(
            "You are a skilled B2B content writer who creates engaging, "
            "SEO-optimized content. You match the language patterns of the target "
            "segment and weave in data from research."
        ),
    )

    editor = create_crew_agent(
        config=config,
        role="Content Editor",
        goal="Review content for quality, brand voice, SEO, and accuracy",
        backstory=(
            "You are a demanding editor with high standards. You ensure content "
            "is clear, accurate, on-brand, and optimized for search. You cut "
            "fluff and strengthen weak arguments."
        ),
    )

    research_task = Task(
        description=(
            "Research the topic for a {content_type} targeting the {segment} segment.\n\n"
            "Winning message: {winning_message}\n\n"
            "Find: relevant statistics, case studies, expert quotes, competitive examples, "
            "and data points that support this message. Return structured research notes."
        ),
        expected_output="Structured research notes with data points, statistics, and examples",
        agent=researcher,
    )

    write_task = Task(
        description=(
            "Write a {content_type} for the {segment} segment using the research provided.\n\n"
            "Winning message: {winning_message}\n"
            "System prompt: " + system_prompt[:500] + "\n\n"
            "Requirements: segment-specific tone, SEO keywords integrated naturally, "
            "clear structure (headline → hook → body → CTA), evidence-based arguments."
        ),
        expected_output="Complete content piece with title, body, and metadata",
        agent=writer,
    )

    edit_task = Task(
        description=(
            "Review and improve this {content_type} for the {segment} segment.\n\n"
            "Check: brand voice consistency, factual accuracy, SEO optimization, "
            "readability, argument strength, CTA effectiveness.\n\n"
            "Return the final polished version with a quality score (0-100) and notes."
        ),
        expected_output="Final polished content with quality_score and quality_notes",
        agent=editor,
    )

    return Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, write_task, edit_task],
        process=Process.sequential,
        verbose=False,
    )
