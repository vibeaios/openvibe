from unittest.mock import patch, MagicMock


def _mock_response(json_data):
    """Create a mock httpx response with .json() returning given data."""
    resp = MagicMock()
    resp.json.return_value = json_data
    return resp


def test_hubspot_contact_get_by_email():
    """hubspot_contact_get searches by email and returns contact with enrichment info."""
    from vibe_inc.tools.crm.hubspot import hubspot_contact_get

    mock_resp = _mock_response({
        "results": [
            {
                "id": "501",
                "properties": {
                    "email": "buyer@acme.com",
                    "firstname": "Jane",
                    "lastname": "Doe",
                    "company": "Acme Corp",
                    "lifecyclestage": "customer",
                    "hs_lead_status": "OPEN",
                },
            },
        ],
    })

    with patch("vibe_inc.tools.crm.hubspot.httpx") as mock_httpx, \
         patch("vibe_inc.tools.crm.hubspot._get_headers", return_value={"Authorization": "Bearer test"}):
        mock_httpx.post.return_value = mock_resp
        result = hubspot_contact_get(email="buyer@acme.com")

    assert "contact" in result
    assert result["contact"]["id"] == "501"
    assert result["contact"]["properties"]["company"] == "Acme Corp"


def test_hubspot_contact_get_has_docstring():
    """Tool function must have a docstring for Anthropic schema generation."""
    from vibe_inc.tools.crm.hubspot import hubspot_contact_get
    assert hubspot_contact_get.__doc__ is not None
    assert "HubSpot" in hubspot_contact_get.__doc__


def test_hubspot_contact_update_sends_patch():
    """hubspot_contact_update PATCHes contact properties."""
    from vibe_inc.tools.crm.hubspot import hubspot_contact_update

    mock_resp = _mock_response({
        "id": "501",
        "properties": {"lifecyclestage": "opportunity"},
    })

    with patch("vibe_inc.tools.crm.hubspot.httpx") as mock_httpx, \
         patch("vibe_inc.tools.crm.hubspot._get_headers", return_value={"Authorization": "Bearer test"}):
        mock_httpx.patch.return_value = mock_resp
        result = hubspot_contact_update(
            contact_id="501",
            properties={"lifecyclestage": "opportunity"},
        )

    assert result["updated"] is True
    assert result["contact"]["properties"]["lifecyclestage"] == "opportunity"
    mock_httpx.patch.assert_called_once()


def test_hubspot_deals_list_returns_deals():
    """hubspot_deals_list returns associated deals for a contact."""
    from vibe_inc.tools.crm.hubspot import hubspot_deals_list

    mock_assoc_resp = _mock_response({
        "results": [
            {"id": "deal_1", "type": "contact_to_deal"},
            {"id": "deal_2", "type": "contact_to_deal"},
        ],
    })

    with patch("vibe_inc.tools.crm.hubspot.httpx") as mock_httpx, \
         patch("vibe_inc.tools.crm.hubspot._get_headers", return_value={"Authorization": "Bearer test"}):
        mock_httpx.get.return_value = mock_assoc_resp
        result = hubspot_deals_list(contact_id="501")

    assert "deals" in result
    assert result["count"] == 2


def test_hubspot_deal_create_posts_with_association():
    """hubspot_deal_create creates deal and associates with contact."""
    from vibe_inc.tools.crm.hubspot import hubspot_deal_create

    mock_resp = _mock_response({
        "id": "deal_new",
        "properties": {
            "dealname": "Acme Corp - Bot",
            "dealstage": "lead",
            "pipeline": "b2b",
            "amount": "3000",
        },
    })

    with patch("vibe_inc.tools.crm.hubspot.httpx") as mock_httpx, \
         patch("vibe_inc.tools.crm.hubspot._get_headers", return_value={"Authorization": "Bearer test"}):
        mock_httpx.post.return_value = mock_resp
        result = hubspot_deal_create(
            contact_id="501",
            dealname="Acme Corp - Bot",
            pipeline="b2b",
            stage="lead",
            amount=3000,
        )

    assert result["created"] is True
    assert result["deal"]["id"] == "deal_new"
    assert mock_httpx.post.call_count == 2  # create deal + create association


def test_hubspot_deal_update_patches_stage():
    """hubspot_deal_update PATCHes deal properties."""
    from vibe_inc.tools.crm.hubspot import hubspot_deal_update

    mock_resp = _mock_response({
        "id": "deal_1",
        "properties": {"dealstage": "mql"},
    })

    with patch("vibe_inc.tools.crm.hubspot.httpx") as mock_httpx, \
         patch("vibe_inc.tools.crm.hubspot._get_headers", return_value={"Authorization": "Bearer test"}):
        mock_httpx.patch.return_value = mock_resp
        result = hubspot_deal_update(
            deal_id="deal_1",
            properties={"dealstage": "mql"},
        )

    assert result["updated"] is True
    assert result["deal"]["properties"]["dealstage"] == "mql"


def test_hubspot_workflow_enroll_posts_enrollment():
    """hubspot_workflow_enroll POSTs contact enrollment to workflow."""
    from vibe_inc.tools.crm.hubspot import hubspot_workflow_enroll

    mock_resp = _mock_response({})
    mock_resp.status_code = 204

    with patch("vibe_inc.tools.crm.hubspot.httpx") as mock_httpx, \
         patch("vibe_inc.tools.crm.hubspot._get_headers", return_value={"Authorization": "Bearer test"}):
        mock_httpx.post.return_value = mock_resp
        result = hubspot_workflow_enroll(
            contact_email="buyer@acme.com",
            workflow_id="12345",
        )

    assert result["enrolled"] is True
    assert result["workflow_id"] == "12345"


def test_hubspot_workflow_enroll_has_docstring():
    """Tool function must have a docstring for Anthropic schema generation."""
    from vibe_inc.tools.crm.hubspot import hubspot_workflow_enroll
    assert hubspot_workflow_enroll.__doc__ is not None
    assert "HubSpot" in hubspot_workflow_enroll.__doc__
