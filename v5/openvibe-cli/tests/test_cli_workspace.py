"""Tests for `vibe workspace` commands."""

import pytest
from typer.testing import CliRunner
from openvibe_cli.main import app

runner = CliRunner()


def test_workspace_list_empty(httpx_mock):
    httpx_mock.add_response(url="http://localhost:8000/tenants/vibe-inc/workspaces", json=[])
    result = runner.invoke(app, ["workspace", "list"])
    assert result.exit_code == 0
    assert "No workspaces" in result.output


def test_workspace_list_with_data(httpx_mock):
    httpx_mock.add_response(
        url="http://localhost:8000/tenants/vibe-inc/workspaces",
        json=[{"id": "vibe-team", "name": "Vibe Team", "owner": "charles"}],
    )
    result = runner.invoke(app, ["workspace", "list"])
    assert result.exit_code == 0
    assert "vibe-team" in result.output


def test_workspace_create(httpx_mock):
    httpx_mock.add_response(url="http://localhost:8000/tenants/vibe-inc/workspaces", json={"id": "new-ws"})
    result = runner.invoke(app, [
        "workspace", "create", "new-ws",
        "--name", "New WS", "--owner", "charles",
    ])
    assert result.exit_code == 0
    assert "new-ws" in result.output


def test_workspace_delete(httpx_mock):
    httpx_mock.add_response(url="http://localhost:8000/tenants/vibe-inc/workspaces/old-ws", json={})
    result = runner.invoke(app, ["workspace", "delete", "old-ws"])
    assert result.exit_code == 0
    assert "old-ws" in result.output


def test_workspace_list_with_tenant_flag(httpx_mock):
    """Verify --tenant flag changes the URL prefix."""
    httpx_mock.add_response(url="http://localhost:8000/tenants/astrocrest/workspaces", json=[])
    result = runner.invoke(app, ["--tenant", "astrocrest", "workspace", "list"])
    assert result.exit_code == 0
