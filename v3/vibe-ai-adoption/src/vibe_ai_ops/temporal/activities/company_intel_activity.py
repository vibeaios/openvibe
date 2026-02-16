"""Temporal activity for the Company Intelligence operator.

This is the bridge between Temporal (scheduling) and LangGraph (workflow).
Temporal calls this activity → activity runs the LangGraph graph → graph uses Claude SDK.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from temporalio import activity


@dataclass
class CompanyIntelInput:
    company_name: str


@dataclass
class CompanyIntelOutput:
    company_name: str
    prospect_quality: str
    report: str
    status: str  # "success" | "error"
    error: str = ""
    duration_seconds: float = 0.0


@activity.defn
async def run_company_intel(inp: CompanyIntelInput) -> CompanyIntelOutput:
    """Temporal activity: run the Company Intel LangGraph graph.

    Chain: Temporal activity → LangGraph graph → Claude API
    """
    start = time.time()

    try:
        # Import here to avoid Temporal sandbox issues
        from vibe_ai_ops.operators.company_intel import create_company_intel_graph

        activity.logger.info(f"Starting company intel for: {inp.company_name}")

        graph = create_company_intel_graph()
        result = graph.invoke({"company_name": inp.company_name})

        duration = time.time() - start
        activity.logger.info(
            f"Company intel complete: {inp.company_name} "
            f"→ {result.get('prospect_quality', '?')} ({duration:.1f}s)"
        )

        return CompanyIntelOutput(
            company_name=inp.company_name,
            prospect_quality=result.get("prospect_quality", "unknown"),
            report=result.get("report", ""),
            status="success",
            duration_seconds=duration,
        )

    except Exception as e:
        return CompanyIntelOutput(
            company_name=inp.company_name,
            prospect_quality="unknown",
            report="",
            status="error",
            error=str(e),
            duration_seconds=time.time() - start,
        )
