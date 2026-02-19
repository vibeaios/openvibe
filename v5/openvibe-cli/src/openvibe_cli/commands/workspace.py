"""vibe workspace commands."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage workspaces")
console = Console()


def _base(ctx: typer.Context) -> str:
    """Return base URL including tenant prefix."""
    obj = ctx.obj or {}
    host = obj.get("host", "http://localhost:8000")
    tenant = obj.get("tenant", "vibe-inc")
    return f"{host}/tenants/{tenant}"


@app.command("list")
def list_workspaces(ctx: typer.Context) -> None:
    """List all workspaces."""
    base = _base(ctx)
    resp = httpx.get(f"{base}/workspaces")
    resp.raise_for_status()
    data = resp.json()
    if not data:
        console.print("No workspaces found.")
        return
    table = Table("ID", "Name", "Owner")
    for ws in data:
        table.add_row(ws.get("id", ""), ws.get("name", ""), ws.get("owner", ""))
    console.print(table)


@app.command("create")
def create_workspace(
    ctx: typer.Context,
    workspace_id: str = typer.Argument(..., help="Workspace ID"),
    name: str = typer.Option(..., "--name", help="Display name"),
    owner: str = typer.Option(..., "--owner", help="Owner ID"),
) -> None:
    """Create a new workspace."""
    base = _base(ctx)
    resp = httpx.post(f"{base}/workspaces",
                      json={"id": workspace_id, "name": name, "owner": owner})
    resp.raise_for_status()
    console.print(f"[green]Created workspace '{workspace_id}'[/green]")


@app.command("delete")
def delete_workspace(
    ctx: typer.Context,
    workspace_id: str = typer.Argument(..., help="Workspace ID"),
) -> None:
    """Delete a workspace."""
    base = _base(ctx)
    resp = httpx.delete(f"{base}/workspaces/{workspace_id}")
    resp.raise_for_status()
    console.print(f"[yellow]Deleted workspace '{workspace_id}'[/yellow]")
