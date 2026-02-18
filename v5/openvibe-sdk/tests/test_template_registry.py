import pytest
from openvibe_sdk.template_registry import TemplateRegistry
from openvibe_sdk.models import TemplateConfig, RoleInstance


def _make_template(name: str) -> TemplateConfig:
    return TemplateConfig(
        name=name,
        soul={"identity": {"name": name, "role": "test"}},
        capabilities=[],
    )


def test_register_and_get():
    reg = TemplateRegistry()
    tmpl = _make_template("Content")
    reg.register("gtm/content-role", tmpl)
    assert reg.get("gtm/content-role") == tmpl


def test_get_missing_raises():
    reg = TemplateRegistry()
    with pytest.raises(KeyError):
        reg.get("does/not/exist")


def test_list_templates():
    reg = TemplateRegistry()
    reg.register("gtm/content-role", _make_template("Content"))
    reg.register("gtm/revenue-role", _make_template("Revenue"))
    assert sorted(reg.list()) == ["gtm/content-role", "gtm/revenue-role"]


def test_instantiate_with_overrides():
    reg = TemplateRegistry()
    reg.register("gtm/content-role", _make_template("Content"))
    spec = reg.instantiate("gtm/content-role", name_override="Vibe Content")
    assert isinstance(spec, RoleInstance)
    assert spec.name == "Vibe Content"


def test_instantiate_without_override_uses_template_name():
    reg = TemplateRegistry()
    reg.register("gtm/content-role", _make_template("Content"))
    spec = reg.instantiate("gtm/content-role")
    assert spec.name == "Content"
