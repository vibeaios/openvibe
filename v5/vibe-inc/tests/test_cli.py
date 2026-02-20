"""Tests for vibe-inc CLI."""
from typer.testing import CliRunner
from openvibe_sdk.llm import LLMResponse


class FakeLLM:
    def call(self, *, system, messages, **kwargs):
        return LLMResponse(content="ok")


runner = CliRunner()


def test_list_shows_roles(monkeypatch):
    """'list' command should show all roles and their operators."""
    monkeypatch.setattr(
        "vibe_inc.cli._create_runtime",
        lambda: __import__("vibe_inc.main", fromlist=["create_runtime"]).create_runtime(llm=FakeLLM()),
    )
    from vibe_inc.cli import app

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "d2c_growth" in result.stdout
    assert "d2c_strategy" in result.stdout
    assert "data_ops" in result.stdout
    assert "meta_ad_ops" in result.stdout


def test_list_shows_workflows(monkeypatch):
    """'list' command should show workflow IDs."""
    monkeypatch.setattr(
        "vibe_inc.cli._create_runtime",
        lambda: __import__("vibe_inc.main", fromlist=["create_runtime"]).create_runtime(llm=FakeLLM()),
    )
    from vibe_inc.cli import app

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "campaign_create" in result.stdout
    assert "weekly_report" in result.stdout
