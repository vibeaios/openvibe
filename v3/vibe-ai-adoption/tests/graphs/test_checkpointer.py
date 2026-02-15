from unittest.mock import patch, MagicMock

from vibe_ai_ops.graphs.checkpointer import create_checkpointer


@patch("vibe_ai_ops.graphs.checkpointer.PostgresSaver")
def test_create_checkpointer_with_postgres(mock_saver):
    mock_saver.from_conn_string.return_value = MagicMock()

    cp = create_checkpointer(conn_string="postgresql://test:test@localhost/test")
    assert cp is not None
    mock_saver.from_conn_string.assert_called_once()


def test_create_checkpointer_falls_back_to_memory():
    cp = create_checkpointer(conn_string=None)
    assert cp is not None  # Returns MemorySaver fallback
