# OpenVibe V5 Roadmap

---

## Phase 0: Housekeeping ✓ (complete)

Simplify root docs, scaffold V5 directory structure.

**Gate to Phase 1:** V5 directory structure in place, root docs updated.

---

## Phase 1: Platform Multi-Tenancy ✓ (complete)

Copy V4 packages to V5, add SDK multi-tenant primitives, add tenant-scoped platform routes.

**What was built:**
- SDK v1.0.0: `TenantContext`, `TemplateConfig`, `RoleInstance`, `TemplateRegistry`, System Roles
- Platform v1.0.0: `TenantStore`, `/tenants` routes, isolated workspace/role/approval/deliverable routes per tenant
- CLI v1.0.0: `--tenant` flag
- Verification: 279 SDK tests, 59 platform tests, 14 CLI tests

**Gate to Phase 2:** All 4 packages pass tests, tenant isolation verified.

---

## Phase 2: Strategy Artifacts ✓ (complete)

Write V5 strategy docs and YAML role templates. No code.

**What was written:**
- `v5/docs/THESIS.md` — two-customer cognition OS
- `v5/docs/DESIGN.md` — multi-tenant Role SDK architecture
- `v5/docs/ROADMAP.md` — this document
- `v5/docs/strategy/ASTROCREST.md` — Astrocrest principles
- `v5/docs/strategy/INCUBATION-LOGIC.md` — six-stage lifecycle
- `v5/docs/strategy/OS-MODEL.md` — sub-segment selection + company architecture
- YAML role templates: 4 GTM + 3 product-dev + 6 Astrocrest
- Application scaffolds: vibe-inc + astrocrest

**Gate to Phase 3:** All docs written, templates in place, scaffold configs complete.

---

## Phase 3: Role Implementations (future)

Implement role internals: LangGraph workflows, tool integrations, memory, output formatting.

**Must be true to start:**
- Vibe Inc feedback on first 3 roles (Content, Revenue, Product Ops)
- At least 1 real workflow completed end-to-end
- Role output format validated (progressive disclosure)

**Planned work:**
- `GTM/Content` role: content brief → draft → review loop
- `GTM/Revenue` role: pipeline scan → lead prioritization → action items
- `Product/ProductOps` role: feature intake → spec → priority ranking
- Memory integration: role learns from feedback over sessions
- Approval workflow: LangGraph → HumanLoopService → CLI review

---

## Phase 4: Astrocrest Live + Vibe Inc Product Dev (future)

Both customers operating with real role workflows. First external brand launched.

**Must be true to start:**
- Vibe Inc: 3 roles live and delivering weekly value
- Astrocrest: Market Scanner role running weekly sub-segment scans
- EduReach brand decision validated (first 5 paid Catholic K-12 clients)

**Planned work:**
- Astrocrest Market Scanner live: weekly sub-segment scoring reports
- EduReach Brand: first client onboard, first AI-delivered marketing campaign
- Vibe Inc Product Dev: Product Ops + Eng Ops roles live
- Studio separation: EduReach as standalone brand with own SOUL config
- Flywheel metrics: referral tracking, AI deliverability measurement

---

## Decision Gates Summary

| Phase | Gate Condition |
|-------|----------------|
| 0 → 1 | Directory structure ready, root docs updated |
| 1 → 2 | All packages with tests, tenant isolation verified |
| 2 → 3 | Docs + templates + scaffolds complete |
| 3 → 4 | 3 Vibe Inc roles live, 1 end-to-end workflow |
| 4 → scale | EduReach: 5+ paying clients, >40% referral-sourced |
