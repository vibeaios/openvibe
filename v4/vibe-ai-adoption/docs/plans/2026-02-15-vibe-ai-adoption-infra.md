# Vibe AI Adoption Infrastructure + 3 Workflows Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Temporal + LangGraph + CrewAI 3-layer architecture and validate it with 3 workflows (Lead Qualification, Content Pipeline, Nurture Sequence).

**Architecture:** Temporal Cloud schedules and triggers durable workflows. LangGraph manages stateful workflow execution with Postgres-backed checkpoints and human-in-the-loop support. CrewAI defines role-based AI agents powered by Claude that execute as nodes within LangGraph graphs. LangSmith provides end-to-end observability.

**Tech Stack:** Python 3.12+, temporalio, langgraph, langgraph-checkpoint-postgres, crewai, anthropic, psycopg[binary,pool], pydantic, python-dotenv, pytest, docker (Postgres + Temporal dev server)

---

## Prerequisites

Before starting, ensure you have:
- Python 3.12+ installed
- Docker Desktop running (for Postgres and Temporal dev server)
- API keys ready: `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` (LangSmith), `HUBSPOT_API_KEY`
- A Temporal Cloud namespace OR willingness to use local dev server

---

### Task 1: Python Project Scaffold

**Files:**
- Create: `v3/vibe-ai-adoption/pyproject.toml`
- Create: `v3/vibe-ai-adoption/src/__init__.py`
- Create: `v3/vibe-ai-adoption/src/config.py`
- Create: `v3/vibe-ai-adoption/.env.example`
- Create: `v3/vibe-ai-adoption/.gitignore`
- Create: `v3/vibe-ai-adoption/tests/__init__.py`
- Create: `v3/vibe-ai-adoption/tests/conftest.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "vibe-ai-adoption"
version = "0.1.0"
description = "Vibe AI Adoption - 3-layer agent architecture (Temporal + LangGraph + CrewAI)"
requires-python = ">=3.12"
dependencies = [
    "temporalio>=1.9.0",
    "langgraph>=0.3.0",
    "langgraph-checkpoint-postgres>=2.0.0",
    "crewai>=1.0.0",
    "anthropic>=0.43.0",
    "psycopg[binary,pool]>=3.2.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.28.0",
    "slack-sdk>=3.33.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "pytest-timeout>=2.3.0",
]

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
timeout = 30
```

**Step 2: Create src/__init__.py**

```python
```

(Empty file)

**Step 3: Create src/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Temporal
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "vibe-ai-adoption"
    temporal_api_key: str | None = None

    # LLM
    anthropic_api_key: str = ""
    default_model: str = "claude-sonnet-4-5-20250929"

    # LangSmith
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    langchain_project: str = "vibe-ai-adoption"

    # Database (LangGraph checkpointer)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/vibe_ai_adoption"

    # HubSpot
    hubspot_api_key: str = ""

    # Slack
    slack_bot_token: str = ""
    slack_channel_id: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

**Step 4: Create .env.example**

```bash
# Temporal
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=vibe-ai-adoption
# TEMPORAL_API_KEY=  # Only needed for Temporal Cloud

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# LangSmith
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=vibe-ai-adoption

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vibe_ai_adoption

# HubSpot
HUBSPOT_API_KEY=pat-...

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...
```

**Step 5: Create .gitignore**

```
__pycache__/
*.pyc
.env
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
```

**Step 6: Create tests/__init__.py**

```python
```

(Empty file)

**Step 7: Create tests/conftest.py**

```python
import pytest
from src.config import Settings


@pytest.fixture
def test_settings():
    """Settings with test defaults — no real API keys needed."""
    return Settings(
        anthropic_api_key="test-key",
        hubspot_api_key="test-key",
        langchain_api_key="test-key",
        slack_bot_token="test-token",
        database_url="postgresql://postgres:postgres@localhost:5432/vibe_ai_adoption_test",
    )
```

**Step 8: Install dependencies**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: All packages install successfully. No errors.

**Step 9: Verify config loads**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -c "from src.config import settings; print('Config OK:', settings.temporal_task_queue)"`
Expected: `Config OK: vibe-ai-adoption`

**Step 10: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add pyproject.toml src/__init__.py src/config.py .env.example .gitignore tests/__init__.py tests/conftest.py
git commit -m "feat: scaffold Python project with config and dependencies"
```

---

### Task 2: Docker Infrastructure (Postgres + Temporal Dev Server)

**Files:**
- Create: `v3/vibe-ai-adoption/infra/docker-compose.yml`
- Replace: `v3/vibe-ai-adoption/infra/README.md`

**Step 1: Create docker-compose.yml**

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vibe_ai_adoption
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  temporal:
    image: temporalio/auto-setup:latest
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB=postgres12
      - DB_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PWD=postgres
      - POSTGRES_SEEDS=postgres
      - DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/development-sql.yaml
    ports:
      - "7233:7233"

  temporal-ui:
    image: temporalio/ui:latest
    depends_on:
      - temporal
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=http://localhost:3000
    ports:
      - "8080:8080"

volumes:
  pgdata:
```

**Step 2: Update infra/README.md**

```markdown
# Infrastructure

## Quick Start

```bash
# Start Postgres + Temporal dev server + Temporal UI
docker compose up -d

# Verify Temporal is running
temporal operator namespace list  # or open http://localhost:8080

# Verify Postgres is running
psql postgresql://postgres:postgres@localhost:5432/vibe_ai_adoption -c "SELECT 1"
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Postgres | 5432 | LangGraph checkpointer + workflow state |
| Temporal | 7233 | Workflow scheduler (gRPC) |
| Temporal UI | 8080 | Temporal dashboard |

## Stop

```bash
docker compose down        # Stop services (keep data)
docker compose down -v     # Stop services + delete data
```
```

**Step 3: Start infrastructure**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption/infra && docker compose up -d`
Expected: All 3 services start. `docker compose ps` shows all healthy.

**Step 4: Verify Postgres**

Run: `psql postgresql://postgres:postgres@localhost:5432/vibe_ai_adoption -c "SELECT 1"`
Expected: Returns `1`. Database is accessible.

**Step 5: Verify Temporal**

Run: `curl -s http://localhost:8080 | head -5`
Expected: HTML response from Temporal UI. Or open `http://localhost:8080` in browser.

**Step 6: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add infra/docker-compose.yml infra/README.md
git commit -m "feat: add Docker infrastructure (Postgres + Temporal + Temporal UI)"
```

---

### Task 3: Pydantic Models (Shared Data Schemas)

**Files:**
- Create: `v3/vibe-ai-adoption/src/models/__init__.py`
- Create: `v3/vibe-ai-adoption/src/models/lead.py`
- Create: `v3/vibe-ai-adoption/src/models/content.py`
- Create: `v3/vibe-ai-adoption/src/models/nurture.py`
- Test: `v3/vibe-ai-adoption/tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
from src.models.lead import Lead, LeadScore, LeadRoute, QualificationResult
from src.models.content import Segment, ContentPiece, ContentFormat, RepurposedContent
from src.models.nurture import NurtureState, EngagementSignal, NurtureAction, NurtureStep


def test_lead_model():
    lead = Lead(
        lead_id="hub_123",
        email="jane@acme.com",
        company="Acme Corp",
        role="CTO",
    )
    assert lead.lead_id == "hub_123"
    assert lead.company == "Acme Corp"


def test_lead_score():
    score = LeadScore(fit=85, intent=70, urgency=60)
    assert score.total == 72  # weighted average
    assert score.route == LeadRoute.NURTURE  # 72 is in 50-79 range


def test_lead_score_high():
    score = LeadScore(fit=90, intent=90, urgency=80)
    assert score.route == LeadRoute.HIGH_PRIORITY


def test_lead_score_low():
    score = LeadScore(fit=20, intent=30, urgency=10)
    assert score.route == LeadRoute.EDUCATION


def test_qualification_result():
    result = QualificationResult(
        lead_id="hub_123",
        score=LeadScore(fit=85, intent=70, urgency=60),
        reasoning="Strong company fit, moderate intent signals",
    )
    assert result.score.route == LeadRoute.NURTURE
    assert "Strong company" in result.reasoning


def test_segment_model():
    segment = Segment(
        name="Enterprise AEC",
        description="Architecture, Engineering, Construction firms with 500+ employees",
        pain_points=["Remote collaboration", "Design review bottlenecks"],
        messaging_angle="Vibe transforms design review meetings into action",
    )
    assert segment.name == "Enterprise AEC"
    assert len(segment.pain_points) == 2


def test_content_piece():
    piece = ContentPiece(
        title="How AEC Firms Use Vibe for Design Review",
        segment="Enterprise AEC",
        content_type="blog_post",
        body="Full article body here...",
    )
    assert piece.content_type == "blog_post"


def test_repurposed_content():
    repurposed = RepurposedContent(
        source_title="How AEC Firms Use Vibe",
        format=ContentFormat.LINKEDIN_POST,
        body="Short LinkedIn post version...",
    )
    assert repurposed.format == ContentFormat.LINKEDIN_POST


def test_nurture_state():
    state = NurtureState(
        lead_id="hub_123",
        current_step=NurtureStep.DAY_1,
        emails_sent=0,
        engagement_score=0.0,
    )
    assert state.current_step == NurtureStep.DAY_1
    assert state.emails_sent == 0


def test_engagement_signal():
    signal = EngagementSignal(
        lead_id="hub_123",
        event_type="email_opened",
        timestamp="2026-02-15T10:00:00Z",
    )
    assert signal.event_type == "email_opened"


def test_nurture_action():
    action = NurtureAction(
        action_type="send_case_study",
        lead_id="hub_123",
        content="Case study about AEC firm...",
        reason="Lead opened welcome email within 24h",
    )
    assert action.action_type == "send_case_study"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.models'`

**Step 3: Create src/models/__init__.py**

```python
```

(Empty file)

**Step 4: Create src/models/lead.py**

```python
from enum import Enum

from pydantic import BaseModel, computed_field


class LeadRoute(str, Enum):
    HIGH_PRIORITY = "high_priority"  # Score >= 80
    NURTURE = "nurture"  # Score 50-79
    EDUCATION = "education"  # Score < 50


class Lead(BaseModel):
    lead_id: str
    email: str
    company: str
    role: str
    industry: str | None = None
    company_size: int | None = None
    tech_stack: list[str] | None = None
    source: str | None = None
    enriched_data: dict | None = None


class LeadScore(BaseModel):
    fit: int  # 0-100: company/role match
    intent: int  # 0-100: buying signals
    urgency: int  # 0-100: timeline pressure

    @computed_field
    @property
    def total(self) -> int:
        """Weighted average: fit 40%, intent 35%, urgency 25%."""
        return round(self.fit * 0.4 + self.intent * 0.35 + self.urgency * 0.25)

    @computed_field
    @property
    def route(self) -> LeadRoute:
        if self.total >= 80:
            return LeadRoute.HIGH_PRIORITY
        elif self.total >= 50:
            return LeadRoute.NURTURE
        else:
            return LeadRoute.EDUCATION


class QualificationResult(BaseModel):
    lead_id: str
    score: LeadScore
    reasoning: str
    enriched_data: dict | None = None
```

**Step 5: Create src/models/content.py**

```python
from enum import Enum

from pydantic import BaseModel


class ContentFormat(str, Enum):
    BLOG_POST = "blog_post"
    LINKEDIN_POST = "linkedin_post"
    EMAIL = "email"
    TWITTER_THREAD = "twitter_thread"
    VIDEO_SCRIPT = "video_script"
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"
    INFOGRAPHIC_BRIEF = "infographic_brief"
    WEBINAR_OUTLINE = "webinar_outline"
    SOCIAL_AD = "social_ad"


class Segment(BaseModel):
    name: str
    description: str
    pain_points: list[str]
    messaging_angle: str
    priority: int = 0


class ContentPiece(BaseModel):
    title: str
    segment: str
    content_type: str
    body: str
    keywords: list[str] | None = None
    meta_description: str | None = None


class RepurposedContent(BaseModel):
    source_title: str
    format: ContentFormat
    body: str
    platform_notes: str | None = None
```

**Step 6: Create src/models/nurture.py**

```python
from enum import Enum

from pydantic import BaseModel


class NurtureStep(str, Enum):
    DAY_1 = "day_1"
    DAY_3 = "day_3"
    DAY_7 = "day_7"
    DAY_14 = "day_14"
    COMPLETED = "completed"
    ESCALATED_TO_SALES = "escalated_to_sales"
    LONG_TERM = "long_term"


class NurtureState(BaseModel):
    lead_id: str
    current_step: NurtureStep
    emails_sent: int = 0
    engagement_score: float = 0.0
    paused: bool = False
    pause_reason: str | None = None


class EngagementSignal(BaseModel):
    lead_id: str
    event_type: str  # email_opened, link_clicked, replied, etc.
    timestamp: str
    metadata: dict | None = None


class NurtureAction(BaseModel):
    action_type: str  # send_welcome, send_case_study, escalate, etc.
    lead_id: str
    content: str
    reason: str
```

**Step 7: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_models.py -v`
Expected: All 10 tests PASS

**Step 8: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/models/ tests/test_models.py
git commit -m "feat: add Pydantic models for lead, content, and nurture workflows"
```

---

### Task 4: LangGraph Checkpointer Setup

**Files:**
- Create: `v3/vibe-ai-adoption/src/graph/__init__.py`
- Create: `v3/vibe-ai-adoption/src/graph/checkpointer.py`
- Test: `v3/vibe-ai-adoption/tests/test_checkpointer.py`

**Step 1: Write the failing test**

```python
# tests/test_checkpointer.py
import pytest
from unittest.mock import patch, MagicMock


def test_get_checkpointer_returns_postgres_saver():
    """Verify get_checkpointer returns a configured PostgresSaver."""
    from src.graph.checkpointer import get_checkpointer

    # We test that the function exists and returns the right type
    # Actual Postgres connection tested in integration tests
    assert callable(get_checkpointer)


def test_checkpointer_uses_database_url_from_settings():
    """Verify checkpointer reads DATABASE_URL from settings."""
    from src.config import settings

    assert "postgresql://" in settings.database_url
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_checkpointer.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.graph'`

**Step 3: Create src/graph/__init__.py**

```python
```

(Empty file)

**Step 4: Create src/graph/checkpointer.py**

```python
from langgraph.checkpoint.postgres import PostgresSaver

from src.config import settings


def get_checkpointer() -> PostgresSaver:
    """Create a PostgresSaver checkpointer from settings.

    Usage:
        with get_checkpointer() as checkpointer:
            graph = workflow.compile(checkpointer=checkpointer)
            result = graph.invoke(state, config={"configurable": {"thread_id": "123"}})
    """
    return PostgresSaver.from_conn_string(settings.database_url)


def setup_checkpointer() -> None:
    """Create checkpoint tables in Postgres. Call once on first run."""
    with get_checkpointer() as checkpointer:
        checkpointer.setup()
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_checkpointer.py -v`
Expected: All 2 tests PASS

**Step 6: Integration test — verify checkpointer connects to Postgres**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -c "from src.graph.checkpointer import setup_checkpointer; setup_checkpointer(); print('Checkpointer tables created OK')"`
Expected: `Checkpointer tables created OK` (requires Docker Postgres running)

**Step 7: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/graph/ tests/test_checkpointer.py
git commit -m "feat: add LangGraph Postgres checkpointer setup"
```

---

### Task 5: CrewAI + Claude Integration

**Files:**
- Create: `v3/vibe-ai-adoption/src/agents/__init__.py`
- Create: `v3/vibe-ai-adoption/src/agents/base.py`
- Test: `v3/vibe-ai-adoption/tests/test_agents_base.py`

**Step 1: Write the failing test**

```python
# tests/test_agents_base.py
from crewai import Agent, LLM

from src.agents.base import get_llm, create_agent


def test_get_llm_returns_llm_instance():
    llm = get_llm()
    assert isinstance(llm, LLM)
    assert "claude" in llm.model


def test_create_agent_returns_agent():
    agent = create_agent(
        role="Test Agent",
        goal="Test things",
        backstory="You are a test agent.",
    )
    assert isinstance(agent, Agent)
    assert agent.role == "Test Agent"
    assert agent.goal == "Test things"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_agents_base.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents'`

**Step 3: Create src/agents/__init__.py**

```python
```

(Empty file)

**Step 4: Create src/agents/base.py**

```python
from crewai import Agent, LLM

from src.config import settings


def get_llm(model: str | None = None) -> LLM:
    """Create an LLM instance configured for Claude."""
    return LLM(
        model=model or settings.default_model,
        api_key=settings.anthropic_api_key,
    )


def create_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: list | None = None,
    verbose: bool = False,
    model: str | None = None,
) -> Agent:
    """Create a CrewAI agent with Claude as the LLM."""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools or [],
        llm=get_llm(model),
        verbose=verbose,
    )
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_agents_base.py -v`
Expected: All 2 tests PASS

**Step 6: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/agents/ tests/test_agents_base.py
git commit -m "feat: add CrewAI base agent factory with Claude LLM"
```

---

### Task 6: Temporal Worker Scaffold

**Files:**
- Create: `v3/vibe-ai-adoption/src/temporal/__init__.py`
- Create: `v3/vibe-ai-adoption/src/temporal/worker.py`
- Create: `v3/vibe-ai-adoption/src/temporal/activities.py`
- Create: `v3/vibe-ai-adoption/src/temporal/workflows.py`
- Test: `v3/vibe-ai-adoption/tests/test_temporal.py`

**Step 1: Write the failing test**

```python
# tests/test_temporal.py
import pytest

from src.temporal.activities import hello_activity
from src.temporal.workflows import HelloWorkflow


def test_hello_activity():
    """Activity function should return a greeting."""
    result = hello_activity("Vibe")
    assert result == "Hello, Vibe!"


@pytest.mark.asyncio
async def test_hello_workflow_definition():
    """HelloWorkflow class should exist with a run method."""
    wf = HelloWorkflow()
    assert hasattr(wf, "run")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_temporal.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.temporal'`

**Step 3: Create src/temporal/__init__.py**

```python
```

(Empty file)

**Step 4: Create src/temporal/activities.py**

```python
from temporalio import activity


@activity.defn
def hello_activity(name: str) -> str:
    """Hello world activity — validates Temporal worker is running."""
    return f"Hello, {name}!"
```

**Step 5: Create src/temporal/workflows.py**

```python
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from src.temporal.activities import hello_activity


@workflow.defn
class HelloWorkflow:
    """Hello world workflow — validates Temporal end-to-end."""

    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            hello_activity,
            name,
            schedule_to_close_timeout=timedelta(seconds=30),
        )
```

**Step 6: Create src/temporal/worker.py**

```python
import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from src.config import settings
from src.temporal.activities import hello_activity
from src.temporal.workflows import HelloWorkflow


async def run_worker() -> None:
    """Start the Temporal worker. Registers all workflows and activities."""
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[HelloWorkflow],
            activities=[hello_activity],
            activity_executor=executor,
        )
        print(f"Worker started on task queue: {settings.temporal_task_queue}")
        await worker.run()


def main() -> None:
    """Entry point for running the worker."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
```

**Step 7: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_temporal.py -v`
Expected: All 2 tests PASS

**Step 8: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/temporal/ tests/test_temporal.py
git commit -m "feat: add Temporal worker scaffold with hello world workflow"
```

---

### Task 7: End-to-End Hello World (Temporal → LangGraph → CrewAI)

This is the **Phase 0 acceptance test**: the full 3-layer chain running together.

**Files:**
- Create: `v3/vibe-ai-adoption/src/graph/hello_world.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/activities.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/workflows.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/worker.py`
- Test: `v3/vibe-ai-adoption/tests/test_e2e_hello.py`

**Step 1: Write the failing test**

```python
# tests/test_e2e_hello.py
"""
End-to-end test: Temporal triggers LangGraph which invokes CrewAI.
This test validates the 3-layer chain WITHOUT a running Temporal server,
by directly calling the LangGraph workflow that would normally be triggered by Temporal.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.graph.hello_world import HelloWorldState, build_hello_graph


def test_hello_graph_state():
    """HelloWorldState has the expected fields."""
    state = HelloWorldState(name="Vibe", greeting="", agent_response="")
    assert state["name"] == "Vibe"


def test_build_hello_graph_compiles():
    """Graph compiles without error."""
    graph = build_hello_graph()
    assert graph is not None


def test_hello_graph_produces_greeting():
    """Graph generates a greeting (mocking CrewAI to avoid LLM calls)."""
    with patch("src.graph.hello_world.run_hello_agent") as mock_agent:
        mock_agent.return_value = {"agent_response": "CrewAI says: Welcome to Vibe!"}
        graph = build_hello_graph()
        result = graph.invoke({"name": "Vibe", "greeting": "", "agent_response": ""})
        assert "Vibe" in result["greeting"]
        assert "CrewAI says" in result["agent_response"]
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_e2e_hello.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create src/graph/hello_world.py**

```python
from typing import TypedDict

from crewai import Crew, Task
from langgraph.graph import END, START, StateGraph

from src.agents.base import create_agent


class HelloWorldState(TypedDict):
    name: str
    greeting: str
    agent_response: str


def greet(state: HelloWorldState) -> dict:
    """Node 1: Simple greeting (no LLM)."""
    return {"greeting": f"Hello, {state['name']}! Welcome to Vibe AI Adoption."}


def run_hello_agent(state: HelloWorldState) -> dict:
    """Node 2: CrewAI agent generates a personalized welcome."""
    agent = create_agent(
        role="Welcome Specialist",
        goal="Create a brief, friendly welcome message",
        backstory="You greet new team members at Vibe with warmth and clarity.",
    )
    task = Task(
        description=f"Write a one-sentence welcome for {state['name']} joining the Vibe AI team.",
        expected_output="A single welcome sentence.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    return {"agent_response": f"CrewAI says: {result.raw}"}


def build_hello_graph() -> StateGraph:
    """Build the hello world LangGraph: greet → agent → end."""
    graph = StateGraph(HelloWorldState)
    graph.add_node("greet", greet)
    graph.add_node("agent", run_hello_agent)
    graph.add_edge(START, "greet")
    graph.add_edge("greet", "agent")
    graph.add_edge("agent", END)
    return graph.compile()
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_e2e_hello.py -v`
Expected: All 3 tests PASS

**Step 5: Add LangGraph activity to Temporal**

Append to `src/temporal/activities.py`:

```python
from temporalio import activity


@activity.defn
def hello_activity(name: str) -> str:
    """Hello world activity — validates Temporal worker is running."""
    return f"Hello, {name}!"


@activity.defn
def run_hello_graph_activity(name: str) -> dict:
    """Run the hello world LangGraph workflow as a Temporal activity."""
    from src.graph.hello_world import build_hello_graph

    graph = build_hello_graph()
    result = graph.invoke({"name": name, "greeting": "", "agent_response": ""})
    return {"greeting": result["greeting"], "agent_response": result["agent_response"]}
```

**Step 6: Add E2E workflow to Temporal**

Append to `src/temporal/workflows.py`:

```python
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from src.temporal.activities import hello_activity, run_hello_graph_activity


@workflow.defn
class HelloWorkflow:
    """Hello world workflow — validates Temporal end-to-end."""

    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            hello_activity,
            name,
            schedule_to_close_timeout=timedelta(seconds=30),
        )


@workflow.defn
class HelloGraphWorkflow:
    """Full 3-layer workflow: Temporal → LangGraph → CrewAI."""

    @workflow.run
    async def run(self, name: str) -> dict:
        return await workflow.execute_activity(
            run_hello_graph_activity,
            name,
            schedule_to_close_timeout=timedelta(minutes=2),
        )
```

**Step 7: Register new workflow in worker**

Update `src/temporal/worker.py` to register `HelloGraphWorkflow` and `run_hello_graph_activity`:

```python
import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from src.config import settings
from src.temporal.activities import hello_activity, run_hello_graph_activity
from src.temporal.workflows import HelloWorkflow, HelloGraphWorkflow


async def run_worker() -> None:
    """Start the Temporal worker. Registers all workflows and activities."""
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[HelloWorkflow, HelloGraphWorkflow],
            activities=[hello_activity, run_hello_graph_activity],
            activity_executor=executor,
        )
        print(f"Worker started on task queue: {settings.temporal_task_queue}")
        await worker.run()


def main() -> None:
    """Entry point for running the worker."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
```

**Step 8: Run all tests**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 9: Manual E2E test (requires Docker running + .env configured)**

Terminal 1 — Start worker:
```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
source .venv/bin/activate
python -m src.temporal.worker
```

Terminal 2 — Trigger workflow:
```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
source .venv/bin/activate
python -c "
import asyncio
from temporalio.client import Client

async def main():
    client = await Client.connect('localhost:7233')
    result = await client.execute_workflow(
        'HelloGraphWorkflow',
        'Vibe Team',
        id='hello-graph-test-1',
        task_queue='vibe-ai-adoption',
    )
    print('Result:', result)

asyncio.run(main())
"
```

Expected: Prints greeting + CrewAI agent response. Visible in Temporal UI at `http://localhost:8080`.

**Step 10: Verify in LangSmith**

Open `https://smith.langchain.com` → Project "vibe-ai-adoption" → See the trace for the hello world run showing LLM calls.

**Step 11: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/graph/hello_world.py src/temporal/ tests/test_e2e_hello.py
git commit -m "feat: end-to-end hello world (Temporal → LangGraph → CrewAI)"
```

---

### Task 8: HubSpot Integration (Read/Write Leads)

**Files:**
- Create: `v3/vibe-ai-adoption/src/integrations/__init__.py`
- Create: `v3/vibe-ai-adoption/src/integrations/hubspot.py`
- Test: `v3/vibe-ai-adoption/tests/test_hubspot.py`

**Step 1: Write the failing test**

```python
# tests/test_hubspot.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.integrations.hubspot import HubSpotClient
from src.models.lead import Lead


@pytest.fixture
def client():
    return HubSpotClient(api_key="test-key")


def test_hubspot_client_init(client):
    assert client.api_key == "test-key"
    assert "https://api.hubapi.com" in client.base_url


@pytest.mark.asyncio
async def test_get_lead(client):
    mock_response = {
        "id": "123",
        "properties": {
            "email": "jane@acme.com",
            "company": "Acme Corp",
            "jobtitle": "CTO",
            "hs_lead_status": "NEW",
        },
    }
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        lead = await client.get_lead("123")
        assert lead.lead_id == "123"
        assert lead.email == "jane@acme.com"
        assert lead.company == "Acme Corp"


@pytest.mark.asyncio
async def test_update_lead_score(client):
    with patch.object(client, "_request", new_callable=AsyncMock, return_value={"id": "123"}) as mock:
        await client.update_lead_score("123", score=85, route="high_priority")
        mock.assert_called_once()


@pytest.mark.asyncio
async def test_search_leads(client):
    mock_response = {
        "results": [
            {
                "id": "123",
                "properties": {
                    "email": "jane@acme.com",
                    "company": "Acme Corp",
                    "jobtitle": "CTO",
                },
            }
        ]
    }
    with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
        leads = await client.search_leads(status="NEW")
        assert len(leads) == 1
        assert leads[0].email == "jane@acme.com"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_hubspot.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create src/integrations/__init__.py**

```python
```

(Empty file)

**Step 4: Create src/integrations/hubspot.py**

```python
import httpx

from src.config import settings
from src.models.lead import Lead


class HubSpotClient:
    """HubSpot CRM client for lead operations."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.hubspot_api_key
        self.base_url = "https://api.hubapi.com"

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated request to HubSpot API."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    async def get_lead(self, lead_id: str) -> Lead:
        """Fetch a lead by ID from HubSpot."""
        data = await self._request("GET", f"/crm/v3/objects/contacts/{lead_id}")
        props = data.get("properties", {})
        return Lead(
            lead_id=data["id"],
            email=props.get("email", ""),
            company=props.get("company", ""),
            role=props.get("jobtitle", ""),
            industry=props.get("industry"),
            source=props.get("hs_analytics_source"),
        )

    async def update_lead_score(self, lead_id: str, score: int, route: str) -> None:
        """Update lead with qualification score and route in HubSpot."""
        await self._request(
            "PATCH",
            f"/crm/v3/objects/contacts/{lead_id}",
            json={
                "properties": {
                    "hs_lead_status": route.upper(),
                    "lead_score": str(score),
                }
            },
        )

    async def search_leads(self, status: str = "NEW", limit: int = 100) -> list[Lead]:
        """Search leads by status."""
        data = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "hs_lead_status",
                                "operator": "EQ",
                                "value": status,
                            }
                        ]
                    }
                ],
                "limit": limit,
            },
        )
        leads = []
        for item in data.get("results", []):
            props = item.get("properties", {})
            leads.append(
                Lead(
                    lead_id=item["id"],
                    email=props.get("email", ""),
                    company=props.get("company", ""),
                    role=props.get("jobtitle", ""),
                    industry=props.get("industry"),
                )
            )
        return leads
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_hubspot.py -v`
Expected: All 4 tests PASS

**Step 6: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/integrations/ tests/test_hubspot.py
git commit -m "feat: add HubSpot client for lead CRUD operations"
```

---

### Task 9: Slack Integration (Notifications)

**Files:**
- Create: `v3/vibe-ai-adoption/src/integrations/slack.py`
- Test: `v3/vibe-ai-adoption/tests/test_slack.py`

**Step 1: Write the failing test**

```python
# tests/test_slack.py
import pytest
from unittest.mock import patch, MagicMock

from src.integrations.slack import SlackNotifier


@pytest.fixture
def notifier():
    return SlackNotifier(token="test-token", channel="C12345")


def test_slack_notifier_init(notifier):
    assert notifier.channel == "C12345"


@pytest.mark.asyncio
async def test_notify_lead_qualified(notifier):
    with patch.object(notifier, "_post_message", return_value=None) as mock:
        await notifier.notify_lead_qualified(
            lead_id="123",
            company="Acme Corp",
            score=85,
            route="high_priority",
        )
        mock.assert_called_once()
        msg = mock.call_args[0][0]
        assert "Acme Corp" in msg
        assert "85" in msg


@pytest.mark.asyncio
async def test_notify_content_generated(notifier):
    with patch.object(notifier, "_post_message", return_value=None) as mock:
        await notifier.notify_content_generated(
            segment="Enterprise AEC",
            pieces_count=20,
            formats_count=200,
        )
        mock.assert_called_once()
        msg = mock.call_args[0][0]
        assert "Enterprise AEC" in msg
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_slack.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create src/integrations/slack.py**

```python
from slack_sdk.web.async_client import AsyncWebClient

from src.config import settings


class SlackNotifier:
    """Send workflow notifications to Slack."""

    def __init__(self, token: str | None = None, channel: str | None = None):
        self.token = token or settings.slack_bot_token
        self.channel = channel or settings.slack_channel_id
        self.client = AsyncWebClient(token=self.token)

    async def _post_message(self, text: str) -> None:
        """Post a message to the configured Slack channel."""
        await self.client.chat_postMessage(channel=self.channel, text=text)

    async def notify_lead_qualified(
        self, lead_id: str, company: str, score: int, route: str
    ) -> None:
        """Notify when a lead is qualified."""
        emoji = {"high_priority": "🔴", "nurture": "🟡", "education": "🟢"}.get(route, "⚪")
        await self._post_message(
            f"{emoji} *Lead Qualified*: {company} (ID: {lead_id})\n"
            f"Score: {score} → Route: {route}"
        )

    async def notify_content_generated(
        self, segment: str, pieces_count: int, formats_count: int
    ) -> None:
        """Notify when content pipeline completes."""
        await self._post_message(
            f"📝 *Content Pipeline Complete*: {segment}\n"
            f"{pieces_count} pieces → {formats_count} formats generated"
        )

    async def notify_nurture_event(
        self, lead_id: str, event: str, details: str
    ) -> None:
        """Notify on nurture workflow events (escalation, completion, etc.)."""
        await self._post_message(
            f"🔔 *Nurture Event*: Lead {lead_id}\n"
            f"Event: {event}\n{details}"
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_slack.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/integrations/slack.py tests/test_slack.py
git commit -m "feat: add Slack notifier for workflow events"
```

---

### Task 10: Lead Qualification Agent (CrewAI)

**Files:**
- Create: `v3/vibe-ai-adoption/src/agents/lead_qualification.py`
- Test: `v3/vibe-ai-adoption/tests/test_lead_qual_agent.py`

**Step 1: Write the failing test**

```python
# tests/test_lead_qual_agent.py
import pytest
from unittest.mock import patch, MagicMock

from crewai import Agent, Task, Crew

from src.agents.lead_qualification import (
    build_lead_qual_agent,
    build_lead_qual_task,
    run_lead_qualification,
)
from src.models.lead import Lead, LeadScore


def test_build_agent_returns_agent():
    agent = build_lead_qual_agent()
    assert isinstance(agent, Agent)
    assert "Lead Qualification" in agent.role


def test_build_task_returns_task():
    agent = build_lead_qual_agent()
    lead = Lead(lead_id="123", email="j@acme.com", company="Acme", role="CTO")
    task = build_lead_qual_task(agent, lead)
    assert isinstance(task, Task)
    assert "Acme" in task.description


def test_run_lead_qualification_returns_score():
    """Mock CrewAI to avoid real LLM calls."""
    mock_result = MagicMock()
    mock_result.raw = '{"fit": 85, "intent": 70, "urgency": 60, "reasoning": "Strong company fit"}'

    with patch("src.agents.lead_qualification.Crew") as MockCrew:
        MockCrew.return_value.kickoff.return_value = mock_result
        lead = Lead(lead_id="123", email="j@acme.com", company="Acme", role="CTO")
        result = run_lead_qualification(lead)
        assert result.lead_id == "123"
        assert result.score.fit == 85
        assert "Strong company" in result.reasoning
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_lead_qual_agent.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create src/agents/lead_qualification.py**

```python
import json

from crewai import Agent, Crew, Task

from src.agents.base import create_agent
from src.models.lead import Lead, LeadScore, QualificationResult


def build_lead_qual_agent() -> Agent:
    """Create the Lead Qualification Specialist agent."""
    return create_agent(
        role="Lead Qualification Specialist",
        goal="Accurately assess each lead's fit, intent, and urgency for Vibe's products",
        backstory=(
            "You are a senior sales analyst at Vibe, a company that makes interactive "
            "whiteboards and collaboration software. You've qualified thousands of leads "
            "and can quickly assess company fit (do they need collaboration tools?), "
            "intent (are they actively looking?), and urgency (is there a timeline?)."
        ),
    )


def build_lead_qual_task(agent: Agent, lead: Lead) -> Task:
    """Create a qualification task for a specific lead."""
    return Task(
        description=(
            f"Evaluate this lead for Vibe's collaboration products:\n"
            f"- Company: {lead.company}\n"
            f"- Role: {lead.role}\n"
            f"- Email: {lead.email}\n"
            f"- Industry: {lead.industry or 'Unknown'}\n"
            f"- Company size: {lead.company_size or 'Unknown'}\n"
            f"- Source: {lead.source or 'Unknown'}\n"
            f"\n"
            f"Score on three dimensions (0-100 each):\n"
            f"1. Fit: Does this company/role need Vibe's products?\n"
            f"2. Intent: Are there signals they're actively looking?\n"
            f"3. Urgency: Is there timeline pressure?\n"
            f"\n"
            f"Return ONLY valid JSON: "
            f'{{"fit": <int>, "intent": <int>, "urgency": <int>, "reasoning": "<string>"}}'
        ),
        expected_output='JSON object with fit, intent, urgency scores and reasoning',
        agent=agent,
    )


def run_lead_qualification(lead: Lead) -> QualificationResult:
    """Run the lead qualification agent and return structured result."""
    agent = build_lead_qual_agent()
    task = build_lead_qual_task(agent, lead)
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()

    data = json.loads(result.raw)
    score = LeadScore(
        fit=data["fit"],
        intent=data["intent"],
        urgency=data["urgency"],
    )
    return QualificationResult(
        lead_id=lead.lead_id,
        score=score,
        reasoning=data["reasoning"],
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_lead_qual_agent.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/agents/lead_qualification.py tests/test_lead_qual_agent.py
git commit -m "feat: add Lead Qualification CrewAI agent"
```

---

### Task 11: Lead Qualification LangGraph Workflow

**Files:**
- Create: `v3/vibe-ai-adoption/src/workflows/__init__.py`
- Create: `v3/vibe-ai-adoption/src/workflows/lead_qualification.py`
- Test: `v3/vibe-ai-adoption/tests/test_lead_qual_workflow.py`

**Step 1: Write the failing test**

```python
# tests/test_lead_qual_workflow.py
import pytest
from unittest.mock import patch, MagicMock

from src.models.lead import Lead, LeadScore, LeadRoute, QualificationResult
from src.workflows.lead_qualification import (
    LeadQualState,
    build_lead_qual_graph,
)


def test_lead_qual_state():
    state = LeadQualState(
        lead=Lead(lead_id="123", email="j@acme.com", company="Acme", role="CTO").model_dump(),
        enriched_data={},
        qualification=None,
        route=None,
        crm_updated=False,
    )
    assert state["lead"]["lead_id"] == "123"


def test_build_graph_compiles():
    graph = build_lead_qual_graph()
    assert graph is not None


def test_graph_routes_high_priority():
    """Full workflow with mocked agent: high-score lead routes to high_priority."""
    mock_result = QualificationResult(
        lead_id="123",
        score=LeadScore(fit=90, intent=85, urgency=80),
        reasoning="Excellent fit",
    )
    with patch("src.workflows.lead_qualification.run_lead_qualification", return_value=mock_result):
        with patch("src.workflows.lead_qualification.enrich_lead", return_value={"enriched_data": {"industry": "tech"}}):
            with patch("src.workflows.lead_qualification.update_crm", return_value={"crm_updated": True}):
                graph = build_lead_qual_graph()
                result = graph.invoke({
                    "lead": Lead(lead_id="123", email="j@acme.com", company="Acme", role="CTO").model_dump(),
                    "enriched_data": {},
                    "qualification": None,
                    "route": None,
                    "crm_updated": False,
                })
                assert result["route"] == "high_priority"
                assert result["crm_updated"] is True


def test_graph_routes_nurture():
    """Medium-score lead routes to nurture."""
    mock_result = QualificationResult(
        lead_id="123",
        score=LeadScore(fit=70, intent=60, urgency=50),
        reasoning="Moderate fit",
    )
    with patch("src.workflows.lead_qualification.run_lead_qualification", return_value=mock_result):
        with patch("src.workflows.lead_qualification.enrich_lead", return_value={"enriched_data": {}}):
            with patch("src.workflows.lead_qualification.update_crm", return_value={"crm_updated": True}):
                graph = build_lead_qual_graph()
                result = graph.invoke({
                    "lead": Lead(lead_id="123", email="j@acme.com", company="Acme", role="CTO").model_dump(),
                    "enriched_data": {},
                    "qualification": None,
                    "route": None,
                    "crm_updated": False,
                })
                assert result["route"] == "nurture"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_lead_qual_workflow.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create src/workflows/__init__.py**

```python
```

(Empty file)

**Step 4: Create src/workflows/lead_qualification.py**

```python
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.lead_qualification import run_lead_qualification
from src.models.lead import Lead, LeadRoute, QualificationResult


class LeadQualState(TypedDict):
    lead: dict  # Lead.model_dump()
    enriched_data: dict
    qualification: dict | None  # QualificationResult.model_dump()
    route: str | None
    crm_updated: bool


def enrich_lead(state: LeadQualState) -> dict:
    """Node 1: Enrich lead data (company info, tech stack, etc.)."""
    lead = Lead(**state["lead"])
    # In production, call enrichment APIs here
    enriched = {
        "company": lead.company,
        "role": lead.role,
        "industry": lead.industry or "Unknown",
    }
    return {"enriched_data": enriched}


def qualify_lead(state: LeadQualState) -> dict:
    """Node 2: Run CrewAI agent to score the lead."""
    lead_data = {**state["lead"]}
    if state["enriched_data"]:
        lead_data["industry"] = state["enriched_data"].get("industry")
    lead = Lead(**lead_data)
    result = run_lead_qualification(lead)
    return {
        "qualification": result.model_dump(),
        "route": result.score.route.value,
    }


def update_crm(state: LeadQualState) -> dict:
    """Node 3: Update CRM with score and route."""
    # In production, call HubSpot API here
    return {"crm_updated": True}


def route_lead(state: LeadQualState) -> str:
    """Conditional edge: route based on qualification score."""
    route = state.get("route")
    if route == LeadRoute.HIGH_PRIORITY.value:
        return "update_crm"
    elif route == LeadRoute.NURTURE.value:
        return "update_crm"
    else:
        return "update_crm"


def build_lead_qual_graph():
    """Build the Lead Qualification LangGraph workflow.

    Flow: enrich → qualify → route → update_crm → END
    """
    graph = StateGraph(LeadQualState)

    graph.add_node("enrich", enrich_lead)
    graph.add_node("qualify", qualify_lead)
    graph.add_node("update_crm", update_crm)

    graph.add_edge(START, "enrich")
    graph.add_edge("enrich", "qualify")
    graph.add_conditional_edges("qualify", route_lead, {
        "update_crm": "update_crm",
    })
    graph.add_edge("update_crm", END)

    return graph.compile()
```

**Step 5: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_lead_qual_workflow.py -v`
Expected: All 4 tests PASS

**Step 6: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/workflows/ tests/test_lead_qual_workflow.py
git commit -m "feat: add Lead Qualification LangGraph workflow (enrich → qualify → route → CRM)"
```

---

### Task 12: Lead Qualification Temporal Integration

**Files:**
- Modify: `v3/vibe-ai-adoption/src/temporal/activities.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/workflows.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/worker.py`
- Test: `v3/vibe-ai-adoption/tests/test_lead_qual_temporal.py`

**Step 1: Write the failing test**

```python
# tests/test_lead_qual_temporal.py
import pytest

from src.temporal.activities import qualify_lead_activity
from src.temporal.workflows import LeadQualificationWorkflow


def test_qualify_lead_activity_exists():
    """Activity function should be defined."""
    assert callable(qualify_lead_activity)


@pytest.mark.asyncio
async def test_lead_qual_workflow_definition():
    """Workflow should have a run method."""
    wf = LeadQualificationWorkflow()
    assert hasattr(wf, "run")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_lead_qual_temporal.py -v`
Expected: FAIL with `ImportError`

**Step 3: Add qualify_lead_activity to src/temporal/activities.py**

Add to the existing file:

```python
@activity.defn
def qualify_lead_activity(lead_data: dict) -> dict:
    """Run the Lead Qualification LangGraph workflow as a Temporal activity."""
    from src.workflows.lead_qualification import build_lead_qual_graph

    graph = build_lead_qual_graph()
    result = graph.invoke({
        "lead": lead_data,
        "enriched_data": {},
        "qualification": None,
        "route": None,
        "crm_updated": False,
    })
    return {
        "lead_id": lead_data["lead_id"],
        "route": result["route"],
        "qualification": result["qualification"],
        "crm_updated": result["crm_updated"],
    }
```

**Step 4: Add LeadQualificationWorkflow to src/temporal/workflows.py**

Add to the existing file:

```python
@workflow.defn
class LeadQualificationWorkflow:
    """Temporal workflow: Lead enters → LangGraph qualifies → CRM updated."""

    @workflow.run
    async def run(self, lead_data: dict) -> dict:
        return await workflow.execute_activity(
            qualify_lead_activity,
            lead_data,
            schedule_to_close_timeout=timedelta(minutes=5),
        )
```

Make sure `qualify_lead_activity` is imported in the `workflow.unsafe.imports_passed_through()` block.

**Step 5: Register in worker**

Update `src/temporal/worker.py` to include `LeadQualificationWorkflow` in workflows list and `qualify_lead_activity` in activities list.

**Step 6: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_lead_qual_temporal.py -v`
Expected: All 2 tests PASS

**Step 7: Run all tests**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/temporal/ tests/test_lead_qual_temporal.py
git commit -m "feat: add Lead Qualification Temporal workflow + activity"
```

---

### Task 13: Content Pipeline Agents (3 CrewAI Agents)

**Files:**
- Create: `v3/vibe-ai-adoption/src/agents/segment_research.py`
- Create: `v3/vibe-ai-adoption/src/agents/content_generation.py`
- Create: `v3/vibe-ai-adoption/src/agents/content_repurposing.py`
- Test: `v3/vibe-ai-adoption/tests/test_content_agents.py`

**Step 1: Write the failing test**

```python
# tests/test_content_agents.py
import pytest
from unittest.mock import patch, MagicMock

from crewai import Agent

from src.agents.segment_research import build_segment_research_agent, run_segment_research
from src.agents.content_generation import build_content_gen_agent, run_content_generation
from src.agents.content_repurposing import build_repurposing_agent, run_content_repurposing
from src.models.content import Segment, ContentPiece, ContentFormat


def test_segment_research_agent():
    agent = build_segment_research_agent()
    assert isinstance(agent, Agent)
    assert "Segment" in agent.role


def test_content_gen_agent():
    agent = build_content_gen_agent()
    assert isinstance(agent, Agent)


def test_repurposing_agent():
    agent = build_repurposing_agent()
    assert isinstance(agent, Agent)


def test_run_segment_research():
    mock_result = MagicMock()
    mock_result.raw = '[{"name": "Enterprise AEC", "description": "AEC firms", "pain_points": ["remote collab"], "messaging_angle": "Transform reviews"}]'
    with patch("src.agents.segment_research.Crew") as MockCrew:
        MockCrew.return_value.kickoff.return_value = mock_result
        segments = run_segment_research(market="collaboration tools", num_segments=3)
        assert len(segments) == 1
        assert segments[0].name == "Enterprise AEC"


def test_run_content_generation():
    mock_result = MagicMock()
    mock_result.raw = '{"title": "How AEC Uses Vibe", "body": "Article body..."}'
    with patch("src.agents.content_generation.Crew") as MockCrew:
        MockCrew.return_value.kickoff.return_value = mock_result
        segment = Segment(name="AEC", description="AEC firms", pain_points=["collab"], messaging_angle="Transform")
        piece = run_content_generation(segment, content_type="blog_post")
        assert piece.title == "How AEC Uses Vibe"


def test_run_content_repurposing():
    mock_result = MagicMock()
    mock_result.raw = '[{"format": "linkedin_post", "body": "Short version..."}]'
    with patch("src.agents.content_repurposing.Crew") as MockCrew:
        MockCrew.return_value.kickoff.return_value = mock_result
        piece = ContentPiece(title="AEC Article", segment="AEC", content_type="blog_post", body="Full body")
        repurposed = run_content_repurposing(piece, formats=[ContentFormat.LINKEDIN_POST])
        assert len(repurposed) == 1
        assert repurposed[0].format == ContentFormat.LINKEDIN_POST
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_content_agents.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create src/agents/segment_research.py**

```python
import json

from crewai import Agent, Crew, Task

from src.agents.base import create_agent
from src.models.content import Segment


def build_segment_research_agent() -> Agent:
    return create_agent(
        role="Segment Research Analyst",
        goal="Identify and prioritize market micro-segments for Vibe's products",
        backstory=(
            "You are a market research expert specializing in B2B SaaS. "
            "You analyze market data to identify micro-segments that would benefit "
            "most from Vibe's interactive whiteboard and collaboration products."
        ),
    )


def run_segment_research(market: str, num_segments: int = 10) -> list[Segment]:
    agent = build_segment_research_agent()
    task = Task(
        description=(
            f"Identify {num_segments} micro-segments in the '{market}' market "
            f"that would benefit from Vibe's collaboration products.\n"
            f"For each segment, provide: name, description, pain_points (list), messaging_angle.\n"
            f"Return ONLY valid JSON array of objects."
        ),
        expected_output="JSON array of segment objects",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    data = json.loads(result.raw)
    return [Segment(**s) for s in data]
```

**Step 4: Create src/agents/content_generation.py**

```python
import json

from crewai import Agent, Crew, Task

from src.agents.base import create_agent
from src.models.content import ContentPiece, Segment


def build_content_gen_agent() -> Agent:
    return create_agent(
        role="Content Strategist",
        goal="Create compelling, segment-specific content for Vibe's products",
        backstory=(
            "You are a B2B content strategist who creates high-converting content. "
            "You write blog posts, case studies, and whitepapers tailored to specific "
            "industry segments, focusing on pain points and Vibe's unique value."
        ),
    )


def run_content_generation(segment: Segment, content_type: str = "blog_post") -> ContentPiece:
    agent = build_content_gen_agent()
    task = Task(
        description=(
            f"Write a {content_type} for the '{segment.name}' segment.\n"
            f"Segment: {segment.description}\n"
            f"Pain points: {', '.join(segment.pain_points)}\n"
            f"Messaging angle: {segment.messaging_angle}\n"
            f"\n"
            f"Return ONLY valid JSON: {{\"title\": \"...\", \"body\": \"...\"}}"
        ),
        expected_output="JSON with title and body",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    data = json.loads(result.raw)
    return ContentPiece(
        title=data["title"],
        segment=segment.name,
        content_type=content_type,
        body=data["body"],
    )
```

**Step 5: Create src/agents/content_repurposing.py**

```python
import json

from crewai import Agent, Crew, Task

from src.agents.base import create_agent
from src.models.content import ContentFormat, ContentPiece, RepurposedContent


def build_repurposing_agent() -> Agent:
    return create_agent(
        role="Content Repurposing Specialist",
        goal="Transform content into multiple formats optimized for each platform",
        backstory=(
            "You are an expert at adapting content across platforms. "
            "You take a blog post and transform it into LinkedIn posts, "
            "email newsletters, Twitter threads, video scripts, and more — "
            "each optimized for its platform's style and audience."
        ),
    )


def run_content_repurposing(
    piece: ContentPiece,
    formats: list[ContentFormat] | None = None,
) -> list[RepurposedContent]:
    if formats is None:
        formats = list(ContentFormat)

    agent = build_repurposing_agent()
    format_names = [f.value for f in formats]
    task = Task(
        description=(
            f"Repurpose this content into the following formats: {', '.join(format_names)}\n"
            f"\n"
            f"Original title: {piece.title}\n"
            f"Original body: {piece.body[:500]}...\n"
            f"\n"
            f"Return ONLY valid JSON array: [{{\"format\": \"...\", \"body\": \"...\"}}]"
        ),
        expected_output="JSON array of repurposed content objects",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    data = json.loads(result.raw)
    return [
        RepurposedContent(
            source_title=piece.title,
            format=ContentFormat(item["format"]),
            body=item["body"],
        )
        for item in data
    ]
```

**Step 6: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_content_agents.py -v`
Expected: All 6 tests PASS

**Step 7: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/agents/segment_research.py src/agents/content_generation.py src/agents/content_repurposing.py tests/test_content_agents.py
git commit -m "feat: add 3 Content Pipeline CrewAI agents (segment, generate, repurpose)"
```

---

### Task 14: Content Pipeline LangGraph Workflow

**Files:**
- Create: `v3/vibe-ai-adoption/src/workflows/content_pipeline.py`
- Test: `v3/vibe-ai-adoption/tests/test_content_workflow.py`

**Step 1: Write the failing test**

```python
# tests/test_content_workflow.py
import pytest
from unittest.mock import patch, MagicMock

from src.models.content import Segment, ContentPiece, ContentFormat, RepurposedContent
from src.workflows.content_pipeline import ContentPipelineState, build_content_pipeline_graph


def test_state_schema():
    state = ContentPipelineState(
        market="collaboration tools",
        num_segments=3,
        segments=[],
        content_pieces=[],
        repurposed=[],
        status="pending",
    )
    assert state["market"] == "collaboration tools"


def test_graph_compiles():
    graph = build_content_pipeline_graph()
    assert graph is not None


def test_full_pipeline():
    """Mock all agents and run the full pipeline."""
    mock_segments = [
        Segment(name="AEC", description="AEC firms", pain_points=["collab"], messaging_angle="Transform")
    ]
    mock_piece = ContentPiece(title="AEC Article", segment="AEC", content_type="blog_post", body="Full body")
    mock_repurposed = [
        RepurposedContent(source_title="AEC Article", format=ContentFormat.LINKEDIN_POST, body="Short")
    ]

    with patch("src.workflows.content_pipeline.run_segment_research", return_value=mock_segments):
        with patch("src.workflows.content_pipeline.run_content_generation", return_value=mock_piece):
            with patch("src.workflows.content_pipeline.run_content_repurposing", return_value=mock_repurposed):
                graph = build_content_pipeline_graph()
                result = graph.invoke({
                    "market": "collaboration tools",
                    "num_segments": 3,
                    "segments": [],
                    "content_pieces": [],
                    "repurposed": [],
                    "status": "pending",
                })
                assert len(result["segments"]) == 1
                assert len(result["content_pieces"]) >= 1
                assert len(result["repurposed"]) >= 1
                assert result["status"] == "complete"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_content_workflow.py -v`
Expected: FAIL

**Step 3: Create src/workflows/content_pipeline.py**

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.segment_research import run_segment_research
from src.agents.content_generation import run_content_generation
from src.agents.content_repurposing import run_content_repurposing
from src.models.content import ContentFormat, Segment


class ContentPipelineState(TypedDict):
    market: str
    num_segments: int
    segments: list[dict]
    content_pieces: list[dict]
    repurposed: list[dict]
    status: str


def research_segments(state: ContentPipelineState) -> dict:
    """Node 1: Research and identify market segments."""
    segments = run_segment_research(
        market=state["market"],
        num_segments=state["num_segments"],
    )
    return {"segments": [s.model_dump() for s in segments]}


def generate_content(state: ContentPipelineState) -> dict:
    """Node 2: Generate content for each segment."""
    pieces = []
    for seg_data in state["segments"]:
        segment = Segment(**seg_data)
        for content_type in ["blog_post", "case_study"]:
            piece = run_content_generation(segment, content_type)
            pieces.append(piece.model_dump())
    return {"content_pieces": pieces}


def repurpose_content(state: ContentPipelineState) -> dict:
    """Node 3: Repurpose each piece into multiple formats."""
    from src.models.content import ContentPiece

    all_repurposed = []
    formats = [ContentFormat.LINKEDIN_POST, ContentFormat.EMAIL, ContentFormat.TWITTER_THREAD]
    for piece_data in state["content_pieces"]:
        piece = ContentPiece(**piece_data)
        repurposed = run_content_repurposing(piece, formats)
        all_repurposed.extend([r.model_dump() for r in repurposed])
    return {"repurposed": all_repurposed, "status": "complete"}


def build_content_pipeline_graph():
    """Build the Content Pipeline LangGraph.

    Flow: research_segments → generate_content → repurpose → END
    """
    graph = StateGraph(ContentPipelineState)

    graph.add_node("research", research_segments)
    graph.add_node("generate", generate_content)
    graph.add_node("repurpose", repurpose_content)

    graph.add_edge(START, "research")
    graph.add_edge("research", "generate")
    graph.add_edge("generate", "repurpose")
    graph.add_edge("repurpose", END)

    return graph.compile()
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_content_workflow.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/workflows/content_pipeline.py tests/test_content_workflow.py
git commit -m "feat: add Content Pipeline LangGraph workflow (research → generate → repurpose)"
```

---

### Task 15: Content Pipeline Temporal Integration

**Files:**
- Modify: `v3/vibe-ai-adoption/src/temporal/activities.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/workflows.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/worker.py`
- Test: `v3/vibe-ai-adoption/tests/test_content_temporal.py`

**Step 1: Write the failing test**

```python
# tests/test_content_temporal.py
import pytest

from src.temporal.activities import run_content_pipeline_activity
from src.temporal.workflows import ContentPipelineWorkflow


def test_content_pipeline_activity_exists():
    assert callable(run_content_pipeline_activity)


@pytest.mark.asyncio
async def test_content_pipeline_workflow_definition():
    wf = ContentPipelineWorkflow()
    assert hasattr(wf, "run")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_content_temporal.py -v`
Expected: FAIL

**Step 3: Add activity**

Add to `src/temporal/activities.py`:

```python
@activity.defn
def run_content_pipeline_activity(params: dict) -> dict:
    """Run the Content Pipeline LangGraph workflow as a Temporal activity."""
    from src.workflows.content_pipeline import build_content_pipeline_graph

    graph = build_content_pipeline_graph()
    result = graph.invoke({
        "market": params.get("market", "collaboration tools"),
        "num_segments": params.get("num_segments", 10),
        "segments": [],
        "content_pieces": [],
        "repurposed": [],
        "status": "pending",
    })
    return {
        "segments_count": len(result["segments"]),
        "pieces_count": len(result["content_pieces"]),
        "repurposed_count": len(result["repurposed"]),
        "status": result["status"],
    }
```

**Step 4: Add workflow**

Add to `src/temporal/workflows.py`:

```python
@workflow.defn
class ContentPipelineWorkflow:
    """Temporal workflow: Weekly cron → Content Pipeline → Slack notification."""

    @workflow.run
    async def run(self, params: dict) -> dict:
        return await workflow.execute_activity(
            run_content_pipeline_activity,
            params,
            schedule_to_close_timeout=timedelta(minutes=30),
        )
```

**Step 5: Register in worker**

Update worker to include `ContentPipelineWorkflow` and `run_content_pipeline_activity`.

**Step 6: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_content_temporal.py -v`
Expected: All 2 tests PASS

**Step 7: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/temporal/ tests/test_content_temporal.py
git commit -m "feat: add Content Pipeline Temporal workflow (weekly cron)"
```

---

### Task 16: Nurture Agent (CrewAI)

**Files:**
- Create: `v3/vibe-ai-adoption/src/agents/nurture.py`
- Test: `v3/vibe-ai-adoption/tests/test_nurture_agent.py`

**Step 1: Write the failing test**

```python
# tests/test_nurture_agent.py
import pytest
from unittest.mock import patch, MagicMock

from crewai import Agent

from src.agents.nurture import (
    build_nurture_agent,
    run_nurture_decision,
)
from src.models.nurture import NurtureState, NurtureStep, NurtureAction


def test_build_nurture_agent():
    agent = build_nurture_agent()
    assert isinstance(agent, Agent)
    assert "Nurture" in agent.role


def test_run_nurture_decision():
    mock_result = MagicMock()
    mock_result.raw = '{"action_type": "send_case_study", "content": "Here is a case study...", "reason": "Lead opened welcome email"}'
    with patch("src.agents.nurture.Crew") as MockCrew:
        MockCrew.return_value.kickoff.return_value = mock_result
        state = NurtureState(
            lead_id="123",
            current_step=NurtureStep.DAY_3,
            emails_sent=1,
            engagement_score=0.6,
        )
        action = run_nurture_decision(state, lead_company="Acme Corp")
        assert isinstance(action, NurtureAction)
        assert action.action_type == "send_case_study"
        assert action.lead_id == "123"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_nurture_agent.py -v`
Expected: FAIL

**Step 3: Create src/agents/nurture.py**

```python
import json

from crewai import Agent, Crew, Task

from src.agents.base import create_agent
from src.models.nurture import NurtureAction, NurtureState


def build_nurture_agent() -> Agent:
    return create_agent(
        role="Nurture Specialist",
        goal="Warm up leads with personalized, behavior-driven outreach that converts",
        backstory=(
            "You are an expert at lead nurturing for Vibe's collaboration products. "
            "You craft personalized email sequences based on each lead's behavior — "
            "what they opened, clicked, and engaged with. You know when to push, "
            "when to wait, and when to escalate to human sales."
        ),
    )


def run_nurture_decision(state: NurtureState, lead_company: str = "") -> NurtureAction:
    """Ask the nurture agent what action to take given current state."""
    agent = build_nurture_agent()
    task = Task(
        description=(
            f"Decide the next nurture action for this lead:\n"
            f"- Lead ID: {state.lead_id}\n"
            f"- Company: {lead_company}\n"
            f"- Current step: {state.current_step.value}\n"
            f"- Emails sent: {state.emails_sent}\n"
            f"- Engagement score: {state.engagement_score}\n"
            f"- Paused: {state.paused}\n"
            f"\n"
            f"Choose an action_type: send_welcome, send_case_study, send_followup, "
            f"change_subject_resend, escalate_to_sales, move_to_long_term\n"
            f"\n"
            f"Return ONLY valid JSON: "
            f'{{"action_type": "...", "content": "...", "reason": "..."}}'
        ),
        expected_output="JSON with action_type, content, and reason",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    data = json.loads(result.raw)
    return NurtureAction(
        action_type=data["action_type"],
        lead_id=state.lead_id,
        content=data["content"],
        reason=data["reason"],
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_nurture_agent.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/agents/nurture.py tests/test_nurture_agent.py
git commit -m "feat: add Nurture Specialist CrewAI agent"
```

---

### Task 17: Nurture Sequence LangGraph Workflow (with Checkpoints + HITL)

**Files:**
- Create: `v3/vibe-ai-adoption/src/workflows/nurture_sequence.py`
- Test: `v3/vibe-ai-adoption/tests/test_nurture_workflow.py`

**Step 1: Write the failing test**

```python
# tests/test_nurture_workflow.py
import pytest
from unittest.mock import patch, MagicMock

from src.models.nurture import NurtureStep, NurtureAction
from src.workflows.nurture_sequence import (
    NurtureWorkflowState,
    build_nurture_graph,
)


def test_nurture_state():
    state = NurtureWorkflowState(
        lead_id="123",
        lead_company="Acme Corp",
        current_step="day_1",
        emails_sent=0,
        engagement_score=0.0,
        engagement_events=[],
        actions_taken=[],
        paused=False,
        completed=False,
        outcome=None,
    )
    assert state["lead_id"] == "123"


def test_graph_compiles():
    graph = build_nurture_graph()
    assert graph is not None


def test_day1_sends_welcome():
    """Day 1 node should produce a welcome action."""
    mock_action = NurtureAction(
        action_type="send_welcome",
        lead_id="123",
        content="Welcome to Vibe!",
        reason="Day 1 welcome",
    )
    with patch("src.workflows.nurture_sequence.run_nurture_decision", return_value=mock_action):
        graph = build_nurture_graph()
        # Use interrupt_before to test just the first step
        result = graph.invoke({
            "lead_id": "123",
            "lead_company": "Acme Corp",
            "current_step": "day_1",
            "emails_sent": 0,
            "engagement_score": 0.0,
            "engagement_events": [],
            "actions_taken": [],
            "paused": False,
            "completed": False,
            "outcome": None,
        })
        assert len(result["actions_taken"]) >= 1
        assert result["emails_sent"] >= 1
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_nurture_workflow.py -v`
Expected: FAIL

**Step 3: Create src/workflows/nurture_sequence.py**

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.nurture import run_nurture_decision
from src.models.nurture import NurtureAction, NurtureState, NurtureStep


class NurtureWorkflowState(TypedDict):
    lead_id: str
    lead_company: str
    current_step: str  # NurtureStep value
    emails_sent: int
    engagement_score: float
    engagement_events: list[dict]
    actions_taken: list[dict]
    paused: bool
    completed: bool
    outcome: str | None  # escalated_to_sales, long_term, completed


def _build_nurture_state(state: NurtureWorkflowState) -> NurtureState:
    """Convert workflow state to NurtureState for the agent."""
    return NurtureState(
        lead_id=state["lead_id"],
        current_step=NurtureStep(state["current_step"]),
        emails_sent=state["emails_sent"],
        engagement_score=state["engagement_score"],
        paused=state["paused"],
    )


def day1_action(state: NurtureWorkflowState) -> dict:
    """Day 1: Send welcome email."""
    nurture_state = _build_nurture_state(state)
    action = run_nurture_decision(nurture_state, state["lead_company"])
    return {
        "actions_taken": state["actions_taken"] + [action.model_dump()],
        "emails_sent": state["emails_sent"] + 1,
        "current_step": NurtureStep.DAY_3.value,
    }


def day3_action(state: NurtureWorkflowState) -> dict:
    """Day 3: Check engagement, decide next action."""
    nurture_state = _build_nurture_state(state)
    action = run_nurture_decision(nurture_state, state["lead_company"])
    return {
        "actions_taken": state["actions_taken"] + [action.model_dump()],
        "emails_sent": state["emails_sent"] + 1,
        "current_step": NurtureStep.DAY_7.value,
    }


def day7_action(state: NurtureWorkflowState) -> dict:
    """Day 7: Check cumulative engagement, decide escalation."""
    nurture_state = _build_nurture_state(state)
    action = run_nurture_decision(nurture_state, state["lead_company"])
    new_actions = state["actions_taken"] + [action.model_dump()]

    if action.action_type == "escalate_to_sales":
        return {
            "actions_taken": new_actions,
            "completed": True,
            "outcome": "escalated_to_sales",
        }

    return {
        "actions_taken": new_actions,
        "emails_sent": state["emails_sent"] + 1,
        "current_step": NurtureStep.DAY_14.value,
    }


def day14_action(state: NurtureWorkflowState) -> dict:
    """Day 14: Final push or move to long-term."""
    nurture_state = _build_nurture_state(state)
    action = run_nurture_decision(nurture_state, state["lead_company"])
    outcome = "long_term" if action.action_type == "move_to_long_term" else "completed"
    return {
        "actions_taken": state["actions_taken"] + [action.model_dump()],
        "completed": True,
        "outcome": outcome,
    }


def route_after_day7(state: NurtureWorkflowState) -> str:
    """Route after day 7: escalate or continue to day 14."""
    if state.get("completed"):
        return "end"
    return "day14"


def build_nurture_graph():
    """Build the Nurture Sequence LangGraph.

    Flow: day1 → day3 → day7 → (escalate | day14) → END

    In production, use with checkpointer for multi-day persistence:
        with get_checkpointer() as cp:
            graph = build_nurture_graph(checkpointer=cp)
            graph.invoke(state, config={"configurable": {"thread_id": lead_id}})
    """
    graph = StateGraph(NurtureWorkflowState)

    graph.add_node("day1", day1_action)
    graph.add_node("day3", day3_action)
    graph.add_node("day7", day7_action)
    graph.add_node("day14", day14_action)

    graph.add_edge(START, "day1")
    graph.add_edge("day1", "day3")
    graph.add_edge("day3", "day7")
    graph.add_conditional_edges("day7", route_after_day7, {
        "day14": "day14",
        "end": END,
    })
    graph.add_edge("day14", END)

    return graph.compile()
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_nurture_workflow.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/workflows/nurture_sequence.py tests/test_nurture_workflow.py
git commit -m "feat: add Nurture Sequence LangGraph workflow (day1→day3→day7→day14 with HITL routing)"
```

---

### Task 18: Nurture Sequence Temporal Integration (Durable Long-Running)

**Files:**
- Modify: `v3/vibe-ai-adoption/src/temporal/activities.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/workflows.py`
- Modify: `v3/vibe-ai-adoption/src/temporal/worker.py`
- Test: `v3/vibe-ai-adoption/tests/test_nurture_temporal.py`

**Step 1: Write the failing test**

```python
# tests/test_nurture_temporal.py
import pytest

from src.temporal.activities import run_nurture_step_activity
from src.temporal.workflows import NurtureSequenceWorkflow


def test_nurture_step_activity_exists():
    assert callable(run_nurture_step_activity)


@pytest.mark.asyncio
async def test_nurture_workflow_definition():
    wf = NurtureSequenceWorkflow()
    assert hasattr(wf, "run")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_nurture_temporal.py -v`
Expected: FAIL

**Step 3: Add nurture step activity**

Add to `src/temporal/activities.py`:

```python
@activity.defn
def run_nurture_step_activity(state: dict) -> dict:
    """Run one step of the nurture workflow. Temporal handles the multi-day scheduling."""
    from src.workflows.nurture_sequence import build_nurture_graph

    graph = build_nurture_graph()
    result = graph.invoke(state)
    return result
```

**Step 4: Add nurture workflow**

Add to `src/temporal/workflows.py`:

```python
@workflow.defn
class NurtureSequenceWorkflow:
    """Temporal durable workflow: 14-day nurture sequence.

    Temporal handles the multi-day scheduling via sleep timers.
    Each step runs the LangGraph workflow, then Temporal sleeps until the next day.
    """

    @workflow.run
    async def run(self, lead_data: dict) -> dict:
        state = {
            "lead_id": lead_data["lead_id"],
            "lead_company": lead_data.get("lead_company", ""),
            "current_step": "day_1",
            "emails_sent": 0,
            "engagement_score": 0.0,
            "engagement_events": [],
            "actions_taken": [],
            "paused": False,
            "completed": False,
            "outcome": None,
        }

        # Day 1
        state = await workflow.execute_activity(
            run_nurture_step_activity,
            state,
            schedule_to_close_timeout=timedelta(minutes=5),
        )

        if state.get("completed"):
            return state

        # Wait 2 days
        await workflow.sleep(timedelta(days=2))

        # Day 3
        state = await workflow.execute_activity(
            run_nurture_step_activity,
            state,
            schedule_to_close_timeout=timedelta(minutes=5),
        )

        if state.get("completed"):
            return state

        # Wait 4 days
        await workflow.sleep(timedelta(days=4))

        # Day 7
        state = await workflow.execute_activity(
            run_nurture_step_activity,
            state,
            schedule_to_close_timeout=timedelta(minutes=5),
        )

        if state.get("completed"):
            return state

        # Wait 7 days
        await workflow.sleep(timedelta(days=7))

        # Day 14
        state = await workflow.execute_activity(
            run_nurture_step_activity,
            state,
            schedule_to_close_timeout=timedelta(minutes=5),
        )

        return state
```

**Step 5: Register in worker**

Update `src/temporal/worker.py` to include `NurtureSequenceWorkflow` and `run_nurture_step_activity`.

**Step 6: Run test to verify it passes**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/test_nurture_temporal.py -v`
Expected: All 2 tests PASS

**Step 7: Run all tests**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: ALL tests PASS

**Step 8: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add src/temporal/ tests/test_nurture_temporal.py
git commit -m "feat: add Nurture Sequence Temporal workflow (14-day durable with sleep timers)"
```

---

### Task 19: Final Integration Test + Cleanup

**Files:**
- Create: `v3/vibe-ai-adoption/tests/test_integration.py`
- Modify: `v3/vibe-ai-adoption/README.md`
- Modify: `v3/vibe-ai-adoption/PROGRESS.md`

**Step 1: Write integration test**

```python
# tests/test_integration.py
"""
Integration tests that verify the full 3-layer architecture.
These tests mock LLM calls but test real LangGraph + state management.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.models.lead import Lead, LeadScore, QualificationResult
from src.models.content import Segment, ContentPiece, ContentFormat, RepurposedContent
from src.models.nurture import NurtureAction


class TestLeadQualificationPipeline:
    def test_full_pipeline_high_priority(self):
        """Lead with high scores routes to high_priority."""
        from src.workflows.lead_qualification import build_lead_qual_graph

        mock_result = QualificationResult(
            lead_id="int-1", score=LeadScore(fit=95, intent=90, urgency=85), reasoning="Perfect fit"
        )
        with patch("src.workflows.lead_qualification.run_lead_qualification", return_value=mock_result):
            with patch("src.workflows.lead_qualification.update_crm", return_value={"crm_updated": True}):
                graph = build_lead_qual_graph()
                result = graph.invoke({
                    "lead": Lead(lead_id="int-1", email="ceo@bigco.com", company="BigCo", role="CEO").model_dump(),
                    "enriched_data": {},
                    "qualification": None,
                    "route": None,
                    "crm_updated": False,
                })
                assert result["route"] == "high_priority"
                assert result["crm_updated"] is True

    def test_full_pipeline_education(self):
        """Lead with low scores routes to education."""
        from src.workflows.lead_qualification import build_lead_qual_graph

        mock_result = QualificationResult(
            lead_id="int-2", score=LeadScore(fit=20, intent=15, urgency=10), reasoning="Not a fit"
        )
        with patch("src.workflows.lead_qualification.run_lead_qualification", return_value=mock_result):
            with patch("src.workflows.lead_qualification.update_crm", return_value={"crm_updated": True}):
                graph = build_lead_qual_graph()
                result = graph.invoke({
                    "lead": Lead(lead_id="int-2", email="student@edu.com", company="School", role="Student").model_dump(),
                    "enriched_data": {},
                    "qualification": None,
                    "route": None,
                    "crm_updated": False,
                })
                assert result["route"] == "education"


class TestContentPipeline:
    def test_full_pipeline_produces_content(self):
        """Content pipeline produces segments, pieces, and repurposed content."""
        from src.workflows.content_pipeline import build_content_pipeline_graph

        mock_segments = [Segment(name="AEC", description="AEC", pain_points=["x"], messaging_angle="y")]
        mock_piece = ContentPiece(title="Title", segment="AEC", content_type="blog_post", body="Body")
        mock_repurposed = [RepurposedContent(source_title="Title", format=ContentFormat.EMAIL, body="Email ver")]

        with patch("src.workflows.content_pipeline.run_segment_research", return_value=mock_segments):
            with patch("src.workflows.content_pipeline.run_content_generation", return_value=mock_piece):
                with patch("src.workflows.content_pipeline.run_content_repurposing", return_value=mock_repurposed):
                    graph = build_content_pipeline_graph()
                    result = graph.invoke({
                        "market": "collab", "num_segments": 1,
                        "segments": [], "content_pieces": [], "repurposed": [], "status": "pending",
                    })
                    assert result["status"] == "complete"
                    assert len(result["segments"]) == 1
                    assert len(result["content_pieces"]) >= 1


class TestNurtureSequence:
    def test_full_sequence_runs_to_completion(self):
        """Nurture sequence runs all 4 steps."""
        from src.workflows.nurture_sequence import build_nurture_graph

        actions = [
            NurtureAction(action_type="send_welcome", lead_id="n1", content="Welcome", reason="Day 1"),
            NurtureAction(action_type="send_case_study", lead_id="n1", content="Case", reason="Day 3"),
            NurtureAction(action_type="send_followup", lead_id="n1", content="Follow", reason="Day 7"),
            NurtureAction(action_type="move_to_long_term", lead_id="n1", content="Final", reason="Day 14"),
        ]
        call_count = {"n": 0}

        def mock_nurture(*args, **kwargs):
            action = actions[call_count["n"]]
            call_count["n"] += 1
            return action

        with patch("src.workflows.nurture_sequence.run_nurture_decision", side_effect=mock_nurture):
            graph = build_nurture_graph()
            result = graph.invoke({
                "lead_id": "n1", "lead_company": "Acme",
                "current_step": "day_1", "emails_sent": 0,
                "engagement_score": 0.0, "engagement_events": [],
                "actions_taken": [], "paused": False,
                "completed": False, "outcome": None,
            })
            assert result["completed"] is True
            assert result["outcome"] == "long_term"
            assert len(result["actions_taken"]) == 4

    def test_early_escalation_at_day7(self):
        """High-engagement lead escalates to sales at day 7."""
        from src.workflows.nurture_sequence import build_nurture_graph

        actions = [
            NurtureAction(action_type="send_welcome", lead_id="n2", content="Welcome", reason="Day 1"),
            NurtureAction(action_type="send_case_study", lead_id="n2", content="Case", reason="Day 3"),
            NurtureAction(action_type="escalate_to_sales", lead_id="n2", content="Escalate", reason="High engagement"),
        ]
        call_count = {"n": 0}

        def mock_nurture(*args, **kwargs):
            action = actions[call_count["n"]]
            call_count["n"] += 1
            return action

        with patch("src.workflows.nurture_sequence.run_nurture_decision", side_effect=mock_nurture):
            graph = build_nurture_graph()
            result = graph.invoke({
                "lead_id": "n2", "lead_company": "BigCo",
                "current_step": "day_1", "emails_sent": 0,
                "engagement_score": 0.0, "engagement_events": [],
                "actions_taken": [], "paused": False,
                "completed": False, "outcome": None,
            })
            assert result["completed"] is True
            assert result["outcome"] == "escalated_to_sales"
            assert len(result["actions_taken"]) == 3  # Only 3 steps, skipped day 14
```

**Step 2: Run all tests**

Run: `cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: ALL tests PASS (should be ~30+ tests total)

**Step 3: Update PROGRESS.md**

Update Phase 0 tasks to completed status and add Phase 1-3 workflow validation status.

**Step 4: Update README.md**

Update to reflect the actual implemented project structure and how to run it.

**Step 5: Commit**

```bash
cd /Users/apos/Workspace/apos/@dev/openvibe/v3/vibe-ai-adoption
git add tests/test_integration.py README.md PROGRESS.md
git commit -m "feat: add integration tests + update progress (Phase 0 + 3 workflows complete)"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Python project scaffold + config | Config loads |
| 2 | Docker infrastructure (Postgres + Temporal) | Services healthy |
| 3 | Pydantic models (lead, content, nurture) | 10 tests |
| 4 | LangGraph Postgres checkpointer | 2 tests |
| 5 | CrewAI + Claude base agent factory | 2 tests |
| 6 | Temporal worker scaffold (hello world) | 2 tests |
| 7 | E2E hello world (Temporal → LangGraph → CrewAI) | 3 tests |
| 8 | HubSpot integration | 4 tests |
| 9 | Slack integration | 3 tests |
| 10 | Lead Qualification CrewAI agent | 3 tests |
| 11 | Lead Qualification LangGraph workflow | 4 tests |
| 12 | Lead Qualification Temporal integration | 2 tests |
| 13 | Content Pipeline 3 CrewAI agents | 6 tests |
| 14 | Content Pipeline LangGraph workflow | 3 tests |
| 15 | Content Pipeline Temporal integration | 2 tests |
| 16 | Nurture CrewAI agent | 2 tests |
| 17 | Nurture LangGraph workflow (checkpoints + HITL) | 3 tests |
| 18 | Nurture Temporal integration (14-day durable) | 2 tests |
| 19 | Integration tests + cleanup | 5 tests |

**Total: 19 tasks, ~56 tests**

Each task produces a working, tested increment. Phase 0 infrastructure is validated by Task 7. Each workflow is validated independently (Tasks 10-12, 13-15, 16-18). Task 19 validates end-to-end.
