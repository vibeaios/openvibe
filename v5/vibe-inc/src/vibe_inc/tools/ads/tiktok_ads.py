"""TikTok Ads API tools for D2C Growth role."""
import os

import httpx

_BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"


def _get_headers():
    """Return authorization headers for TikTok Ads API.

    Requires: TIKTOK_ADS_ACCESS_TOKEN
    """
    return {"Access-Token": os.environ["TIKTOK_ADS_ACCESS_TOKEN"]}


def _get_advertiser_id():
    """Return the TikTok Ads advertiser ID from environment."""
    return os.environ["TIKTOK_ADS_ADVERTISER_ID"]


def tiktok_ads_report(
    metrics: list[str],
    dimensions: list[str],
    date_range: str,
    data_level: str = "AUCTION_AD",
) -> dict:
    """Pull a TikTok Ads performance report.

    Args:
        metrics: Metrics to retrieve (e.g. spend, impressions, clicks, cpc, cpm, ctr,
            conversion, cost_per_conversion).
        dimensions: Dimensions to group by (e.g. ad_id, campaign_id, stat_time_day).
        date_range: Date range as 'YYYY-MM-DD,YYYY-MM-DD' (start,end).
        data_level: Reporting level — AUCTION_AD, AUCTION_ADGROUP, AUCTION_CAMPAIGN,
            or AUCTION_ADVERTISER. Default AUCTION_AD.

    Returns:
        Dict with 'rows' (list of metric records) and 'data_level'.
    """
    start, end = date_range.split(",", 1)
    body = {
        "advertiser_id": _get_advertiser_id(),
        "report_type": "BASIC",
        "data_level": data_level,
        "dimensions": dimensions,
        "metrics": metrics,
        "start_date": start.strip(),
        "end_date": end.strip(),
    }
    resp = httpx.post(
        f"{_BASE_URL}/report/integrated/get/",
        headers=_get_headers(),
        json=body,
    )
    data = resp.json().get("data", {})
    return {"rows": data.get("list", []), "data_level": data_level}


def tiktok_ads_campaigns(
    status: str | None = None,
) -> dict:
    """List TikTok Ads campaigns.

    Args:
        status: Optional filter — CAMPAIGN_STATUS_ENABLE, CAMPAIGN_STATUS_DISABLE,
            CAMPAIGN_STATUS_DELETE, etc. None returns all.

    Returns:
        Dict with 'campaigns' list.
    """
    params = {"advertiser_id": _get_advertiser_id()}
    if status:
        params["filtering"] = {"status": status}
    resp = httpx.get(
        f"{_BASE_URL}/campaign/get/",
        headers=_get_headers(),
        params=params,
    )
    data = resp.json().get("data", {})
    return {"campaigns": data.get("list", [])}


def tiktok_ads_create(
    campaign_name: str,
    objective: str,
    budget: float,
    budget_mode: str = "BUDGET_MODE_DAY",
) -> dict:
    """Create a new TikTok Ads campaign.

    Args:
        campaign_name: Name for the campaign (e.g. 'Bot - TikTok - Foundation - 2026-02').
        objective: Campaign objective — CONVERSIONS, TRAFFIC, REACH, VIDEO_VIEWS, etc.
        budget: Budget amount in USD.
        budget_mode: BUDGET_MODE_DAY (daily) or BUDGET_MODE_TOTAL (lifetime).

    Returns:
        Dict with 'campaign_id' of the newly created campaign.
    """
    body = {
        "advertiser_id": _get_advertiser_id(),
        "campaign_name": campaign_name,
        "objective_type": objective,
        "budget": budget,
        "budget_mode": budget_mode,
    }
    resp = httpx.post(
        f"{_BASE_URL}/campaign/create/",
        headers=_get_headers(),
        json=body,
    )
    data = resp.json().get("data", {})
    return {"campaign_id": data.get("campaign_id")}


def tiktok_ads_update(
    campaign_id: str,
    updates: dict,
) -> dict:
    """Update an existing TikTok Ads campaign.

    Args:
        campaign_id: ID of the campaign to update.
        updates: Fields to update (budget, campaign_name, status, etc.).

    Returns:
        Dict with 'updated' status and 'campaign_id'.
    """
    body = {
        "advertiser_id": _get_advertiser_id(),
        "campaign_id": campaign_id,
        **updates,
    }
    resp = httpx.post(
        f"{_BASE_URL}/campaign/update/",
        headers=_get_headers(),
        json=body,
    )
    resp.json()  # ensure valid response
    return {"updated": True, "campaign_id": campaign_id}


def tiktok_ads_creatives(
    campaign_id: str | None = None,
) -> dict:
    """List TikTok Ads creatives (ad-level assets).

    Args:
        campaign_id: Optional campaign ID to filter creatives.

    Returns:
        Dict with 'creatives' list.
    """
    params = {"advertiser_id": _get_advertiser_id()}
    if campaign_id:
        params["filtering"] = {"campaign_ids": [campaign_id]}
    resp = httpx.get(
        f"{_BASE_URL}/creative/get/",
        headers=_get_headers(),
        params=params,
    )
    data = resp.json().get("data", {})
    return {"creatives": data.get("list", [])}


def tiktok_ads_audiences(
    action: str = "list",
    audience_id: str | None = None,
) -> dict:
    """Manage TikTok Ads custom audiences.

    Args:
        action: Action — list, read, or refresh.
        audience_id: Required for read/refresh actions.

    Returns:
        Dict with 'audiences' list or single audience data.
    """
    headers = _get_headers()
    advertiser_id = _get_advertiser_id()

    if action == "list":
        resp = httpx.get(
            f"{_BASE_URL}/dmp/custom_audience/list/",
            headers=headers,
            params={"advertiser_id": advertiser_id},
        )
        data = resp.json().get("data", {})
        return {"audiences": data.get("list", [])}
    elif action == "read" and audience_id:
        resp = httpx.get(
            f"{_BASE_URL}/dmp/custom_audience/get/",
            headers=headers,
            params={"advertiser_id": advertiser_id, "custom_audience_ids": [audience_id]},
        )
        data = resp.json().get("data", {})
        audiences = data.get("list", [])
        return {"audiences": audiences}
    elif action == "refresh" and audience_id:
        resp = httpx.post(
            f"{_BASE_URL}/dmp/custom_audience/update/",
            headers=headers,
            json={"advertiser_id": advertiser_id, "custom_audience_id": audience_id},
        )
        return {"audiences": [{"audience_id": audience_id, "refreshed": True}]}
    return {"audiences": [], "error": "Invalid action or missing audience_id"}
