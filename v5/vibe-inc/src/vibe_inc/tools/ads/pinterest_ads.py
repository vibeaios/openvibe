"""Pinterest Ads API tools for D2C Growth role."""
import os

import httpx

_BASE_URL = "https://api.pinterest.com/v5"


def _get_headers():
    """Return authorization headers for Pinterest Ads API.

    Requires: PINTEREST_ADS_ACCESS_TOKEN
    """
    return {"Authorization": f"Bearer {os.environ['PINTEREST_ADS_ACCESS_TOKEN']}"}


def _get_ad_account_id():
    """Return the Pinterest Ads ad account ID from environment.

    Requires: PINTEREST_ADS_AD_ACCOUNT_ID
    """
    return os.environ["PINTEREST_ADS_AD_ACCOUNT_ID"]


def pinterest_ads_report(
    metrics: list[str],
    date_range: str,
    granularity: str = "DAY",
    entity_type: str = "CAMPAIGN",
) -> dict:
    """Pull a Pinterest Ads performance report.

    Args:
        metrics: Metrics to retrieve (e.g. OUTBOUND_CLICK, IMPRESSION, SPEND,
            OUTBOUND_CLICK_RATE, CPC, CPM). IMPORTANT: Use OUTBOUND_CLICK, not CLICK —
            Pinterest distinguishes outbound clicks (user leaves Pinterest) from total clicks.
        date_range: Date range as 'YYYY-MM-DD,YYYY-MM-DD' (start,end).
        granularity: Time granularity — DAY, WEEK, or MONTH. Default DAY.
        entity_type: Reporting entity — CAMPAIGN, AD_GROUP, or PIN_PROMOTION. Default CAMPAIGN.

    Returns:
        Dict with 'rows' (list of metric records) and 'granularity'.
    """
    ad_account_id = _get_ad_account_id()
    start, end = date_range.split(",", 1)
    params = {
        "start_date": start.strip(),
        "end_date": end.strip(),
        "granularity": granularity,
        "columns": ",".join(metrics),
        "level": entity_type,
    }
    resp = httpx.get(
        f"{_BASE_URL}/ad_accounts/{ad_account_id}/reports",
        headers=_get_headers(),
        params=params,
    )
    data = resp.json()
    return {"rows": data if isinstance(data, list) else data.get("rows", []), "granularity": granularity}


def pinterest_ads_campaigns(
    status: str | None = None,
) -> dict:
    """List Pinterest Ads campaigns for the ad account.

    Args:
        status: Optional status filter — ACTIVE, PAUSED, ARCHIVED. None returns all.

    Returns:
        Dict with 'campaigns' list.
    """
    ad_account_id = _get_ad_account_id()
    params = {}
    if status:
        params["entity_statuses"] = status
    resp = httpx.get(
        f"{_BASE_URL}/ad_accounts/{ad_account_id}/campaigns",
        headers=_get_headers(),
        params=params,
    )
    data = resp.json()
    return {"campaigns": data.get("items", [])}


def pinterest_ads_create(
    campaign_name: str,
    objective: str,
    budget: float,
    budget_type: str = "DAILY",
) -> dict:
    """Create a new Pinterest Ads campaign.

    Args:
        campaign_name: Name for the campaign (e.g. 'Bot - Pinterest - Discovery - 2026-02').
        objective: Campaign objective — AWARENESS, CONSIDERATION, CONVERSIONS, CATALOG_SALES,
            VIDEO_VIEW, SHOPPING. Pinterest is a visual discovery platform.
        budget: Budget amount in micro-currency (USD cents * 1_000_000).
        budget_type: DAILY or LIFETIME budget. Default DAILY.

    Returns:
        Dict with 'campaign_id' of the newly created campaign.
    """
    ad_account_id = _get_ad_account_id()
    body = {
        "ad_account_id": ad_account_id,
        "name": campaign_name,
        "objective_type": objective,
        "status": "PAUSED",
        "daily_spend_cap": budget if budget_type == "DAILY" else None,
        "lifetime_spend_cap": budget if budget_type == "LIFETIME" else None,
    }
    resp = httpx.post(
        f"{_BASE_URL}/ad_accounts/{ad_account_id}/campaigns",
        headers=_get_headers(),
        json=body,
    )
    data = resp.json()
    return {"campaign_id": data.get("id")}


def pinterest_ads_update(
    campaign_id: str,
    updates: dict,
) -> dict:
    """Update an existing Pinterest Ads campaign.

    Args:
        campaign_id: ID of the Pinterest campaign to update.
        updates: Fields to update (status, daily_spend_cap, name, etc.).

    Returns:
        Dict with 'updated' status and 'campaign_id'.
    """
    ad_account_id = _get_ad_account_id()
    body = {
        "id": campaign_id,
        **updates,
    }
    resp = httpx.patch(
        f"{_BASE_URL}/ad_accounts/{ad_account_id}/campaigns/{campaign_id}",
        headers=_get_headers(),
        json=body,
    )
    resp.json()  # ensure valid response
    return {"updated": True, "campaign_id": campaign_id}


def pinterest_ads_pins(
    campaign_id: str | None = None,
) -> dict:
    """List Pinterest Ads promoted pins (ad creatives).

    Args:
        campaign_id: Optional campaign ID to filter pins. None returns all ad pins.

    Returns:
        Dict with 'pins' list. Pinterest pins have long shelf life (months),
        unlike other platforms where creative fatigue hits faster.
    """
    ad_account_id = _get_ad_account_id()
    params = {}
    if campaign_id:
        params["campaign_ids"] = campaign_id
    resp = httpx.get(
        f"{_BASE_URL}/ad_accounts/{ad_account_id}/ad_pins",
        headers=_get_headers(),
        params=params,
    )
    data = resp.json()
    return {"pins": data.get("items", [])}
