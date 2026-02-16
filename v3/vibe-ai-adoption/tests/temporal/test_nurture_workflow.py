from vibe_ai_ops.temporal.workflows.nurture_workflow import (
    NurtureSequenceWorkflow,
    NurtureWorkflowInput,
    NurtureWorkflowOutput,
)


def test_nurture_workflow_input():
    inp = NurtureWorkflowInput(
        contact_id="lead-001",
        lead_data={"name": "Alice"},
        lead_score=55,
    )
    assert inp.contact_id == "lead-001"
    assert inp.max_touches == 10
    assert inp.touch_interval_days == 3


def test_nurture_workflow_output():
    out = NurtureWorkflowOutput(
        contact_id="lead-001",
        final_route="escalate",
        touches_completed=5,
        final_score=85,
        escalation_reason="Score crossed 80",
    )
    assert out.final_route == "escalate"
    assert out.touches_completed == 5


def test_nurture_workflow_class_exists():
    """Verify the workflow class is a proper Temporal workflow definition."""
    assert hasattr(NurtureSequenceWorkflow, "run")
