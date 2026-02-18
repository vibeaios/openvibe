"""OpenVibe CLI entry point."""

import typer

from openvibe_cli.commands import workspace, role, task, deliverable

app = typer.Typer(name="vibe", help="OpenVibe CLI — manage workspaces, roles, tasks, deliverables")
app.add_typer(workspace.app, name="workspace")
app.add_typer(role.app, name="role")
app.add_typer(task.app, name="task")
app.add_typer(deliverable.app, name="deliverable")


@app.callback()
def main(
    ctx: typer.Context,
    host: str = typer.Option(
        "http://localhost:8000",
        "--host",
        help="Platform host URL",
        envvar="VIBE_HOST",
    ),
    tenant: str = typer.Option(
        "vibe-inc",
        "--tenant",
        "-t",
        help="Tenant ID",
        envvar="VIBE_TENANT",
    ),
) -> None:
    """OpenVibe CLI — manage workspaces, roles, tasks, deliverables."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["tenant"] = tenant
