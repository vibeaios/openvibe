"""Temporal workflow for the Company Intelligence operator.

This is the outermost layer — Temporal decides WHEN to run,
then delegates to the activity (which runs the LangGraph graph).

In production, this workflow could be triggered by:
  - Cron schedule (e.g., research new leads every Monday)
  - Webhook (e.g., new lead in HubSpot)
  - On-demand (e.g., someone asks "research Stripe")
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from vibe_ai_ops.temporal.activities.company_intel_activity import (
        run_company_intel,
        CompanyIntelInput,
        CompanyIntelOutput,
    )


@dataclass
class CompanyIntelWorkflowInput:
    company_name: str


@workflow.defn
class CompanyIntelWorkflow:
    """Temporal workflow: research a company through the full stack.

    Temporal (this workflow)
      → Activity (company_intel_activity)
        → LangGraph (4-node graph)
          → Claude API (via call_claude)
    """

    @workflow.run
    async def run(self, inp: CompanyIntelWorkflowInput) -> CompanyIntelOutput:
        workflow.logger.info(f"Starting Company Intel workflow for: {inp.company_name}")

        result = await workflow.execute_activity(
            run_company_intel,
            CompanyIntelInput(company_name=inp.company_name),
            start_to_close_timeout=timedelta(minutes=5),
        )

        if result.status == "success":
            workflow.logger.info(
                f"Company Intel complete: {inp.company_name} "
                f"→ {result.prospect_quality} ({result.duration_seconds:.1f}s)"
            )
        else:
            workflow.logger.error(f"Company Intel failed: {result.error}")

        return result
