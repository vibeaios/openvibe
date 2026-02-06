# Vibe AI Workspace - Monorepo Architecture

> Complete code structure design supporting multi-industry vertical deployment

---

## Directory Structure

```
vibe-ai/
│
├── nx.json
├── package.json
├── tsconfig.base.json
│
├── ═══════════════════════════════════════════════════════
│   APPS (Deployable Units)
├── ═══════════════════════════════════════════════════════
│
├── apps/
│   │
│   ├── web/                          # User-facing applications
│   │   ├── workspace/                # Main Workspace UI (Next.js)
│   │   ├── admin/                    # Admin Console UI
│   │   └── onboarding/               # Setup wizard
│   │
│   ├── api/                          # Backend services
│   │   ├── gateway/                  # API Gateway (auth, routing)
│   │   ├── realtime/                 # WebSocket service (Supabase Realtime)
│   │   └── webhooks/                 # Webhook receivers
│   │
│   └── devices/                      # Device-related
│       ├── hub/                      # Device Registry & Connection Hub
│       └── bridge/                   # Hardware -> Memory Pipeline (Bot/Dot)
│
├── ═══════════════════════════════════════════════════════
│   SERVICES (Core Business Services)
├── ═══════════════════════════════════════════════════════
│
├── services/
│   │
│   ├── memory/                       # Core! (90% of value)
│   │   ├── core/                     # Memory API, schemas
│   │   ├── storage/                  # Pluggable backends (pg/sqlite/file)
│   │   ├── vector/                   # Embedding + RAG
│   │   ├── sync/                     # Multi-device sync
│   │   └── zoom/                     # Permission zoom levels
│   │
│   ├── agents/                       # Agent system
│   │   ├── runtime/                  # Containerized OpenClaw
│   │   ├── orchestrator/             # Routing + scheduling
│   │   ├── pool/                     # Agent pool management
│   │   └── collaboration/            # Multi-agent collaboration protocol
│   │
│   ├── threads/                      # Git-like Thread Engine
│   │   ├── engine/                   # Branch/Merge logic
│   │   ├── storage/                  # Thread persistence
│   │   └── realtime/                 # Real-time sync
│   │
│   ├── config/                       # Configuration system
│   │   ├── engine/                   # 4-layer config engine
│   │   ├── templates/                # Industry templates
│   │   └── admin/                    # Console command handling
│   │
│   ├── iam/                          # Identity and permissions
│   │   ├── auth/                     # Supabase Auth wrapper
│   │   ├── rbac/                     # Role-based access control
│   │   ├── workspaces/               # Multi-tenancy
│   │   └── teams/                    # Team management
│   │
│   ├── channels/                     # External channels
│   │   ├── slack/
│   │   ├── discord/
│   │   ├── teams/
│   │   ├── email/
│   │   └── voice/                    # Phone/voice
│   │
│   ├── integrations/                 # External system integrations
│   │   ├── core/                     # Integration framework
│   │   ├── ehr/                      # Epic, Cerner (medical)
│   │   ├── legal/                    # Clio, MyCase (legal)
│   │   ├── construction/             # Procore, PlanGrid
│   │   └── crm/                      # Salesforce, HubSpot
│   │
│   ├── devices/                      # Device services
│   │   ├── registry/                 # Device as Entity
│   │   ├── status/                   # Online/offline/health
│   │   ├── capture/                  # Bot/Dot data capture
│   │   └── assignment/               # Device -> User/Space assignment
│   │
│   ├── llm/                          # LLM routing
│   │   ├── router/                   # Model selection
│   │   ├── providers/                # Claude, GPT, Local
│   │   └── cost/                     # Token tracking
│   │
│   ├── billing/                      # Billing
│   │   ├── metering/                 # Usage statistics
│   │   ├── plans/                    # Pricing plans
│   │   └── stripe/                   # Stripe integration
│   │
│   └── observability/                # Monitoring
│       ├── logging/
│       ├── metrics/
│       └── tracing/
│
├── ═══════════════════════════════════════════════════════
│   LIBS (Shared Libraries)
├── ═══════════════════════════════════════════════════════
│
├── libs/
│   │
│   ├── core/                         # Core types/utilities
│   │   ├── types/                    # Shared TypeScript types
│   │   ├── utils/                    # General utility functions
│   │   ├── errors/                   # Error definitions
│   │   └── constants/                # Constants
│   │
│   ├── ui/                           # UI component library
│   │   ├── primitives/               # Base components (button, input)
│   │   ├── thread/                   # Thread-related components
│   │   ├── agent/                    # Agent UI components
│   │   ├── device/                   # Device panel
│   │   ├── memory/                   # Memory browser
│   │   └── admin/                    # Admin components
│   │
│   ├── schemas/                      # Data schemas
│   │   ├── memory/
│   │   ├── thread/
│   │   ├── agent/
│   │   ├── device/
│   │   └── config/
│   │
│   └── clients/                      # Service SDKs
│       ├── memory-client/
│       ├── agent-client/
│       └── device-client/
│
├── ═══════════════════════════════════════════════════════
│   VERTICALS (Industry Templates)
├── ═══════════════════════════════════════════════════════
│
├── verticals/
│   │
│   ├── _base/                        # Base template
│   │   ├── agents/                   # General Agents
│   │   ├── skills/                   # General Skills
│   │   ├── thread-types/             # General Thread Types
│   │   └── config.yaml               # Default configuration
│   │
│   ├── medical-clinic/               # Medical Clinic
│   │   ├── agents/
│   │   ├── skills/
│   │   ├── thread-types/
│   │   ├── roles/
│   │   ├── workflows/
│   │   └── config.yaml
│   │
│   ├── pi-lawyer/                    # Personal Injury Law Firm
│   │   ├── agents/
│   │   ├── skills/
│   │   ├── thread-types/
│   │   └── config.yaml
│   │
│   ├── construction/                 # Construction
│   │   ├── agents/
│   │   ├── skills/
│   │   ├── thread-types/
│   │   └── config.yaml
│   │
│   └── enterprise-general/           # General Enterprise
│       ├── agents/
│       ├── skills/
│       └── config.yaml
│
├── ═══════════════════════════════════════════════════════
│   PACKAGES (Published Packages)
├── ═══════════════════════════════════════════════════════
│
├── packages/
│   │
│   ├── sdk/                          # Developer SDK
│   │   ├── js/                       # JavaScript/TypeScript
│   │   ├── python/                   # Python
│   │   └── cli/                      # CLI tools
│   │
│   ├── types/                        # Shared types (npm publish)
│   │
│   └── extensions/                   # Extension framework
│       ├── agent-template/           # Custom Agent template
│       ├── skill-template/           # Custom Skill template
│       └── integration-template/     # Custom integration template
│
├── ═══════════════════════════════════════════════════════
│   TOOLS & INFRA
├── ═══════════════════════════════════════════════════════
│
├── tools/
│   ├── generators/                   # Nx generators
│   │   ├── vertical/                 # nx g @vibe/vertical --name=dental
│   │   ├── agent/                    # nx g @vibe/agent --name=receptionist
│   │   └── skill/                    # nx g @vibe/skill --name=calendar
│   │
│   ├── scripts/                      # Development scripts
│   └── migrations/                   # DB migrations
│
├── infra/
│   ├── terraform/                    # IaC
│   │   ├── modules/
│   │   ├── environments/
│   │   └── ...
│   │
│   ├── k8s/                          # Kubernetes manifests
│   │   ├── base/
│   │   └── overlays/
│   │
│   └── docker/                       # Docker configuration
│       ├── agent/
│       ├── api/
│       └── ...
│
├── ═══════════════════════════════════════════════════════
│   DOCS & CONFIG
├── ═══════════════════════════════════════════════════════
│
├── docs/
│   ├── architecture/                 # Architecture documentation
│   ├── api/                          # API documentation
│   ├── guides/                       # Development guides
│   └── specs/                        # Design specifications
│
└── config/
    ├── platform/                     # Platform defaults
    └── environments/                 # Environment configuration
```

---

## Dependency Relationships

```
libs/core/types ────────────────────────────────────────────────┐
       │                                                        │
       ▼                                                        │
libs/schemas/* ─────────────────────────────────────────────────┤
       │                                                        │
       ├──────────────────┬──────────────────┬─────────────────┤
       ▼                  ▼                  ▼                  │
services/memory    services/threads   services/agents           │
       │                  │                  │                  │
       └─────────┬────────┴─────────┬────────┘                  │
                 │                  │                           │
                 ▼                  ▼                           │
        services/config     services/iam                        │
                 │                  │                           │
                 └────────┬─────────┘                           │
                          │                                     │
                          ▼                                     │
                    apps/api/gateway                            │
                          │                                     │
          ┌───────────────┼───────────────┐                    │
          ▼               ▼               ▼                    │
    apps/web/*      services/channels  services/devices        │
          │               │               │                    │
          └───────────────┼───────────────┘                    │
                          │                                     │
                          ▼                                     │
                  verticals/* (inherits libs + services)        │
                          │                                     │
                          └─────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology Choice | Rationale |
|------|----------|------|
| **Monorepo** | Nx | Enterprise-grade, dependency graph, code generators |
| **Frontend** | Next.js 14 + React | SSR, App Router, ecosystem |
| **UI** | TailwindCSS + shadcn/ui | Rapid development, customizable |
| **Backend** | Node.js + tRPC | End-to-end type safety |
| **Database** | PostgreSQL + Supabase | Managed, RLS, Realtime |
| **Vector** | pgvector | Integrates with Postgres |
| **Queue** | BullMQ + Redis | Reliable task queue |
| **Container** | Docker + K8s | Isolated Agent execution |
| **IaC** | Terraform | Multi-cloud support |

---

*See DESIGN-SPEC.md for detailed design rationale*
