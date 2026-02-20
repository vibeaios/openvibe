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
        console.print("[bold]Dry run:[/bold]")
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
