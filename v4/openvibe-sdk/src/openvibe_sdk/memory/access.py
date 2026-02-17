"""Access control — ClearanceProfile, AccessFilter."""

from __future__ import annotations

from dataclasses import dataclass, field

from openvibe_sdk.memory.types import Classification, Fact

CLASSIFICATION_RANK: dict[Classification, int] = {
    Classification.PUBLIC: 0,
    Classification.INTERNAL: 1,
    Classification.CONFIDENTIAL: 2,
    Classification.RESTRICTED: 3,
}


@dataclass
class ClearanceProfile:
    """Per-agent/human permission config."""

    agent_id: str
    domain_clearance: dict[str, Classification] = field(default_factory=dict)

    def can_access(self, fact: Fact) -> bool:
        """Check if this profile can access a fact."""
        if fact.classification == Classification.PUBLIC:
            return True
        clearance = self.domain_clearance.get(fact.domain)
        if not clearance:
            return False
        return (
            CLASSIFICATION_RANK[clearance]
            >= CLASSIFICATION_RANK[fact.classification]
        )


class AccessFilter:
    """Filter a list of facts by clearance."""

    def __init__(self, clearance: ClearanceProfile) -> None:
        self._clearance = clearance

    def filter(self, facts: list[Fact]) -> list[Fact]:
        return [f for f in facts if self._clearance.can_access(f)]
