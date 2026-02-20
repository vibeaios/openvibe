from unittest.mock import patch, MagicMock


def _mock_response(json_data):
    """Create a mock httpx response with .json() returning given data."""
    resp = MagicMock()
    resp.json.return_value = json_data
    return resp


def test_pinterest_ads_report_returns_rows():
    """pinterest_ads_report gets reporting endpoint and returns structured rows."""
    from vibe_inc.tools.ads.pinterest_ads import pinterest_ads_report

    mock_resp = _mock_response({"rows": [{"OUTBOUND_CLICK": 150, "IMPRESSION": 5000}]})

    with patch("vibe_inc.tools.ads.pinterest_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.pinterest_ads._get_headers", return_value={"Authorization": "Bearer test"}), \
         patch("vibe_inc.tools.ads.pinterest_ads._get_ad_account_id", return_value="acc_123"):
        mock_httpx.get.return_value = mock_resp
        result = pinterest_ads_report(
            metrics=["OUTBOUND_CLICK", "IMPRESSION"],
            date_range="2026-02-01,2026-02-07",
        )

    assert "rows" in result
    assert len(result["rows"]) == 1
    assert result["granularity"] == "DAY"


def test_pinterest_ads_report_has_docstring():
    """Tool function must have a docstring for Anthropic schema generation."""
    from vibe_inc.tools.ads.pinterest_ads import pinterest_ads_report
    assert pinterest_ads_report.__doc__ is not None
    assert "Pinterest" in pinterest_ads_report.__doc__


def test_pinterest_ads_campaigns_returns_list():
    """pinterest_ads_campaigns returns campaign list from GET endpoint."""
    from vibe_inc.tools.ads.pinterest_ads import pinterest_ads_campaigns

    mock_resp = _mock_response({
        "items": [
            {"id": "c_1", "name": "Bot - Pinterest - Discovery"},
            {"id": "c_2", "name": "Dot - Pinterest - Awareness"},
        ],
    })

    with patch("vibe_inc.tools.ads.pinterest_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.pinterest_ads._get_headers", return_value={"Authorization": "Bearer test"}), \
         patch("vibe_inc.tools.ads.pinterest_ads._get_ad_account_id", return_value="acc_123"):
        mock_httpx.get.return_value = mock_resp
        result = pinterest_ads_campaigns()

    assert "campaigns" in result
    assert len(result["campaigns"]) == 2


def test_pinterest_ads_create_returns_id():
    """pinterest_ads_create posts to campaign endpoint and returns campaign_id."""
    from vibe_inc.tools.ads.pinterest_ads import pinterest_ads_create

    mock_resp = _mock_response({"id": "c_new_456"})

    with patch("vibe_inc.tools.ads.pinterest_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.pinterest_ads._get_headers", return_value={"Authorization": "Bearer test"}), \
         patch("vibe_inc.tools.ads.pinterest_ads._get_ad_account_id", return_value="acc_123"):
        mock_httpx.post.return_value = mock_resp
        result = pinterest_ads_create(
            campaign_name="Bot - Pinterest - Discovery",
            objective="CONVERSIONS",
            budget=500000000,
        )

    assert "campaign_id" in result
    assert result["campaign_id"] == "c_new_456"


def test_pinterest_ads_update_returns_result():
    """pinterest_ads_update patches campaign and returns success."""
    from vibe_inc.tools.ads.pinterest_ads import pinterest_ads_update

    mock_resp = _mock_response({"id": "c_123", "status": "ACTIVE"})

    with patch("vibe_inc.tools.ads.pinterest_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.pinterest_ads._get_headers", return_value={"Authorization": "Bearer test"}), \
         patch("vibe_inc.tools.ads.pinterest_ads._get_ad_account_id", return_value="acc_123"):
        mock_httpx.patch.return_value = mock_resp
        result = pinterest_ads_update(
            campaign_id="c_123",
            updates={"status": "ACTIVE"},
        )

    assert result["updated"] is True
    assert result["campaign_id"] == "c_123"


def test_pinterest_ads_pins_returns_list():
    """pinterest_ads_pins returns promoted pin assets list."""
    from vibe_inc.tools.ads.pinterest_ads import pinterest_ads_pins

    mock_resp = _mock_response({
        "items": [
            {"id": "pin_1", "title": "Bot Lifestyle Pin"},
        ],
    })

    with patch("vibe_inc.tools.ads.pinterest_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.pinterest_ads._get_headers", return_value={"Authorization": "Bearer test"}), \
         patch("vibe_inc.tools.ads.pinterest_ads._get_ad_account_id", return_value="acc_123"):
        mock_httpx.get.return_value = mock_resp
        result = pinterest_ads_pins(campaign_id="c_123")

    assert "pins" in result
    assert len(result["pins"]) == 1
