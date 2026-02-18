"""TemplateRegistry — manage pre-built role templates for tenant instantiation."""
from __future__ import annotations

from openvibe_sdk.models import RoleInstance, TemplateConfig


class TemplateRegistry:
    """Registry of pre-built TemplateConfigs. Tenants instantiate and override."""

    def __init__(self) -> None:
        self._templates: dict[str, TemplateConfig] = {}

    def register(self, template_id: str, template: TemplateConfig) -> None:
        self._templates[template_id] = template

    def get(self, template_id: str) -> TemplateConfig:
        if template_id not in self._templates:
            raise KeyError(f"Template not found: {template_id!r}")
        return self._templates[template_id]

    def list(self) -> list[str]:
        return list(self._templates.keys())

    def instantiate(
        self, template_id: str, name_override: str | None = None
    ) -> RoleInstance:
        tmpl = self.get(template_id)
        name = name_override or tmpl.name
        return RoleInstance(
            name=name,
            template_id=template_id,
            soul=tmpl.soul,
            capabilities=tmpl.capabilities,
        )
