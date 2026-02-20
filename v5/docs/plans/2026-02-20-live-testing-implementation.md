# Live Testing Infrastructure — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add live API smoke tests, real LLM agent loop tests, and a CLI runner to vibe-inc so workflows can be validated against real services.

**Architecture:** Three layers — (1) `@pytest.mark.live` tool tests that verify API credentials and read operations work, (2) `@pytest.mark.live_agent` tests that run a full operator node with real Claude + real tools, (3) a `python -m vibe_inc.cli` CLI with `list` and `run` commands for interactive workflow execution.

**Tech Stack:** pytest markers, AnthropicProvider (openvibe-sdk), typer + rich (CLI), python-dotenv (.env loading)

**Design doc:** `v5/docs/plans/2026-02-20-live-testing-design.md`

---

### Task 1: Add pytest markers to pyproject.toml

**Files:**
- Modify: `v5/vibe-inc/pyproject.toml`

**Step 1: Add markers config**

Add to existing `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
markers = [
    "live: requires real API credentials (skip with '-m not live')",
    "live_agent: requires ANTHROPIC_API_KEY + API credentials (skip with '-m not live_agent')",
]
```

**Step 2: Add typer + rich to dependencies**

Add `typer>=0.12` and `rich>=13.0` to the `dependencies` list (they're needed for the CLI in Task 5).

**Step 3: Verify existing tests still pass**

Run: `cd v5/vibe-inc && pytest tests/ -q`
Expected: `367 passed`

**Step 4: Commit**

```bash
git add v5/vibe-inc/pyproject.toml
git commit -m "chore(vibe-inc): add live test markers + CLI deps to pyproject.toml"
```

---

### Task 2: Create live tool smoke tests

**Files:**
- Create: `v5/vibe-inc/tests/test_live_tools.py`

**Step 1: Write test file**

```python
"""Live smoke tests — real API calls, read-only.

Run: pytest tests/test_live_tools.py -m live -v
Requires: API credentials in environment or .env file.
"""
import os

import pytest

live = pytest.mark.live


def _skip_unless_env(*keys):
    """Skip test if any required env var is missing."""
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Missing env: {', '.join(missing)}")


@live
def test_meta_ads_read_live():
    """meta_ads_read returns campaign data from the real Meta API."""
    _skip_unless_env("META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID")
    from vibe_inc.tools.ads.meta_ads import meta_ads_read

    result = meta_ads_read(level="campaign", date_range="last_7d")
    assert "rows" in result
    assert "level" in result
    assert result["level"] == "campaign"


@live
def test_google_ads_query_live():
    """google_ads_query returns campaign data from the real Google Ads API."""
    _skip_unless_env("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID")
    from vibe_inc.tools.ads.google_ads import google_ads_query

    result = google_ads_query(
        query="SELECT campaign.name, campaign.status FROM campaign LIMIT 5"
    )
    assert "rows" in result
    assert "query" in result


@live
def test_hubspot_contact_get_live():
    """hubspot_contact_get returns contact data from the real HubSpot API."""
    _skip_unless_env("HUBSPOT_API_KEY")
    from vibe_inc.tools.crm.hubspot import hubspot_contact_get

    # Use a known-safe lookup that returns empty or a real contact
    result = hubspot_contact_get(email="test-nonexistent@example.com")
    assert isinstance(result, dict)
    # Should return empty or a contact — either is fine, just no crash
```

**Step 2: Run without live marker (should collect 0)**

Run: `cd v5/vibe-inc && pytest tests/test_live_tools.py -v`
Expected: `3 passed` or `3 skipped` (tests run but skip due to missing env vars)

**Step 3: Run with live marker if credentials available**

Run: `cd v5/vibe-inc && pytest tests/test_live_tools.py -m live -v`
Expected: Tests run against real APIs (or skip if env vars not set)

**Step 4: Commit**

```bash
git add v5/vibe-inc/tests/test_live_tools.py
git commit -m "test(vibe-inc): add live API smoke tests — Meta, Google Ads, HubSpot"
```

---

### Task 3: Create live agent loop test

**Files:**
- Create: `v5/vibe-inc/tests/test_live_agent.py`

**Step 1: Write test file**

```python
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

    Validates the complete chain: soul injection → agent prompt → tool call →
    tool execution → agent response → state update.
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
    # Agent should produce non-trivial text (not just "ok")
    assert isinstance(result["report"], str)
    assert len(result["report"]) > 50
```

**Step 2: Verify test is collected but skips without credentials**

Run: `cd v5/vibe-inc && pytest tests/test_live_agent.py -v`
Expected: `1 skipped` (missing ANTHROPIC_API_KEY)

**Step 3: Commit**

```bash
git add v5/vibe-inc/tests/test_live_agent.py
git commit -m "test(vibe-inc): add live agent loop test — MetaAdOps weekly_report"
```

---

### Task 4: Create CLI entry point (`__main__.py`)

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/__main__.py`

**Step 1: Write entry point**

```python
"""Allow running vibe_inc as a module: python -m vibe_inc.cli"""
from vibe_inc.cli import app

app()
```

**Step 2: Verify it runs (will fail because cli.py doesn't exist yet — that's expected)**

Run: `cd v5/vibe-inc && python -m vibe_inc.cli --help 2>&1 || echo "Expected: cli.py not found yet"`
Expected: ImportError (cli.py not created yet)

**Step 3: Commit (just the entry point)**

```bash
git add v5/vibe-inc/src/vibe_inc/__main__.py
git commit -m "feat(vibe-inc): add __main__.py for python -m vibe_inc.cli"
```

---

### Task 5: Create CLI with `list` command

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/cli.py`
- Create: `v5/vibe-inc/tests/test_cli.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd v5/vibe-inc && pytest tests/test_cli.py -v`
Expected: FAIL (cli.py doesn't exist yet)

**Step 3: Write cli.py with `list` command**

```python
"""Vibe Inc CLI — run workflows locally against real APIs."""
import json
import os

import typer
from rich.console import Console
from rich.tree import Tree

app = typer.Typer(name="vibe-inc", help="Vibe Inc — run D2C marketing workflows")
console = Console()


def _create_runtime():
    """Create RoleRuntime with AnthropicProvider."""
    from openvibe_sdk.llm.anthropic import AnthropicProvider
    from vibe_inc.main import create_runtime

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Missing ANTHROPIC_API_KEY[/red]")
        raise typer.Exit(1)
    return create_runtime(llm=AnthropicProvider(api_key=api_key))


@app.command("list")
def list_workflows() -> None:
    """List all available roles, operators, and workflows."""
    from openvibe_sdk.llm import LLMResponse

    class _StubLLM:
        def call(self, **kw):
            return LLMResponse(content="")

    from vibe_inc.main import create_runtime

    runtime = create_runtime(llm=_StubLLM())

    tree = Tree("[bold]Vibe Inc Workflows[/bold]")
    for role in runtime.list_roles():
        role_branch = tree.add(f"[cyan]{role.role_id}[/cyan]")
        for op_id in role.list_operators():
            op_branch = role_branch.add(f"[green]{op_id}[/green]")
            wf_ids = runtime._workflow_factories.get(op_id, {})
            for wf_id in sorted(wf_ids):
                op_branch.add(wf_id)
    console.print(tree)


@app.command("run")
def run_workflow(
    role: str = typer.Option(..., "--role", "-r", help="Role ID (e.g. d2c_growth)"),
    operator: str = typer.Option(..., "--operator", "-o", help="Operator ID (e.g. meta_ad_ops)"),
    workflow: str = typer.Option(..., "--workflow", "-w", help="Workflow ID (e.g. weekly_report)"),
    input_data: str = typer.Option("{}", "--input", "-i", help="JSON input data"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show execution plan without running"),
) -> None:
    """Run a workflow with real LLM + real API tools."""
    parsed = json.loads(input_data)

    if dry_run:
        console.print(f"[bold]Dry run:[/bold]")
        console.print(f"  Role:     {role}")
        console.print(f"  Operator: {operator}")
        console.print(f"  Workflow: {workflow}")
        console.print(f"  Input:    {json.dumps(parsed, indent=2)}")
        console.print(f"\n  Would call: runtime.activate('{role}', '{operator}', '{workflow}', ...)")
        return

    runtime = _create_runtime()

    console.print(f"[bold]Running:[/bold] {role} / {operator} / {workflow}")
    console.print(f"[dim]Input: {json.dumps(parsed)}[/dim]\n")

    try:
        result = runtime.activate(
            role_id=role,
            operator_id=operator,
            workflow_id=workflow,
            input_data=parsed,
        )
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)

    console.print("[bold green]Result:[/bold green]")
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 200:
            console.print(f"\n[cyan]{key}:[/cyan]")
            console.print(value)
        else:
            console.print(f"  [cyan]{key}:[/cyan] {value}")
```

**Step 4: Run tests to verify they pass**

Run: `cd v5/vibe-inc && pytest tests/test_cli.py -v`
Expected: `2 passed`

**Step 5: Verify CLI runs from command line**

Run: `cd v5/vibe-inc && python -m vibe_inc.cli list`
Expected: Tree output showing all roles, operators, workflows

**Step 6: Verify dry-run**

Run: `cd v5/vibe-inc && python -m vibe_inc.cli run -r d2c_growth -o meta_ad_ops -w weekly_report --dry-run`
Expected: Prints execution plan without calling APIs

**Step 7: Commit**

```bash
git add v5/vibe-inc/src/vibe_inc/cli.py v5/vibe-inc/tests/test_cli.py
git commit -m "feat(vibe-inc): add CLI runner — list + run commands"
```

---

### Task 6: Run full suite + update .env.example + commit

**Step 1: Run full vibe-inc test suite**

Run: `cd v5/vibe-inc && pytest tests/ -v`
Expected: `~373 passed` (367 existing + 3 live skipped + 1 live_agent skipped + 2 CLI)

**Step 2: Update .env.example with all credentials**

Add to `v5/vibe-inc/.env.example`:
```
# Anthropic API (agent loop)
ANTHROPIC_API_KEY=

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=

# HubSpot API
HUBSPOT_API_KEY=
```

**Step 3: Commit**

```bash
git add v5/vibe-inc/.env.example
git commit -m "feat(vibe-inc): live testing infrastructure — 3 tool tests, 1 agent test, CLI runner"
```

---

## Verification

```bash
# All tests (mock + skipped live)
cd v5/vibe-inc && pytest tests/ -q

# Live tool tests only (needs credentials)
pytest tests/test_live_tools.py -m live -v

# Live agent test (needs ANTHROPIC_API_KEY + Meta credentials)
pytest tests/test_live_agent.py -m live_agent -v

# CLI list
python -m vibe_inc.cli list

# CLI dry-run
python -m vibe_inc.cli run -r d2c_growth -o meta_ad_ops -w weekly_report --dry-run

# CLI real run (needs all credentials)
python -m vibe_inc.cli run -r d2c_growth -o meta_ad_ops -w weekly_report -i '{"week": "current"}'
```
