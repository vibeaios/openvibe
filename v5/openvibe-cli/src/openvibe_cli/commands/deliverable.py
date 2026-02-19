"""vibe deliverable commands."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage deliverables")
console = Console()


def _base(ctx: typer.Context) -> str:
    """Return base URL including tenant prefix."""
    obj = ctx.obj or {}
    host = obj.get("host", "http://localhost:8000")
    tenant = obj.get("tenant", "vibe-inc")
    return f"{host}/tenants/{tenant}"


@app.command("list")
def list_deliverables(
    ctx: typer.Context,
    workspace: str = typer.Option(..., "--workspace", help="Workspace ID"),
    role: str = typer.Option("", "--role", help="Filter by role ID"),
) -> None:
    """List deliverables."""
    base = _base(ctx)
    params: dict[str, str] = {}
    if role:
        params["role_id"] = role
    resp = httpx.get(f"{base}/deliverables", params=params)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        console.print("No deliverables found.")
        return
    table = Table("ID", "Role", "Type", "Status")
    for d in data:
        table.add_row(d.get("id", ""), d.get("role_id", ""),
                      d.get("type", ""), d.get("status", ""))
    console.print(table)


@app.command("view")
def view_deliverable(
    ctx: typer.Context,
    deliverable_id: str = typer.Argument(..., help="Deliverable ID"),
) -> None:
    """View a deliverable's content."""
    base = _base(ctx)
    resp = httpx.get(f"{base}/deliverables/{deliverable_id}")
    resp.raise_for_status()
    data = resp.json()
    console.print(data.get("content", ""))


@app.command("ack")
def ack_deliverable(
    ctx: typer.Context,
    deliverable_id: str = typer.Argument(..., help="Deliverable ID"),
) -> None:
    """Acknowledge a deliverable."""
    base = _base(ctx)
    resp = httpx.post(f"{base}/deliverables/{deliverable_id}/acknowledge")
    resp.raise_for_status()
    console.print(f"[green]Acknowledged '{deliverable_id}'[/green]")
