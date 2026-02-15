import os
import tempfile

from vibe_ai_ops.shared.logger import RunLogger
from vibe_ai_ops.shared.models import AgentRun


def test_logger_creates_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        logger = RunLogger(db_path)
        assert os.path.exists(db_path)
        logger.close()


def test_logger_logs_and_retrieves_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        logger = RunLogger(db_path)

        run = AgentRun(
            agent_id="m3",
            status="success",
            input_summary="Generate blog for fintech",
            output_summary="1200 words on AI in fintech",
            tokens_in=500,
            tokens_out=2000,
            cost_usd=0.03,
            duration_seconds=4.5,
        )
        logger.log_run(run)

        runs = logger.get_runs("m3", limit=10)
        assert len(runs) == 1
        assert runs[0]["agent_id"] == "m3"
        assert runs[0]["status"] == "success"
        logger.close()


def test_logger_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        logger = RunLogger(db_path)

        for i in range(5):
            logger.log_run(AgentRun(
                agent_id="m3",
                status="success" if i < 4 else "error",
                cost_usd=0.03,
                duration_seconds=4.0,
            ))

        stats = logger.get_agent_stats("m3")
        assert stats["total_runs"] == 5
        assert stats["success_count"] == 4
        assert stats["error_count"] == 1
        assert stats["total_cost_usd"] == 0.15
        logger.close()
