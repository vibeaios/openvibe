from unittest.mock import patch, MagicMock


def _mock_response(json_data):
    """Create a mock httpx response with .json() returning given data."""
    resp = MagicMock()
    resp.json.return_value = json_data
    return resp


def test_tiktok_ads_report_returns_rows():
    """tiktok_ads_report posts to reporting endpoint and returns structured rows."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_report

    mock_resp = _mock_response({
        "data": {"list": [{"spend": "120.50", "impressions": "5000"}]},
    })

    with patch("vibe_inc.tools.ads.tiktok_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.tiktok_ads._get_headers", return_value={"Access-Token": "test"}), \
         patch("vibe_inc.tools.ads.tiktok_ads._get_advertiser_id", return_value="adv_123"):
        mock_httpx.post.return_value = mock_resp
        result = tiktok_ads_report(
            metrics=["spend", "impressions"],
            dimensions=["stat_time_day"],
            date_range="2026-02-01,2026-02-07",
        )

    assert "rows" in result
    assert len(result["rows"]) == 1
    assert result["data_level"] == "AUCTION_AD"


def test_tiktok_ads_report_has_docstring():
    """Tool function must have a docstring for Anthropic schema generation."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_report
    assert tiktok_ads_report.__doc__ is not None
    assert "TikTok" in tiktok_ads_report.__doc__


def test_tiktok_ads_campaigns_returns_list():
    """tiktok_ads_campaigns returns campaign list from GET endpoint."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_campaigns

    mock_resp = _mock_response({
        "data": {"list": [
            {"campaign_id": "c_1", "campaign_name": "Bot - TikTok"},
            {"campaign_id": "c_2", "campaign_name": "Dot - TikTok"},
        ]},
    })

    with patch("vibe_inc.tools.ads.tiktok_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.tiktok_ads._get_headers", return_value={"Access-Token": "test"}), \
         patch("vibe_inc.tools.ads.tiktok_ads._get_advertiser_id", return_value="adv_123"):
        mock_httpx.get.return_value = mock_resp
        result = tiktok_ads_campaigns()

    assert "campaigns" in result
    assert len(result["campaigns"]) == 2


def test_tiktok_ads_create_returns_id():
    """tiktok_ads_create posts to campaign/create and returns campaign_id."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_create

    mock_resp = _mock_response({
        "data": {"campaign_id": "c_new_123"},
    })

    with patch("vibe_inc.tools.ads.tiktok_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.tiktok_ads._get_headers", return_value={"Access-Token": "test"}), \
         patch("vibe_inc.tools.ads.tiktok_ads._get_advertiser_id", return_value="adv_123"):
        mock_httpx.post.return_value = mock_resp
        result = tiktok_ads_create(
            campaign_name="Bot - TikTok - Foundation",
            objective="CONVERSIONS",
            budget=500.0,
        )

    assert "campaign_id" in result
    assert result["campaign_id"] == "c_new_123"


def test_tiktok_ads_update_returns_result():
    """tiktok_ads_update posts to campaign/update and returns success."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_update

    mock_resp = _mock_response({"code": 0, "message": "OK"})

    with patch("vibe_inc.tools.ads.tiktok_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.tiktok_ads._get_headers", return_value={"Access-Token": "test"}), \
         patch("vibe_inc.tools.ads.tiktok_ads._get_advertiser_id", return_value="adv_123"):
        mock_httpx.post.return_value = mock_resp
        result = tiktok_ads_update(
            campaign_id="c_123",
            updates={"budget": 600.0},
        )

    assert result["updated"] is True
    assert result["campaign_id"] == "c_123"


def test_tiktok_ads_creatives_returns_list():
    """tiktok_ads_creatives returns creative assets list."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_creatives

    mock_resp = _mock_response({
        "data": {"list": [
            {"ad_id": "ad_1", "ad_name": "Bot Video 1"},
        ]},
    })

    with patch("vibe_inc.tools.ads.tiktok_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.tiktok_ads._get_headers", return_value={"Access-Token": "test"}), \
         patch("vibe_inc.tools.ads.tiktok_ads._get_advertiser_id", return_value="adv_123"):
        mock_httpx.get.return_value = mock_resp
        result = tiktok_ads_creatives(campaign_id="c_123")

    assert "creatives" in result
    assert len(result["creatives"]) == 1


def test_tiktok_ads_audiences_returns_list():
    """tiktok_ads_audiences returns audience list from DMP endpoint."""
    from vibe_inc.tools.ads.tiktok_ads import tiktok_ads_audiences

    mock_resp = _mock_response({
        "data": {"list": [
            {"custom_audience_id": "aud_1", "name": "Site Visitors"},
            {"custom_audience_id": "aud_2", "name": "Purchasers"},
        ]},
    })

    with patch("vibe_inc.tools.ads.tiktok_ads.httpx") as mock_httpx, \
         patch("vibe_inc.tools.ads.tiktok_ads._get_headers", return_value={"Access-Token": "test"}), \
         patch("vibe_inc.tools.ads.tiktok_ads._get_advertiser_id", return_value="adv_123"):
        mock_httpx.get.return_value = mock_resp
        result = tiktok_ads_audiences(action="list")

    assert "audiences" in result
    assert len(result["audiences"]) == 2
