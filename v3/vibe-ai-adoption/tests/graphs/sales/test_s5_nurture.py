import json
from unittest.mock import patch

from vibe_ai_ops.graphs.sales.s5_nurture_sequence import (
    create_nurture_graph,
    NurtureState,
    STAGE_PROGRESSION,
)


MOCK_TOUCH_RESPONSE = json.dumps({
    "content": "Hi, here's an article about how fintech teams save time...",
    "channel": "email",
    "updated_score": 55,
})

MOCK_TOUCH_ESCALATE = json.dumps({
    "content": "Ready for a demo?",
    "channel": "email",
    "updated_score": 85,
})


def test_nurture_state_initial():
    state = NurtureState(contact_id="123", lead_score=50)
    assert state["contact_id"] == "123"
    assert state.get("route") is None


def test_nurture_graph_compiles():
    graph = create_nurture_graph()
    assert graph is not None


def test_stage_progression_order():
    assert STAGE_PROGRESSION == [
        "educational", "solution_aware", "product_aware", "decision_ready",
    ]


@patch("vibe_ai_ops.graphs.sales.s5_nurture_sequence.s5_kickoff", return_value=MOCK_TOUCH_RESPONSE)
def test_nurture_single_touch_continue(mock_s5):
    """Low-score lead: one touch, route=continue."""
    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "lead-001",
        "lead_data": {"name": "Alice", "company": "FinCorp"},
        "lead_score": 50,
    })

    assert mock_s5.called
    assert result["touches_completed"] == 1
    assert result["current_stage"] == "solution_aware"
    assert result["route"] == "continue"
    assert len(result["touch_history"]) == 1
    assert result["lead_score"] == 55  # updated by crew


@patch("vibe_ai_ops.graphs.sales.s5_nurture_sequence.s5_kickoff", return_value=MOCK_TOUCH_ESCALATE)
def test_nurture_escalates_on_high_score(mock_s5):
    """Lead score crosses 80 → escalate to sales."""
    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "lead-002",
        "lead_data": {"name": "Bob"},
        "lead_score": 75,
    })

    assert result["route"] == "escalate"
    assert result["lead_score"] == 85
    assert "ready for sales" in result["escalation_reason"]


@patch("vibe_ai_ops.graphs.sales.s5_nurture_sequence.s5_kickoff", return_value=MOCK_TOUCH_RESPONSE)
def test_nurture_completes_at_max_touches(mock_s5):
    """Max touches reached → complete."""
    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "lead-003",
        "lead_data": {"name": "Carol"},
        "lead_score": 40,
        "touches_completed": 9,
        "max_touches": 10,
        "touch_history": [{"touch_number": i} for i in range(1, 10)],
    })

    assert result["route"] == "complete"
    assert result["touches_completed"] == 10
    assert "Max touches" in result["escalation_reason"]


@patch("vibe_ai_ops.graphs.sales.s5_nurture_sequence.s5_kickoff", return_value="not json")
def test_nurture_handles_bad_json(mock_s5):
    """Graceful degradation when crew output isn't valid JSON."""
    graph = create_nurture_graph()
    result = graph.invoke({
        "contact_id": "lead-004",
        "lead_data": {},
        "lead_score": 30,
    })

    assert result["touch_content"] == "not json"
    assert result["touch_channel"] == "email"
    assert result["route"] == "continue"


def test_nurture_stage_assignment():
    """Stage is determined by score thresholds."""
    graph = create_nurture_graph()

    for score, expected_stage in [
        (10, "educational"),
        (39, "educational"),
        (40, "solution_aware"),
        (59, "solution_aware"),
        (60, "product_aware"),
        (79, "product_aware"),
        (80, "decision_ready"),
        (95, "decision_ready"),
    ]:
        with patch("vibe_ai_ops.graphs.sales.s5_nurture_sequence.s5_kickoff", return_value=MOCK_TOUCH_RESPONSE):
            result = graph.invoke({
                "contact_id": "test",
                "lead_data": {},
                "lead_score": score,
            })
            assert result["current_stage"] == expected_stage, (
                f"score={score}: expected {expected_stage}, got {result['current_stage']}"
            )
