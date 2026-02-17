# Inter-Operator Communication Design

> **Date:** 2026-02-16
> **Status:** Proposed
> **Depends on:** Operator pattern (implemented), NATS JetStream

---

## Problem

5 operators run independently. No cross-operator data flow. In production:
- Revenue Ops needs Company Intel research results
- Content Engine needs Revenue Ops segment data
- Customer Success needs deal context from Revenue Ops
- Market Intel insights should feed back to Content Engine

## Architecture: Two Planes

```
┌─────────────────────────────────────────────────────┐
│  Control Plane: Temporal Cloud                       │
│  "who does what, when"                               │
│  - Scheduling, durable execution, retries            │
│  - Already distributed — workers on any server       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Data Plane: NATS Cluster                            │
│  "what data flows between operators"                 │
│  - Event Bus: async notifications (JetStream)        │
│  - KV Store: shared context (built-in)               │
│  - Request/Reply: sync queries (built-in)            │
└─────────────────────────────────────────────────────┘
```

## Communication Patterns

### Pattern 1: Event Bus (async)

Operators emit events on completion. Others subscribe.

```
Company Intel completes research → emit "company.researched"
  ├── Revenue Ops → enrich lead scoring
  ├── Content Engine → adjust content by industry
  └── Customer Success → update account context

Revenue Ops qualifies lead → emit "lead.qualified"
  ├── Content Engine → trigger personalized content
  └── Customer Success → prepare onboarding
```

### Pattern 2: Shared Context Store (KV)

Each operator writes its output, reads others' output.

```
context/companies/{company_id}/intel      ← Company Intel writes
context/leads/{lead_id}/qualification     ← Revenue Ops writes
context/leads/{lead_id}/content_plan      ← Content Engine writes
context/accounts/{account_id}/health      ← Customer Success writes
context/market/{segment_id}/analysis      ← Market Intel writes
```

### Pattern 3: Request/Reply (sync)

Direct queries when an operator needs another's data mid-workflow.

```
Revenue Ops → request("company_intel.research", {company: "Stripe"})
Company Intel → reply({industry: "fintech", size: "10K+", ...})
```

## Recommended Combination

**Event Bus + KV Store.** Event Bus handles "when" (notifications), KV Store handles "what" (data).

## Server: NATS + JetStream

| Feature | NATS Capability |
|---------|----------------|
| Event Bus | JetStream streams (durable, at-least-once) |
| KV Store | Built-in KV buckets |
| Request/Reply | Native protocol |
| Subject routing | `operators.{id}.events.{type}` |
| Wildcard subscribe | `operators.*.events.>` |
| Deployment | Single binary, `nats-server -js` |
| Python client | `nats-py` (async native) |

## NATS Subject Schema

```
operators.company_intel.events.research_complete
operators.revenue_ops.events.lead_qualified
operators.revenue_ops.events.deal_updated
operators.content_engine.events.content_published
operators.customer_success.events.health_changed
operators.market_intel.events.analysis_complete

operators.{id}.request.{capability}   # for request/reply
operators.{id}.heartbeat              # for health checks
```

## KV Buckets

```
context-companies    # Company Intel output
context-leads        # Revenue Ops output
context-content      # Content Engine output
context-accounts     # Customer Success output
context-market       # Market Intel output
registry             # Service registry (operator capabilities)
```

## Distributed Deployment

Operators can run on different servers. Each server runs a Temporal worker registering its own activities.

```
Server A (GPU-heavy)                Server B (I/O-heavy)
┌─────────────────────┐            ┌─────────────────────┐
│ Content Engine       │            │ Revenue Ops          │
│ Market Intel         │            │ Customer Success     │
│ Temporal Worker A    │            │ Company Intel        │
│ (task queue: content)│            │ Temporal Worker B    │
└────────┬────────────┘            └────────┬────────────┘
         │                                  │
         └──────────┬───────────────────────┘
                    ▼
         ┌─────────────────────┐
         │   NATS Cluster       │
         │   Temporal Cloud     │
         └─────────────────────┘
```

NATS communication is transparent to operators — `bus.publish()` and `bus.subscribe()` work identically regardless of server topology.

## Implementation

### MessageBus (shared/message_bus.py)

```python
import nats
from dataclasses import dataclass

@dataclass
class OperatorEvent:
    operator_id: str
    event_type: str
    payload: dict
    timestamp: str

class MessageBus:
    def __init__(self, nats_url="nats://localhost:4222"):
        self._nc = None
        self._js = None
        self._url = nats_url

    async def connect(self):
        self._nc = await nats.connect(self._url)
        self._js = self._nc.jetstream()

    async def publish(self, operator_id: str, event_type: str, payload: dict):
        subject = f"operators.{operator_id}.events.{event_type}"
        await self._js.publish(subject, json.dumps(payload).encode())

    async def subscribe(self, pattern: str, handler):
        await self._js.subscribe(pattern, cb=handler)

    async def put_context(self, bucket: str, key: str, value: dict):
        kv = await self._js.key_value(bucket)
        await kv.put(key, json.dumps(value).encode())

    async def get_context(self, bucket: str, key: str) -> dict | None:
        kv = await self._js.key_value(bucket)
        entry = await kv.get(key)
        return json.loads(entry.value) if entry else None
```

### Service Registry

```python
class OperatorRegistry:
    async def register(self, operator_id, server, capabilities):
        await self.bus.put_context("registry", operator_id, {
            "server": server,
            "capabilities": capabilities,
            "last_heartbeat": now(),
        })

    async def discover(self, capability) -> list[str]:
        # scan KV bucket "registry"
```

### Minimal Code Changes

1. Add `shared/message_bus.py` — NATS client wrapper
2. Each workflow's final node adds `await bus.publish(...)`
3. Add subscriber handlers to trigger cross-operator workflows
4. Split `main.py` into per-server workers if distributed

Core operator logic (LangGraph graphs, call_claude, state) unchanged.

## Cross-Server Scenario

```
1. HubSpot webhook → Temporal Cloud
2. Temporal routes to Server B (revenue-ops task queue)
3. Revenue Ops: lead_qualification workflow
   - enrich node needs company data
   - → NATS request("company_intel.request.research", {company: "Stripe"})
4. Company Intel on Server B receives request
   - runs research workflow
   - → NATS reply({industry: "fintech", ...})
5. Revenue Ops scores lead (with company intel) → score 85
6. → emit "lead.qualified" via NATS
7. Server A: Content Engine receives event → personalized content
8. Server B: Customer Success receives event → onboarding prep
```

---

*Source of truth: This file (design) + `PROGRESS.md` (status)*
