from unittest.mock import patch, MagicMock


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
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = provider.query_metrics(metrics=["event_count"], date_range="last_7d")

    assert "results" in result
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs["auth"] == ("user", "secret")


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
    mock_response.raise_for_status = MagicMock()

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
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        result = provider.query_events(event_name="purchase", date_range="last_7d")

    assert "events" in result


def test_query_sql_raises_not_supported():
    from vibe_inc.tools.analytics.mixpanel import MixpanelProvider
    import pytest

    provider = MixpanelProvider(
        project_id="123", service_account="user", service_secret="secret"
    )
    with pytest.raises(NotImplementedError):
        provider.query_sql("SELECT 1")
