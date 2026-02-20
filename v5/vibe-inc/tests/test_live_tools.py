"""Live smoke tests — real API calls, read-only.

Run: pytest tests/test_live_tools.py -m live -v
Requires: API credentials in environment or .env file.
"""
import os

import pytest

live = pytest.mark.live


def _skip_unless_env(*keys):
    """Skip test if any required env var is missing."""
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Missing env: {', '.join(missing)}")


@live
def test_meta_ads_read_live():
    """meta_ads_read returns campaign data from the real Meta API."""
    _skip_unless_env("META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID")
    from vibe_inc.tools.ads.meta_ads import meta_ads_read

    result = meta_ads_read(level="campaign", date_range="last_7d")
    assert "rows" in result
    assert "level" in result
    assert result["level"] == "campaign"


@live
def test_google_ads_query_live():
    """google_ads_query returns campaign data from the real Google Ads API."""
    _skip_unless_env("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID")
    from vibe_inc.tools.ads.google_ads import google_ads_query

    result = google_ads_query(
        query="SELECT campaign.name, campaign.status FROM campaign LIMIT 5"
    )
    assert "rows" in result
    assert "query" in result


@live
def test_hubspot_contact_get_live():
    """hubspot_contact_get returns contact data from the real HubSpot API."""
    _skip_unless_env("HUBSPOT_API_KEY")
    from vibe_inc.tools.crm.hubspot import hubspot_contact_get

    result = hubspot_contact_get(email="test-nonexistent@example.com")
    assert isinstance(result, dict)
