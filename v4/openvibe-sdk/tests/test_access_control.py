from openvibe_sdk.memory.types import Classification, Fact
from openvibe_sdk.memory.access import (
    CLASSIFICATION_RANK,
    AccessFilter,
    ClearanceProfile,
)


def test_classification_rank_order():
    assert CLASSIFICATION_RANK[Classification.PUBLIC] == 0
    assert CLASSIFICATION_RANK[Classification.INTERNAL] == 1
    assert CLASSIFICATION_RANK[Classification.CONFIDENTIAL] == 2
    assert CLASSIFICATION_RANK[Classification.RESTRICTED] == 3


def test_clearance_public_always_accessible():
    profile = ClearanceProfile(agent_id="cro", domain_clearance={})
    fact = Fact(id="f1", content="public info", classification=Classification.PUBLIC)
    assert profile.can_access(fact) is True


def test_clearance_internal_with_domain():
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.INTERNAL},
    )
    fact = Fact(
        id="f1", content="internal", domain="revenue",
        classification=Classification.INTERNAL,
    )
    assert profile.can_access(fact) is True


def test_clearance_denied_insufficient():
    profile = ClearanceProfile(
        agent_id="cmo",
        domain_clearance={"marketing": Classification.INTERNAL},
    )
    fact = Fact(
        id="f1", content="secret", domain="revenue",
        classification=Classification.CONFIDENTIAL,
    )
    assert profile.can_access(fact) is False


def test_clearance_denied_no_domain():
    profile = ClearanceProfile(
        agent_id="cmo",
        domain_clearance={"marketing": Classification.CONFIDENTIAL},
    )
    fact = Fact(
        id="f1", content="revenue data", domain="revenue",
        classification=Classification.INTERNAL,
    )
    assert profile.can_access(fact) is False


def test_clearance_confidential_can_access_internal():
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.CONFIDENTIAL},
    )
    fact = Fact(
        id="f1", content="internal data", domain="revenue",
        classification=Classification.INTERNAL,
    )
    assert profile.can_access(fact) is True


def test_access_filter():
    profile = ClearanceProfile(
        agent_id="cro",
        domain_clearance={"revenue": Classification.CONFIDENTIAL},
    )
    facts = [
        Fact(id="f1", content="public", classification=Classification.PUBLIC),
        Fact(id="f2", content="revenue internal", domain="revenue",
             classification=Classification.INTERNAL),
        Fact(id="f3", content="marketing secret", domain="marketing",
             classification=Classification.CONFIDENTIAL),
    ]
    af = AccessFilter(profile)
    filtered = af.filter(facts)
    assert len(filtered) == 2
    assert {f.id for f in filtered} == {"f1", "f2"}
