"""vibe task commands (approval queue)."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage approval tasks")
console = Console()


def _base(ctx: typer.Context) -> str:
    """Return base URL including tenant prefix."""
    obj = ctx.obj or {}
    host = obj.get("host", "http://localhost:8000")
    tenant = obj.get("tenant", "vibe-inc")
    return f"{host}/tenants/{tenant}"


@app.command("list")
def list_tasks(
    ctx: typer.Context,
    workspace: str = typer.Option(..., "--workspace", help="Workspace ID"),
) -> None:
    """List pending approval requests."""
    base = _base(ctx)
    resp = httpx.get(f"{base}/workspaces/{workspace}/approvals")
    resp.raise_for_status()
    data = resp.json()
    if not data:
        console.print("No pending approvals.")
        return
    table = Table("ID", "Role", "Action", "Status")
    for item in data:
        table.add_row(item.get("id", ""), item.get("role_id", ""),
                      item.get("action", ""), item.get("status", ""))
    console.print(table)


@app.command("approve")
def approve_task(
    ctx: typer.Context,
    request_id: str = typer.Argument(..., help="Approval request ID"),
) -> None:
    """Approve a pending request."""
    base = _base(ctx)
    resp = httpx.post(f"{base}/approvals/{request_id}/approve")
    resp.raise_for_status()
    console.print(f"[green]Approved request '{request_id}'[/green]")


@app.command("reject")
def reject_task(
    ctx: typer.Context,
    request_id: str = typer.Argument(..., help="Approval request ID"),
    reason: str = typer.Option("", "--reason", help="Rejection reason"),
) -> None:
    """Reject a pending request."""
    base = _base(ctx)
    resp = httpx.post(f"{base}/approvals/{request_id}/reject",
                      json={"reason": reason})
    resp.raise_for_status()
    console.print(f"[yellow]Rejected request '{request_id}'[/yellow]")
