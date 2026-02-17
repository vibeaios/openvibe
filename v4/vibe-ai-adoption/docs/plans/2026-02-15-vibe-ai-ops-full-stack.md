# Vibe AI Ops Implementation Plan (Full Stack)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy 20 AI agents across Marketing, Sales, CS, and Revenue Intelligence using a production-grade 3-layer architecture: Temporal (orchestration) + LangGraph (stateful workflows) + CrewAI (agent roles).

**Architecture:** Temporal Cloud handles durable scheduling, retries, and long-running workflows (nurture = 14 days). LangGraph provides stateful agent workflows with checkpointing and human-in-the-loop. CrewAI defines agent roles with goals, tools, and multi-agent coordination. LangSmith traces every LLM call for observability. All agents share Claude API, HubSpot, Slack, and PostgreSQL clients.

**Tech Stack:** Python 3.12+, temporalio, langgraph, langgraph-checkpoint-postgres, langchain-anthropic, langsmith, crewai, crewai-tools, anthropic, slack-sdk, hubspot-api-client, psycopg, pydantic, pyyaml, httpx, python-dotenv, pytest

**Design Doc:** `v3/vibe-ai-adoption/docs/DESIGN.md`

**Supersedes:** `v3/vibe-ai-adoption/docs/plans/2026-02-15-vibe-ai-ops.md` (simplified plan)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: TEMPORAL (Orchestration)                          │
│  - Schedules agents (cron, webhook, event triggers)         │
│  - Durable execution (survives crashes, restarts)           │
│  - Manages long-running flows (nurture = 14 days)           │
│  - Automatic retries, timeouts, error handling              │
│  - Dashboard: all workflow runs visible                     │
└────────────────────────┬────────────────────────────────────┘
                         │ triggers
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: LANGGRAPH (Stateful Workflows)                    │
│  - State machines with checkpointing (PostgreSQL)           │
│  - Human-in-the-loop (pause/approve/reject)                 │
│  - Complex routing (score → different paths)                │
│  - Multi-step pipelines with intermediate state             │
│  - Observable via LangSmith                                 │
└────────────────────────┬────────────────────────────────────┘
                         │ executes
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: CREWAI (Agent Roles)                              │
│  - Role, goal, backstory per agent                          │
│  - Tool bindings (HubSpot, web search, Slack)               │
│  - Multi-agent crews for deep-dive agents                   │
│  - Single-agent tasks for validation agents                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ Claude  │         │ HubSpot │         │  Slack  │
    │   API   │         │   CRM   │         │ Output  │
    └─────────┘         └─────────┘         └─────────┘
```

---

## Phase 1: Infrastructure Foundation (Week 1-2)

### Task 1: Project Scaffolding

**Files:**
- Create: `v3/vibe-ai-adoption/pyproject.toml` (update existing)
- Create: `v3/vibe-ai-adoption/.env.example` (update existing)
- Create: `v3/vibe-ai-adoption/docker-compose.yml`
- Create: directory structure for all 3 layers

**Step 1: Update pyproject.toml with full-stack dependencies**

```toml
[project]
name = "vibe-ai-ops"
version = "0.1.0"
description = "20 AI agents powering Vibe's GTM — Temporal + LangGraph + CrewAI"
requires-python = ">=3.12"
dependencies = [
    # Layer 1: Temporal
    "temporalio>=1.7.0",

    # Layer 2: LangGraph
    "langgraph>=0.3.0",
    "langgraph-checkpoint-postgres>=2.0.0",
    "langchain-anthropic>=0.3.0",
    "langsmith>=0.2.0",

    # Layer 3: CrewAI
    "crewai>=0.100.0",
    "crewai-tools>=0.17.0",

    # Shared services
    "anthropic>=0.40.0",
    "slack-sdk>=3.27.0",
    "hubspot-api-client>=9.0.0",
    "pydantic>=2.6.0",
    "pyyaml>=6.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",

    # Database
    "psycopg[binary]>=3.2.0",
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
asyncio_mode = "auto"
```

**Step 2: Update .env.example**

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

# PostgreSQL (for LangGraph checkpointer)
POSTGRES_URL=postgresql://vibe:vibe@localhost:5432/vibe_ai_ops

# Temporal
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=vibe-ai-ops
# For Temporal Cloud:
# TEMPORAL_ADDRESS=<namespace>.tmprl.cloud:7233
# TEMPORAL_TLS_CERT_PATH=./certs/client.pem
# TEMPORAL_TLS_KEY_PATH=./certs/client.key

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=vibe-ai-ops
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**Step 3: Create docker-compose.yml for local development**

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: vibe
      POSTGRES_PASSWORD: vibe
      POSTGRES_DB: vibe_ai_ops
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  temporal:
    image: temporalio/auto-setup:latest
    environment:
      DB: postgres12
      DB_PORT: 5432
      POSTGRES_USER: vibe
      POSTGRES_PWD: vibe
      POSTGRES_SEEDS: postgres
    ports:
      - "7233:7233"
    depends_on:
      - postgres

  temporal-ui:
    image: temporalio/ui:latest
    environment:
      TEMPORAL_ADDRESS: temporal:7233
    ports:
      - "8233:8080"
    depends_on:
      - temporal

volumes:
  pgdata:
```

**Step 4: Create directory structure**

```bash
cd v3/vibe-ai-adoption
# Layer 1: Temporal
mkdir -p src/vibe_ai_ops/temporal/{workflows,activities}
touch src/vibe_ai_ops/temporal/__init__.py
touch src/vibe_ai_ops/temporal/workflows/__init__.py
touch src/vibe_ai_ops/temporal/activities/__init__.py

# Layer 2: LangGraph
mkdir -p src/vibe_ai_ops/graphs/{marketing,sales,cs,intelligence}
touch src/vibe_ai_ops/graphs/__init__.py
touch src/vibe_ai_ops/graphs/marketing/__init__.py
touch src/vibe_ai_ops/graphs/sales/__init__.py
touch src/vibe_ai_ops/graphs/cs/__init__.py
touch src/vibe_ai_ops/graphs/intelligence/__init__.py

# Layer 3: CrewAI
mkdir -p src/vibe_ai_ops/crews/{marketing,sales,cs,intelligence}
touch src/vibe_ai_ops/crews/__init__.py
touch src/vibe_ai_ops/crews/marketing/__init__.py
touch src/vibe_ai_ops/crews/sales/__init__.py
touch src/vibe_ai_ops/crews/cs/__init__.py
touch src/vibe_ai_ops/crews/intelligence/__init__.py

# Shared (already exists from previous scaffolding)
# src/vibe_ai_ops/shared/

# Tests mirror source
mkdir -p tests/{temporal,graphs/{marketing,sales,cs,intelligence},crews/{marketing,sales,cs,intelligence}}
touch tests/temporal/__init__.py
touch tests/graphs/__init__.py
touch tests/graphs/marketing/__init__.py
touch tests/graphs/sales/__init__.py
touch tests/graphs/cs/__init__.py
touch tests/graphs/intelligence/__init__.py
touch tests/crews/__init__.py
touch tests/crews/marketing/__init__.py
touch tests/crews/sales/__init__.py
touch tests/crews/cs/__init__.py
touch tests/crews/intelligence/__init__.py

# Config
mkdir -p config/prompts/{marketing,sales,cs,intelligence}
mkdir -p data
```

**Step 5: Re-install dependencies**

```bash
cd v3/vibe-ai-adoption
source .venv/bin/activate
pip install -e ".[dev]"
```

**Step 6: Start infrastructure**

```bash
docker compose up -d
# Wait for Temporal to be ready
sleep 10
docker compose ps  # All services should be "running"
```

**Step 7: Verify setup**

```bash
python -c "import vibe_ai_ops; print('OK')"
python -c "import temporalio; print('Temporal SDK OK')"
python -c "import langgraph; print('LangGraph OK')"
python -c "import crewai; print('CrewAI OK')"
python -c "import langsmith; print('LangSmith OK')"
```

Expected: All print OK.

**Step 8: Commit**

```bash
git add pyproject.toml .env.example docker-compose.yml \
  src/vibe_ai_ops/temporal/ src/vibe_ai_ops/graphs/ src/vibe_ai_ops/crews/ \
  tests/temporal/ tests/graphs/ tests/crews/
git commit -m "feat: full-stack scaffolding — Temporal + LangGraph + CrewAI"
```

---

### Task 2: Data Models + Config System

**Files:**
- Modify: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/models.py` (extend existing)
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/config.py`
- Create: `v3/vibe-ai-adoption/config/agents.yaml`
- Create: `v3/vibe-ai-adoption/tests/shared/test_config.py`
- Modify: `v3/vibe-ai-adoption/tests/shared/test_models.py` (extend existing)

**Step 1: Write the failing test for extended models**

```python
# tests/shared/test_models.py — add these tests to existing file
from vibe_ai_ops.shared.models import (
    AgentConfig, AgentOutput, AgentRun, Tier, TriggerType,
    ArchitectureType,  # NEW
)


def test_agent_config_with_architecture():
    data = {
        "id": "m3",
        "name": "Content Generation",
        "engine": "marketing",
        "tier": "deep_dive",
        "architecture": "temporal_langgraph_crewai",
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "output_channel": "slack:#marketing-agents",
        "prompt_file": "marketing/m3_content_generation.md",
        "crew_config": {
            "agents": ["researcher", "writer", "editor"],
            "process": "sequential",
        },
    }
    config = AgentConfig(**data)
    assert config.architecture == ArchitectureType.TEMPORAL_LANGGRAPH_CREWAI
    assert config.crew_config is not None
    assert len(config.crew_config["agents"]) == 3


def test_validation_agent_uses_simple_architecture():
    data = {
        "id": "m1",
        "name": "Segment Research",
        "engine": "marketing",
        "tier": "validation",
        "architecture": "temporal_crewai",
        "trigger": {"type": "cron", "schedule": "0 9 * * 1"},
        "output_channel": "slack:#marketing-agents",
        "prompt_file": "marketing/m1_segment_research.md",
    }
    config = AgentConfig(**data)
    assert config.architecture == ArchitectureType.TEMPORAL_CREWAI
    assert config.crew_config is None
```

**Step 2: Run test to verify it fails**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_models.py -v`
Expected: FAIL (ArchitectureType not found)

**Step 3: Extend models.py**

Add to `src/vibe_ai_ops/shared/models.py`:

```python
class ArchitectureType(str, Enum):
    TEMPORAL_LANGGRAPH_CREWAI = "temporal_langgraph_crewai"  # Deep dive: full pipeline
    TEMPORAL_CREWAI = "temporal_crewai"  # Validation: Temporal triggers CrewAI directly
```

Update `AgentConfig` to include:

```python
class AgentConfig(BaseModel):
    # ... existing fields ...
    architecture: ArchitectureType = ArchitectureType.TEMPORAL_CREWAI
    crew_config: dict[str, Any] | None = None  # CrewAI crew setup
    graph_config: dict[str, Any] | None = None  # LangGraph workflow setup
```

**Step 4: Run test to verify it passes**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_models.py -v`
Expected: All tests pass (6 total)

**Step 5: Write the failing test for config loader**

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
                "architecture": "temporal_langgraph_crewai",
                "trigger": {"type": "cron", "schedule": "0 9 * * *"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m3_content_generation.md",
                "crew_config": {
                    "agents": ["researcher", "writer", "editor"],
                    "process": "sequential",
                },
            },
            {
                "id": "m1",
                "name": "Segment Research",
                "engine": "marketing",
                "tier": "validation",
                "architecture": "temporal_crewai",
                "trigger": {"type": "cron", "schedule": "0 9 * * 1"},
                "output_channel": "slack:#marketing-agents",
                "prompt_file": "marketing/m1_segment_research.md",
            },
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        configs = load_agent_configs(f.name)

    assert len(configs) == 2
    assert configs[0].id == "m3"
    assert configs[0].architecture.value == "temporal_langgraph_crewai"
    os.unlink(f.name)


def test_load_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = os.path.join(tmpdir, "test_prompt.md")
        with open(prompt_path, "w") as f:
            f.write("You are a marketing agent.\n\nGenerate content for {{segment}}.")
        content = load_prompt(prompt_path)
        assert "marketing agent" in content


def test_load_configs_filters_disabled():
    config_data = {
        "agents": [
            {
                "id": "m3", "name": "Content Gen", "engine": "marketing",
                "tier": "deep_dive", "architecture": "temporal_langgraph_crewai",
                "trigger": {"type": "cron", "schedule": "0 9 * * *"},
                "output_channel": "slack:#test", "prompt_file": "test.md",
                "enabled": True,
            },
            {
                "id": "m4", "name": "Content Repurposing", "engine": "marketing",
                "tier": "validation", "architecture": "temporal_crewai",
                "trigger": {"type": "event", "event_source": "m3:complete"},
                "output_channel": "slack:#test", "prompt_file": "test.md",
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

**Step 6: Implement config loader**

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

**Step 7: Run all tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/ -v`
Expected: All pass

**Step 8: Commit**

```bash
git add src/vibe_ai_ops/shared/models.py src/vibe_ai_ops/shared/config.py \
  tests/shared/test_models.py tests/shared/test_config.py
git commit -m "feat: extended models with architecture types + config loader"
```

---

### Task 3: Shared Clients (Claude, HubSpot, Slack)

**Files:**
- Keep: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/claude_client.py` (already done)
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/hubspot_client.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/slack_client.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/logger.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_hubspot_client.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_slack_client.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_logger.py`

These are the same as Tasks 4-6 from the simple plan. The clients don't change — they're shared services used by all 3 layers.

**Step 1: Write failing tests for all 3 clients**

HubSpot test:
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

Slack test:
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

Logger test:
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

**Step 2: Run tests — all should fail**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/test_hubspot_client.py tests/shared/test_slack_client.py tests/shared/test_logger.py -v`

**Step 3: Implement all 3 clients**

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

**Step 4: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/shared/ -v`
Expected: All pass (12+ tests)

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/hubspot_client.py src/vibe_ai_ops/shared/slack_client.py \
  src/vibe_ai_ops/shared/logger.py \
  tests/shared/test_hubspot_client.py tests/shared/test_slack_client.py tests/shared/test_logger.py
git commit -m "feat: shared clients — HubSpot, Slack, SQLite logger"
```

---

### Task 4: LangSmith Tracing Setup

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/shared/tracing.py`
- Create: `v3/vibe-ai-adoption/tests/shared/test_tracing.py`

**Step 1: Write the failing test**

```python
# tests/shared/test_tracing.py
import os
from unittest.mock import patch

from vibe_ai_ops.shared.tracing import init_tracing, get_tracer


@patch.dict(os.environ, {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_API_KEY": "ls__test",
    "LANGCHAIN_PROJECT": "vibe-ai-ops-test",
})
def test_init_tracing_returns_config():
    config = init_tracing()
    assert config["enabled"] is True
    assert config["project"] == "vibe-ai-ops-test"


@patch.dict(os.environ, {}, clear=True)
def test_init_tracing_disabled_without_env():
    config = init_tracing()
    assert config["enabled"] is False


def test_get_tracer_returns_callable():
    tracer = get_tracer("test-agent")
    assert callable(tracer)
```

**Step 2: Run test — fails**

**Step 3: Implement tracing setup**

```python
# src/vibe_ai_ops/shared/tracing.py
from __future__ import annotations

import os
from typing import Any

from langsmith import traceable


def init_tracing() -> dict[str, Any]:
    """Initialize LangSmith tracing from environment variables."""
    enabled = os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"
    project = os.environ.get("LANGCHAIN_PROJECT", "vibe-ai-ops")
    api_key = os.environ.get("LANGCHAIN_API_KEY", "")

    return {
        "enabled": enabled and bool(api_key),
        "project": project,
    }


def get_tracer(agent_name: str):
    """Return a LangSmith traceable decorator for an agent."""
    return traceable(name=agent_name, run_type="chain")
```

**Step 4: Run tests — pass**

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/shared/tracing.py tests/shared/test_tracing.py
git commit -m "feat: LangSmith tracing initialization"
```

---

### Task 5: LangGraph Checkpointer Setup

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/graphs/checkpointer.py`
- Create: `v3/vibe-ai-adoption/tests/graphs/test_checkpointer.py`

This creates the PostgreSQL-backed checkpointer that all LangGraph workflows will use for state persistence.

**Step 1: Write the failing test**

```python
# tests/graphs/test_checkpointer.py
from unittest.mock import patch, MagicMock

from vibe_ai_ops.graphs.checkpointer import create_checkpointer


@patch("vibe_ai_ops.graphs.checkpointer.PostgresSaver")
def test_create_checkpointer_with_postgres(mock_saver):
    mock_saver.from_conn_string.return_value = MagicMock()

    cp = create_checkpointer(conn_string="postgresql://test:test@localhost/test")
    assert cp is not None
    mock_saver.from_conn_string.assert_called_once()


def test_create_checkpointer_falls_back_to_memory():
    cp = create_checkpointer(conn_string=None)
    assert cp is not None  # Returns MemorySaver fallback
```

**Step 2: Run test — fails**

**Step 3: Implement checkpointer factory**

```python
# src/vibe_ai_ops/graphs/checkpointer.py
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None


def create_checkpointer(conn_string: str | None = None):
    """Create a LangGraph checkpointer — Postgres in prod, memory in dev/test."""
    if conn_string and PostgresSaver is not None:
        return PostgresSaver.from_conn_string(conn_string)
    return MemorySaver()
```

**Step 4: Run tests — pass**

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/graphs/checkpointer.py tests/graphs/test_checkpointer.py
git commit -m "feat: LangGraph checkpointer with Postgres + memory fallback"
```

---

### Task 6: CrewAI Base Agent Factory

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/crews/base.py`
- Create: `v3/vibe-ai-adoption/tests/crews/test_base.py`

Creates the standard pattern for defining CrewAI agents from config.

**Step 1: Write the failing test**

```python
# tests/crews/test_base.py
from unittest.mock import MagicMock, patch

from vibe_ai_ops.crews.base import create_crew_agent, create_validation_crew
from vibe_ai_ops.shared.models import AgentConfig


def test_create_crew_agent():
    config = AgentConfig(
        id="m1", name="Segment Research", engine="marketing",
        tier="validation", architecture="temporal_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1_segment_research.md",
    )

    agent = create_crew_agent(
        config=config,
        role="Market Research Specialist",
        goal="Identify and analyze micro-segments for targeted marketing",
        backstory="You are Vibe's expert market researcher.",
    )

    assert agent.role == "Market Research Specialist"
    assert agent.goal == "Identify and analyze micro-segments for targeted marketing"


def test_create_validation_crew():
    config = AgentConfig(
        id="m1", name="Segment Research", engine="marketing",
        tier="validation", architecture="temporal_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1_segment_research.md",
    )

    crew = create_validation_crew(
        config=config,
        role="Market Research Specialist",
        goal="Identify and analyze micro-segments",
        backstory="You are Vibe's expert market researcher.",
        task_description="Research the {segment} micro-segment.",
        expected_output="A detailed segment profile with firmographics, pain points, and messaging angles.",
    )

    assert crew is not None
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
```

**Step 2: Run test — fails**

**Step 3: Implement CrewAI base**

```python
# src/vibe_ai_ops/crews/base.py
from __future__ import annotations

from crewai import Agent, Crew, Task, Process
from langchain_anthropic import ChatAnthropic

from vibe_ai_ops.shared.models import AgentConfig


def _get_llm(model: str = "claude-sonnet-4-5-20250929", temperature: float = 0.7):
    """Create a LangChain-compatible Claude LLM for CrewAI."""
    return ChatAnthropic(
        model=model,
        temperature=temperature,
    )


def create_crew_agent(
    config: AgentConfig,
    role: str,
    goal: str,
    backstory: str,
    tools: list | None = None,
) -> Agent:
    """Create a single CrewAI Agent from config."""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=_get_llm(model=config.model, temperature=config.temperature),
        tools=tools or [],
        verbose=False,
        max_tokens=config.max_tokens,
    )


def create_validation_crew(
    config: AgentConfig,
    role: str,
    goal: str,
    backstory: str,
    task_description: str,
    expected_output: str,
    tools: list | None = None,
) -> Crew:
    """Create a single-agent, single-task Crew for validation-tier agents."""
    agent = create_crew_agent(config, role, goal, backstory, tools)

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
```

**Step 4: Run tests — pass**

**Step 5: Commit**

```bash
git add src/vibe_ai_ops/crews/base.py tests/crews/test_base.py
git commit -m "feat: CrewAI base agent factory + validation crew builder"
```

---

### Task 7: Temporal Worker + Base Workflow

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/temporal/worker.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/temporal/workflows/base.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/temporal/activities/agent_activity.py`
- Create: `v3/vibe-ai-adoption/tests/temporal/test_worker.py`
- Create: `v3/vibe-ai-adoption/tests/temporal/test_base_workflow.py`

This creates the Temporal worker, the base workflow pattern, and the activity that bridges Temporal → LangGraph/CrewAI.

**Step 1: Write the failing test for the activity**

```python
# tests/temporal/test_base_workflow.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from vibe_ai_ops.temporal.activities.agent_activity import (
    run_validation_agent,
    AgentActivityInput,
    AgentActivityOutput,
)


@pytest.mark.asyncio
async def test_agent_activity_input_model():
    inp = AgentActivityInput(
        agent_id="m1",
        agent_config_path="config/agents.yaml",
        input_data={"segments": ["enterprise-fintech"]},
    )
    assert inp.agent_id == "m1"


@pytest.mark.asyncio
@patch("vibe_ai_ops.temporal.activities.agent_activity._execute_agent")
async def test_run_validation_agent(mock_execute):
    mock_execute.return_value = AgentActivityOutput(
        agent_id="m1",
        status="success",
        content="Segment analysis for enterprise-fintech...",
        cost_usd=0.03,
        duration_seconds=4.5,
    )

    result = await run_validation_agent(AgentActivityInput(
        agent_id="m1",
        agent_config_path="config/agents.yaml",
        input_data={"segments": ["enterprise-fintech"]},
    ))

    assert result.status == "success"
    assert result.agent_id == "m1"
```

**Step 2: Run test — fails**

**Step 3: Implement Temporal activity**

```python
# src/vibe_ai_ops/temporal/activities/agent_activity.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from temporalio import activity


@dataclass
class AgentActivityInput:
    agent_id: str
    agent_config_path: str
    input_data: dict[str, Any]


@dataclass
class AgentActivityOutput:
    agent_id: str
    status: str  # "success" | "error"
    content: str = ""
    error: str = ""
    cost_usd: float = 0.0
    duration_seconds: float = 0.0


async def _execute_agent(inp: AgentActivityInput) -> AgentActivityOutput:
    """Execute agent — this will be wired to real CrewAI/LangGraph in later tasks."""
    # Placeholder — each agent type will implement this
    raise NotImplementedError("Wire to specific agent implementation")


@activity.defn
async def run_validation_agent(inp: AgentActivityInput) -> AgentActivityOutput:
    """Temporal activity: run a validation-tier agent."""
    return await _execute_agent(inp)


@activity.defn
async def run_deep_dive_agent(inp: AgentActivityInput) -> AgentActivityOutput:
    """Temporal activity: run a deep-dive agent via LangGraph."""
    return await _execute_agent(inp)
```

**Step 4: Implement Temporal worker**

```python
# src/vibe_ai_ops/temporal/worker.py
from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from vibe_ai_ops.temporal.activities.agent_activity import (
    run_validation_agent,
    run_deep_dive_agent,
)

TASK_QUEUE = "vibe-ai-ops"


async def create_client() -> Client:
    """Create a Temporal client from environment variables."""
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")

    # Check for TLS (Temporal Cloud)
    tls_cert_path = os.environ.get("TEMPORAL_TLS_CERT_PATH")
    tls_key_path = os.environ.get("TEMPORAL_TLS_KEY_PATH")

    if tls_cert_path and tls_key_path:
        with open(tls_cert_path, "rb") as f:
            cert = f.read()
        with open(tls_key_path, "rb") as f:
            key = f.read()
        from temporalio.client import TLSConfig
        tls = TLSConfig(client_cert=cert, client_private_key=key)
        return await Client.connect(address, namespace=namespace, tls=tls)

    return await Client.connect(address, namespace=namespace)


async def run_worker():
    """Start the Temporal worker."""
    client = await create_client()
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        activities=[run_validation_agent, run_deep_dive_agent],
    )
    print(f"Worker started on task queue: {TASK_QUEUE}")
    await worker.run()


def main():
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
```

**Step 5: Write worker test**

```python
# tests/temporal/test_worker.py
from unittest.mock import patch, AsyncMock

from vibe_ai_ops.temporal.worker import TASK_QUEUE


def test_task_queue_name():
    assert TASK_QUEUE == "vibe-ai-ops"
```

**Step 6: Run tests**

Run: `cd v3/vibe-ai-adoption && pytest tests/temporal/ -v`
Expected: Pass

**Step 7: Commit**

```bash
git add src/vibe_ai_ops/temporal/ tests/temporal/
git commit -m "feat: Temporal worker + base agent activities"
```

---

### Task 8: Temporal Cron Schedules

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/temporal/workflows/scheduled.py`
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/temporal/schedules.py`
- Create: `v3/vibe-ai-adoption/tests/temporal/test_schedules.py`

This creates Temporal Schedules for all cron-triggered agents.

**Step 1: Write the failing test**

```python
# tests/temporal/test_schedules.py
from vibe_ai_ops.temporal.schedules import parse_cron_to_temporal, build_schedule_specs
from vibe_ai_ops.shared.models import AgentConfig


def test_parse_cron_to_temporal():
    spec = parse_cron_to_temporal("0 9 * * 1")
    assert spec["minute"] == [0]
    assert spec["hour"] == [9]
    assert spec["day_of_week"] == [1]


def test_build_schedule_specs_filters_cron_agents():
    configs = [
        AgentConfig(
            id="m1", name="Segment Research", engine="marketing",
            tier="validation", architecture="temporal_crewai",
            trigger={"type": "cron", "schedule": "0 9 * * 1"},
            output_channel="slack:#test", prompt_file="test.md",
        ),
        AgentConfig(
            id="s1", name="Lead Qual", engine="sales",
            tier="deep_dive", architecture="temporal_langgraph_crewai",
            trigger={"type": "webhook", "event_source": "hubspot:new_lead"},
            output_channel="slack:#test", prompt_file="test.md",
        ),
    ]
    specs = build_schedule_specs(configs)
    assert len(specs) == 1
    assert specs[0]["agent_id"] == "m1"
```

**Step 2: Implement schedules**

```python
# src/vibe_ai_ops/temporal/schedules.py
from __future__ import annotations

from vibe_ai_ops.shared.models import AgentConfig


def parse_cron_to_temporal(cron_expr: str) -> dict:
    """Parse 5-field cron to Temporal ScheduleSpec fields."""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron: {cron_expr}")

    minute, hour, day, month, dow = parts

    def parse_field(val: str) -> list[int] | None:
        if val == "*":
            return None
        return [int(v) for v in val.split(",")]

    result = {}
    if minute != "*":
        result["minute"] = parse_field(minute)
    if hour != "*":
        result["hour"] = parse_field(hour)
    if day != "*":
        result["day_of_month"] = parse_field(day)
    if month != "*":
        result["month"] = parse_field(month)
    if dow != "*":
        result["day_of_week"] = parse_field(dow)
    return result


def build_schedule_specs(configs: list[AgentConfig]) -> list[dict]:
    """Build Temporal schedule specs for all cron-triggered agents."""
    specs = []
    for config in configs:
        if config.trigger.type.value == "cron" and config.trigger.schedule:
            cron_spec = parse_cron_to_temporal(config.trigger.schedule)
            specs.append({
                "agent_id": config.id,
                "name": config.name,
                "cron_spec": cron_spec,
                "cron_expression": config.trigger.schedule,
            })
    return specs
```

**Step 3: Run tests — pass**

**Step 4: Commit**

```bash
git add src/vibe_ai_ops/temporal/schedules.py tests/temporal/test_schedules.py
git commit -m "feat: Temporal cron schedule parser for agent triggers"
```

---

### Task 9: End-to-End Smoke Test (All Layers)

**Files:**
- Create: `v3/vibe-ai-adoption/tests/test_integration.py`

This test verifies the full 3-layer stack wires together: config → CrewAI agent → LangGraph state → Temporal activity format.

**Step 1: Write the integration test**

```python
# tests/test_integration.py
"""Integration test: verify all 3 layers wire together."""
from unittest.mock import patch, MagicMock

from vibe_ai_ops.shared.models import AgentConfig
from vibe_ai_ops.shared.config import load_agent_configs
from vibe_ai_ops.crews.base import create_validation_crew, create_crew_agent
from vibe_ai_ops.graphs.checkpointer import create_checkpointer
from vibe_ai_ops.temporal.schedules import build_schedule_specs
from vibe_ai_ops.temporal.activities.agent_activity import AgentActivityInput


def test_config_loads_into_all_layers():
    """Config → CrewAI + LangGraph + Temporal all connect."""
    # Create a test config
    config = AgentConfig(
        id="m1", name="Segment Research", engine="marketing",
        tier="validation", architecture="temporal_crewai",
        trigger={"type": "cron", "schedule": "0 9 * * 1"},
        output_channel="slack:#marketing-agents",
        prompt_file="marketing/m1_segment_research.md",
    )

    # Layer 3: CrewAI — can create an agent
    agent = create_crew_agent(
        config=config,
        role="Market Research Specialist",
        goal="Identify micro-segments",
        backstory="You are Vibe's market researcher.",
    )
    assert agent.role == "Market Research Specialist"

    # Layer 2: LangGraph — can create a checkpointer
    cp = create_checkpointer(conn_string=None)  # memory fallback
    assert cp is not None

    # Layer 1: Temporal — can build schedule specs
    specs = build_schedule_specs([config])
    assert len(specs) == 1
    assert specs[0]["agent_id"] == "m1"

    # Activity input works
    inp = AgentActivityInput(
        agent_id="m1",
        agent_config_path="config/agents.yaml",
        input_data={"segments": ["enterprise-fintech"]},
    )
    assert inp.agent_id == "m1"
```

**Step 2: Run the full test suite**

Run: `cd v3/vibe-ai-adoption && pytest tests/ -v --tb=short`
Expected: All tests pass (20+ tests)

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: integration smoke test — all 3 layers wire together"
```

---

## Phase 2: First Agent — Lead Qualification S1 (Week 3-4)

This phase builds the complete end-to-end pipeline for one agent, establishing the pattern for all others.

### Task 10: Master Agent Config (agents.yaml)

**Files:**
- Create: `v3/vibe-ai-adoption/config/agents.yaml`

**Step 1: Write the complete 20-agent config**

```yaml
# config/agents.yaml
# All 20 agents — 3 deep-dive (temporal_langgraph_crewai), 17 validation (temporal_crewai)

agents:
  # ═══════════════════════════════════════════
  # ENGINE 1: MARKETING (6 agents)
  # ═══════════════════════════════════════════

  - id: m1
    name: Segment Research
    engine: marketing
    tier: validation
    architecture: temporal_crewai
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
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 10 * * 1,4" }  # Mon/Thu 10am
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m2_message_testing.md
    enabled: true

  - id: m3
    name: Content Generation
    engine: marketing
    tier: deep_dive
    architecture: temporal_langgraph_crewai
    trigger: { type: cron, schedule: "0 9 * * *" }  # Daily 9am
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m3_content_generation.md
    enabled: true
    max_tokens: 8192
    crew_config:
      agents: [researcher, writer, editor]
      process: sequential
    graph_config:
      nodes: [research, outline, draft, polish]
      checkpointed: true

  - id: m4
    name: Content Repurposing
    engine: marketing
    tier: validation
    architecture: temporal_crewai
    trigger: { type: event, event_source: "m3:complete" }
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m4_content_repurposing.md
    enabled: true

  - id: m5
    name: Distribution
    engine: marketing
    tier: validation
    architecture: temporal_crewai
    trigger: { type: event, event_source: "m4:complete" }
    output_channel: "slack:#marketing-agents"
    prompt_file: marketing/m5_distribution.md
    enabled: true

  - id: m6
    name: Journey Optimization
    engine: marketing
    tier: validation
    architecture: temporal_crewai
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
    architecture: temporal_langgraph_crewai
    trigger: { type: webhook, event_source: "hubspot:new_lead" }
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s1_lead_qualification.md
    enabled: true
    model: claude-sonnet-4-5-20250929
    max_tokens: 4096
    temperature: 0.3
    crew_config:
      agents: [enricher, scorer, router]
      process: sequential
    graph_config:
      nodes: [enrich, score, route, update_crm]
      checkpointed: true

  - id: s2
    name: Buyer Intelligence
    engine: sales
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 7 * * *" }  # Daily 7am
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s2_buyer_intelligence.md
    enabled: true
    max_tokens: 8192

  - id: s3
    name: Engagement
    engine: sales
    tier: deep_dive
    architecture: temporal_langgraph_crewai
    trigger: { type: event, event_source: "s1:qualified" }
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s3_engagement.md
    enabled: true
    crew_config:
      agents: [researcher, copywriter, strategist]
      process: sequential
    graph_config:
      nodes: [research_buyer, generate_sequence, personalize, format]
      checkpointed: true

  - id: s4
    name: Deal Support
    engine: sales
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 7 * * 1,2,3,4,5" }  # Weekdays 7am
    output_channel: "slack:#sales-agents"
    prompt_file: sales/s4_deal_support.md
    enabled: true
    max_tokens: 8192

  - id: s5
    name: Nurture
    engine: sales
    tier: validation
    architecture: temporal_crewai
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
    architecture: temporal_crewai
    trigger: { type: webhook, event_source: "hubspot:deal_won" }
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c1_onboarding.md
    enabled: true

  - id: c2
    name: Success Advisor
    engine: cs
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 10 * * 2" }  # Tuesday 10am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c2_success_advisor.md
    enabled: true
    max_tokens: 8192

  - id: c3
    name: Health Intelligence
    engine: cs
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 2 * * *" }  # Daily 2am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c3_health_intelligence.md
    enabled: true

  - id: c4
    name: Expansion
    engine: cs
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 9 * * 3" }  # Wednesday 9am
    output_channel: "slack:#cs-agents"
    prompt_file: cs/c4_expansion.md
    enabled: true

  - id: c5
    name: Customer Voice
    engine: cs
    tier: validation
    architecture: temporal_crewai
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
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 6 * * *" }  # Daily 6am
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r1_funnel_monitor.md
    enabled: true

  - id: r2
    name: Deal Risk & Forecast
    engine: intelligence
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 7 * * 1,2,3,4,5" }  # Weekdays 7am
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r2_deal_risk_forecast.md
    enabled: true
    max_tokens: 8192

  - id: r3
    name: Conversation Analysis
    engine: intelligence
    tier: validation
    architecture: temporal_crewai
    trigger: { type: cron, schedule: "0 8 * * 1" }  # Monday 8am
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r3_conversation_analysis.md
    enabled: true
    max_tokens: 8192

  - id: r4
    name: NL Revenue Interface
    engine: intelligence
    tier: validation
    architecture: temporal_crewai
    trigger: { type: on_demand }
    output_channel: "slack:#revenue-intelligence"
    prompt_file: intelligence/r4_nl_revenue_interface.md
    enabled: true
    max_tokens: 4096
    temperature: 0.3
```

**Step 2: Verify config loads**

Run: `cd v3/vibe-ai-adoption && source .venv/bin/activate && python -c "from vibe_ai_ops.shared.config import load_agent_configs; cs = load_agent_configs('config/agents.yaml'); print(f'{len(cs)} agents loaded'); [print(f'  {c.id}: {c.name} ({c.architecture.value})') for c in cs]"`

Expected: `20 agents loaded` with architecture types shown.

**Step 3: Commit**

```bash
git add config/agents.yaml
git commit -m "feat: master agent config — all 20 agents with architecture types"
```

---

### Task 11: S1 Lead Qualification — CrewAI Crew

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/crews/sales/s1_lead_qualification.py`
- Create: `v3/vibe-ai-adoption/config/prompts/sales/s1_lead_qualification.md`
- Create: `v3/vibe-ai-adoption/tests/crews/sales/test_s1_crew.py`

**Reference:** DESIGN.md Section 5 — S1 Lead Qualification Agent spec.

**Step 1: Write the system prompt**

Create `config/prompts/sales/s1_lead_qualification.md` with the full Lead Qualification agent prompt based on DESIGN.md Section 5 (S1). Include: role, scoring rubric (fit 0-100, intent 0-100, urgency 0-100), routing rules (80+ sales, 50-79 nurture, <50 education), output format (JSON with scores + reasoning + route).

**Step 2: Write the failing test**

```python
# tests/crews/sales/test_s1_crew.py
from unittest.mock import patch, MagicMock

from vibe_ai_ops.crews.sales.s1_lead_qualification import (
    create_lead_qual_crew,
    LeadScore,
)
from vibe_ai_ops.shared.models import AgentConfig


def _make_config():
    return AgentConfig(
        id="s1", name="Lead Qualification", engine="sales",
        tier="deep_dive", architecture="temporal_langgraph_crewai",
        trigger={"type": "webhook", "event_source": "hubspot:new_lead"},
        output_channel="slack:#sales-agents",
        prompt_file="sales/s1_lead_qualification.md",
        temperature=0.3,
    )


def test_lead_score_composite():
    score = LeadScore(fit_score=80, intent_score=70, urgency_score=60,
                      reasoning="test", route="sales")
    expected = 0.4 * 80 + 0.35 * 70 + 0.25 * 60
    assert score.composite == expected


def test_lead_score_routing_logic():
    high = LeadScore(fit_score=90, intent_score=85, urgency_score=80,
                     reasoning="great", route="sales")
    assert high.composite >= 80

    mid = LeadScore(fit_score=60, intent_score=55, urgency_score=50,
                    reasoning="okay", route="nurture")
    assert 50 <= mid.composite < 80

    low = LeadScore(fit_score=30, intent_score=20, urgency_score=10,
                    reasoning="poor", route="education")
    assert low.composite < 50


def test_create_lead_qual_crew():
    config = _make_config()
    crew = create_lead_qual_crew(config, system_prompt="You are a lead qualifier.")
    assert crew is not None
    assert len(crew.agents) == 1  # Single agent for scoring
    assert len(crew.tasks) == 1
```

**Step 3: Run test — fails**

**Step 4: Implement Lead Qual crew**

```python
# src/vibe_ai_ops/crews/sales/s1_lead_qualification.py
from __future__ import annotations

from pydantic import BaseModel
from crewai import Crew, Task, Process

from vibe_ai_ops.crews.base import create_crew_agent
from vibe_ai_ops.shared.models import AgentConfig


class LeadScore(BaseModel):
    fit_score: int  # 0-100
    intent_score: int  # 0-100
    urgency_score: int  # 0-100
    reasoning: str
    route: str  # "sales" | "nurture" | "education" | "disqualify"

    @property
    def composite(self) -> float:
        return 0.4 * self.fit_score + 0.35 * self.intent_score + 0.25 * self.urgency_score


def create_lead_qual_crew(config: AgentConfig, system_prompt: str) -> Crew:
    """Create the Lead Qualification crew — single agent, single task."""
    agent = create_crew_agent(
        config=config,
        role="Lead Qualification Specialist",
        goal="Score and route incoming leads based on fit, intent, and urgency",
        backstory=system_prompt,
    )

    task = Task(
        description=(
            "Score this lead. Evaluate:\n"
            "- Fit (0-100): Does this match our ICP?\n"
            "- Intent (0-100): Are there buying signals?\n"
            "- Urgency (0-100): Is there a trigger event?\n\n"
            "Route: 80+ → sales, 50-79 → nurture, <50 → education, ICP mismatch → disqualify\n\n"
            "Lead data: {lead_data}\n\n"
            "Return ONLY valid JSON with: fit_score, intent_score, urgency_score, reasoning, route"
        ),
        expected_output="JSON with fit_score, intent_score, urgency_score, reasoning, route",
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
```

**Step 5: Run tests — pass**

**Step 6: Commit**

```bash
git add src/vibe_ai_ops/crews/sales/s1_lead_qualification.py \
  tests/crews/sales/test_s1_crew.py
git commit -m "feat: S1 Lead Qualification CrewAI crew + scoring model"
```

---

### Task 12: S1 Lead Qualification — LangGraph Workflow

**Files:**
- Create: `v3/vibe-ai-adoption/src/vibe_ai_ops/graphs/sales/s1_lead_qualification.py`
- Create: `v3/vibe-ai-adoption/tests/graphs/sales/test_s1_graph.py`

This creates the LangGraph state machine: enrich → score → route → update CRM.

**Step 1: Write the failing test**

```python
# tests/graphs/sales/test_s1_graph.py
from unittest.mock import MagicMock, patch
import json

from vibe_ai_ops.graphs.sales.s1_lead_qualification import (
    create_lead_qual_graph,
    LeadQualState,
)


def test_lead_qual_state_initial():
    state = LeadQualState(
        contact_id="123",
        source="website",
    )
    assert state.contact_id == "123"
    assert state.enriched_data == {}
    assert state.score is None
    assert state.route is None


@patch("vibe_ai_ops.graphs.sales.s1_lead_qualification._enrich_lead")
@patch("vibe_ai_ops.graphs.sales.s1_lead_qualification._score_lead")
@patch("vibe_ai_ops.graphs.sales.s1_lead_qualification._route_lead")
@patch("vibe_ai_ops.graphs.sales.s1_lead_qualification._update_crm")
def test_graph_executes_all_nodes(mock_crm, mock_route, mock_score, mock_enrich):
    mock_enrich.return_value = {
        "contact_id": "123", "source": "website",
        "enriched_data": {"company": "BigCorp", "title": "CTO"},
    }
    mock_score.return_value = {
        "contact_id": "123", "source": "website",
        "enriched_data": {"company": "BigCorp", "title": "CTO"},
        "score": {"fit_score": 85, "intent_score": 70, "urgency_score": 60,
                  "reasoning": "CTO at large corp", "route": "sales"},
    }
    mock_route.return_value = {
        "contact_id": "123", "source": "website",
        "enriched_data": {"company": "BigCorp", "title": "CTO"},
        "score": {"fit_score": 85, "intent_score": 70, "urgency_score": 60,
                  "reasoning": "CTO at large corp", "route": "sales"},
        "route": "sales",
    }
    mock_crm.return_value = {
        "contact_id": "123", "source": "website",
        "enriched_data": {"company": "BigCorp", "title": "CTO"},
        "score": {"fit_score": 85, "intent_score": 70, "urgency_score": 60,
                  "reasoning": "CTO at large corp", "route": "sales"},
        "route": "sales",
        "crm_updated": True,
    }

    graph = create_lead_qual_graph()
    assert graph is not None
```

**Step 2: Implement LangGraph workflow**

```python
# src/vibe_ai_ops/graphs/sales/s1_lead_qualification.py
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END


class LeadQualState(TypedDict, total=False):
    contact_id: str
    source: str
    enriched_data: dict[str, Any]
    score: dict[str, Any] | None
    route: str | None
    crm_updated: bool


def _enrich_lead(state: LeadQualState) -> LeadQualState:
    """Node 1: Enrich lead from HubSpot + web research."""
    # Will be wired to HubSpotClient in Task 13
    return state


def _score_lead(state: LeadQualState) -> LeadQualState:
    """Node 2: Score lead using CrewAI Lead Qual crew."""
    # Will be wired to CrewAI crew in Task 13
    return state


def _route_lead(state: LeadQualState) -> LeadQualState:
    """Node 3: Route based on composite score."""
    score = state.get("score", {})
    composite = (
        0.4 * score.get("fit_score", 0)
        + 0.35 * score.get("intent_score", 0)
        + 0.25 * score.get("urgency_score", 0)
    )
    if composite >= 80:
        state["route"] = "sales"
    elif composite >= 50:
        state["route"] = "nurture"
    else:
        state["route"] = "education"
    return state


def _update_crm(state: LeadQualState) -> LeadQualState:
    """Node 4: Update HubSpot with scores and route."""
    # Will be wired to HubSpotClient in Task 13
    state["crm_updated"] = True
    return state


def create_lead_qual_graph(checkpointer=None) -> StateGraph:
    """Create the Lead Qualification LangGraph workflow."""
    workflow = StateGraph(LeadQualState)

    workflow.add_node("enrich", _enrich_lead)
    workflow.add_node("score", _score_lead)
    workflow.add_node("route", _route_lead)
    workflow.add_node("update_crm", _update_crm)

    workflow.set_entry_point("enrich")
    workflow.add_edge("enrich", "score")
    workflow.add_edge("score", "route")
    workflow.add_edge("route", "update_crm")
    workflow.add_edge("update_crm", END)

    return workflow.compile(checkpointer=checkpointer)
```

**Step 3: Run tests — pass**

**Step 4: Commit**

```bash
git add src/vibe_ai_ops/graphs/sales/s1_lead_qualification.py \
  tests/graphs/sales/test_s1_graph.py
git commit -m "feat: S1 Lead Qualification LangGraph workflow (enrich → score → route → CRM)"
```

---

### Task 13: S1 Lead Qualification — Wire All 3 Layers

**Files:**
- Modify: `v3/vibe-ai-adoption/src/vibe_ai_ops/graphs/sales/s1_lead_qualification.py`
- Modify: `v3/vibe-ai-adoption/src/vibe_ai_ops/temporal/activities/agent_activity.py`
- Create: `v3/vibe-ai-adoption/tests/test_s1_e2e.py`

Wire the real implementations: HubSpot enrichment, CrewAI scoring, CRM update, Slack output — all flowing through Temporal → LangGraph → CrewAI.

**Step 1: Write the end-to-end test**

```python
# tests/test_s1_e2e.py
"""End-to-end test for S1 Lead Qualification through all 3 layers."""
from unittest.mock import MagicMock, patch
import json

from vibe_ai_ops.graphs.sales.s1_lead_qualification import create_lead_qual_graph
from vibe_ai_ops.graphs.checkpointer import create_checkpointer


@patch("vibe_ai_ops.graphs.sales.s1_lead_qualification.hubspot_client")
@patch("vibe_ai_ops.graphs.sales.s1_lead_qualification.crew_kickoff")
def test_s1_full_pipeline(mock_crew, mock_hs):
    """S1: HubSpot enrich → CrewAI score → route → CRM update."""
    mock_hs.get_contact.return_value = {
        "email": "jane@bigcorp.com",
        "firstname": "Jane",
        "lastname": "Smith",
        "company": "BigCorp",
        "jobtitle": "CTO",
    }
    mock_crew.return_value = json.dumps({
        "fit_score": 85, "intent_score": 70, "urgency_score": 60,
        "reasoning": "CTO at large corp", "route": "sales",
    })

    graph = create_lead_qual_graph(checkpointer=create_checkpointer())
    result = graph.invoke({
        "contact_id": "123",
        "source": "website",
    })

    assert result["route"] == "sales"
    assert result["crm_updated"] is True
    mock_hs.update_contact.assert_called_once()
```

This test will guide the wiring implementation. The actual implementation connects:
- `_enrich_lead` → calls `hubspot_client.get_contact()`
- `_score_lead` → calls `crew.kickoff()` (CrewAI)
- `_update_crm` → calls `hubspot_client.update_contact()`

**Step 2: Wire implementations in s1_lead_qualification.py graph nodes**

**Step 3: Run tests — pass**

**Step 4: Commit**

```bash
git add src/vibe_ai_ops/graphs/sales/s1_lead_qualification.py \
  src/vibe_ai_ops/temporal/activities/agent_activity.py \
  tests/test_s1_e2e.py
git commit -m "feat: S1 Lead Qual wired end-to-end — Temporal → LangGraph → CrewAI → HubSpot"
```

---

## Phase 3: Marketing Engine (Week 5-6)

Follows the same 3-layer pattern established in Phase 2. For each agent:
1. Write CrewAI crew definition
2. Write LangGraph graph (deep-dive only)
3. Wire to Temporal activity
4. Write system prompt
5. Test

### Task 14: Marketing Agent Prompts (M1-M6)

Write all 6 marketing system prompts. Reference DESIGN.md Section 4 for each agent's spec.

### Task 15: M3 Content Generation — Deep Dive Pipeline

Same 3-layer pattern as S1: CrewAI crew (researcher + writer + editor) → LangGraph graph (research → outline → draft → polish) → Temporal activity.

### Task 16: Validation Agents — Marketing (M1, M2, M4, M5, M6)

For each: CrewAI validation crew → Temporal activity. No LangGraph needed for validation tier.

---

## Phase 4: Sales + CS + Intelligence (Week 7-10)

### Task 17: Sales Agent Prompts (S1-S5)
### Task 18: S3 Engagement — Deep Dive Pipeline
### Task 19: Validation Agents — Sales (S2, S4, S5)
### Task 20: CS Agent Prompts (C1-C5) + Validation Agents
### Task 21: Intelligence Agent Prompts (R1-R4) + Validation Agents

---

## Phase 5: Production Wiring (Week 11-12)

### Task 22: Main Entry Point + Temporal Schedule Registration

Wire `build_system()` that:
1. Loads all configs
2. Creates all CrewAI crews
3. Registers Temporal schedules for all cron agents
4. Starts Temporal worker

### Task 23: CLI for Manual Agent Execution

```bash
python -m vibe_ai_ops.cli run s1 --input '{"contact_id": "123"}'
python -m vibe_ai_ops.cli list
python -m vibe_ai_ops.cli stats m3
```

### Task 24: Full Test Suite

Run all tests, fix failures.

### Task 25: Smoke Test with Real APIs

Set up .env, docker compose up, run single agents with real Claude/HubSpot/Slack.

### Task 26: Go Live

Start Temporal worker, register all schedules, verify first runs complete.

---

## Summary

| Phase | Tasks | What's Built | Timeline |
|-------|-------|-------------|----------|
| **Phase 1: Foundation** | Tasks 1-9 | 3-layer infra: Temporal worker + LangGraph checkpointer + CrewAI factory + shared clients | Week 1-2 |
| **Phase 2: First Agent (S1)** | Tasks 10-13 | Full S1 pipeline through all 3 layers — the pattern for everything else | Week 3-4 |
| **Phase 3: Marketing** | Tasks 14-16 | M1-M6 agents + M3 deep-dive pipeline | Week 5-6 |
| **Phase 4: Sales+CS+Intel** | Tasks 17-21 | S2-S5, C1-C5, R1-R4 + S3 deep-dive pipeline | Week 7-10 |
| **Phase 5: Production** | Tasks 22-26 | Main entry, CLI, full tests, smoke test, go live | Week 11-12 |

**Total: 26 tasks. 12-week timeline. All 20 agents running on Temporal + LangGraph + CrewAI.**

---

## Infrastructure Costs (Monthly)

| Component | Cost |
|-----------|------|
| Temporal Cloud | $200-500 |
| Claude API (20 agents) | $2,000-5,000 |
| LangSmith | $400 |
| PostgreSQL (managed) | $50-100 |
| **Total** | **$2,650-6,000/month** |

---

## Post-Launch (Week 13+)

- Graduate validation agents to deep-dive based on data
- Add human-in-the-loop gates for S3 outbound emails
- Build Slack command interface for R4 (NL Revenue Interface)
- Dashboard for agent health monitoring
- Add Temporal Signal handlers for webhook-triggered agents
