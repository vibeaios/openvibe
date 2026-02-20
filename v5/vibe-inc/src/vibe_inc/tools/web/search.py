"""Web search and fetch tools for competitive intelligence."""
import os


def web_search(query: str, count: int = 10) -> dict:
    """Search the web using Brave Search API.

    Args:
        query: Search query string.
        count: Number of results to return (default 10, max 20).

    Returns:
        Dict with 'query', 'count', and 'results' (list of {title, url, description}).
    """
    import httpx

    api_key = os.environ["BRAVE_SEARCH_API_KEY"]
    resp = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
        params={"q": query, "count": min(count, 20)},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        })

    return {"query": query, "count": len(results), "results": results}


def web_fetch(url: str, max_chars: int = 4000) -> dict:
    """Fetch a web page and return its text content, truncated.

    Args:
        url: URL to fetch.
        max_chars: Maximum characters to return (default 4000).

    Returns:
        Dict with 'url', 'content', 'truncated' (bool), and 'status_code'.
    """
    import httpx

    resp = httpx.get(
        url,
        headers={"User-Agent": "VibeBot/1.0 (competitive-intel)"},
        timeout=15.0,
        follow_redirects=True,
    )
    resp.raise_for_status()
    text = resp.text
    truncated = len(text) > max_chars

    return {
        "url": url,
        "content": text[:max_chars],
        "truncated": truncated,
        "status_code": resp.status_code,
    }
