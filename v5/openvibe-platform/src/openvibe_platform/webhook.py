"""WebhookTranslator — external HTTP webhooks → standard Event objects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from openvibe_sdk.models import Event


@dataclass
class WebhookRule:
    source: str
    event_type_field: str              # payload field containing event type
    event_type_map: dict[str, str]     # raw type -> standard Event.type
    domain: str                        # which domain these events belong to


class WebhookTranslator:
    def __init__(self) -> None:
        self._rules: dict[str, WebhookRule] = {}

    def add_rule(self, rule: WebhookRule) -> None:
        self._rules[rule.source] = rule

    def translate(self, source: str, payload: dict[str, Any]) -> Event | None:
        rule = self._rules.get(source)
        if not rule:
            return None
        raw_type = payload.get(rule.event_type_field, "")
        event_type = rule.event_type_map.get(raw_type)
        if not event_type:
            return None
        return Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            domain=rule.domain,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
        )
