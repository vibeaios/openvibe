# Agents (CrewAI)

Agent 角色定义，每个 agent 包含:
- role: 角色名称
- goal: 目标
- backstory: 背景设定
- tools: 可用工具

## 目录结构

```
agents/
├── marketing/
│   ├── segment_research.py
│   ├── content_generation.py
│   ├── content_repurposing.py
│   ├── campaign.py
│   ├── seo.py
│   ├── competitor_intel.py
│   └── customer_insights.py
├── sales/
│   ├── lead_qualification.py
│   ├── outbound_followup.py
│   ├── prospect_research.py
│   ├── proposal.py
│   ├── nurture.py
│   └── crm.py
└── cs/
    ├── onboarding.py
    ├── support.py
    ├── health_monitor.py
    ├── proactive_outreach.py
    ├── expansion.py
    └── feedback.py
```

## 示例 Agent 定义

```python
from crewai import Agent

lead_qualification_agent = Agent(
    role="Lead Qualification Specialist",
    goal="快速准确地评估每个 lead 的质量和意向",
    backstory="你是 Vibe 的资深销售，能从有限信息判断 lead 价值",
    tools=[
        hubspot_enrichment_tool,
        company_research_tool,
        scoring_model_tool
    ],
    verbose=True
)
```
