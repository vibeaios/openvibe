# Infrastructure

## 三层架构

```
┌──────────────────────────────────────┐
│  Temporal (调度)                      │
│  - Durable execution                 │
│  - 定时触发                           │
│  - 重试 + 超时                        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  LangGraph (执行)                     │
│  - 状态机                             │
│  - Checkpoint (Postgres)             │
│  - Human-in-the-loop                 │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  CrewAI (角色)                        │
│  - Agent 定义                         │
│  - 团队协作                           │
└──────────────────────────────────────┘
```

## Setup

### Temporal

```bash
# Option 1: Temporal Cloud (推荐)
# 在 https://cloud.temporal.io 创建 namespace

# Option 2: Self-hosted (dev)
docker-compose up -d temporal
```

### LangSmith

```bash
# 在 https://smith.langchain.com 创建账号
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your-key>
export LANGCHAIN_PROJECT=vibe-ai-adoption
```

### Database (Checkpoint)

```bash
# Postgres for LangGraph checkpointer
docker run -d \
  --name langgraph-postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15
```

## 环境变量

```bash
# .env
TEMPORAL_ADDRESS=<namespace>.tmprl.cloud:7233
TEMPORAL_NAMESPACE=vibe-ai-adoption
TEMPORAL_API_KEY=<key>

LANGCHAIN_API_KEY=<key>
LANGCHAIN_TRACING_V2=true

DATABASE_URL=postgresql://postgres:password@localhost:5432/langgraph

ANTHROPIC_API_KEY=<key>  # Claude
HUBSPOT_API_KEY=<key>    # CRM
```

## 成本估算 (月)

| 项目 | 成本 |
|------|------|
| Temporal Cloud | $200-500 |
| Claude API | $2,000-5,000 |
| LangSmith | $400 |
| Postgres | $50-100 |
| **Total** | **$3,000-6,000** |
