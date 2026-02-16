import json
from unittest.mock import patch

from vibe_ai_ops.graphs.marketing.content_pipeline import (
    create_content_pipeline_graph,
    ContentPipelineState,
)

MOCK_SEGMENT_PROFILE = json.dumps({
    "segment": "enterprise-fintech",
    "pain_points": ["meeting overload", "context loss"],
    "messaging_hypotheses": [
        "Vibe eliminates 80% of meeting prep time",
        "AI-powered meeting intelligence for fintech teams",
    ],
})

MOCK_CONTENT = json.dumps({
    "content": "# How Fintech Teams Save 80% on Meeting Prep\n\nFull blog post...",
    "quality_score": 85,
    "quality_notes": "Strong data-driven narrative",
})

MOCK_VARIANTS = json.dumps([
    {"format": "linkedin_post", "content": "Did you know fintech teams waste..."},
    {"format": "email_nurture", "content": "Subject: Your meetings are costing you..."},
    {"format": "twitter_thread", "content": "Thread: 5 ways AI changes meetings..."},
])


def test_content_pipeline_state_initial():
    state = ContentPipelineState(
        segment_id="enterprise-fintech",
        content_type="blog_post",
    )
    assert state["segment_id"] == "enterprise-fintech"
    assert state.get("pipeline_status") is None


def test_content_pipeline_graph_compiles():
    graph = create_content_pipeline_graph()
    assert graph is not None


@patch("vibe_ai_ops.graphs.marketing.content_pipeline.m4_kickoff", return_value=MOCK_VARIANTS)
@patch("vibe_ai_ops.graphs.marketing.content_pipeline.m3_kickoff", return_value=MOCK_CONTENT)
@patch("vibe_ai_ops.graphs.marketing.content_pipeline.m1_kickoff", return_value=MOCK_SEGMENT_PROFILE)
def test_content_pipeline_runs_full(mock_m1, mock_m3, mock_m4):
    graph = create_content_pipeline_graph()
    result = graph.invoke({
        "segment_id": "enterprise-fintech",
        "content_type": "blog_post",
    })

    # M1 ran
    assert mock_m1.called
    assert result["winning_message"] == "Vibe eliminates 80% of meeting prep time"
    assert len(result["messaging_hypotheses"]) == 2

    # M3 ran
    assert mock_m3.called
    assert result["quality_score"] == 85
    assert "Fintech" in result["final_content"]

    # M4 ran
    assert mock_m4.called
    assert len(result["repurposed_variants"]) == 3
    assert result["pipeline_status"] == "complete"


@patch("vibe_ai_ops.graphs.marketing.content_pipeline.m4_kickoff", return_value="not json")
@patch("vibe_ai_ops.graphs.marketing.content_pipeline.m3_kickoff", return_value="not json")
@patch("vibe_ai_ops.graphs.marketing.content_pipeline.m1_kickoff", return_value="not json")
def test_content_pipeline_handles_bad_json(mock_m1, mock_m3, mock_m4):
    """Pipeline degrades gracefully when crew output isn't valid JSON."""
    graph = create_content_pipeline_graph()
    result = graph.invoke({
        "segment_id": "enterprise-fintech",
        "content_type": "blog_post",
    })

    # M1 fallback
    assert result["segment_profile"] == {"raw": "not json"}
    assert result["messaging_hypotheses"] == []
    assert result["winning_message"] == ""

    # M3 fallback
    assert result["final_content"] == "not json"
    assert result["quality_score"] == 0

    # M4 fallback
    assert len(result["repurposed_variants"]) == 1
    assert result["pipeline_status"] == "complete"
