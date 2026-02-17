from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from vibe_ai_ops.shared.models import AgentRun


class RunLogger:
    def __init__(self, db_path: str = "data/runs.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_summary TEXT DEFAULT '',
                output_summary TEXT DEFAULT '',
                error TEXT,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                duration_seconds REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_id
            ON agent_runs(agent_id)
        """)
        self._conn.commit()

    def log_run(self, run: AgentRun):
        self._conn.execute(
            """INSERT INTO agent_runs
               (agent_id, status, input_summary, output_summary, error,
                tokens_in, tokens_out, cost_usd, duration_seconds, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.agent_id, run.status, run.input_summary, run.output_summary,
                run.error, run.tokens_in, run.tokens_out, run.cost_usd,
                run.duration_seconds, run.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_runs(self, agent_id: str, limit: int = 20) -> list[dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM agent_runs WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            """SELECT
                 COUNT(*) as total_runs,
                 SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                 SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                 SUM(cost_usd) as total_cost_usd,
                 AVG(duration_seconds) as avg_duration
               FROM agent_runs WHERE agent_id = ?""",
            (agent_id,),
        ).fetchone()
        return dict(row)

    def close(self):
        self._conn.close()
