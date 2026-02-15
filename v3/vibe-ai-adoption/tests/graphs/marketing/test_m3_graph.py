from vibe_ai_ops.graphs.marketing.m3_content_generation import (
    create_content_gen_graph,
    ContentGenState,
)


def test_content_gen_state_initial():
    state = ContentGenState(
        segment_id="enterprise-fintech",
        content_type="blog_post",
        winning_message="Vibe eliminates 80% of meeting prep time",
    )
    assert state["segment_id"] == "enterprise-fintech"
    assert state.get("final_content") is None


def test_content_gen_graph_compiles():
    graph = create_content_gen_graph()
    assert graph is not None


def test_content_gen_graph_runs_all_nodes():
    graph = create_content_gen_graph()
    result = graph.invoke({
        "segment_id": "enterprise-fintech",
        "content_type": "blog_post",
        "winning_message": "Vibe eliminates 80% of meeting prep time",
    })
    # All nodes executed — quality_score set in polish step
    assert "quality_score" in result
