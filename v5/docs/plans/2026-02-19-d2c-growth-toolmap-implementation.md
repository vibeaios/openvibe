# D2C Growth Tool Map + DataOps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the two-role architecture (DataOps + D2C Growth) with 13 operators, ~56 tools, and ~350 tests.

**Architecture:** DataOps provides unified analytics (Mixpanel/GA4/Redshift) and data governance. D2C Growth has 10 operators: 7 ad platforms (Meta/Google/Amazon/TikTok/LinkedIn/Pinterest) + CrossPlatformOps + EmailOps (Klaviyo) + expanded CROps. All operators read data through DataOps, write actions through platform-specific tools.

**Tech Stack:** Python 3.13, openvibe-sdk v1.0.0, LangGraph, httpx, platform SDKs (facebook-business, google-ads, python-amazon-ad-api, klaviyo-api), pytest

**Design Doc:** `v5/docs/plans/2026-02-19-d2c-growth-toolmap-design.md`

**Existing Code Patterns:** See `v5/vibe-inc/src/vibe_inc/roles/d2c_growth/` for Role/Operator/tool/workflow patterns.

---

## Phase 0: DataOps Foundation

> Everything depends on this. DataOps must be built first.

### Task 1: AnalyticsProvider Protocol

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/analytics/__init__.py`
- Test: `v5/vibe-inc/tests/test_analytics_provider.py`

**Step 1: Write the failing test**

```python
# tests/test_analytics_provider.py
def test_analytics_provider_protocol_exists():
    from vibe_inc.tools.analytics import AnalyticsProvider
    assert hasattr(AnalyticsProvider, "query_metrics")
    assert hasattr(AnalyticsProvider, "query_funnel")
    assert hasattr(AnalyticsProvider, "query_events")
    assert hasattr(AnalyticsProvider, "query_cohort")
    assert hasattr(AnalyticsProvider, "query_sql")


def test_analytics_provider_is_protocol():
    from vibe_inc.tools.analytics import AnalyticsProvider
    from typing import runtime_checkable, Protocol
    assert issubclass(AnalyticsProvider, Protocol)
```

**Step 2:** Run: `cd v5/vibe-inc && pytest tests/test_analytics_provider.py -v` — Expected: FAIL (ImportError)

**Step 3: Implement**

```python
# src/vibe_inc/tools/analytics/__init__.py
"""Analytics abstraction layer — unified query interface for Mixpanel, GA4, Redshift."""
from typing import Protocol, runtime_checkable


@runtime_checkable
class AnalyticsProvider(Protocol):
    """Unified analytics interface. Each data source implements this."""

    def query_metrics(
        self,
        metrics: list[str],
        dimensions: list[str] | None = None,
        date_range: str = "last_7d",
        filters: dict | None = None,
    ) -> dict:
        """Aggregated metrics. e.g. sessions, conversions, revenue by channel."""
        ...

    def query_funnel(
        self,
        steps: list[str],
        date_range: str = "last_7d",
        filters: dict | None = None,
    ) -> dict:
        """Funnel drop-off analysis."""
        ...

    def query_events(
        self,
        event_name: str,
        date_range: str = "last_7d",
        properties: list[str] | None = None,
        filters: dict | None = None,
    ) -> dict:
        """Raw event stream with property breakdowns."""
        ...

    def query_cohort(
        self,
        cohort_property: str,
        metric: str,
        date_range: str = "last_90d",
    ) -> dict:
        """Cohort analysis. e.g. retention by signup week."""
        ...

    def query_sql(self, sql: str) -> dict:
        """Raw SQL. Redshift only. Errors on other providers."""
        ...
```

**Step 4:** Run: `cd v5/vibe-inc && pytest tests/test_analytics_provider.py -v` — Expected: PASS

**Step 5:** `git add src/vibe_inc/tools/analytics/__init__.py tests/test_analytics_provider.py && git commit -m "feat(dataops): add AnalyticsProvider protocol"`

---

### Task 2: MixpanelProvider

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/analytics/mixpanel.py`
- Test: `v5/vibe-inc/tests/test_mixpanel_provider.py`

**Context:** No read SDK exists. Build custom httpx wrapper against Mixpanel Query API. Auth: HTTP Basic with service_account_username:service_account_secret.

**Step 1: Write failing tests**

```python
# tests/test_mixpanel_provider.py
from unittest.mock import patch, MagicMock
import json


def test_mixpanel_provider_implements_protocol():
    from vibe_inc.tools.analytics import AnalyticsProvider
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider
    provider = MixpanelProvider(
        project_id="test", service_account="user", service_secret="secret"
    )
    assert isinstance(provider, AnalyticsProvider)


def test_query_metrics_calls_insights_api():
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider

    provider = MixpanelProvider(
        project_id="123", service_account="user", service_secret="secret"
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": {"values": {"event": {"2026-02-19": 100}}}}

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = provider.query_metrics(metrics=["event_count"], date_range="last_7d")

    assert "results" in result
    mock_get.assert_called_once()
    # Verify auth header
    call_kwargs = mock_get.call_args
    assert "auth" in call_kwargs.kwargs or call_kwargs.kwargs.get("headers", {}).get("Authorization")


def test_query_funnel_calls_funnels_api():
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider

    provider = MixpanelProvider(
        project_id="123", service_account="user", service_secret="secret"
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "meta": {"dates": ["2026-02-19"]},
        "data": {"2026-02-19": {"steps": [1000, 500, 200, 50]}}
    }

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = provider.query_funnel(
            steps=["page_view", "add_to_cart", "checkout", "purchase"],
            date_range="last_7d",
        )

    assert "data" in result


def test_query_events_calls_export_api():
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider

    provider = MixpanelProvider(
        project_id="123", service_account="user", service_secret="secret"
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"event":"purchase","properties":{"revenue":99.0}}\n'

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = provider.query_events(event_name="purchase", date_range="last_7d")

    assert "events" in result


def test_query_sql_raises_not_supported():
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider

    provider = MixpanelProvider(
        project_id="123", service_account="user", service_secret="secret"
    )
    import pytest
    with pytest.raises(NotImplementedError):
        provider.query_sql("SELECT 1")
```

**Step 2:** Run: `cd v5/vibe-inc && pytest tests/test_mixpanel_provider.py -v` — Expected: FAIL

**Step 3: Implement**

```python
# src/vibe_inc/tools/analytics/mixpanel.py
"""Mixpanel analytics provider — custom httpx wrapper for Query API.

No read SDK exists. Uses direct HTTP against:
- /api/2.0/insights — segmentation/metrics
- /api/2.0/funnels — funnel analysis
- /api/2.0/export — raw event export
- /api/2.0/retention — cohort retention
Auth: HTTP Basic with service_account:service_secret
"""
import httpx
from datetime import datetime, timedelta


_BASE = "https://mixpanel.com"


def _parse_date_range(date_range: str) -> tuple[str, str]:
    """Convert date_range string to (from_date, to_date) in YYYY-MM-DD."""
    if "," in date_range:
        parts = date_range.split(",", 1)
        return parts[0].strip(), parts[1].strip()
    days = {"last_7d": 7, "last_28d": 28, "last_90d": 90, "last_24h": 1}
    n = days.get(date_range, 7)
    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=n)).strftime("%Y-%m-%d")
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
            "funnel_id": ",".join(steps),  # or use event names
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


import json  # moved to top in real implementation
```

**Step 4:** Run tests — Expected: PASS

**Step 5:** Commit: `git commit -m "feat(dataops): add MixpanelProvider with httpx wrapper"`

---

### Task 3: GA4Provider (refactor)

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/analytics/ga4.py`
- Test: `v5/vibe-inc/tests/test_ga4_provider.py`

**Context:** Refactor existing `tools/ga4.py` into the AnalyticsProvider pattern. Keep the old `ga4_read` function as a thin wrapper for backward compat during migration.

**Step 1: Write failing tests** — same pattern as MixpanelProvider but wrapping `google.analytics.data_v1beta`. 4 tests: implements protocol, query_metrics mocks BetaAnalyticsDataClient, query_funnel, query_sql raises NotImplementedError.

**Step 2-5:** Implement, verify, commit.

---

### Task 4: RedshiftProvider

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/analytics/redshift.py`
- Test: `v5/vibe-inc/tests/test_redshift_provider.py`

**Context:** Uses `redshift_connector` or `psycopg2`. All query methods translate to SQL. `query_sql` is the native method; others generate SQL from params.

**Step 1: Write failing tests** — 5 tests: implements protocol, query_metrics generates correct SQL, query_funnel generates funnel SQL, query_sql executes raw, connection uses env vars.

**Step 2-5:** Implement, verify, commit.

**Dependencies to add to pyproject.toml:**
```toml
httpx = ">=0.27"
redshift-connector = ">=2.1"
```

---

### Task 5: Analytics Tool Functions

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/analytics_tools.py`
- Test: `v5/vibe-inc/tests/test_analytics_tools.py`

**Context:** Expose analytics provider methods as plain tool functions that can be passed to `@agent_node(tools=[...])`. These are the tools all operators will use.

**Step 1: Write failing tests**

```python
# tests/test_analytics_tools.py
def test_analytics_query_metrics_has_docstring():
    from vibe_inc.tools.analytics_tools import analytics_query_metrics
    assert analytics_query_metrics.__doc__ is not None


def test_analytics_query_metrics_returns_dict():
    from vibe_inc.tools.analytics_tools import analytics_query_metrics
    from unittest.mock import patch, MagicMock

    mock_provider = MagicMock()
    mock_provider.query_metrics.return_value = {"results": {}}

    with patch("vibe_inc.tools.analytics_tools._get_provider", return_value=mock_provider):
        result = analytics_query_metrics(metrics=["sessions"], date_range="last_7d")

    assert isinstance(result, dict)


def test_analytics_query_funnel_returns_dict():
    from vibe_inc.tools.analytics_tools import analytics_query_funnel
    from unittest.mock import patch, MagicMock

    mock_provider = MagicMock()
    mock_provider.query_funnel.return_value = {"data": {}}

    with patch("vibe_inc.tools.analytics_tools._get_provider", return_value=mock_provider):
        result = analytics_query_funnel(steps=["view", "cart", "purchase"])

    assert isinstance(result, dict)


def test_analytics_query_sql_returns_dict():
    from vibe_inc.tools.analytics_tools import analytics_query_sql
    from unittest.mock import patch, MagicMock

    mock_provider = MagicMock()
    mock_provider.query_sql.return_value = {"rows": []}

    with patch("vibe_inc.tools.analytics_tools._get_redshift", return_value=mock_provider):
        result = analytics_query_sql(sql="SELECT 1")

    assert isinstance(result, dict)
```

**Step 3: Implement**

```python
# src/vibe_inc/tools/analytics_tools.py
"""Analytics tool functions — exposed to all operators via @agent_node(tools=[...]).

These delegate to the configured AnalyticsProvider (Mixpanel by default, GA4 for traffic).
"""
import os


def _get_provider():
    """Get the default analytics provider (Mixpanel)."""
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider
    return MixpanelProvider(
        project_id=os.environ.get("MIXPANEL_PROJECT_ID", ""),
        service_account=os.environ.get("MIXPANEL_SERVICE_ACCOUNT", ""),
        service_secret=os.environ.get("MIXPANEL_SERVICE_SECRET", ""),
    )


def _get_redshift():
    """Get the Redshift provider for raw SQL."""
    from vibe_inc.tools.analytics.redshift import RedshiftProvider
    return RedshiftProvider()


def analytics_query_metrics(
    metrics: list[str],
    dimensions: list[str] | None = None,
    date_range: str = "last_7d",
    filters: dict | None = None,
) -> dict:
    """Query aggregated metrics from analytics (Mixpanel).

    Args:
        metrics: Metric names to query (e.g. sessions, conversions, revenue).
        dimensions: Optional dimension breakdowns (e.g. source, product).
        date_range: Date range — last_7d, last_28d, last_90d, or YYYY-MM-DD,YYYY-MM-DD.
        filters: Optional filters as dict.

    Returns:
        Dict with 'results' and 'date_range'.
    """
    return _get_provider().query_metrics(metrics, dimensions, date_range, filters)


def analytics_query_funnel(
    steps: list[str],
    date_range: str = "last_7d",
    filters: dict | None = None,
) -> dict:
    """Query funnel drop-off analysis from analytics (Mixpanel).

    Args:
        steps: Ordered list of funnel step event names.
        date_range: Date range.
        filters: Optional filters.

    Returns:
        Dict with funnel data including per-step counts and drop-off rates.
    """
    return _get_provider().query_funnel(steps, date_range, filters)


def analytics_query_events(
    event_name: str,
    date_range: str = "last_7d",
    properties: list[str] | None = None,
    filters: dict | None = None,
) -> dict:
    """Query raw event data from analytics (Mixpanel).

    Args:
        event_name: Event name to query.
        date_range: Date range.
        properties: Event properties to include.
        filters: Optional filters.

    Returns:
        Dict with 'events' list.
    """
    return _get_provider().query_events(event_name, date_range, properties, filters)


def analytics_query_cohort(
    cohort_property: str,
    metric: str,
    date_range: str = "last_90d",
) -> dict:
    """Query cohort retention analysis from analytics (Mixpanel).

    Args:
        cohort_property: Property to define cohorts (e.g. signup_week).
        metric: Metric to measure retention against.
        date_range: Date range.

    Returns:
        Dict with cohort retention data.
    """
    return _get_provider().query_cohort(cohort_property, metric, date_range)


def analytics_query_sql(sql: str) -> dict:
    """Execute raw SQL against Redshift data warehouse.

    Args:
        sql: SQL query string.

    Returns:
        Dict with 'rows' and 'columns'.
    """
    return _get_redshift().query_sql(sql)
```

**Step 4-5:** Run tests, commit.

---

### Task 6: DataOps Role — CatalogOps Operator

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/roles/data_ops/__init__.py`
- Create: `v5/vibe-inc/src/vibe_inc/roles/data_ops/catalog_ops.py`
- Test: `v5/vibe-inc/tests/test_catalog_ops.py`

**Step 1: Write failing tests**

```python
# tests/test_catalog_ops.py
from openvibe_sdk.llm import LLMResponse


def _text_response(content="done"):
    return LLMResponse(content=content, stop_reason="end_turn")


class FakeLLM:
    def __init__(self, responses=None):
        self.responses = list(responses or [_text_response()])
        self.calls = []
    def call(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def test_catalog_ops_is_operator():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    from openvibe_sdk import Operator
    assert issubclass(CatalogOps, Operator)
    assert CatalogOps.operator_id == "catalog_ops"


def test_schema_audit_is_agent_node():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    assert hasattr(CatalogOps.schema_audit, "_is_agent_node")
    assert CatalogOps.schema_audit._is_agent_node is True


def test_field_mapping_is_agent_node():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    assert hasattr(CatalogOps.field_mapping, "_is_agent_node")


def test_coverage_report_is_agent_node():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    assert hasattr(CatalogOps.coverage_report, "_is_agent_node")


def test_schema_audit_output_key():
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    llm = FakeLLM([_text_response("Audit complete")])
    op = CatalogOps(llm=llm)
    result = op.schema_audit({})
    assert "audit_result" in result
```

**Step 3: Implement** — Follow the same Operator pattern as AdOps. 3 agent_nodes: schema_audit, field_mapping, coverage_report. Tools: `catalog_read`, `catalog_update` (shared memory read/write wrappers).

**Step 4-5:** Run tests, commit.

---

### Task 7: DataOps Role — QualityOps Operator

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/roles/data_ops/quality_ops.py`
- Test: `v5/vibe-inc/tests/test_quality_ops.py`

Same pattern as Task 6. 3 agent_nodes: freshness_monitor, discrepancy_report, credibility_assessment. Tools: analytics_query_metrics (from Task 5), shared_memory read/write.

---

### Task 8: DataOps Role — AccessOps Operator

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/roles/data_ops/access_ops.py`
- Test: `v5/vibe-inc/tests/test_access_ops.py`

3 agent_nodes: route_query, build_report, cache_refresh. Tools: all analytics_* functions from Task 5, shared_memory.

---

### Task 9: DataOps Role Wiring

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/roles/data_ops/__init__.py` (Role class)
- Create: `v5/vibe-inc/src/vibe_inc/roles/data_ops/workflows.py`
- Modify: `v5/vibe-inc/src/vibe_inc/main.py` (add DataOps to runtime)
- Test: `v5/vibe-inc/tests/test_data_ops.py`
- Test: `v5/vibe-inc/tests/test_data_ops_workflows.py`

**Step 1: Write failing tests**

```python
# tests/test_data_ops.py
def test_data_ops_role_exists():
    from vibe_inc.roles.data_ops import DataOps
    assert DataOps.role_id == "data_ops"
    assert len(DataOps.operators) == 3  # CatalogOps, QualityOps, AccessOps


def test_data_ops_has_soul():
    from vibe_inc.roles.data_ops import DataOps
    assert "source of truth" in DataOps.soul.lower()
```

```python
# tests/test_data_ops_workflows.py
from openvibe_sdk.llm import LLMResponse

class FakeLLM:
    def call(self, **kwargs):
        return LLMResponse(content="done", stop_reason="end_turn")

def test_data_catalog_audit_workflow_compiles():
    from vibe_inc.roles.data_ops.workflows import create_data_catalog_audit_graph
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    op = CatalogOps(llm=FakeLLM())
    graph = create_data_catalog_audit_graph(op)
    assert graph is not None
```

**Step 3: Implement** — DataOps Role class, workflow factories (same StateGraph pattern), register in main.py.

**Step 4-5:** Run tests, commit.

---

### Task 10: Shared Memory Bootstrap — Data Catalog

**Files:**
- Create: `v5/vibe-inc/data/shared_memory/data/catalog.yaml`
- Create: `v5/vibe-inc/data/shared_memory/data/field_mapping.yaml`
- Test: `v5/vibe-inc/tests/test_data_catalog_bootstrap.py`

**Step 1: Write failing test**

```python
# tests/test_data_catalog_bootstrap.py
import os
import yaml

_MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "shared_memory")

def test_catalog_yaml_exists():
    path = os.path.join(_MEMORY_DIR, "data", "catalog.yaml")
    assert os.path.exists(path)
    data = yaml.safe_load(open(path))
    assert "sources" in data
    for source in ["mixpanel", "ga4", "redshift", "shopify"]:
        assert source in data["sources"]

def test_field_mapping_yaml_exists():
    path = os.path.join(_MEMORY_DIR, "data", "field_mapping.yaml")
    assert os.path.exists(path)
    data = yaml.safe_load(open(path))
    assert "conversion" in data
    assert "revenue" in data
    assert "new_customer" in data
```

**Step 3:** Create the YAML files per design doc §3.1.

**Step 4-5:** Run tests, commit.

---

## Phase 1: MetaAdOps Refactor (Establishes Pattern for All Ad Operators)

> This phase refactors the existing AdOps into MetaAdOps and establishes the pattern.

### Task 11: Refactor AdOps → MetaAdOps

**Files:**
- Rename: `roles/d2c_growth/ad_ops.py` → `roles/d2c_growth/meta_ad_ops.py`
- Modify: `roles/d2c_growth/__init__.py` (update imports)
- Modify: `main.py` (update workflow registrations)
- Test: `v5/vibe-inc/tests/test_meta_ad_ops.py` (rename + extend)

**Step 1:** Rename file and class: `AdOps` → `MetaAdOps`, `operator_id = "meta_ad_ops"`.

**Step 2:** Add 2 new agent_nodes: `audience_refresh` and `creative_fatigue_check` (per design doc §4.1).

**Step 3:** Add 2 new tool functions: `meta_ads_rules` and `meta_audiences` in `tools/ads/meta_ads.py`.

**Step 4:** Move `tools/meta_ads.py` → `tools/ads/meta_ads.py` (new directory structure).

**Step 5:** Update all imports, run existing tests (should still pass with minor path changes).

**Step 6:** Write new tests for the 2 new agent_nodes + 2 new tools.

**Step 7:** Commit.

---

### Task 12: Meta Workflow Expansion

**Files:**
- Modify: `roles/d2c_growth/workflows.py`
- Test: Update `tests/test_workflows.py`

Add `meta_audience_refresh` workflow. Update existing workflow names from `create_daily_optimize_graph` → `create_meta_daily_optimize_graph` etc.

---

### Task 13: Platform Benchmarks Shared Memory

**Files:**
- Create: `v5/vibe-inc/data/shared_memory/performance/platform_benchmarks.yaml`
- Test: `v5/vibe-inc/tests/test_platform_benchmarks_bootstrap.py`

Content per design doc §9 — targets for all 7 platforms + cross-platform allocation.

---

## Phase 2: Google + Amazon Ad Operators

> Each ad platform operator follows the same pattern established in Phase 1.

### Ad Operator Implementation Pattern (applies to Tasks 14-23)

For each platform operator, the implementation steps are identical:

**A. Create tool functions** (`tools/ads/{platform}_ads.py`):
- Each tool is a plain Python function with docstring + type hints
- Mock the SDK client via `_get_client()` helper (same pattern as `_get_account()` in meta_ads.py)
- Write ~5 tool tests with `unittest.mock.patch` on the client

**B. Create operator** (`roles/d2c_growth/{platform}_ad_ops.py`):
- Inherit `Operator`, set `operator_id`
- 4-5 `@agent_node` methods with tools and output_key
- Write ~5 operator tests checking `_is_agent_node`, output keys, docstrings

**C. Create workflows** (add to `roles/d2c_growth/workflows.py`):
- TypedDict state classes + factory functions
- Write ~3-4 workflow compile + invoke tests

**D. Register in runtime** (update `main.py`):
- Import operator, import workflow factories, register

**E. Update role** (update `roles/d2c_growth/__init__.py`):
- Add operator to `operators` list

### Task 14: Google Ads Tools

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/ads/google_ads.py`
- Test: `v5/vibe-inc/tests/test_google_ads_tools.py`

5 tool functions: `google_ads_query`, `google_ads_mutate`, `google_ads_budget`, `google_ads_recommendations`, `google_ads_conversions`.

**Key implementation detail:** Uses `google-ads` SDK v29.x. Load config from dict via `GoogleAdsClient.load_from_dict()`. Cost values are in micros (÷1,000,000).

```python
def _get_client():
    from google.ads.googleads.client import GoogleAdsClient
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus": True,
    })
```

~7 tests mocking GoogleAdsClient.

### Task 15: GoogleAdOps Operator

Same pattern as MetaAdOps. 5 agent_nodes: campaign_create, daily_optimize, search_term_mining, weekly_report, recommendations_review. ~7 tests.

### Task 16: Amazon Ads Tools

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/ads/amazon_ads.py`
- Test: `v5/vibe-inc/tests/test_amazon_ads_tools.py`

6 tool functions. **Key detail:** Reporting is async 3-step. The `amazon_ads_report` function must handle request → poll → download internally.

```python
def amazon_ads_report(
    ad_product: str,
    report_type: str,
    columns: list[str],
    date_range: str,
) -> dict:
    """Request, poll, and download an Amazon Ads async report.

    Args:
        ad_product: SPONSORED_PRODUCTS, SPONSORED_BRANDS, or SPONSORED_DISPLAY.
        report_type: Report type (spSearchTerm, spCampaigns, etc.).
        columns: Metrics to include.
        date_range: YYYY-MM-DD,YYYY-MM-DD format.

    Returns:
        Dict with 'rows' (list of dicts from the report).
    """
    client = _get_client()
    # Step 1: Request
    report_id = client.post_report(body={...})
    # Step 2: Poll (with tenacity retry)
    # Step 3: Download + decompress
    ...
```

~8 tests mocking the 3-step flow.

### Task 17: AmazonAdOps Operator

5 agent_nodes. ~7 tests.

---

## Phase 3: TikTok + LinkedIn + Pinterest

### Task 18: TikTok Ads Tools

Direct `httpx` — no SDK. **Key detail:** Advertiser access tokens are non-expiring (corrected from design). 6 tools. ~7 tests.

### Task 19: TikTokAdOps Operator

5 agent_nodes. **Key rule:** Learning phase guard in daily_optimize. ~7 tests.

### Task 20: LinkedIn Ads Tools

Direct `httpx` with Rest.li headers. **Key detail:** `Linkedin-Version: YYYYMM` header required on every request. 6 tools. ~7 tests.

### Task 21: LinkedInAdOps Operator

5 agent_nodes. ~7 tests.

### Task 22: Pinterest Ads Tools

Use `pinterest-api-sdk` for CRUD, `httpx` for async reporting. **Key detail:** Outbound clicks, not total clicks. 5 tools. ~6 tests.

### Task 23: PinterestAdOps Operator

4 agent_nodes. ~6 tests.

---

## Phase 4: Email + CRO

### Task 24: Klaviyo Tools

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/commerce/klaviyo.py`
- Test: `v5/vibe-inc/tests/test_klaviyo_tools.py`

Uses `klaviyo-api` SDK (v22.x). Simple API key auth. 6 tools: campaigns, flows, segments, metrics, profiles, catalogs. ~7 tests.

### Task 25: EmailOps Operator

5 agent_nodes: campaign_create, flow_optimize, segment_refresh, lifecycle_report, list_hygiene. ~7 tests.

### Task 26: EmailOps Workflows

4 workflows. ~4 tests.

### Task 27: Shopify Tools Expansion

**Files:**
- Modify: `v5/vibe-inc/src/vibe_inc/tools/commerce/shopify.py` (move from tools/shopify.py)
- Test: `v5/vibe-inc/tests/test_shopify_tools_expanded.py`

Add 4 new functions: `shopify_products`, `shopify_orders`, `shopify_collections`, `shopify_discounts`. Keep existing `shopify_page_read` and `shopify_page_update`. ~8 tests.

### Task 28: A/B Testing Tools (VWO)

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/optimization/ab_testing.py`
- Test: `v5/vibe-inc/tests/test_ab_testing_tools.py`

Direct `httpx` against VWO REST API. 2 tools: `ab_test_read`, `ab_test_manage`. ~4 tests.

### Task 29: CROps Expansion

**Files:**
- Modify: `v5/vibe-inc/src/vibe_inc/roles/d2c_growth/cro_ops.py`
- Test: `v5/vibe-inc/tests/test_cro_ops_expanded.py`

Add 3 new agent_nodes: product_optimize, discount_strategy, conversion_report. Update existing nodes to use analytics_* tools instead of ga4_read. ~8 tests.

### Task 30: CROps Workflows Update

Update existing + add new workflows. ~5 tests.

---

## Phase 5: Cross-Platform Orchestration

### Task 31: CrossPlatformOps Tools

**Files:**
- Create: `v5/vibe-inc/src/vibe_inc/tools/ads/unified_metrics.py`
- Test: `v5/vibe-inc/tests/test_unified_metrics_tools.py`

3 tools: `unified_metrics_read` (aggregates from all platforms), `budget_allocator`, shared_memory. ~5 tests.

### Task 32: CrossPlatformOps Operator

3 agent_nodes: unified_cac_report, budget_rebalance, platform_health_check. ~5 tests.

### Task 33: CrossPlatformOps Workflows

3 workflows. ~3 tests.

### Task 34: D2C Growth Role Update

**Files:**
- Modify: `v5/vibe-inc/src/vibe_inc/roles/d2c_growth/__init__.py`
- Modify: `v5/vibe-inc/src/vibe_inc/main.py`

Update D2CGrowth to include all 10 operators. Update soul. Register all workflows. Update existing tests.

---

## Phase 6: Validation

### Task 35: Integration Tests

**Files:**
- Create: `v5/vibe-inc/tests/test_integration_dataops_growth.py`

Test DataOps ↔ D2C Growth interaction: operator calls analytics tools, gets result, uses in decision. ~15 tests.

### Task 36: Email + CRO Benchmarks

**Files:**
- Create: `v5/vibe-inc/data/shared_memory/performance/email_benchmarks.yaml`
- Create: `v5/vibe-inc/data/shared_memory/performance/cro_benchmarks.yaml`
- Test: `v5/vibe-inc/tests/test_benchmarks_bootstrap.py`

### Task 37: Final Wiring + Docs Update

- Update `v5/vibe-inc/pyproject.toml` with all new dependencies
- Run full test suite: `cd v5/vibe-inc && pytest tests/ -v`
- Target: ~350+ tests passing
- Update PROGRESS.md, DESIGN.md

---

## Dependencies Graph

```
Phase 0 (DataOps) ──┐
                     ├── Phase 1 (Meta refactor) ──┐
                     │                              ├── Phase 2 (Google + Amazon)
                     │                              ├── Phase 3 (TikTok + LinkedIn + Pinterest)
                     │                              └── Phase 4 (Email + CRO)
                     │                                        │
                     └────────────────────────────────────────├── Phase 5 (CrossPlatform)
                                                              └── Phase 6 (Validation)
```

Phases 2, 3, 4 can run in parallel after Phase 1 establishes the pattern.

---

## pyproject.toml Final Dependencies

```toml
dependencies = [
    "openvibe-sdk>=1.0.0",
    "openvibe-runtime>=1.0.0",
    # Ad Platforms
    "facebook-business>=22.0",
    "google-ads>=25.0.0",
    "python-amazon-ad-api>=0.4.3",
    "httpx>=0.27",
    # Analytics
    "google-analytics-data>=0.18.0",
    "redshift-connector>=2.1",
    # Commerce + Email
    "ShopifyAPI>=12.0.0",
    "klaviyo-api>=9.0",
    # Infrastructure
    "tenacity>=8.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
]
```

---

## Test Count Estimate

| Phase | Tasks | Est. Tests |
|-------|-------|-----------|
| Phase 0: DataOps | 1-10 | ~45 |
| Phase 1: Meta refactor | 11-13 | ~20 |
| Phase 2: Google + Amazon | 14-17 | ~60 |
| Phase 3: TikTok + LinkedIn + Pinterest | 18-23 | ~80 |
| Phase 4: Email + CRO | 24-30 | ~45 |
| Phase 5: CrossPlatform | 31-34 | ~20 |
| Phase 6: Validation | 35-37 | ~20 |
| **Total** | **37** | **~290** |

Combined with existing 51 vibe-inc tests: **~341 total**.
