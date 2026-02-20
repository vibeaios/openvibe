"""Tests for web search and fetch tools."""
from unittest.mock import MagicMock, patch


# --- web_search tests ---


def test_web_search_calls_brave_api():
    """web_search sends correct request to Brave Search API."""
    from vibe_inc.tools.web.search import web_search

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Owl Labs", "url": "https://owllabs.com", "description": "Meeting owl"},
                {"title": "Otter.ai", "url": "https://otter.ai", "description": "AI notes"},
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"BRAVE_SEARCH_API_KEY": "test-key"}), \
         patch("httpx.get", return_value=mock_response) as mock_get:
        result = web_search("meeting hardware competitors")

    mock_get.assert_called_once()
    assert result["query"] == "meeting hardware competitors"
    assert result["count"] == 2
    assert result["results"][0]["title"] == "Owl Labs"
    assert result["results"][1]["url"] == "https://otter.ai"


def test_web_search_has_docstring():
    """web_search has a descriptive docstring for agent use."""
    from vibe_inc.tools.web.search import web_search

    assert web_search.__doc__
    assert "Brave Search" in web_search.__doc__


def test_web_search_count_param():
    """web_search passes count parameter, capped at 20."""
    from vibe_inc.tools.web.search import web_search

    mock_response = MagicMock()
    mock_response.json.return_value = {"web": {"results": []}}
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"BRAVE_SEARCH_API_KEY": "k"}), \
         patch("httpx.get", return_value=mock_response) as mock_get:
        web_search("test", count=50)

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["count"] == 20  # capped


# --- web_fetch tests ---


def test_web_fetch_returns_content():
    """web_fetch returns page content with metadata."""
    from vibe_inc.tools.web.search import web_fetch

    mock_response = MagicMock()
    mock_response.text = "<html><body>Pricing: $249</body></html>"
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = web_fetch("https://example.com/pricing")

    assert result["url"] == "https://example.com/pricing"
    assert "Pricing: $249" in result["content"]
    assert result["truncated"] is False
    assert result["status_code"] == 200


def test_web_fetch_truncates_content():
    """web_fetch truncates content beyond max_chars."""
    from vibe_inc.tools.web.search import web_fetch

    mock_response = MagicMock()
    mock_response.text = "A" * 10000
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = web_fetch("https://example.com", max_chars=100)

    assert len(result["content"]) == 100
    assert result["truncated"] is True


def test_web_fetch_has_docstring():
    """web_fetch has a descriptive docstring for agent use."""
    from vibe_inc.tools.web.search import web_fetch

    assert web_fetch.__doc__
    assert "truncated" in web_fetch.__doc__
