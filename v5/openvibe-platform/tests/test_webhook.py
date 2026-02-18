from openvibe_platform.webhook import WebhookTranslator, WebhookRule


def test_hubspot_lead_created():
    translator = WebhookTranslator()
    translator.add_rule(WebhookRule(
        source="hubspot",
        event_type_field="subscriptionType",
        event_type_map={"contact.creation": "lead.created"},
        domain="revenue",
    ))
    payload = {"subscriptionType": "contact.creation",
               "objectId": "123", "portalId": "456"}
    event = translator.translate("hubspot", payload)
    assert event is not None
    assert event.type == "lead.created"
    assert event.domain == "revenue"
    assert event.source == "hubspot"


def test_unknown_source_returns_none():
    translator = WebhookTranslator()
    event = translator.translate("unknown-source", {"foo": "bar"})
    assert event is None


def test_unmapped_event_type_returns_none():
    translator = WebhookTranslator()
    translator.add_rule(WebhookRule(
        source="hubspot",
        event_type_field="subscriptionType",
        event_type_map={"contact.creation": "lead.created"},
        domain="revenue",
    ))
    payload = {"subscriptionType": "deal.deletion"}
    event = translator.translate("hubspot", payload)
    assert event is None
