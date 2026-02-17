"""CLI for Vibe AI Ops — operator-based interface."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from vibe_ai_ops.operators.base import OperatorRuntime


def _create_runtime(config_path: str = "config/operators.yaml") -> OperatorRuntime:
    """Create and load the operator runtime."""
    runtime = OperatorRuntime(config_path=config_path)
    runtime.load(enabled_only=False)
    return runtime


def list_operators(
    config_path: str = "config/operators.yaml",
    enabled_only: bool = True,
) -> list[dict[str, Any]]:
    """List all operators."""
    runtime = _create_runtime(config_path)
    operators = runtime.list_operators()
    if enabled_only:
        operators = [op for op in operators if op.enabled]
    return [
        {
            "id": op.id,
            "name": op.name,
            "workflows": len(op.workflows),
            "triggers": len(op.triggers),
            "enabled": op.enabled,
        }
        for op in operators
    ]


def get_operator_info(
    operator_id: str,
    config_path: str = "config/operators.yaml",
) -> dict[str, Any] | None:
    """Get detailed info for a single operator."""
    runtime = _create_runtime(config_path)
    op = runtime.get_operator(operator_id)
    if not op:
        return None

    total_nodes = sum(len(wf.nodes) for wf in op.workflows)
    llm_nodes = sum(
        1 for wf in op.workflows for n in wf.nodes if n.type.value == "llm"
    )
    logic_nodes = total_nodes - llm_nodes

    return {
        "id": op.id,
        "name": op.name,
        "description": op.description,
        "owner": op.owner,
        "enabled": op.enabled,
        "workflows": [wf.id for wf in op.workflows],
        "triggers": [t.id for t in op.triggers],
        "output_channels": op.output_channels,
        "total_nodes": total_nodes,
        "llm_nodes": llm_nodes,
        "logic_nodes": logic_nodes,
    }


def get_system_summary(
    config_path: str = "config/operators.yaml",
) -> dict[str, Any]:
    """Get a summary of the entire operator system."""
    runtime = _create_runtime(config_path)
    return runtime.summary()


def _cmd_list(args: argparse.Namespace) -> None:
    operators = list_operators()
    if not operators:
        print("No operators found.")
        return
    print(f"{'ID':<20} {'Name':<25} {'Workflows':<10} {'Triggers':<10} {'Enabled'}")
    print("-" * 75)
    for op in operators:
        print(
            f"{op['id']:<20} {op['name']:<25} {op['workflows']:<10} "
            f"{op['triggers']:<10} {op['enabled']}"
        )
    print(f"\n{len(operators)} operators")


def _cmd_info(args: argparse.Namespace) -> None:
    info = get_operator_info(args.operator_id)
    if not info:
        print(f"Operator '{args.operator_id}' not found.")
        sys.exit(1)
    for k, v in info.items():
        print(f"  {k}: {v}")


def _cmd_summary(args: argparse.Namespace) -> None:
    summary = get_system_summary()
    print(f"Operators:    {summary['operators']}")
    print(f"Workflows:    {summary['workflows']}")
    print(f"Triggers:     {summary['triggers']}")
    print(f"Total nodes:  {summary['nodes']}")
    print(f"  LLM nodes:  {summary['llm_nodes']}")
    print(f"  Logic nodes: {summary['logic_nodes']}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="vibe-ai-ops", description="Vibe AI Ops CLI")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="List all operators")
    p_list.set_defaults(func=_cmd_list)

    # info
    p_info = sub.add_parser("info", help="Show operator details")
    p_info.add_argument("operator_id", help="Operator ID (e.g. revenue_ops)")
    p_info.set_defaults(func=_cmd_info)

    # summary
    p_summary = sub.add_parser("summary", help="System summary")
    p_summary.set_defaults(func=_cmd_summary)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
