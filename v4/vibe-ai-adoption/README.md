# Vibe AI Adoption Project

> 用 AI agents 替代执行层，实现 GTM 10-25x 提升

## 项目结构

```
vibe-ai-adoption/
├── README.md           # 项目说明
├── PROGRESS.md         # 进度追踪 ⭐
├── agents/             # Agent 定义 (CrewAI)
│   ├── marketing/
│   ├── sales/
│   └── cs/
├── workflows/          # Workflow 定义 (LangGraph)
│   ├── lead_qualification.py
│   ├── content_pipeline.py
│   ├── nurture_sequence.py
│   └── health_monitor.py
├── infra/              # 基础设施配置
│   ├── temporal/
│   └── langsmith/
└── docs/               # 文档
    ├── architecture.md
    └── decisions.md
```

## 架构

```
Temporal (调度) → LangGraph (执行) → CrewAI (角色)
```

## Quick Links

- **进度追踪**: [PROGRESS.md](./PROGRESS.md)
- **执行计划**: [docs/v3/VIBE-AI-ADOPTION-EXECUTION-PLAN.md](../../docs/v3/VIBE-AI-ADOPTION-EXECUTION-PLAN.md)
- **Published**: https://by-cy.com/vibe-ai-adoption-plan/

## Timeline

| Phase | Weeks | Focus |
|-------|-------|-------|
| 0 | 1-2 | 基础设施 (Temporal + LangGraph + CrewAI) |
| 1 | 3-4 | Lead Qualification Agent |
| 2 | 5-8 | Marketing Agents (7个) |
| 3 | 9-12 | Sales Agents (6个) |
| 4 | 13-16 | CS Agents (6个) |

## Team

| Role | Owner |
|------|-------|
| AI Orchestrator | TBD |
| Backend Eng | TBD |
| Marketing Lead | TBD |
| Sales Lead | TBD |

## Getting Started

```bash
# 1. 确认 Temporal Cloud access
# 2. 开通 LangSmith
# 3. 初始化 Python 环境
cd infra
pip install -r requirements.txt
```

---

*Started: 2026-02-14*
