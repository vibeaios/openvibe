"""vibe role commands."""

import json
import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage roles")
console = Console()


def _base(ctx: typer.Context) -> str:
    """Return base URL including tenant prefix."""
    obj = ctx.obj or {}
    host = obj.get("host", "http://localhost:8000")
    tenant = obj.get("tenant", "vibe-inc")
    return f"{host}/tenants/{tenant}"


@app.command("list")
def list_roles(
    ctx: typer.Context,
    workspace: str = typer.Option(..., "--workspace", help="Workspace ID"),
) -> None:
    """List roles in a workspace."""
    base = _base(ctx)
    resp = httpx.get(f"{base}/workspaces/{workspace}/roles")
    resp.raise_for_status()
    data = resp.json()
    if not data:
        console.print("No roles found.")
        return
    table = Table("ID", "Domains")
    for r in data:
        table.add_row(r.get("id", ""), ", ".join(r.get("domains", [])))
    console.print(table)


@app.command("spawn")
def spawn_role(
    ctx: typer.Context,
    template: str = typer.Argument(..., help="Template ID"),
    workspace: str = typer.Option(..., "--workspace", help="Workspace ID"),
    params: str = typer.Option("{}", "--params", help="JSON params for template"),
) -> None:
    """Spawn a new role from a template."""
    base = _base(ctx)
    resp = httpx.post(
        f"{base}/workspaces/{workspace}/roles/spawn",
        json={"template": template, "params": json.loads(params)},
    )
    resp.raise_for_status()
    result = resp.json()
    console.print(f"[green]Spawned role '{result.get('role_id')}'[/green]")


@app.command("inspect")
def inspect_role(
    ctx: typer.Context,
    role_id: str = typer.Argument(..., help="Role ID"),
) -> None:
    """Inspect a role."""
    base = _base(ctx)
    resp = httpx.get(f"{base}/roles/{role_id}")
    resp.raise_for_status()
    console.print_json(data=resp.json())
