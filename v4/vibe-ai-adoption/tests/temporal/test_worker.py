from vibe_ai_ops.temporal.worker import TASK_QUEUE


def test_task_queue_name():
    assert TASK_QUEUE == "vibe-ai-ops"
