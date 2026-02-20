# Vibe Inc Live Testing Infrastructure — Design Document

> Three-layer verification: tool smoke tests → real agent loops → CLI runner.

Created: 2026-02-20T07:17:12Z

---

## 1. Context

V5 has 749 tests passing, but all use FakeLLM and mock APIs. No real API calls have been validated. We need to verify the full stack: API tool functions → Anthropic agent loop → complete workflow execution.

Available credentials: Meta Ads API, Google Ads API, HubSpot API, Anthropic API.

### Goal

Build three layers of live testing plus a CLI runner that lets you invoke any workflow from the terminal.

---

## 2. Architecture

```
Layer 1: Live Tool Tests          pytest -m live
Layer 2: Live Agent Tests         pytest -m live_agent
Layer 3: CLI Runner               python -m vibe_inc.cli run ...
```

All three layers share: `AnthropicProvider` → `create_runtime(llm)` → `runtime.activate()`.

---

## 3. Layer 1 — Live Tool Smoke Tests

**File:** `tests/test_live_tools.py`

Read-only smoke tests for each available API. Marked `@pytest.mark.live`, default skip.

| Test | Tool | API | Operation |
|------|------|-----|-----------|
| test_meta_ads_read_live | meta_ads_read | Meta Marketing API | Read campaign performance (last_7d) |
| test_google_ads_read_live | google_ads_read | Google Ads API | Read campaign performance (last_7d) |
| test_hubspot_contact_get_live | hubspot_contact_get | HubSpot API v3 | Get contact by email |

No write operations. Pure read, verifying credentials work and return format is correct.

---

## 4. Layer 2 — Live Agent Loop Tests

**File:** `tests/test_live_agent.py`

Full agent node execution with real Claude API + real tool APIs. Marked `@pytest.mark.live_agent`.

| Test | Operator | Node | What it validates |
|------|----------|------|-------------------|
| test_meta_weekly_report_live | MetaAdOps | weekly_report | Agent calls meta_ads_read, produces structured report |

Validates: agent receives tools → makes tool calls → processes results → returns text in state.

---

## 5. Layer 3 — CLI Runner

**Files:** `src/vibe_inc/cli.py` + `src/vibe_inc/__main__.py`

```bash
# List all available workflows
python -m vibe_inc.cli list

# Run a specific workflow
python -m vibe_inc.cli run \
  --role d2c_growth \
  --operator meta_ad_ops \
  --workflow weekly_report \
  --input '{"week": "current"}'

# Dry run (show what would execute)
python -m vibe_inc.cli run \
  --role d2c_growth \
  --operator meta_ad_ops \
  --workflow weekly_report \
  --dry-run
```

Implementation:
- Typer CLI with two commands: `list` + `run`
- `list`: traverse runtime, display role → operator → workflow tree via rich
- `run`: AnthropicProvider → create_runtime → activate → rich print result
- `--model` option (default: sonnet)
- `--dry-run` flag: print execution plan without calling APIs

---

## 6. Configuration

### pytest markers in pyproject.toml

```toml
[tool.pytest.ini_options]
markers = [
    "live: requires real API credentials (deselect with '-m not live')",
    "live_agent: requires ANTHROPIC_API_KEY + API credentials",
]
```

### Environment variables

All read from `.env` or shell environment:
- `ANTHROPIC_API_KEY` — Claude API
- `META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` — Meta Ads
- `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID` — Google Ads
- `HUBSPOT_API_KEY` — HubSpot

---

## 7. Out of Scope

- GA4 live tests (no credentials confirmed)
- Write operations (no campaign/contact creation)
- Changes to openvibe-cli package
- HTTP server entry point (platform layer)
- Amazon, TikTok, LinkedIn, Pinterest live tests (no credentials)

---

## 8. Expected Deliverables

| What | Count |
|------|-------|
| New test files | 2 (test_live_tools.py, test_live_agent.py) |
| New source files | 2 (cli.py, __main__.py) |
| New live tests | ~4 |
| CLI commands | 2 (list, run) |
