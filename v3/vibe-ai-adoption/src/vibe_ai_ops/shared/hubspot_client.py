from __future__ import annotations

from typing import Any

from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest, SimplePublicObjectInput


class HubSpotClient:
    def __init__(self, api_key: str | None = None):
        self._client = HubSpot(access_token=api_key)

    def get_new_leads(self, limit: int = 50) -> list[dict[str, Any]]:
        request = PublicObjectSearchRequest(
            filter_groups=[{
                "filters": [{
                    "propertyName": "hs_lead_status",
                    "operator": "EQ",
                    "value": "NEW",
                }]
            }],
            limit=limit,
            properties=[
                "email", "firstname", "lastname", "company",
                "jobtitle", "phone", "hs_lead_status",
                "lifecyclestage", "hs_analytics_source",
            ],
        )
        response = self._client.crm.contacts.search_api.do_search(
            public_object_search_request=request
        )
        return [r.properties for r in response.results]

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        response = self._client.crm.contacts.basic_api.get_by_id(
            contact_id=contact_id,
            properties=[
                "email", "firstname", "lastname", "company",
                "jobtitle", "phone", "hs_lead_status",
                "lifecyclestage", "hs_analytics_source",
            ],
        )
        return response.properties

    def update_contact(self, contact_id: str, properties: dict[str, str]):
        self._client.crm.contacts.basic_api.update(
            contact_id=contact_id,
            simple_public_object_input=SimplePublicObjectInput(
                properties=properties
            ),
        )

    def get_active_deals(self, limit: int = 100) -> list[dict[str, Any]]:
        request = PublicObjectSearchRequest(
            filter_groups=[{
                "filters": [{
                    "propertyName": "dealstage",
                    "operator": "NEQ",
                    "value": "closedwon",
                }]
            }],
            limit=limit,
            properties=[
                "dealname", "amount", "dealstage", "closedate",
                "pipeline", "hs_lastmodifieddate",
            ],
        )
        response = self._client.crm.deals.search_api.do_search(
            public_object_search_request=request
        )
        return [r.properties for r in response.results]
