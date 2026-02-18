"""Shared test fixtures for platform HTTP tests."""

import pytest
from fastapi.testclient import TestClient

from openvibe_platform.app import create_app


@pytest.fixture
def client():
    """TestClient with all services in-memory (no file I/O)."""
    return TestClient(create_app(data_dir=":memory:"))
