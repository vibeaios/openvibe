# Vibe AI Ops Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy 20 AI agents across Marketing, Sales, CS, and Revenue Intelligence — all running in parallel from day one.

**Architecture:** Python agent runner framework with standard agent interface. All agents share Claude API, HubSpot, Slack, and logging clients. 3 deep-dive agents (Content Gen, Lead Qual, Engagement) get multi-step pipelines; 17 validation-tier agents use single Claude API call pattern. Cron + webhooks for triggers, SQLite for logging.

**Tech Stack:** Python 3.12, anthropic SDK, slack-sdk, hubspot-api-client, sqlite3, pytest, pydantic, pyyaml, APScheduler

**Design Doc:** `v3/vibe-ai-adoption/docs/DESIGN.md`

---

## Phase 1: Foundation (Week 1)

### Task 1: Project Scaffolding

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/__init__.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/__init__.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/__init__.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/marketing/__init__.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/sales/__init__.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/cs/__init__.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/intelligence/__init__.py`
- Create: `v3/vibe-ai-adoption/pyproject.toml`
- Create: `v3/vibe-ai-adoption/.env.example`
- Create: `v3/vibe-ai-adoption/config/agents.yaml`
- Create: `v3/vibe-ai-adoption/tests/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "vibe-ai-ops"
version = "0.1.0"
description = "20 AI agents powering Vibe's GTM"
requires-python = ">=3.12"
dependencies = [
    "anthropic>=0.40.0",
    "slack-sdk>=3.27.0",
    "hubspot-api-client>=9.0.0",
    "pydantic>=2.6.0",
    "pyyaml>=6.0",
    "apscheduler>=3.10.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
]

[build-system]
requires = ["setuptools>=69.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Create .env.example**

```bash
# Claude
ANTHROPIC_API_KEY=sk-ant-...

# HubSpot
HUBSPOT_API_KEY=pat-...

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_MARKETING=C...
SLACK_CHANNEL_SALES=C...
SLACK_CHANNEL_CS=C...
SLACK_CHANNEL_INTELLIGENCE=C...

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=vibe-ai-ops

# Database
DATABASE_PATH=data/runs.db
```

**Step 3: Create directory structure**

```bash
cd v3/vibe-ai-adoption
mkdir -p src/vibe_ai_ops/{shared,agents/{marketing,sales,cs,intelligence}}
mkdir -p tests/{shared,agents/{marketing,sales,cs,intelligence}}
mkdir -p config/prompts/{marketing,sales,cs,intelligence}
mkdir -p data
touch src/vibe_ai_ops/__init__.py
touch src/vibe_ai_ops/shared/__init__.py
touch src/vibe_ai_ops/agents/__init__.py
touch src/vibe_ai_ops/agents/marketing/__init__.py
touch src/vibe_ai_ops/agents/sales/__init__.py
touch src/vibe_ai_ops/agents/cs/__init__.py
touch src/vibe_ai_ops/agents/intelligence/__init__.py
touch tests/__init__.py
touch tests/shared/__init__.py
touch tests/agents/__init__.py
touch tests/agents/marketing/__init__.py
touch tests/agents/sales/__init__.py
touch tests/agents/cs/__init__.py
touch tests/agents/intelligence/__init__.py
```

**Step 4: Install dependencies**

```bash
cd v3/vibe-ai-adoption
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Step 5: Verify setup**

Run: `cd v3/vibe-ai-adoption && source .venv/bin/activate && python -c "import vibe_ai_ops; print('OK')"`
Expected: `OK`

**Step 6: Commit**

```bash
git add v3/vibe-ai-adoption/pyproject.toml v3/vibe-ai-adoption/.env.example \
  v3/vibe-ai-adoption/src/ v3/vibe-ai-adoption/tests/ \
  v3/vibe-ai-adoption/config/ v3/vibe-ai-adoption/data/
git commit -m "feat: project scaffolding for vibe-ai-ops"
```

---

### Task 2: Agent Data Models

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/models.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_models.py`

**Step 1: Write the failing test**

```python
# tests/shared/test_models.py
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput, AgentRun, Tier, TriggerType


def test_agent_config_from_dict():
    data = {
        "id": "m3",
        "name": "Content Generation",
        "engine": "marketing",
        "tier": "deep_dive",
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "output_channel": "slack:#marketing-agents",
        "prompt_file": "marketing/m3_content_generation.md",
        "enabled": True,
    }
    config = AgentConfig(**data)
    assert config.id == "m3"
    assert config.tier == Tier.DEEP_DIVE
    assert config.trigger.type == TriggerType.CRON


def test_agent_output():
    output = AgentOutput(
        agent_id="m3",
        content="Generated blog post about...",
        destination="slack:#marketing-agents",
        tokens_in=500,
        tokens_out=2000,
        cost_usd=0.03,
        duration_seconds=4.5,
        metadata={"segment": "enterprise-fintech", "format": "blog"},
    )
    assert output.agent_id == "m3"
    assert output.cost_usd == 0.03


def test_agent_run_tracks_success():
    run = AgentRun(
        agent_id="m3",
        status="success",
        input_summary="Generate blog for enterprise-fintech",
        output_summary="1200-word blog post on AI in fintech",
        tokens_in=500,
        tokens_out=2000,
        cost_usd=0.03,
        duration_seconds=4.5,
    )
    assert run.status == "success"
    assert run.agent_id == "m3"


def test_agent_run_tracks_failure():
    run = AgentRun(
        agent_id="m3",
        status="error",
        input_summary="Generate blog for enterprise-fintech",
        error="Rate limited by Claude API",
        tokens_in=0,
        tokens_out=0,
        cost_usd=0.0,
        duration_seconds=1.2,
    )
    assert run.status == "error"
    assert run.error == "Rate limited by Claude API"
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && source .venv/bin/activate && pytest tests/shared/test_models.py -v`
Expected: FAIL (module not found)

**Step 3: Implement models**

```python
# src/vibe_ai_ops/shared/models.py
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Tier(str, Enum):
    DEEP_DIVE = "deep_dive"
    VALIDATION = "validation"


class TriggerType(str, Enum):
    CRON = "cron"
    WEBHOOK = "webhook"
    ON_DEMAND = "on_demand"
    EVENT = "event"


class TriggerConfig(BaseModel):
    type: TriggerType
    schedule: str | None = None  # cron expression
    event_source: str | None = None  # e.g. "hubspot:new_lead"


class AgentConfig(BaseModel):
    id: str
    name: str
    engine: str  # marketing | sales | cs | intelligence
    tier: Tier
    trigger: TriggerConfig
    output_channel: str  # e.g. "slack:#marketing-agents"
    prompt_file: str  # relative to config/prompts/
    enabled: bool = True
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    temperature: float = 0.7


class AgentOutput(BaseModel):
    agent_id: str
    content: str
    destination: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRun(BaseModel):
    agent_id: str
    status: str  # "success" | "error" | "skipped"
    input_summary: str = ""
    output_summary: str = ""
    error: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Step 4: Run test to verify it passes**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_models.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/models.py tests/shared/test_models.py
git commit -m "feat: agent data models (AgentConfig, AgentOutput, AgentRun)"
```

---

### Task 3: Claude API Client

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/claude_client.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_claude_client.py`

**Step 1: Write the failing test**

```python
# tests/shared/test_claude_client.py
import pytest
from unittest.mock import MagicMock, patch

from vibe_ai_ops.shared.claude_client import ClaudeClient, ClaudeResponse


def test_claude_client_sends_message(mocker):
    mock_anthropic = mocker.patch("vibe_ai_ops.shared.claude_client.Anthropic")
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello from Claude")],
        usage=MagicMock(input_tokens=10, output_tokens=20),
    )

    client = ClaudeClient(api_key="test-key")
    response = client.send(
        system_prompt="You are a helpful assistant.",
        user_message="Say hello.",
        model="claude-sonnet-4-5-20250929",
    )

    assert isinstance(response, ClaudeResponse)
    assert response.content == "Hello from Claude"
    assert response.tokens_in == 10
    assert response.tokens_out == 20
    assert response.cost_usd > 0


def test_claude_client_calculates_cost():
    # Sonnet pricing: $3/M input, $15/M output
    response = ClaudeResponse(
        content="test",
        tokens_in=1000,
        tokens_out=1000,
        model="claude-sonnet-4-5-20250929",
    )
    assert response.cost_usd == pytest.approx(0.018, abs=0.001)


def test_claude_client_handles_error(mocker):
    mock_anthropic = mocker.patch("vibe_ai_ops.shared.claude_client.Anthropic")
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create.side_effect = Exception("API error")

    client = ClaudeClient(api_key="test-key")
    with pytest.raises(Exception, match="API error"):
        client.send(
            system_prompt="test",
            user_message="test",
        )
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_claude_client.py -v`
Expected: FAIL

**Step 3: Implement Claude client**

```python
# src/vibe_ai_ops/shared/claude_client.py
from __future__ import annotations

from dataclasses import dataclass

from anthropic import Anthropic


# Pricing per 1M tokens (as of 2026-02)
MODEL_PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
}


@dataclass
class ClaudeResponse:
    content: str
    tokens_in: int
    tokens_out: int
    model: str = "claude-sonnet-4-5-20250929"

    @property
    def cost_usd(self) -> float:
        pricing = MODEL_PRICING.get(self.model, {"input": 3.0, "output": 15.0})
        return (
            self.tokens_in * pricing["input"] / 1_000_000
            + self.tokens_out * pricing["output"] / 1_000_000
        )


class ClaudeClient:
    def __init__(self, api_key: str | None = None):
        self._client = Anthropic(api_key=api_key)

    def send(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ClaudeResponse:
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return ClaudeResponse(
            content=response.content[0].text,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=model,
        )
```

**Step 4: Run test to verify it passes**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_claude_client.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/claude_client.py tests/shared/test_claude_client.py
git commit -m "feat: Claude API client with cost tracking"
```

---

### Task 4: Run Logger (SQLite)

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/logger.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_logger.py`

**Step 1: Write the failing test**

```python
# tests/shared/test_logger.py
import os
import tempfile

from vibe_ai_ops.shared.logger import RunLogger
from vibe_ai_ops.shared.models import AgentRun


def test_logger_creates_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        logger = RunLogger(db_path)
        assert os.path.exists(db_path)
        logger.close()


def test_logger_logs_and_retrieves_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        logger = RunLogger(db_path)

        run = AgentRun(
            agent_id="m3",
            status="success",
            input_summary="Generate blog for fintech",
            output_summary="1200 words on AI in fintech",
            tokens_in=500,
            tokens_out=2000,
            cost_usd=0.03,
            duration_seconds=4.5,
        )
        logger.log_run(run)

        runs = logger.get_runs("m3", limit=10)
        assert len(runs) == 1
        assert runs[0]["agent_id"] == "m3"
        assert runs[0]["status"] == "success"
        logger.close()


def test_logger_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        logger = RunLogger(db_path)

        for i in range(5):
            logger.log_run(AgentRun(
                agent_id="m3",
                status="success" if i < 4 else "error",
                cost_usd=0.03,
                duration_seconds=4.0,
            ))

        stats = logger.get_agent_stats("m3")
        assert stats["total_runs"] == 5
        assert stats["success_count"] == 4
        assert stats["error_count"] == 1
        assert stats["total_cost_usd"] == 0.15
        logger.close()
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_logger.py -v`
Expected: FAIL

**Step 3: Implement logger**

```python
# src/vibe_ai_ops/shared/logger.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from vibe_ai_ops.shared.models import AgentRun


class RunLogger:
    def __init__(self, db_path: str = "data/runs.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_summary TEXT DEFAULT '',
                output_summary TEXT DEFAULT '',
                error TEXT,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                duration_seconds REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_id
            ON agent_runs(agent_id)
        """)
        self._conn.commit()

    def log_run(self, run: AgentRun):
        self._conn.execute(
            """INSERT INTO agent_runs
               (agent_id, status, input_summary, output_summary, error,
                tokens_in, tokens_out, cost_usd, duration_seconds, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run.agent_id, run.status, run.input_summary, run.output_summary,
                run.error, run.tokens_in, run.tokens_out, run.cost_usd,
                run.duration_seconds, run.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_runs(self, agent_id: str, limit: int = 20) -> list[dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM agent_runs WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            """SELECT
                 COUNT(*) as total_runs,
                 SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                 SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                 SUM(cost_usd) as total_cost_usd,
                 AVG(duration_seconds) as avg_duration
               FROM agent_runs WHERE agent_id = ?""",
            (agent_id,),
        ).fetchone()
        return dict(row)

    def close(self):
        self._conn.close()
```

**Step 4: Run test to verify it passes**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_logger.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/logger.py tests/shared/test_logger.py
git commit -m "feat: SQLite run logger with stats"
```

---

### Task 5: Slack Output Client

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/slack_client.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_slack_client.py`

**Step 1: Write the failing test**

```python
# tests/shared/test_slack_client.py
from vibe_ai_ops.shared.slack_client import SlackOutput, format_agent_output
from vibe_ai_ops.shared.models import AgentOutput


def test_format_agent_output():
    output = AgentOutput(
        agent_id="m3",
        content="# Blog Post: AI in Fintech\n\nContent here...",
        destination="slack:#marketing-agents",
        tokens_in=500,
        tokens_out=2000,
        cost_usd=0.03,
        duration_seconds=4.5,
        metadata={"segment": "enterprise-fintech"},
    )
    formatted = format_agent_output(output, agent_name="Content Generation")
    assert "Content Generation" in formatted
    assert "m3" in formatted
    assert "$0.03" in formatted
    assert "enterprise-fintech" in formatted


def test_slack_output_send(mocker):
    mock_webclient = mocker.patch("vibe_ai_ops.shared.slack_client.WebClient")
    mock_instance = mock_webclient.return_value

    client = SlackOutput(token="xoxb-test")
    output = AgentOutput(
        agent_id="m3",
        content="Test output",
        destination="slack:#marketing-agents",
    )
    client.send(output, agent_name="Content Generation")

    mock_instance.chat_postMessage.assert_called_once()
    call_kwargs = mock_instance.chat_postMessage.call_args[1]
    assert call_kwargs["channel"] == "#marketing-agents"
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_slack_client.py -v`
Expected: FAIL

**Step 3: Implement Slack client**

```python
# src/vibe_ai_ops/shared/slack_client.py
from __future__ import annotations

from slack_sdk import WebClient

from vibe_ai_ops.shared.models import AgentOutput


def format_agent_output(output: AgentOutput, agent_name: str) -> str:
    meta = ""
    if output.metadata:
        meta = " | ".join(f"{k}: {v}" for k, v in output.metadata.items())
        meta = f"\n_{meta}_"

    return (
        f"*[{agent_name}]* (`{output.agent_id}`) "
        f"| ${output.cost_usd:.2f} | {output.duration_seconds:.1f}s"
        f"{meta}\n\n{output.content}"
    )


class SlackOutput:
    def __init__(self, token: str | None = None):
        self._client = WebClient(token=token)

    def send(self, output: AgentOutput, agent_name: str = "Agent"):
        channel = output.destination.replace("slack:", "")
        text = format_agent_output(output, agent_name)
        self._client.chat_postMessage(channel=channel, text=text)

    def send_alert(self, channel: str, message: str):
        self._client.chat_postMessage(channel=channel, text=message)
```

**Step 4: Run test to verify it passes**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_slack_client.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/slack_client.py tests/shared/test_slack_client.py
git commit -m "feat: Slack output client with agent formatting"
```

---

### Task 6: HubSpot Client (Read + Write)

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/hubspot_client.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_hubspot_client.py`

**Step 1: Write the failing test**

```python
# tests/shared/test_hubspot_client.py
from vibe_ai_ops.shared.hubspot_client import HubSpotClient


def test_hubspot_client_get_leads(mocker):
    mock_hs = mocker.patch("vibe_ai_ops.shared.hubspot_client.HubSpot")
    mock_instance = mock_hs.return_value
    mock_instance.crm.contacts.search_api.do_search.return_value = mocker.MagicMock(
        results=[
            mocker.MagicMock(properties={
                "email": "test@example.com",
                "firstname": "John",
                "lastname": "Doe",
                "company": "Acme",
                "hs_lead_status": "NEW",
            })
        ]
    )

    client = HubSpotClient(api_key="test-key")
    leads = client.get_new_leads(limit=10)
    assert len(leads) == 1
    assert leads[0]["email"] == "test@example.com"


def test_hubspot_client_update_lead(mocker):
    mock_hs = mocker.patch("vibe_ai_ops.shared.hubspot_client.HubSpot")
    mock_instance = mock_hs.return_value

    client = HubSpotClient(api_key="test-key")
    client.update_contact("123", {"hs_lead_status": "QUALIFIED", "ai_score": "85"})

    mock_instance.crm.contacts.basic_api.update.assert_called_once()


def test_hubspot_client_get_deals(mocker):
    mock_hs = mocker.patch("vibe_ai_ops.shared.hubspot_client.HubSpot")
    mock_instance = mock_hs.return_value
    mock_instance.crm.deals.search_api.do_search.return_value = mocker.MagicMock(
        results=[
            mocker.MagicMock(properties={
                "dealname": "Acme Corp",
                "amount": "50000",
                "dealstage": "qualifiedtobuy",
            })
        ]
    )

    client = HubSpotClient(api_key="test-key")
    deals = client.get_active_deals()
    assert len(deals) == 1
    assert deals[0]["dealname"] == "Acme Corp"
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_hubspot_client.py -v`
Expected: FAIL

**Step 3: Implement HubSpot client**

```python
# src/vibe_ai_ops/shared/hubspot_client.py
from __future__ import annotations

from typing import Any

from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest, SimplePublicObjectInput


class HubSpotClient:
    def __init__(self, api_key: str | None = None):
        self._client = HubSpot(access_token=api_key)

    def get_new_leads(self, limit: int = 50) -> list[dict[str, Any]]:
        request = PublicObjectSearchRequest(
            filter_groups=[{
                "filters": [{
                    "propertyName": "hs_lead_status",
                    "operator": "EQ",
                    "value": "NEW",
                }]
            }],
            limit=limit,
            properties=[
                "email", "firstname", "lastname", "company",
                "jobtitle", "phone", "hs_lead_status",
                "lifecyclestage", "hs_analytics_source",
            ],
        )
        response = self._client.crm.contacts.search_api.do_search(
            public_object_search_request=request
        )
        return [r.properties for r in response.results]

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        response = self._client.crm.contacts.basic_api.get_by_id(
            contact_id=contact_id,
            properties=[
                "email", "firstname", "lastname", "company",
                "jobtitle", "phone", "hs_lead_status",
                "lifecyclestage", "hs_analytics_source",
            ],
        )
        return response.properties

    def update_contact(self, contact_id: str, properties: dict[str, str]):
        self._client.crm.contacts.basic_api.update(
            contact_id=contact_id,
            simple_public_object_input=SimplePublicObjectInput(
                properties=properties
            ),
        )

    def get_active_deals(self, limit: int = 100) -> list[dict[str, Any]]:
        request = PublicObjectSearchRequest(
            filter_groups=[{
                "filters": [{
                    "propertyName": "dealstage",
                    "operator": "NEQ",
                    "value": "closedwon",
                }]
            }],
            limit=limit,
            properties=[
                "dealname", "amount", "dealstage", "closedate",
                "pipeline", "hs_lastmodifieddate",
            ],
        )
        response = self._client.crm.deals.search_api.do_search(
            public_object_search_request=request
        )
        return [r.properties for r in response.results]
```

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_hubspot_client.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/hubspot_client.py tests/shared/test_hubspot_client.py
git commit -m "feat: HubSpot client (leads, contacts, deals)"
```

---

### Task 7: Config Loader

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/config.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_config.py`
- Create: `v3/vibe-ai-adoption/config/agents.yaml`

**Step 1: Write the failing test**

```python
# tests/shared/test_config.py
import os
import tempfile

import yaml

from vibe_ai_ops.shared.config import load_agent_configs, load_prompt


def test_load_agent_configs():
    config_data = {
        "agents": [
            {
                "id": "m3",
                "name": "Content Generation",
                "engine": "marketing",
                "tier": "deep_dive",
                "trigger": {"type": "cron", "schedule": "0 9 * * *"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m3_content_generation.md",
                "enabled": True,
            },
            {
                "id": "m1",
                "name": "Segment Research",
                "engine": "marketing",
                "tier": "validation",
                "trigger": {"type": "cron", "schedule": "0 9 * * 1"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m1_segment_research.md",
                "enabled": True,
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_agent_configs(f.name)

    assert len(configs) == 2
    assert configs[0].id == "m3"
    assert configs[0].tier.value == "deep_dive"
    os.unlink(f.name)


def test_load_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = os.path.join(tmpdir, "test_prompt.md")
        with open(prompt_path, "w") as f:
            f.write("You are a marketing agent.\n\nGenerate content for {{segment}}.")

        content = load_prompt(prompt_path)
        assert "marketing agent" in content
        assert "{{segment}}" in content


def test_load_configs_filters_disabled():
    config_data = {
        "agents": [
            {
                "id": "m3",
                "name": "Content Generation",
                "engine": "marketing",
                "tier": "deep_dive",
                "trigger": {"type": "cron", "schedule": "0 9 * * *"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m3.md",
                "enabled": True,
            },
            {
                "id": "m4",
                "name": "Content Repurposing",
                "engine": "marketing",
                "tier": "validation",
                "trigger": {"type": "event", "event_source": "m3:complete"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m4.md",
                "enabled": False,
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_agent_configs(f.name, enabled_only=True)

    assert len(configs) == 1
    assert configs[0].id == "m3"
    os.unlink(f.name)
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_config.py -v`
Expected: FAIL

**Step 3: Implement config loader**

```python
# src/vibe_ai_ops/shared/config.py
from __future__ import annotations

from pathlib import Path

import yaml

from vibe_ai_ops.shared.models import AgentConfig


def load_agent_configs(
    config_path: str = "config/agents.yaml",
    enabled_only: bool = False,
) -> list[AgentConfig]:
    with open(config_path) as f:
        data = yaml.safe_load(f)

    configs = [AgentConfig(**agent) for agent in data["agents"]]
    if enabled_only:
        configs = [c for c in configs if c.enabled]
    return configs


def load_prompt(prompt_path: str) -> str:
    return Path(prompt_path).read_text()
```

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_config.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/config.py tests/shared/test_config.py
git commit -m "feat: YAML config loader for agent definitions"
```

---

### Task 8: Base Agent + Runner

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/base_agent.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/runner.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_base_agent.py`
- Create: `v3/vibe-ai-adoption/tests/test_runner.py`

**Step 1: Write the failing test for base agent**

```python
# tests/shared/test_base_agent.py
import time
from unittest.mock import MagicMock

from vibe_ai_ops.shared.base_agent import BaseAgent, ValidationAgent
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


def test_validation_agent_runs():
    mock_claude = MagicMock()
    mock_claude.send.return_value = MagicMock(
        content="Generated segment analysis for fintech...",
        tokens_in=200,
        tokens_out=1500,
        cost_usd=0.024,
    )

    config = AgentConfig(
        id="m1",
        name="Segment Research",
        engine="marketing",
        tier="validation",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1_segment_research.md",
    )

    agent = ValidationAgent(
        config=config,
        claude_client=mock_claude,
        system_prompt="You are a segment research agent.",
    )

    output = agent.run({"segments": ["enterprise-fintech", "mid-market-healthcare"]})
    assert isinstance(output, AgentOutput)
    assert output.agent_id == "m1"
    assert "fintech" in output.content
    assert output.tokens_in == 200


def test_validation_agent_formats_input():
    config = AgentConfig(
        id="m1",
        name="Segment Research",
        engine="marketing",
        tier="validation",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1.md",
    )
    agent = ValidationAgent(
        config=config,
        claude_client=MagicMock(),
        system_prompt="test",
    )
    formatted = agent.format_input({"key": "value", "list": [1, 2, 3]})
    assert "key" in formatted
    assert "value" in formatted
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_base_agent.py -v`
Expected: FAIL

**Step 3: Implement base agent**

```python
# src/vibe_ai_ops/shared/base_agent.py
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from vibe_ai_ops.shared.claude_client import ClaudeClient
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


class BaseAgent(ABC):
    def __init__(self, config: AgentConfig, claude_client: ClaudeClient):
        self.config = config
        self.claude = claude_client

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        ...

    def format_input(self, input_data: dict[str, Any]) -> str:
        return json.dumps(input_data, indent=2, default=str)


class ValidationAgent(BaseAgent):
    """Standard single-call agent for validation tier."""

    def __init__(
        self,
        config: AgentConfig,
        claude_client: ClaudeClient,
        system_prompt: str,
    ):
        super().__init__(config, claude_client)
        self.system_prompt = system_prompt

    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        start = time.time()
        user_message = self.format_input(input_data)

        response = self.claude.send(
            system_prompt=self.system_prompt,
            user_message=user_message,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        duration = time.time() - start
        return AgentOutput(
            agent_id=self.config.id,
            content=response.content,
            destination=self.config.output_channel,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=response.cost_usd,
            duration_seconds=duration,
            metadata={"input_keys": list(input_data.keys())},
        )
```

**Step 4: Run test to verify it passes**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_base_agent.py -v`
Expected: 2 passed

**Step 5: Write the runner test**

```python
# tests/test_runner.py
from unittest.mock import MagicMock, patch

from vibe_ai_ops.runner import AgentRunner
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


def test_runner_executes_agent():
    mock_agent = MagicMock()
    mock_agent.run.return_value = AgentOutput(
        agent_id="m1",
        content="test output",
        destination="slack:#test",
    )

    mock_logger = MagicMock()
    mock_slack = MagicMock()

    runner = AgentRunner(logger=mock_logger, slack=mock_slack)
    runner.register_agent("m1", mock_agent)

    result = runner.execute("m1", {"test": "data"})
    assert result.agent_id == "m1"
    mock_logger.log_run.assert_called_once()
    mock_slack.send.assert_called_once()


def test_runner_handles_agent_error():
    mock_agent = MagicMock()
    mock_agent.run.side_effect = Exception("Agent failed")
    mock_agent.config = MagicMock(id="m1")

    mock_logger = MagicMock()
    mock_slack = MagicMock()

    runner = AgentRunner(logger=mock_logger, slack=mock_slack)
    runner.register_agent("m1", mock_agent)

    result = runner.execute("m1", {"test": "data"})
    assert result is None
    # Should still log the error
    mock_logger.log_run.assert_called_once()
    logged_run = mock_logger.log_run.call_args[0][0]
    assert logged_run.status == "error"
```

**Step 6: Implement runner**

```python
# src/vibe_ai_ops/runner.py
from __future__ import annotations

import time
from typing import Any

from vibe_ai_ops.shared.base_agent import BaseAgent
from vibe_ai_ops.shared.logger import RunLogger
from vibe_ai_ops.shared.models import AgentOutput, AgentRun
from vibe_ai_ops.shared.slack_client import SlackOutput


class AgentRunner:
    def __init__(self, logger: RunLogger, slack: SlackOutput | None = None):
        self._agents: dict[str, BaseAgent] = {}
        self._logger = logger
        self._slack = slack

    def register_agent(self, agent_id: str, agent: BaseAgent):
        self._agents[agent_id] = agent

    def execute(
        self,
        agent_id: str,
        input_data: dict[str, Any],
    ) -> AgentOutput | None:
        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not registered")

        start = time.time()
        try:
            output = agent.run(input_data)

            self._logger.log_run(AgentRun(
                agent_id=agent_id,
                status="success",
                input_summary=str(input_data)[:200],
                output_summary=output.content[:200],
                tokens_in=output.tokens_in,
                tokens_out=output.tokens_out,
                cost_usd=output.cost_usd,
                duration_seconds=output.duration_seconds,
            ))

            if self._slack:
                agent_name = agent.config.name if hasattr(agent, "config") else agent_id
                self._slack.send(output, agent_name=agent_name)

            return output

        except Exception as e:
            duration = time.time() - start
            self._logger.log_run(AgentRun(
                agent_id=agent_id,
                status="error",
                input_summary=str(input_data)[:200],
                error=str(e),
                duration_seconds=duration,
            ))
            return None

    def execute_all_scheduled(self, trigger_type: str, input_data: dict[str, Any]):
        results = {}
        for agent_id, agent in self._agents.items():
            if agent.config.trigger.type.value == trigger_type:
                results[agent_id] = self.execute(agent_id, input_data)
        return results
```

**Step 7: Run all tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/test_runner.py tests/shared/test_base_agent.py -v`
Expected: 4 passed

**Step 8: Commit**

```bash
git add src/vibe_ai_ops/shared/base_agent.py src/vibe_ai_ops/runner.py \
  tests/shared/test_base_agent.py tests/test_runner.py
git commit -m "feat: base agent + runner with logging and Slack output"
```

---

### Task 9: Scheduler

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/scheduler.py`
- Create: `v3/vibe-ai-adoption/tests/test_scheduler.py`

**Step 1: Write the failing test**

```python
# tests/test_scheduler.py
from unittest.mock import MagicMock

from vibe_ai_ops.scheduler import AgentScheduler
from vibe_ai_ops.shared.models import AgentConfig


def test_scheduler_registers_cron_agents():
    mock_runner = MagicMock()

    configs = [
        AgentConfig(
            id="m1", name="Segment Research", engine="marketing",
            tier="validation", trigger={"type": "cron", "schedule": "0 9 * * 1"},
            output_channel="slack:#test", prompt_file="test.md",
        ),
        AgentConfig(
            id="s1", name="Lead Qualification", engine="sales",
            tier="deep_dive", trigger={"type": "webhook", "event_source": "hubspot:new_lead"},
            output_channel="slack:#test", prompt_file="test.md",
        ),
    ]

    scheduler = AgentScheduler(runner=mock_runner)
    cron_count = scheduler.register_configs(configs)

    # Only m1 has cron trigger
    assert cron_count == 1


def test_scheduler_parses_cron():
    from vibe_ai_ops.scheduler import parse_cron
    result = parse_cron("0 9 * * 1")
    assert result["hour"] == "9"
    assert result["minute"] == "0"
    assert result["day_of_week"] == "1"
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/test_scheduler.py -v`
Expected: FAIL

**Step 3: Implement scheduler**

```python
# src/vibe_ai_ops/scheduler.py
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from vibe_ai_ops.runner import AgentRunner
from vibe_ai_ops.shared.models import AgentConfig


def parse_cron(cron_expr: str) -> dict[str, str]:
    """Parse standard 5-field cron to APScheduler kwargs."""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr}")
    fields = ["minute", "hour", "day", "month", "day_of_week"]
    return {f: v for f, v in zip(fields, parts) if v != "*"}


class AgentScheduler:
    def __init__(self, runner: AgentRunner):
        self._runner = runner
        self._scheduler = BackgroundScheduler()
        self._jobs: dict[str, str] = {}

    def register_configs(self, configs: list[AgentConfig]) -> int:
        count = 0
        for config in configs:
            if config.trigger.type.value == "cron" and config.trigger.schedule:
                cron_kwargs = parse_cron(config.trigger.schedule)
                self._scheduler.add_job(
                    self._runner.execute,
                    "cron",
                    args=[config.id, {}],
                    id=config.id,
                    **cron_kwargs,
                )
                self._jobs[config.id] = config.trigger.schedule
                count += 1
        return count

    def start(self):
        self._scheduler.start()

    def stop(self):
        self._scheduler.shutdown()

    def list_jobs(self) -> dict[str, str]:
        return dict(self._jobs)
```

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/test_scheduler.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/scheduler.py tests/test_scheduler.py
git commit -m "feat: cron-based agent scheduler using APScheduler"
```

---

## Phase 2: Agent Definitions (Week 1-2)

All 20 agent system prompts + the master agents.yaml config.

### Task 10: Master Agent Config (agents.yaml)

**Files:**
- Create: `v3/vibe-ai-adoption/config/agents.yaml`

**Step 1: Write the complete agent config**

```yaml
# config/agents.yaml
# All 20 agents — 3 deep-dive, 17 validation
# Trigger types: cron | webhook | event | on_demand

agents:
  # ═══════════════════════════════════════════
  # ENGINE 1: MARKETING (6 agents)
  # ═══════════════════════════════════════════

  - id: m1
    name: Segment Research
    engine: marketing
    tier: validation
    trigger: { type: cron, schedule: "0 9 * * 1" }  # Monday 9am
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m1_segment_research.md
    enabled: true
    model: claude-sonnet-4-5-20250929
    max_tokens: 8192
    temperature: 0.7

  - id: m2
    name: Message Testing
    engine: marketing
    tier: validation
    trigger: { type: cron, schedule: "0 10 * * 1,4" }  # Mon/Thu 10am
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m2_message_testing.md
    enabled: true

  - id: m3
    name: Content Generation
    engine: marketing
    tier: deep_dive
    trigger: { type: cron, schedule: "0 9 * * *" }  # Daily 9am
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m3_content_generation.md
    enabled: true
    max_tokens: 8192

  - id: m4
    name: Content Repurposing
    engine: marketing
    tier: validation
    trigger: { type: event, event_source: "m3:complete" }
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m4_content_repurposing.md
    enabled: true

  - id: m5
    name: Distribution
    engine: marketing
    tier: validation
    trigger: { type: event, event_source: "m4:complete" }
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m5_distribution.md
    enabled: true

  - id: m6
    name: Journey Optimization
    engine: marketing
    tier: validation
    trigger: { type: cron, schedule: "0 8 * * 5" }  # Friday 8am
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m6_journey_optimization.md
    enabled: true

  # ═══════════════════════════════════════════
  # ENGINE 2: SALES (5 agents)
  # ═══════════════════════════════════════════

  - id: s1
    name: Lead Qualification
    engine: sales
    tier: deep_dive
    trigger: { type: webhook, event_source: "hubspot:new_lead" }
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s1_lead_qualification.md
    enabled: true
    model: claude-sonnet-4-5-20250929
    max_tokens: 4096
    temperature: 0.3  # lower temp for scoring consistency

  - id: s2
    name: Buyer Intelligence
    engine: sales
    tier: validation
    trigger: { type: cron, schedule: "0 7 * * *" }  # Daily 7am
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s2_buyer_intelligence.md
    enabled: true
    max_tokens: 8192

  - id: s3
    name: Engagement
    engine: sales
    tier: deep_dive
    trigger: { type: event, event_source: "s1:qualified" }
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s3_engagement.md
    enabled: true

  - id: s4
    name: Deal Support
    engine: sales
    tier: validation
    trigger: { type: cron, schedule: "0 7 * * 1,2,3,4,5" }  # Weekdays 7am
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s4_deal_support.md
    enabled: true
    max_tokens: 8192

  - id: s5
    name: Nurture
    engine: sales
    tier: validation
    trigger: { type: event, event_source: "s1:nurture" }
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s5_nurture.md
    enabled: true

  # ═══════════════════════════════════════════
  # ENGINE 3: CUSTOMER SUCCESS (5 agents)
  # ═══════════════════════════════════════════

  - id: c1
    name: Onboarding
    engine: cs
    tier: validation
    trigger: { type: webhook, event_source: "hubspot:deal_won" }
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c1_onboarding.md
    enabled: true

  - id: c2
    name: Success Advisor
    engine: cs
    tier: validation
    trigger: { type: cron, schedule: "0 10 * * 2" }  # Tuesday 10am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c2_success_advisor.md
    enabled: true
    max_tokens: 8192

  - id: c3
    name: Health Intelligence
    engine: cs
    tier: validation
    trigger: { type: cron, schedule: "0 2 * * *" }  # Daily 2am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c3_health_intelligence.md
    enabled: true

  - id: c4
    name: Expansion
    engine: cs
    tier: validation
    trigger: { type: cron, schedule: "0 9 * * 3" }  # Wednesday 9am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c4_expansion.md
    enabled: true

  - id: c5
    name: Customer Voice
    engine: cs
    tier: validation
    trigger: { type: cron, schedule: "0 8 * * 5" }  # Friday 8am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c5_customer_voice.md
    enabled: true
    max_tokens: 8192

  # ═══════════════════════════════════════════
  # REVENUE INTELLIGENCE (4 agents)
  # ═══════════════════════════════════════════

  - id: r1
    name: Funnel Monitor
    engine: intelligence
    tier: validation
    trigger: { type: cron, schedule: "0 6 * * *" }  # Daily 6am
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r1_funnel_monitor.md
    enabled: true

  - id: r2
    name: Deal Risk & Forecast
    engine: intelligence
    tier: validation
    trigger: { type: cron, schedule: "0 7 * * 1,2,3,4,5" }  # Weekdays 7am
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r2_deal_risk_forecast.md
    enabled: true
    max_tokens: 8192

  - id: r3
    name: Conversation Analysis
    engine: intelligence
    tier: validation
    trigger: { type: cron, schedule: "0 8 * * 1" }  # Monday 8am
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r3_conversation_analysis.md
    enabled: true
    max_tokens: 8192

  - id: r4
    name: NL Revenue Interface
    engine: intelligence
    tier: validation
    trigger: { type: on_demand }
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r4_nl_revenue_interface.md
    enabled: true
    max_tokens: 4096
    temperature: 0.3
```

**Step 2: Verify config loads**

Run: `cd v3/vibe-ai-adoption && python -c "from vibe_ai_ops.shared.config import load_agent_configs; cs = load_agent_configs('config/agents.yaml'); print(f'{len(cs)} agents loaded'); print([c.id for c in cs])"`
Expected: `20 agents loaded` + list of all IDs

**Step 3: Commit**

```bash
git add config/agents.yaml
git commit -m "feat: master agent config — all 20 agents defined"
```

---

### Task 11: Marketing Agent Prompts (M1-M6)

**Files:**
- Create: `v3/vibe-ai-adoption/config/prompts/marketing/m1_segment_research.md`
- Create: `v3/vibe-ai-adoption/config/prompts/marketing/m2_message_testing.md`
- Create: `v3/vibe-ai-adoption/config/prompts/marketing/m3_content_generation.md`
- Create: `v3/vibe-ai-adoption/config/prompts/marketing/m4_content_repurposing.md`
- Create: `v3/vibe-ai-adoption/config/prompts/marketing/m5_distribution.md`
- Create: `v3/vibe-ai-adoption/config/prompts/marketing/m6_journey_optimization.md`

Each prompt follows the same structure. Write each as a detailed system prompt that tells Claude exactly what role it plays, what input it expects, and what output format to produce.

**Reference:** Design doc Section 4 (Engine 1: Marketing) for each agent's specification.

**Key principles for prompt writing:**
- Start with role and goal
- Specify exact input format expected
- Specify exact output format (markdown with headers)
- Include examples where helpful
- For M3 (deep dive): include multi-step instructions (outline → draft → edit)

**Step 1: Write all 6 prompts** (see design doc for each agent's spec)

**Step 2: Verify prompts load**

Run: `cd v3/vibe-ai-adoption && for f in config/prompts/marketing/*.md; do echo "$f: $(wc -l < $f) lines"; done`
Expected: 6 files, each with substantive content

**Step 3: Commit**

```bash
git add config/prompts/marketing/
git commit -m "feat: marketing agent prompts (M1-M6)"
```

---

### Task 12: Sales Agent Prompts (S1-S5)

**Files:**
- Create: `v3/vibe-ai-adoption/config/prompts/sales/s1_lead_qualification.md`
- Create: `v3/vibe-ai-adoption/config/prompts/sales/s2_buyer_intelligence.md`
- Create: `v3/vibe-ai-adoption/config/prompts/sales/s3_engagement.md`
- Create: `v3/vibe-ai-adoption/config/prompts/sales/s4_deal_support.md`
- Create: `v3/vibe-ai-adoption/config/prompts/sales/s5_nurture.md`

**Reference:** Design doc Section 5 (Engine 2: Sales).

**Key:** S1 (Lead Qual) prompt must include scoring rubric with explicit ranges. S3 (Engagement) prompt must include behavior-response mapping.

**Step 1: Write all 5 prompts**
**Step 2: Verify prompts load**
**Step 3: Commit**

```bash
git add config/prompts/sales/
git commit -m "feat: sales agent prompts (S1-S5)"
```

---

### Task 13: CS Agent Prompts (C1-C5)

**Files:**
- Create: `v3/vibe-ai-adoption/config/prompts/cs/c1_onboarding.md`
- Create: `v3/vibe-ai-adoption/config/prompts/cs/c2_success_advisor.md`
- Create: `v3/vibe-ai-adoption/config/prompts/cs/c3_health_intelligence.md`
- Create: `v3/vibe-ai-adoption/config/prompts/cs/c4_expansion.md`
- Create: `v3/vibe-ai-adoption/config/prompts/cs/c5_customer_voice.md`

**Reference:** Design doc Section 6 (Engine 3: CS).

**Step 1: Write all 5 prompts**
**Step 2: Verify prompts load**
**Step 3: Commit**

```bash
git add config/prompts/cs/
git commit -m "feat: CS agent prompts (C1-C5)"
```

---

### Task 14: Intelligence Agent Prompts (R1-R4)

**Files:**
- Create: `v3/vibe-ai-adoption/config/prompts/intelligence/r1_funnel_monitor.md`
- Create: `v3/vibe-ai-adoption/config/prompts/intelligence/r2_deal_risk_forecast.md`
- Create: `v3/vibe-ai-adoption/config/prompts/intelligence/r3_conversation_analysis.md`
- Create: `v3/vibe-ai-adoption/config/prompts/intelligence/r4_nl_revenue_interface.md`

**Reference:** Design doc Section 7 (Revenue Intelligence Layer).

**Step 1: Write all 4 prompts**
**Step 2: Verify prompts load**
**Step 3: Commit**

```bash
git add config/prompts/intelligence/
git commit -m "feat: intelligence agent prompts (R1-R4)"
```

---

## Phase 3: Deep Dive — Content Generation (M3) (Week 2)

### Task 15: Content Generation Pipeline

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/marketing/m3_content_generation.py`
- Create: `v3/vibe-ai-adoption/tests/agents/marketing/test_m3_content_generation.py`

**Step 1: Write the failing test**

```python
# tests/agents/marketing/test_m3_content_generation.py
from unittest.mock import MagicMock

from vibe_ai_ops.agents.marketing.m3_content_generation import ContentGenerationAgent
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


def _make_config():
    return AgentConfig(
        id="m3", name="Content Generation", engine="marketing",
        tier="deep_dive", trigger={"type": "cron", "schedule": "0 9 * * *"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m3_content_generation.md",
    )


def test_content_generation_produces_outline_then_draft():
    mock_claude = MagicMock()

    # Call 1: outline, Call 2: draft, Call 3: edit/polish
    mock_claude.send.side_effect = [
        MagicMock(content="## Outline\n1. Intro\n2. Problem\n3. Solution",
                  tokens_in=200, tokens_out=500, cost_usd=0.01),
        MagicMock(content="# AI in Fintech\n\nFull blog post content here...",
                  tokens_in=800, tokens_out=3000, cost_usd=0.05),
        MagicMock(content="# AI in Fintech: How Smart Companies Save 50%\n\nPolished...",
                  tokens_in=3500, tokens_out=3200, cost_usd=0.06),
    ]

    agent = ContentGenerationAgent(
        config=_make_config(),
        claude_client=mock_claude,
        system_prompt="You are a content generation agent.",
    )

    output = agent.run({
        "segment": "enterprise-fintech",
        "topic": "AI cost reduction",
        "winning_message": "Smart fintech companies are cutting costs 50% with AI agents",
        "format": "blog",
        "target_words": 1200,
    })

    assert isinstance(output, AgentOutput)
    assert output.agent_id == "m3"
    # Should have called Claude 3 times (outline → draft → polish)
    assert mock_claude.send.call_count == 3
    # Cost should be sum of all 3 calls
    assert output.cost_usd == 0.12
    assert "segment" in output.metadata


def test_content_generation_includes_seo_metadata():
    mock_claude = MagicMock()
    mock_claude.send.side_effect = [
        MagicMock(content="outline", tokens_in=100, tokens_out=200, cost_usd=0.005),
        MagicMock(content="draft", tokens_in=300, tokens_out=1500, cost_usd=0.025),
        MagicMock(content="final", tokens_in=1800, tokens_out=1600, cost_usd=0.03),
    ]

    agent = ContentGenerationAgent(
        config=_make_config(),
        claude_client=mock_claude,
        system_prompt="test",
    )

    output = agent.run({
        "segment": "mid-market-healthcare",
        "topic": "patient engagement",
        "winning_message": "test",
        "format": "blog",
        "keywords": ["patient engagement", "healthcare AI"],
    })

    assert output.metadata["segment"] == "mid-market-healthcare"
    assert output.metadata["format"] == "blog"
    assert output.metadata["pipeline_steps"] == 3
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/agents/marketing/test_m3_content_generation.py -v`
Expected: FAIL

**Step 3: Implement Content Generation agent**

```python
# src/vibe_ai_ops/agents/marketing/m3_content_generation.py
from __future__ import annotations

import time
from typing import Any

from vibe_ai_ops.shared.base_agent import BaseAgent
from vibe_ai_ops.shared.claude_client import ClaudeClient
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


class ContentGenerationAgent(BaseAgent):
    """Deep-dive agent: multi-step content pipeline (outline → draft → polish)."""

    def __init__(
        self,
        config: AgentConfig,
        claude_client: ClaudeClient,
        system_prompt: str,
    ):
        super().__init__(config, claude_client)
        self.system_prompt = system_prompt

    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        start = time.time()
        segment = input_data.get("segment", "general")
        topic = input_data.get("topic", "")
        winning_message = input_data.get("winning_message", "")
        content_format = input_data.get("format", "blog")
        target_words = input_data.get("target_words", 1200)
        keywords = input_data.get("keywords", [])

        total_tokens_in = 0
        total_tokens_out = 0
        total_cost = 0.0

        # Step 1: Generate outline
        outline_response = self.claude.send(
            system_prompt=self.system_prompt,
            user_message=(
                f"STEP: Generate outline only.\n"
                f"Segment: {segment}\n"
                f"Topic: {topic}\n"
                f"Core message: {winning_message}\n"
                f"Format: {content_format}\n"
                f"Target length: {target_words} words\n"
                f"SEO keywords: {', '.join(keywords) if keywords else 'none'}\n\n"
                f"Output a structured outline with section headers and key points."
            ),
            model=self.config.model,
            max_tokens=2048,
            temperature=0.7,
        )
        total_tokens_in += outline_response.tokens_in
        total_tokens_out += outline_response.tokens_out
        total_cost += outline_response.cost_usd

        # Step 2: Write full draft from outline
        draft_response = self.claude.send(
            system_prompt=self.system_prompt,
            user_message=(
                f"STEP: Write the full {content_format} based on this outline.\n\n"
                f"OUTLINE:\n{outline_response.content}\n\n"
                f"Segment: {segment}\n"
                f"Core message: {winning_message}\n"
                f"Target: {target_words} words\n"
                f"SEO keywords to include naturally: {', '.join(keywords) if keywords else 'none'}\n\n"
                f"Write the complete {content_format}. Be specific, use data, avoid fluff."
            ),
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=0.7,
        )
        total_tokens_in += draft_response.tokens_in
        total_tokens_out += draft_response.tokens_out
        total_cost += draft_response.cost_usd

        # Step 3: Polish and optimize
        polish_response = self.claude.send(
            system_prompt=self.system_prompt,
            user_message=(
                f"STEP: Polish and optimize this draft.\n\n"
                f"DRAFT:\n{draft_response.content}\n\n"
                f"Instructions:\n"
                f"- Sharpen the headline for {segment} audience\n"
                f"- Ensure core message comes through: {winning_message}\n"
                f"- Check SEO keyword density for: {', '.join(keywords) if keywords else 'n/a'}\n"
                f"- Cut fluff, strengthen arguments with specifics\n"
                f"- Add meta description (160 chars) at the top\n\n"
                f"Output the final polished version."
            ),
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=0.4,  # lower temp for polish step
        )
        total_tokens_in += polish_response.tokens_in
        total_tokens_out += polish_response.tokens_out
        total_cost += polish_response.cost_usd

        duration = time.time() - start
        return AgentOutput(
            agent_id=self.config.id,
            content=polish_response.content,
            destination=self.config.output_channel,
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            cost_usd=total_cost,
            duration_seconds=duration,
            metadata={
                "segment": segment,
                "topic": topic,
                "format": content_format,
                "pipeline_steps": 3,
                "keywords": keywords,
            },
        )
```

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/agents/marketing/test_m3_content_generation.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/agents/marketing/m3_content_generation.py \
  tests/agents/marketing/test_m3_content_generation.py
git commit -m "feat: Content Generation agent (deep dive) — 3-step pipeline"
```

---

## Phase 4: Deep Dive — Lead Qualification (S1) (Week 2-3)

### Task 16: Lead Qualification Agent

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/sales/s1_lead_qualification.py`
- Create: `v3/vibe-ai-adoption/tests/agents/sales/test_s1_lead_qualification.py`

**Step 1: Write the failing test**

```python
# tests/agents/sales/test_s1_lead_qualification.py
from unittest.mock import MagicMock
import json

from vibe_ai_ops.agents.sales.s1_lead_qualification import (
    LeadQualificationAgent,
    LeadScore,
)
from vibe_ai_ops.shared.models import AgentConfig


def _make_config():
    return AgentConfig(
        id="s1", name="Lead Qualification", engine="sales",
        tier="deep_dive",
        trigger={"type": "webhook", "event_source": "hubspot:new_lead"},
        output_channel="slack:#sales-agents",
        prompt_file="sales/s1_lead_qualification.md",
        temperature=0.3,
    )


def test_lead_qualification_scores_and_routes():
    mock_claude = MagicMock()
    mock_hubspot = MagicMock()

    # Enrichment call returns company data
    mock_hubspot.get_contact.return_value = {
        "email": "cto@bigcorp.com",
        "firstname": "Jane",
        "lastname": "Smith",
        "company": "BigCorp",
        "jobtitle": "CTO",
    }

    # Claude returns structured scoring
    mock_claude.send.return_value = MagicMock(
        content=json.dumps({
            "fit_score": 85,
            "intent_score": 70,
            "urgency_score": 60,
            "reasoning": "CTO at large corp, visited pricing page",
            "route": "sales",
        }),
        tokens_in=500,
        tokens_out=300,
        cost_usd=0.01,
    )

    agent = LeadQualificationAgent(
        config=_make_config(),
        claude_client=mock_claude,
        hubspot_client=mock_hubspot,
        system_prompt="You are a lead qualification specialist.",
    )

    output = agent.run({"contact_id": "123", "source": "website"})
    assert output.agent_id == "s1"

    score = LeadScore(**json.loads(output.metadata["score_json"]))
    assert score.fit_score == 85
    assert score.composite >= 70
    assert score.route == "sales"

    # Should have updated HubSpot
    mock_hubspot.update_contact.assert_called_once()


def test_lead_score_composite():
    score = LeadScore(fit_score=80, intent_score=70, urgency_score=60,
                      reasoning="test", route="sales")
    # Composite = 0.4*fit + 0.35*intent + 0.25*urgency
    expected = 0.4 * 80 + 0.35 * 70 + 0.25 * 60
    assert score.composite == expected


def test_lead_score_routing():
    high = LeadScore(fit_score=90, intent_score=85, urgency_score=80,
                     reasoning="great lead", route="sales")
    assert high.composite >= 80

    medium = LeadScore(fit_score=60, intent_score=55, urgency_score=50,
                       reasoning="okay lead", route="nurture")
    assert 50 <= medium.composite < 80

    low = LeadScore(fit_score=30, intent_score=20, urgency_score=10,
                    reasoning="poor fit", route="education")
    assert low.composite < 50
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/agents/sales/test_s1_lead_qualification.py -v`
Expected: FAIL

**Step 3: Implement Lead Qualification agent**

```python
# src/vibe_ai_ops/agents/sales/s1_lead_qualification.py
from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from vibe_ai_ops.shared.base_agent import BaseAgent
from vibe_ai_ops.shared.claude_client import ClaudeClient
from vibe_ai_ops.shared.hubspot_client import HubSpotClient
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


class LeadScore(BaseModel):
    fit_score: int  # 0-100
    intent_score: int  # 0-100
    urgency_score: int  # 0-100
    reasoning: str
    route: str  # "sales" | "nurture" | "education" | "disqualify"

    @property
    def composite(self) -> float:
        return 0.4 * self.fit_score + 0.35 * self.intent_score + 0.25 * self.urgency_score


class LeadQualificationAgent(BaseAgent):
    """Deep-dive agent: enrich → score → route → update CRM."""

    def __init__(
        self,
        config: AgentConfig,
        claude_client: ClaudeClient,
        hubspot_client: HubSpotClient,
        system_prompt: str,
    ):
        super().__init__(config, claude_client)
        self.hubspot = hubspot_client
        self.system_prompt = system_prompt

    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        start = time.time()
        contact_id = input_data["contact_id"]
        source = input_data.get("source", "unknown")

        # Step 1: Enrich from HubSpot
        contact = self.hubspot.get_contact(contact_id)

        # Step 2: Score with Claude
        score_response = self.claude.send(
            system_prompt=self.system_prompt,
            user_message=(
                f"Score this lead. Return ONLY valid JSON.\n\n"
                f"Lead data:\n{json.dumps(contact, indent=2)}\n\n"
                f"Source: {source}\n\n"
                f"Return JSON with: fit_score (0-100), intent_score (0-100), "
                f"urgency_score (0-100), reasoning (string), "
                f'route ("sales" if composite>=80, "nurture" if 50-79, '
                f'"education" if <50, "disqualify" if ICP mismatch)'
            ),
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        score_data = json.loads(score_response.content)
        score = LeadScore(**score_data)

        # Step 3: Update HubSpot
        route_map = {
            "sales": "QUALIFIED",
            "nurture": "NURTURE",
            "education": "UNQUALIFIED",
            "disqualify": "DISQUALIFIED",
        }
        self.hubspot.update_contact(contact_id, {
            "hs_lead_status": route_map.get(score.route, "NEW"),
            "ai_fit_score": str(score.fit_score),
            "ai_intent_score": str(score.intent_score),
            "ai_urgency_score": str(score.urgency_score),
            "ai_composite_score": str(int(score.composite)),
            "ai_qualification_reasoning": score.reasoning[:500],
        })

        duration = time.time() - start

        route_emoji = {"sales": "🔥", "nurture": "🌱", "education": "📚", "disqualify": "❌"}
        summary = (
            f"{route_emoji.get(score.route, '?')} **{contact.get('firstname', '')} "
            f"{contact.get('lastname', '')}** ({contact.get('company', 'Unknown')})\n"
            f"Score: {int(score.composite)} (Fit:{score.fit_score} Intent:{score.intent_score} "
            f"Urgency:{score.urgency_score})\n"
            f"Route: {score.route.upper()}\n"
            f"Reasoning: {score.reasoning}"
        )

        return AgentOutput(
            agent_id=self.config.id,
            content=summary,
            destination=self.config.output_channel,
            tokens_in=score_response.tokens_in,
            tokens_out=score_response.tokens_out,
            cost_usd=score_response.cost_usd,
            duration_seconds=duration,
            metadata={
                "contact_id": contact_id,
                "source": source,
                "composite_score": int(score.composite),
                "route": score.route,
                "score_json": json.dumps(score_data),
            },
        )
```

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/agents/sales/test_s1_lead_qualification.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/agents/sales/s1_lead_qualification.py \
  tests/agents/sales/test_s1_lead_qualification.py
git commit -m "feat: Lead Qualification agent (deep dive) — enrich/score/route/CRM"
```

---

## Phase 5: Deep Dive — Engagement Agent (S3) (Week 3)

### Task 17: Engagement Agent

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/sales/s3_engagement.py`
- Create: `v3/vibe-ai-adoption/tests/agents/sales/test_s3_engagement.py`

This agent generates personalized multi-touch outreach sequences. For the first version, it generates the full sequence as email drafts (human reviews before send).

**Step 1: Write the failing test**

```python
# tests/agents/sales/test_s3_engagement.py
from unittest.mock import MagicMock
import json

from vibe_ai_ops.agents.sales.s3_engagement import EngagementAgent
from vibe_ai_ops.shared.models import AgentConfig


def _make_config():
    return AgentConfig(
        id="s3", name="Engagement", engine="sales",
        tier="deep_dive",
        trigger={"type": "event", "event_source": "s1:qualified"},
        output_channel="slack:#sales-agents",
        prompt_file="sales/s3_engagement.md",
    )


def test_engagement_generates_sequence():
    mock_claude = MagicMock()
    mock_claude.send.return_value = MagicMock(
        content=json.dumps({
            "sequence": [
                {
                    "day": 1,
                    "channel": "email",
                    "subject": "Quick question about your fintech stack",
                    "body": "Hi Jane, I noticed BigCorp is scaling...",
                    "purpose": "Initial personalized outreach",
                },
                {
                    "day": 3,
                    "channel": "linkedin",
                    "body": "Hi Jane, I shared an article on AI in fintech...",
                    "purpose": "Value-add touchpoint",
                },
                {
                    "day": 7,
                    "channel": "email",
                    "subject": "Case study: How FinCo saved 50%",
                    "body": "Hi Jane, thought you'd find this relevant...",
                    "purpose": "Social proof",
                },
            ],
            "personalization_signals": [
                "CTO role → technical messaging",
                "Fintech industry → cost reduction angle",
                "Recently funded → growth mode",
            ],
        }),
        tokens_in=1000,
        tokens_out=2000,
        cost_usd=0.04,
    )

    agent = EngagementAgent(
        config=_make_config(),
        claude_client=mock_claude,
        system_prompt="You are a sales engagement specialist.",
    )

    output = agent.run({
        "contact": {
            "name": "Jane Smith",
            "title": "CTO",
            "company": "BigCorp",
            "industry": "Fintech",
        },
        "score": {"composite": 85, "route": "sales"},
        "segment": "enterprise-fintech",
        "winning_message": "Smart fintech companies cut costs 50% with AI",
    })

    assert output.agent_id == "s3"
    assert output.metadata["touch_count"] == 3
    assert output.metadata["segment"] == "enterprise-fintech"


def test_engagement_adapts_to_segment():
    mock_claude = MagicMock()
    mock_claude.send.return_value = MagicMock(
        content=json.dumps({
            "sequence": [{"day": 1, "channel": "email", "subject": "test",
                          "body": "test", "purpose": "test"}],
            "personalization_signals": ["healthcare focus"],
        }),
        tokens_in=500, tokens_out=1000, cost_usd=0.02,
    )

    agent = EngagementAgent(
        config=_make_config(),
        claude_client=mock_claude,
        system_prompt="test",
    )

    output = agent.run({
        "contact": {"name": "Dr. Lee", "title": "CMO", "company": "HealthCo",
                     "industry": "Healthcare"},
        "score": {"composite": 75, "route": "sales"},
        "segment": "mid-market-healthcare",
        "winning_message": "Improve patient engagement with AI",
    })

    # Should have passed segment context to Claude
    call_args = mock_claude.send.call_args
    assert "mid-market-healthcare" in call_args[1]["user_message"]
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/agents/sales/test_s3_engagement.py -v`
Expected: FAIL

**Step 3: Implement Engagement agent**

```python
# src/vibe_ai_ops/agents/sales/s3_engagement.py
from __future__ import annotations

import json
import time
from typing import Any

from vibe_ai_ops.shared.base_agent import BaseAgent
from vibe_ai_ops.shared.claude_client import ClaudeClient
from vibe_ai_ops.shared.models import AgentConfig, AgentOutput


class EngagementAgent(BaseAgent):
    """Deep-dive agent: generates personalized multi-touch outreach sequences."""

    def __init__(
        self,
        config: AgentConfig,
        claude_client: ClaudeClient,
        system_prompt: str,
    ):
        super().__init__(config, claude_client)
        self.system_prompt = system_prompt

    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        start = time.time()
        contact = input_data.get("contact", {})
        score = input_data.get("score", {})
        segment = input_data.get("segment", "general")
        winning_message = input_data.get("winning_message", "")

        response = self.claude.send(
            system_prompt=self.system_prompt,
            user_message=(
                f"Generate a personalized multi-touch outreach sequence.\n"
                f"Return ONLY valid JSON.\n\n"
                f"Contact:\n{json.dumps(contact, indent=2)}\n\n"
                f"Lead score: {json.dumps(score)}\n"
                f"Segment: {segment}\n"
                f"Winning message for this segment: {winning_message}\n\n"
                f"Generate a sequence of 3-5 touches over 14 days.\n"
                f"Each touch: day, channel (email/linkedin/phone), "
                f"subject (if email), body, purpose.\n"
                f"Also include personalization_signals (what you used to customize).\n\n"
                f"JSON format:\n"
                f'{{"sequence": [...], "personalization_signals": [...]}}'
            ),
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        sequence_data = json.loads(response.content)
        touches = sequence_data.get("sequence", [])

        # Format for human review
        formatted = f"**Engagement Sequence for {contact.get('name', 'Unknown')}** "
        formatted += f"({contact.get('company', '')} | {segment})\n\n"

        for touch in touches:
            formatted += f"**Day {touch['day']}** — {touch['channel'].upper()}\n"
            if touch.get("subject"):
                formatted += f"Subject: {touch['subject']}\n"
            formatted += f"{touch['body']}\n"
            formatted += f"_Purpose: {touch['purpose']}_\n\n"

        signals = sequence_data.get("personalization_signals", [])
        if signals:
            formatted += "**Personalization signals:** " + ", ".join(signals)

        duration = time.time() - start
        return AgentOutput(
            agent_id=self.config.id,
            content=formatted,
            destination=self.config.output_channel,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=response.cost_usd,
            duration_seconds=duration,
            metadata={
                "contact_name": contact.get("name", "Unknown"),
                "company": contact.get("company", "Unknown"),
                "segment": segment,
                "touch_count": len(touches),
                "channels": list({t["channel"] for t in touches}),
            },
        )
```

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/agents/sales/test_s3_engagement.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/agents/sales/s3_engagement.py \
  tests/agents/sales/test_s3_engagement.py
git commit -m "feat: Engagement agent (deep dive) — personalized multi-touch sequences"
```

---

## Phase 6: Wire Up + Go Live (Week 3-4)

### Task 18: Validation Agent Wiring

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/marketing/validation.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/sales/validation.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/cs/validation.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/agents/intelligence/validation.py`

Each file creates `ValidationAgent` instances for all non-deep-dive agents in that engine, loading their system prompts from `config/prompts/`.

**Step 1: Implement factory for each engine**

```python
# src/vibe_ai_ops/agents/marketing/validation.py
from __future__ import annotations

from pathlib import Path

from vibe_ai_ops.shared.base_agent import ValidationAgent
from vibe_ai_ops.shared.claude_client import ClaudeClient
from vibe_ai_ops.shared.models import AgentConfig


def create_marketing_validation_agents(
    configs: list[AgentConfig],
    claude_client: ClaudeClient,
    prompts_dir: str = "config/prompts",
) -> dict[str, ValidationAgent]:
    agents = {}
    for config in configs:
        if config.engine != "marketing" or config.tier.value != "validation":
            continue
        prompt_path = Path(prompts_dir) / config.prompt_file
        if not prompt_path.exists():
            continue
        prompt = prompt_path.read_text()
        agents[config.id] = ValidationAgent(
            config=config,
            claude_client=claude_client,
            system_prompt=prompt,
        )
    return agents
```

Same pattern for sales, cs, intelligence (just change `engine` filter).

**Step 2: Test that factory loads agents**

Run quick smoke test after prompts exist.

**Step 3: Commit**

```bash
git add src/vibe_ai_ops/agents/
git commit -m "feat: validation agent factories for all 4 engines"
```

---

### Task 19: Main Entry Point

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/main.py`
- Create: `v3/vibe-ai-adoption/tests/test_main.py`

**Step 1: Implement main.py**

This wires everything together: loads config, creates all agents (deep-dive + validation), registers with runner, starts scheduler.

```python
# src/vibe_ai_ops/main.py
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from vibe_ai_ops.runner import AgentRunner
from vibe_ai_ops.scheduler import AgentScheduler
from vibe_ai_ops.shared.claude_client import ClaudeClient
from vibe_ai_ops.shared.config import load_agent_configs
from vibe_ai_ops.shared.hubspot_client import HubSpotClient
from vibe_ai_ops.shared.logger import RunLogger
from vibe_ai_ops.shared.slack_client import SlackOutput

# Deep-dive agents
from vibe_ai_ops.agents.marketing.m3_content_generation import ContentGenerationAgent
from vibe_ai_ops.agents.sales.s1_lead_qualification import LeadQualificationAgent
from vibe_ai_ops.agents.sales.s3_engagement import EngagementAgent

# Validation factories
from vibe_ai_ops.agents.marketing.validation import create_marketing_validation_agents
from vibe_ai_ops.agents.sales.validation import create_sales_validation_agents
from vibe_ai_ops.agents.cs.validation import create_cs_validation_agents
from vibe_ai_ops.agents.intelligence.validation import create_intelligence_validation_agents


def build_system(config_path: str = "config/agents.yaml") -> tuple[AgentRunner, AgentScheduler]:
    load_dotenv()

    # Shared services
    claude = ClaudeClient(api_key=os.environ["ANTHROPIC_API_KEY"])
    hubspot = HubSpotClient(api_key=os.environ.get("HUBSPOT_API_KEY"))
    slack = SlackOutput(token=os.environ.get("SLACK_BOT_TOKEN"))
    logger = RunLogger(os.environ.get("DATABASE_PATH", "data/runs.db"))
    prompts_dir = "config/prompts"

    # Load all configs
    configs = load_agent_configs(config_path, enabled_only=True)
    runner = AgentRunner(logger=logger, slack=slack)

    # Register deep-dive agents
    for config in configs:
        prompt_path = Path(prompts_dir) / config.prompt_file
        prompt = prompt_path.read_text() if prompt_path.exists() else ""

        if config.id == "m3":
            runner.register_agent("m3", ContentGenerationAgent(
                config=config, claude_client=claude, system_prompt=prompt))
        elif config.id == "s1":
            runner.register_agent("s1", LeadQualificationAgent(
                config=config, claude_client=claude,
                hubspot_client=hubspot, system_prompt=prompt))
        elif config.id == "s3":
            runner.register_agent("s3", EngagementAgent(
                config=config, claude_client=claude, system_prompt=prompt))

    # Register validation agents
    for factory in [
        create_marketing_validation_agents,
        create_sales_validation_agents,
        create_cs_validation_agents,
        create_intelligence_validation_agents,
    ]:
        agents = factory(configs, claude, prompts_dir)
        for agent_id, agent in agents.items():
            runner.register_agent(agent_id, agent)

    # Set up scheduler
    scheduler = AgentScheduler(runner=runner)
    scheduler.register_configs(configs)

    return runner, scheduler


def main():
    runner, scheduler = build_system()
    print(f"Registered agents: {list(runner._agents.keys())}")
    print(f"Scheduled jobs: {scheduler.list_jobs()}")
    print("Starting scheduler... (Ctrl+C to stop)")
    scheduler.start()

    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Stopped.")


if __name__ == "__main__":
    main()
```

**Step 2: Test build_system (with mocks)**

```python
# tests/test_main.py
from unittest.mock import patch, MagicMock

from vibe_ai_ops.main import build_system


@patch.dict("os.environ", {
    "ANTHROPIC_API_KEY": "test",
    "HUBSPOT_API_KEY": "test",
    "SLACK_BOT_TOKEN": "test",
    "DATABASE_PATH": "/tmp/test_vibe_ai.db",
})
@patch("vibe_ai_ops.main.ClaudeClient")
@patch("vibe_ai_ops.main.HubSpotClient")
@patch("vibe_ai_ops.main.SlackOutput")
def test_build_system_loads_all_agents(mock_slack, mock_hs, mock_claude):
    # This test verifies the wiring works — requires config + prompts to exist
    # Will be a smoke test after all prompts are written
    pass  # Placeholder until prompts exist
```

**Step 3: Commit**

```bash
git add src/vibe_ai_ops/main.py tests/test_main.py
git commit -m "feat: main entry point — wires all 20 agents + scheduler"
```

---

### Task 20: CLI for Manual Agent Execution

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/cli.py`

A simple CLI to run any agent on-demand with test data:

```bash
# Run a specific agent with test input
python -m vibe_ai_ops.cli run m3 --input '{"segment": "fintech", "topic": "AI costs"}'

# List all registered agents
python -m vibe_ai_ops.cli list

# Show stats for an agent
python -m vibe_ai_ops.cli stats m3

# Run all agents in an engine
python -m vibe_ai_ops.cli run-engine marketing
```

**Step 1: Implement CLI**

```python
# src/vibe_ai_ops/cli.py
from __future__ import annotations

import argparse
import json
import sys

from vibe_ai_ops.main import build_system


def cmd_list(runner, _args):
    for agent_id, agent in sorted(runner._agents.items()):
        tier = agent.config.tier.value
        trigger = agent.config.trigger.type.value
        print(f"  {agent_id:5s} | {agent.config.name:25s} | {tier:12s} | {trigger}")


def cmd_run(runner, args):
    input_data = json.loads(args.input) if args.input else {}
    print(f"Running {args.agent_id}...")
    result = runner.execute(args.agent_id, input_data)
    if result:
        print(f"\n--- Output ({result.duration_seconds:.1f}s, ${result.cost_usd:.3f}) ---")
        print(result.content[:2000])
    else:
        print("Agent execution failed. Check logs.")


def cmd_run_engine(runner, args):
    engine = args.engine
    for agent_id, agent in sorted(runner._agents.items()):
        if agent.config.engine == engine:
            print(f"\nRunning {agent_id} ({agent.config.name})...")
            result = runner.execute(agent_id, {})
            if result:
                print(f"  OK ({result.duration_seconds:.1f}s, ${result.cost_usd:.3f})")
            else:
                print(f"  FAILED")


def main():
    parser = argparse.ArgumentParser(description="Vibe AI Ops CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all agents")

    run_p = sub.add_parser("run", help="Run a specific agent")
    run_p.add_argument("agent_id", help="Agent ID (e.g., m3, s1)")
    run_p.add_argument("--input", help="JSON input data", default="{}")

    engine_p = sub.add_parser("run-engine", help="Run all agents in an engine")
    engine_p.add_argument("engine", choices=["marketing", "sales", "cs", "intelligence"])

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    runner, _ = build_system()
    commands = {"list": cmd_list, "run": cmd_run, "run-engine": cmd_run_engine}
    commands[args.command](runner, args)


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add src/vibe_ai_ops/cli.py
git commit -m "feat: CLI for manual agent execution and testing"
```

---

### Task 21: Run Full Test Suite

**Step 1: Run all tests**

```bash
cd v3/vibe-ai-adoption && pytest tests/ -v --tb=short
```

Expected: All tests pass (12+ tests across shared, agents, runner, scheduler)

**Step 2: Fix any failures, then commit**

```bash
git add -A && git commit -m "fix: resolve test issues from full suite run"
```

---

### Task 22: Smoke Test with Real APIs

**Step 1: Set up .env with real credentials**

```bash
cp .env.example .env
# Fill in real API keys
```

**Step 2: Run a single validation agent**

```bash
python -m vibe_ai_ops.cli run m1 --input '{"segments": ["enterprise-fintech"]}'
```

Expected: Agent produces segment research output, logged to SQLite, posted to Slack.

**Step 3: Run a deep-dive agent**

```bash
python -m vibe_ai_ops.cli run m3 --input '{"segment": "enterprise-fintech", "topic": "AI cost reduction", "winning_message": "Cut costs 50% with AI agents", "format": "blog", "target_words": 800}'
```

Expected: 3-step pipeline (outline → draft → polish), final blog post in Slack.

**Step 4: Run the full marketing engine**

```bash
python -m vibe_ai_ops.cli run-engine marketing
```

Expected: All 6 marketing agents execute and produce output.

**Step 5: Commit any fixes from smoke testing**

```bash
git add -A && git commit -m "fix: adjustments from smoke testing with real APIs"
```

---

### Task 23: Start Scheduler (Go Live)

**Step 1: Start the system**

```bash
cd v3/vibe-ai-adoption
source .venv/bin/activate
python -m vibe_ai_ops.main
```

Expected output:
```
Registered agents: ['m1', 'm2', 'm3', 'm4', 'm5', 'm6', 's1', 's2', 's3', 's4', 's5', 'c1', 'c2', 'c3', 'c4', 'c5', 'r1', 'r2', 'r3', 'r4']
Scheduled jobs: {'m1': '0 9 * * 1', 'm2': '0 10 * * 1,4', ...}
Starting scheduler... (Ctrl+C to stop)
```

**Step 2: Verify first scheduled run completes**

Wait for next scheduled trigger (or manually trigger via CLI).

**Step 3: Check Slack channels for output**

Verify agent output appears in the designated Slack channels.

**Step 4: Commit final state**

```bash
git add -A && git commit -m "feat: system go-live — all 20 agents registered and scheduled"
```

---

## Summary

| Phase | Tasks | What's Built |
|-------|-------|-------------|
| **Phase 1: Foundation** | Tasks 1-9 | Agent runner, Claude/HubSpot/Slack clients, logging, config, scheduler |
| **Phase 2: Definitions** | Tasks 10-14 | agents.yaml + 20 system prompts |
| **Phase 3: Deep Dive M3** | Task 15 | Content Generation 3-step pipeline |
| **Phase 4: Deep Dive S1** | Task 16 | Lead Qualification enrich/score/route |
| **Phase 5: Deep Dive S3** | Task 17 | Engagement personalized sequences |
| **Phase 6: Go Live** | Tasks 18-23 | Validation wiring, main, CLI, smoke test, launch |

**Total: 23 tasks. Week 1-4 timeline. All 20 agents running.**

---

## Post-Launch (Week 5+)

After week 4 data collection, decide:
- Which validation agents to graduate to deep-dive
- Which agents to kill
- Whether to add LangGraph for S1 (Lead Qual) state management
- Whether to add webhook handlers for real-time triggers
- Dashboard for agent health monitoring
