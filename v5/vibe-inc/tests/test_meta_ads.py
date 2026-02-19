from unittest.mock import patch, MagicMock


def test_meta_ads_read_returns_campaign_data():
    """meta_ads_read returns structured performance data."""
    from vibe_inc.tools.meta_ads import meta_ads_read

    mock_campaign = MagicMock()
    mock_campaign.get_insights.return_value = [
        {"campaign_name": "Bot - Foundation", "spend": "150.00",
         "impressions": "10000", "clicks": "200", "actions": [{"action_type": "purchase", "value": "5"}]}
    ]
    mock_account = MagicMock()
    mock_account.get_campaigns.return_value = [mock_campaign]

    with patch("vibe_inc.tools.ads.meta_ads._get_account", return_value=mock_account):
        result = meta_ads_read(level="campaign", date_range="last_7d")

    assert "rows" in result
    assert result["level"] == "campaign"


def test_meta_ads_read_has_docstring():
    """Tool function must have a docstring for Anthropic schema generation."""
    from vibe_inc.tools.meta_ads import meta_ads_read
    assert meta_ads_read.__doc__ is not None
    assert "Read" in meta_ads_read.__doc__


def test_meta_ads_read_accepts_date_range():
    """meta_ads_read accepts custom date ranges."""
    from vibe_inc.tools.meta_ads import meta_ads_read

    mock_account = MagicMock()
    mock_account.get_campaigns.return_value = []

    with patch("vibe_inc.tools.ads.meta_ads._get_account", return_value=mock_account):
        result = meta_ads_read(level="campaign", date_range="2026-02-01,2026-02-15")

    assert result["date_range"] == "2026-02-01,2026-02-15"


def test_meta_ads_read_supports_adset_level():
    """meta_ads_read can report at adset level."""
    from vibe_inc.tools.meta_ads import meta_ads_read

    mock_account = MagicMock()
    mock_account.get_ad_sets.return_value = []

    with patch("vibe_inc.tools.ads.meta_ads._get_account", return_value=mock_account):
        result = meta_ads_read(level="adset", date_range="last_7d")

    assert result["level"] == "adset"


def test_meta_ads_create_returns_ids():
    """meta_ads_create returns campaign, adset, and ad IDs."""
    from vibe_inc.tools.meta_ads import meta_ads_create

    mock_account = MagicMock()
    mock_campaign = MagicMock()
    mock_campaign.__getitem__ = MagicMock(return_value="camp_123")
    mock_account.create_campaign.return_value = mock_campaign

    mock_adset = MagicMock()
    mock_adset.__getitem__ = MagicMock(return_value="adset_456")

    mock_ad = MagicMock()
    mock_ad.__getitem__ = MagicMock(return_value="ad_789")

    with patch("vibe_inc.tools.ads.meta_ads._get_account", return_value=mock_account), \
         patch("vibe_inc.tools.ads.meta_ads._create_adset", return_value=mock_adset), \
         patch("vibe_inc.tools.ads.meta_ads._create_ad", return_value=mock_ad):
        result = meta_ads_create(
            campaign_name="Bot - Foundation Test",
            objective="OUTCOME_SALES",
            budget_daily=50.0,
            targeting={"age_min": 25, "age_max": 55, "interests": ["technology"]},
            creative={"headline": "The room that remembers", "body": "Test body", "link": "https://vibe.us/bot"},
        )

    assert "campaign_id" in result
    assert "adset_id" in result
    assert "ad_id" in result


def test_meta_ads_create_has_docstring():
    from vibe_inc.tools.meta_ads import meta_ads_create
    assert meta_ads_create.__doc__ is not None


def test_meta_ads_update_changes_status():
    """meta_ads_update can pause a campaign."""
    from vibe_inc.tools.meta_ads import meta_ads_update

    mock_obj = MagicMock()
    mock_obj.api_update.return_value = True

    with patch("vibe_inc.tools.ads.meta_ads._get_object", return_value=mock_obj):
        result = meta_ads_update(
            object_type="campaign",
            object_id="camp_123",
            updates={"status": "PAUSED"},
        )

    assert result["updated"] is True
    assert result["object_id"] == "camp_123"


def test_meta_ads_update_has_docstring():
    from vibe_inc.tools.meta_ads import meta_ads_update
    assert meta_ads_update.__doc__ is not None
