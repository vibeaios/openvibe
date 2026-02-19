# OpenVibe V5 Design

> Multi-tenant platform with Role SDK foundation.

---

## 1. Overview

V5 is a multi-tenant FastAPI platform where organizations run as **role collections** — AI participants with identity, memory, and authority, coordinated through a shared workspace.

The architecture is built in four layers:

```
Application Layer   (vibe-inc/, astrocrest/ — YAML configs, role instantiations)
Platform Layer      (openvibe-platform — FastAPI, tenant-scoped HTTP API)
Runtime Layer       (openvibe-runtime — LangGraph execution)
SDK Layer           (openvibe-sdk — Role, Operator, Memory, Registry, Templates)
```

---

## 2. Role SDK (openvibe-sdk v1.0.0)

The SDK is the foundation. Everything else builds on it.

### Core Concepts

**Role** — an AI participant with identity (SOUL), memory, authority config, and execution capabilities. Roles are not functions; they have persistent context and shaped behavior.

**TemplateConfig** — a YAML-driven role definition with soul and capability specs. Pre-built, versioned, reusable across tenants.

**TemplateRegistry** — manages pre-built templates. Tenants look up, instantiate, and override templates.

**RoleInstance** — a role instantiated from a template, with tenant-specific name and overrides.

**System Roles** — three roles automatically present in every workspace:
- `Coordinator` — routes tasks, manages approvals, handles escalation
- `Archivist` — manages memory, knowledge base, episodic retention
- `Auditor` — tracks deliverables, metrics, feedback loop

**TenantContext** — identity and data isolation context for a platform tenant. Each tenant has a unique `id`, `name`, and `data_dir`.

### Template Hierarchy

```
TemplateRegistry
    └── TemplateConfig (name, soul: dict, capabilities: list)
            └── RoleInstance (instantiated with name_override, tenant-specific)
```

Templates are stored as YAML under `v5/openvibe-sdk/templates/`:
- `templates/gtm/` — GTM roles (content, revenue, customer-success, market-intelligence)
- `templates/product-dev/` — Product dev roles (product-ops, engineering-ops, qa)
- `templates/research/` — Astrocrest research roles
- `templates/lifecycle/` — Astrocrest lifecycle roles
- `templates/system/` — System roles (auto-present in every workspace)

---

## 3. Multi-Tenant Platform (openvibe-platform v1.0.0)

### Tenant Isolation Model

Each tenant gets isolated service instances:
- `WorkspaceService` — separate workspace namespace
- `HumanLoopService` — separate approvals and deliverables queue
- `InMemoryRegistry` — separate role registry

Tenants are configured in `config/tenants.yaml` and loaded into `TenantStore` on startup.

### API Structure

```
/tenants                                  → list / get tenants
/tenants/{tenant_id}/workspaces           → CRUD workspaces (isolated per tenant)
/tenants/{tenant_id}/workspaces/{ws}/roles/spawn   → spawn roles
/tenants/{tenant_id}/workspaces/{ws}/approvals     → list approvals
/tenants/{tenant_id}/deliverables                  → list deliverables
/api/v1/...                               → legacy routes (backward compat)
```

### App State

```python
app.state.tenant_store            # TenantStore — tenant config lookup
app.state.tenant_workspace_svcs   # dict[tenant_id, WorkspaceService]
app.state.tenant_human_loop_svcs  # dict[tenant_id, HumanLoopService]
app.state.tenant_registries       # dict[tenant_id, InMemoryRegistry]
```

---

## 4. Package Structure

```
v5/
├── openvibe-sdk/           # SDK v1.0.0 — Role, Memory, Templates, Registry
│   ├── src/openvibe_sdk/
│   │   ├── models.py       # TenantContext, TemplateConfig, RoleInstance, + V3 models
│   │   ├── template_registry.py
│   │   ├── system_roles.py
│   │   └── ...
│   └── templates/          # YAML role templates
│
├── openvibe-runtime/       # Runtime v1.0.0 — LangGraph execution layer
│
├── openvibe-platform/      # Platform v1.0.0 — FastAPI, tenant-scoped HTTP API
│   ├── src/openvibe_platform/
│   │   ├── app.py          # create_app() factory
│   │   ├── tenant.py       # TenantStore, TenantNotFound
│   │   └── routers/        # tenants, workspaces, roles, approvals, deliverables
│   └── config/
│       └── tenants.yaml    # tenant configuration
│
├── openvibe-cli/           # CLI v1.0.0 — `vibe` command with --tenant flag
│
├── vibe-inc/               # Vibe Inc application (YAML configs)
│   └── config/             # soul.yaml, roles.yaml
│
└── astrocrest/             # Astrocrest application (YAML configs)
    └── config/             # soul.yaml, roles.yaml, scoring.yaml
```

---

## 5. SOUL Config (Role Identity)

Every role is configured with a SOUL — a structured identity definition in YAML:

```yaml
soul:
  identity:
    name: Content
    role: Content strategist and producer
    description: Researches segments, generates content, manages distribution
  philosophy:
    principles:
      - Quality over quantity
      - Segment-first thinking
    values: [Clarity, Relevance, Consistency]
  behavior:
    response_style: progressive_disclosure
    proactive: true
  constraints:
    trust_level: L2
    escalation_rules: Approve all external publishing
```

The SOUL is the moat. A role shaped by months of real feedback from Vibe's team is worth more than a generic prompt.

---

## 6. Known Debt: Model Duality (V3 vs V5)

`models.py` contains two parallel template/spec hierarchies:

| Origin | Models | Fields |
|--------|--------|--------|
| V3 (from V4 SDK) | `RoleTemplate`, `RoleSpec` | authority, domains, TTL, trust, goals, operator_ids |
| V5 (new) | `TemplateConfig`, `RoleInstance` | name, soul dict, capabilities list |

**Current state:** `Role.spawn()` uses V3 models. `TemplateRegistry` uses V5 models. They do not interoperate.

**Phase 3 resolution:** V5 models will absorb the relevant V3 fields (authority, domains, trust) as the template YAML schema matures. V3 models will be deprecated once all role instantiation flows through `TemplateRegistry`. The migration path:

1. Extend `TemplateConfig` with optional authority/domains/trust fields
2. Update `TemplateRegistry.instantiate()` to produce enriched `RoleInstance` objects
3. Bridge `RoleInstance` → `Role` (connect to LLM, memory, operators)
4. Remove V3 `RoleTemplate`/`RoleSpec` once no code references them

---

## 7. Legacy vs Tenant Routes

The platform serves two parallel route sets:

- **Legacy** (`/api/v1/...`) — shared service instances, persisted via `JSONFileStore`
- **Tenant-scoped** (`/tenants/{id}/...`) — per-tenant isolated instances, in-memory only

Data does not flow between them. This is intentional: legacy routes exist for backward compatibility during migration. New code should use tenant-scoped routes exclusively. Legacy routes will be removed once all clients migrate.
