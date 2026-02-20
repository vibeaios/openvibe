"""Live agent loop tests — real Claude API + real tool APIs.

Run: pytest tests/test_live_agent.py -m live_agent -v
Requires: ANTHROPIC_API_KEY + tool-specific API credentials.
"""
import os

import pytest

live_agent = pytest.mark.live_agent


def _skip_unless_env(*keys):
    """Skip test if any required env var is missing."""
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Missing env: {', '.join(missing)}")


@live_agent
def test_meta_weekly_report_live():
    """Full agent loop: MetaAdOps.weekly_report with real Claude + real Meta API.

    Validates the complete chain: soul injection -> agent prompt -> tool call ->
    tool execution -> agent response -> state update.
    """
    _skip_unless_env(
        "ANTHROPIC_API_KEY",
        "META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID",
    )
    from openvibe_sdk.llm.anthropic import AnthropicProvider
    from vibe_inc.main import create_runtime

    llm = AnthropicProvider()
    runtime = create_runtime(llm=llm)
    result = runtime.activate(
        role_id="d2c_growth",
        operator_id="meta_ad_ops",
        workflow_id="weekly_report",
        input_data={"week": "current"},
    )

    assert "report" in result
    assert isinstance(result["report"], str)
    assert len(result["report"]) > 50
