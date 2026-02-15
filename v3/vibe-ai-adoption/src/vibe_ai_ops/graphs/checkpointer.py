from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None


def create_checkpointer(conn_string: str | None = None):
    """Create a LangGraph checkpointer — Postgres in prod, memory in dev/test."""
    if conn_string and PostgresSaver is not None:
        return PostgresSaver.from_conn_string(conn_string)
    return MemorySaver()
