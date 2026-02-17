#!/usr/bin/env python3
"""End-to-end smoke test: Temporal → LangGraph → Claude API.

This script runs the full stack in a single process:
1. Connects to Temporal server (must be running)
2. Starts a local worker (listens for tasks)
3. Submits a CompanyIntelWorkflow
4. Waits for result and prints it

Usage:
    python smoke_e2e.py                    # default: research "Stripe"
    python smoke_e2e.py "Anthropic"        # research a specific company
    python smoke_e2e.py --list             # just test Temporal connection

Requirements:
    - Temporal server running at localhost:7233 (or TEMPORAL_ADDRESS env var)
    - ANTHROPIC_API_KEY set in environment or .env file
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Initialize LangFuse tracing
_langfuse_client = None
if os.environ.get("LANGFUSE_PUBLIC_KEY"):
    from langfuse import get_client
    _langfuse_client = get_client()
    if _langfuse_client.auth_check():
        print(f"[Tracing] LangFuse connected → {os.environ.get('LANGFUSE_HOST')}")
    else:
        print("[Tracing] LangFuse auth failed — tracing disabled")


async def check_connection():
    """Just verify we can connect to Temporal."""
    from temporalio.client import Client

    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    print(f"Connecting to Temporal at {address}...")

    try:
        client = await Client.connect(address, namespace="default")
        print(f"  Connected to Temporal")
        return client
    except Exception as e:
        print(f"  FAILED: {e}")
        print(f"\n  Is Temporal running? Check: docker ps | grep temporal")
        sys.exit(1)


async def run_smoke_test(company_name: str):
    """Run the full 3-layer smoke test."""
    from temporalio.worker import Worker

    from vibe_ai_ops.temporal.activities.company_intel_activity import (
        run_company_intel,
    )
    from vibe_ai_ops.temporal.workflows.company_intel_workflow import (
        CompanyIntelWorkflow,
        CompanyIntelWorkflowInput,
    )

    # --- Step 1: Connect to Temporal ---
    client = await check_connection()

    # --- Step 2: Check ANTHROPIC_API_KEY ---
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  ANTHROPIC_API_KEY not set. Add it to .env or environment.")
        sys.exit(1)
    print(f"  ANTHROPIC_API_KEY is set")

    # --- Step 3: Start worker + run workflow ---
    task_queue = "vibe-ai-ops-demo"
    workflow_id = f"company-intel-{company_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"

    print(f"\n{'='*60}")
    print(f"  Company: {company_name}")
    print(f"  Workflow ID: {workflow_id}")
    print(f"  Task Queue: {task_queue}")
    print(f"{'='*60}")

    print(f"\n[Temporal] Starting worker on queue: {task_queue}")
    print(f"[Temporal] Submitting CompanyIntelWorkflow...")

    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[CompanyIntelWorkflow],
        activities=[run_company_intel],
    ):
        print(f"[Temporal] Worker running. Executing workflow...\n")

        result = await client.execute_workflow(
            CompanyIntelWorkflow.run,
            CompanyIntelWorkflowInput(company_name=company_name),
            id=workflow_id,
            task_queue=task_queue,
        )

    # --- Step 4: Print result ---
    print(f"\n{'='*60}")
    if result.status == "success":
        print(f"  Status: SUCCESS ({result.duration_seconds:.1f}s)")
        print(f"  Prospect Quality: {result.prospect_quality.upper()}")
        print(f"{'='*60}")
        print(f"\n{result.report}")
    else:
        print(f"  Status: ERROR")
        print(f"  Error: {result.error}")
        print(f"{'='*60}")

    # --- Step 5: Point to Temporal UI ---
    temporal_ui = os.environ.get("TEMPORAL_UI_URL", "http://localhost:8080")
    print(f"\nView in Temporal UI: {temporal_ui}")
    print(f"Look for workflow ID: {workflow_id}")

    return result


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        asyncio.run(check_connection())
        print("  Connection OK")
        return

    company = sys.argv[1] if len(sys.argv) > 1 else "Stripe"
    asyncio.run(run_smoke_test(company))

    # Flush LangFuse traces
    if _langfuse_client:
        _langfuse_client.flush()
        _langfuse_client.shutdown()


if __name__ == "__main__":
    main()
