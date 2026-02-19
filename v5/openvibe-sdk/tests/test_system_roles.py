from openvibe_sdk.system_roles import SYSTEM_ROLES, Coordinator, Archivist, Auditor
from openvibe_sdk.models import RoleInstance


def test_system_roles_are_role_instances():
    for role in SYSTEM_ROLES:
        assert isinstance(role, RoleInstance)


def test_system_role_names():
    names = {r.name for r in SYSTEM_ROLES}
    assert names == {"Coordinator", "Archivist", "Auditor"}


def test_system_roles_have_valid_soul():
    """Every system role must have an identity in its soul config."""
    for role in SYSTEM_ROLES:
        assert "identity" in role.soul
        assert "name" in role.soul["identity"]
        assert "role" in role.soul["identity"]
        assert len(role.soul["identity"]["role"]) > 0


def test_system_roles_have_template_ids():
    """System roles use system/ namespace for template_id."""
    for role in SYSTEM_ROLES:
        assert role.template_id.startswith("system/")


def test_system_roles_count():
    assert len(SYSTEM_ROLES) == 3
