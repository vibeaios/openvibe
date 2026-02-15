from vibe_ai_ops.shared.hubspot_client import HubSpotClient


def test_hubspot_client_get_leads(mocker):
    mock_hs = mocker.patch("vibe_ai_ops.shared.hubspot_client.HubSpot")
    mock_instance = mock_hs.return_value
    mock_instance.crm.contacts.search_api.do_search.return_value = mocker.MagicMock(
        results=[
            mocker.MagicMock(properties={
                "email": "test@example.com",
                "firstname": "John",
                "lastname": "Doe",
                "company": "Acme",
                "hs_lead_status": "NEW",
            })
        ]
    )

    client = HubSpotClient(api_key="test-key")
    leads = client.get_new_leads(limit=10)
    assert len(leads) == 1
    assert leads[0]["email"] == "test@example.com"


def test_hubspot_client_update_lead(mocker):
    mock_hs = mocker.patch("vibe_ai_ops.shared.hubspot_client.HubSpot")
    mock_instance = mock_hs.return_value

    client = HubSpotClient(api_key="test-key")
    client.update_contact("123", {"hs_lead_status": "QUALIFIED", "ai_score": "85"})

    mock_instance.crm.contacts.basic_api.update.assert_called_once()


def test_hubspot_client_get_deals(mocker):
    mock_hs = mocker.patch("vibe_ai_ops.shared.hubspot_client.HubSpot")
    mock_instance = mock_hs.return_value
    mock_instance.crm.deals.search_api.do_search.return_value = mocker.MagicMock(
        results=[
            mocker.MagicMock(properties={
                "dealname": "Acme Corp",
                "amount": "50000",
                "dealstage": "qualifiedtobuy",
            })
        ]
    )

    client = HubSpotClient(api_key="test-key")
    deals = client.get_active_deals()
    assert len(deals) == 1
    assert deals[0]["dealname"] == "Acme Corp"
