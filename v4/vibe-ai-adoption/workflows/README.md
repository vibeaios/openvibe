# Workflows (LangGraph)

状态机 + 执行逻辑，每个 workflow 包含:
- Nodes: 执行节点
- Edges: 跳转逻辑
- State: 持久化状态
- Checkpointer: 断点保存

## 核心 Workflows

| Workflow | 类型 | Agent 调用 |
|----------|------|-----------|
| lead_qualification | 触发式 | Lead Qual Agent |
| content_pipeline | 定时 (weekly) | Segment + Content + Repurpose |
| campaign_optimization | 循环 | Campaign Agent |
| nurture_sequence | 长期 (14天) | Nurture Agent |
| health_monitor | 定时 (daily) | Health Monitor Agent |
| onboarding | 长期 (30天) | Onboarding Agent |

## 示例 Workflow (LangGraph)

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres import PostgresSaver

# Define state
class LeadState(TypedDict):
    lead_id: str
    enriched_data: dict
    score: int
    route: str

# Define nodes
def enrich_lead(state: LeadState) -> LeadState:
    # Call enrichment API
    return {"enriched_data": {...}}

def score_lead(state: LeadState) -> LeadState:
    # Call CrewAI agent
    crew = Crew(agents=[lead_qualification_agent], tasks=[...])
    result = crew.kickoff()
    return {"score": result.score}

def route_lead(state: LeadState) -> str:
    if state["score"] >= 80:
        return "high_priority"
    elif state["score"] >= 50:
        return "nurture"
    else:
        return "education"

# Build graph
graph = StateGraph(LeadState)
graph.add_node("enrich", enrich_lead)
graph.add_node("score", score_lead)
graph.add_conditional_edges("score", route_lead, {...})

# Compile with checkpointer
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
app = graph.compile(checkpointer=checkpointer)
```
