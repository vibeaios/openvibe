"""Tests for role, task, deliverable commands."""

import pytest
from typer.testing import CliRunner
from openvibe_cli.main import app

runner = CliRunner()


# ── role ──────────────────────────────────────────────────────

def test_role_list(httpx_mock):
    httpx_mock.add_response(json=[
        {"id": "cro", "domains": ["revenue"]},
    ])
    result = runner.invoke(app, ["role", "list", "--workspace", "vibe-team"])
    assert result.exit_code == 0
    assert "cro" in result.output


def test_role_list_empty(httpx_mock):
    httpx_mock.add_response(json=[])
    result = runner.invoke(app, ["role", "list", "--workspace", "vibe-team"])
    assert result.exit_code == 0
    assert "No roles" in result.output


# ── task ──────────────────────────────────────────────────────

def test_task_list_empty(httpx_mock):
    httpx_mock.add_response(json=[])
    result = runner.invoke(app, ["task", "list", "--workspace", "vibe-team"])
    assert result.exit_code == 0
    assert "No pending" in result.output


def test_task_approve(httpx_mock):
    httpx_mock.add_response(json={}, status_code=200)
    result = runner.invoke(app, ["task", "approve", "req-123"])
    assert result.exit_code == 0
    assert "req-123" in result.output


def test_task_reject(httpx_mock):
    httpx_mock.add_response(json={}, status_code=200)
    result = runner.invoke(app, ["task", "reject", "req-456", "--reason", "too risky"])
    assert result.exit_code == 0
    assert "req-456" in result.output


# ── deliverable ───────────────────────────────────────────────

def test_deliverable_list_empty(httpx_mock):
    httpx_mock.add_response(json=[])
    result = runner.invoke(app, ["deliverable", "list", "--workspace", "vibe-team"])
    assert result.exit_code == 0
    assert "No deliverables" in result.output


def test_deliverable_ack(httpx_mock):
    httpx_mock.add_response(json={}, status_code=200)
    result = runner.invoke(app, ["deliverable", "ack", "del-789"])
    assert result.exit_code == 0
    assert "del-789" in result.output
