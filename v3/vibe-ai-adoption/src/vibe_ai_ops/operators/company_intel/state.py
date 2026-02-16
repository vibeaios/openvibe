"""Company Intelligence Operator state."""

from __future__ import annotations

from typing import TypedDict


class CompanyIntelState(TypedDict, total=False):
    company_name: str
    research: str
    analysis: str
    prospect_quality: str  # high / medium / low
    report: str
    completed: bool
