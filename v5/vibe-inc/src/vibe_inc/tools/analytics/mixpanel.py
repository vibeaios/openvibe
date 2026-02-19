"""Mixpanel analytics provider — custom httpx wrapper for Query API.

No read SDK exists. Uses direct HTTP against:
- /api/2.0/insights — segmentation/metrics
- /api/2.0/funnels — funnel analysis
- /api/2.0/export — raw event export
- /api/2.0/retention — cohort retention
Auth: HTTP Basic with service_account:service_secret
"""
import json
from datetime import UTC, datetime, timedelta

import httpx


_BASE = "https://mixpanel.com"


def _parse_date_range(date_range: str) -> tuple[str, str]:
    """Convert date_range string to (from_date, to_date) in YYYY-MM-DD."""
    if "," in date_range:
        parts = date_range.split(",", 1)
        return parts[0].strip(), parts[1].strip()
    days = {"last_7d": 7, "last_28d": 28, "last_90d": 90, "last_24h": 1}
    n = days.get(date_range, 7)
    end = datetime.now(UTC).strftime("%Y-%m-%d")
    start = (datetime.now(UTC) - timedelta(days=n)).strftime("%Y-%m-%d")
    return start, end


class MixpanelProvider:
    """Mixpanel analytics provider using Query API."""

    def __init__(self, project_id: str, service_account: str, service_secret: str):
        self.project_id = project_id
        self._auth = (service_account, service_secret)

    def query_metrics(
        self,
        metrics: list[str],
        dimensions: list[str] | None = None,
        date_range: str = "last_7d",
        filters: dict | None = None,
    ) -> dict:
        from_date, to_date = _parse_date_range(date_range)
        params = {
            "project_id": self.project_id,
            "from_date": from_date,
            "to_date": to_date,
        }
        if metrics:
            params["event"] = json.dumps(metrics)
        resp = httpx.get(
            f"{_BASE}/api/2.0/insights",
            params=params,
            auth=self._auth,
        )
        resp.raise_for_status()
        return {"results": resp.json(), "date_range": date_range}

    def query_funnel(
        self,
        steps: list[str],
        date_range: str = "last_7d",
        filters: dict | None = None,
    ) -> dict:
        from_date, to_date = _parse_date_range(date_range)
        params = {
            "project_id": self.project_id,
            "from_date": from_date,
            "to_date": to_date,
            "funnel_id": ",".join(steps),
        }
        resp = httpx.get(
            f"{_BASE}/api/2.0/funnels",
            params=params,
            auth=self._auth,
        )
        resp.raise_for_status()
        return {"data": resp.json(), "steps": steps, "date_range": date_range}

    def query_events(
        self,
        event_name: str,
        date_range: str = "last_7d",
        properties: list[str] | None = None,
        filters: dict | None = None,
    ) -> dict:
        from_date, to_date = _parse_date_range(date_range)
        params = {
            "project_id": self.project_id,
            "from_date": from_date,
            "to_date": to_date,
            "event": json.dumps([event_name]),
        }
        resp = httpx.get(
            f"{_BASE}/api/2.0/export",
            params=params,
            auth=self._auth,
        )
        resp.raise_for_status()
        events = []
        for line in resp.text.strip().split("\n"):
            if line:
                events.append(json.loads(line))
        return {"events": events, "event_name": event_name, "date_range": date_range}

    def query_cohort(
        self,
        cohort_property: str,
        metric: str,
        date_range: str = "last_90d",
    ) -> dict:
        from_date, to_date = _parse_date_range(date_range)
        params = {
            "project_id": self.project_id,
            "from_date": from_date,
            "to_date": to_date,
            "born_event": cohort_property,
            "event": metric,
        }
        resp = httpx.get(
            f"{_BASE}/api/2.0/retention",
            params=params,
            auth=self._auth,
        )
        resp.raise_for_status()
        return {"data": resp.json(), "cohort_property": cohort_property, "date_range": date_range}

    def query_sql(self, sql: str) -> dict:
        raise NotImplementedError("Mixpanel does not support raw SQL. Use RedshiftProvider.")
