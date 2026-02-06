# R6: Privacy Granularity & Hybrid Deployment

> Status: Research Complete | Researcher: privacy-hybrid-researcher | Date: 2026-02-07

---

## Research Question

Can OpenVibe build ONE universal privacy model that serves 5 deployment modes (edge/VPS/container/local/cloud) across regulated industries (HIPAA medical, attorney-client legal, OSHA construction, general enterprise), while maintaining user trust and enabling an open source strategy?

This research covers 7 sub-questions:
1. Unified privacy API across deployment modes
2. Data classification and residency
3. Per-industry compliance requirements
4. Trust boundaries per runtime
5. Open source strategy
6. LLM privacy: the fundamental tension
7. Practical hybrid deployment architecture

---

## Sources Consulted

### Internal Design Docs Read
- `docs/design/M6-AUTH.md` -- Current auth model (Supabase Auth, RBAC, RLS, API keys)
- `docs/architecture/DESIGN-SPEC.md` -- Memory-first architecture, 4-layer config, pluggable storage, containerized agents
- `docs/specs/CONFIG-SYSTEM.md` -- 4-layer config inheritance (Platform > Template > Workspace > User)
- `docs/specs/VERTICALS.md` -- Medical/Legal/Construction vertical templates, compliance flags
- `docs/INTENT.md` -- Phase 1 research goals, dogfood context, 7 core research questions

### External Research Conducted
- Supabase self-hosted: Docker architecture (GoTrue, PostgREST, Realtime, Kong, Supavisor, pgvector), operational overhead ($120K-$240K/yr FTE), feature parity gaps
- GitLab CE/EE model: Free tier (CE) vs Premium/Ultimate (source-available paid), install EE even for free use
- Bitwarden: Zero-knowledge encryption, open source + self-hosted enterprise, end-to-end encryption where provider never sees plaintext
- HIPAA 2025 updates: Proposed Security Rule overhaul eliminating addressable/required distinction, mandatory AES-256/TLS 1.3/MFA, BAA requirements for SaaS
- Attorney-client privilege + AI: Waiver risk from cloud LLM disclosure, "reasonable precautions" standard, private vs public AI distinction
- OSHA/Construction: 5-year injury/illness retention, 30-year exposure records, digital submission mandates
- Cal.com, PostHog, Appsmith: Open source + hosted SaaS models, freemium tiers
- GDPR data residency: No explicit localization mandate but practical transfer restrictions, SCCs, BCRs
- US state privacy laws: 20 state-level laws by October 2025, patchwork regulation
- Edge AI / Federated Learning: NVIDIA FLARE + ExecuTorch, data stays on device, model updates only
- HashiCorp Vault / SOPS: Centralized secrets, dynamic credentials, encrypted secrets in Git
- Zero-knowledge architecture: Encryption at device level, provider never holds keys, Bitwarden/Keeper model
- Anthropic Claude BAA: Available for API with zero data retention, Enterprise plans HIPAA-ready since late 2025
- Local LLM (Ollama, vLLM): Air-gapped deployment, 80-90% cost savings, Ollama for dev/edge, vLLM for production multi-user
- Open source licensing: AGPL, BSL, SSPL trends; Redis returning to AGPLv3 in 2025; open-core vs dual licensing

---

## Question 1: Can ONE Privacy API Serve All 5 Deployment Modes?

### Options Explored

#### Option A: Deployment-Specific Code Paths
- **Description:** Write separate privacy/data handling code per deployment target (cloud, VPS, container, local, edge).
- **Pros:** Each path is optimized; no abstraction overhead.
- **Cons:** 5x maintenance burden; divergent behavior; bugs in one path don't surface in others. Impossible to test combinatorially.
- **Why rejected:** Violates the "Configuration over Code" principle already established in DESIGN-SPEC. Unscalable.

#### Option B: Abstraction Layer with Provider Pattern (Recommended)
- **Description:** Single `PrivacyProvider` interface with deployment-specific implementations. The application code calls the same API regardless of where it runs. The configuration layer (already 4-tier: Platform > Template > Workspace > User) determines which provider implementation is active.
- **Pros:** Single codebase; testable against interface; deployment differences are configuration, not code. Aligns with existing pluggable storage design (PostgreSQL/SQLite/File backends).
- **Cons:** Abstraction may leak for edge cases (e.g., network-dependent features unavailable in air-gapped mode). Requires careful interface design upfront.
- **Why adopted:** This is the natural extension of the existing architecture. The DESIGN-SPEC already shows pluggable storage (PostgreSQL + pgvector / SQLite + sqlite-vec / File system). The privacy layer follows the same pattern.

#### Option C: Platform-as-a-Service with Self-Hosted Option
- **Description:** Build only for cloud, offer a "self-hosted" checkbox that bundles everything into Docker. Like Supabase's approach.
- **Pros:** Simpler initial development; most customers start with cloud.
- **Cons:** Self-hosted becomes second-class citizen. Feature parity gaps (Supabase's own community complains about this). Doesn't address air-gapped / edge scenarios at all. Violates the trust-building mission for regulated industries.
- **Why rejected:** The whole point of R6 is that regulated industries need REAL data sovereignty, not a checkbox.

### Recommendation: Provider Pattern with 4 Tiers

The abstraction layer has three components:

**1. Data Store Provider** (already designed in DESIGN-SPEC)
```
Interface: MemoryStore
  - PostgreSQL + pgvector (cloud/VPS)
  - SQLite + sqlite-vec (local/edge)
  - File system (OpenClaw compat)
```

**2. Secrets Provider** (new)
```
Interface: SecretsProvider
  - HashiCorp Vault (enterprise/VPS)
  - SOPS + age/GPG (container/local)
  - Environment variables (dev/minimal)
  - Cloud KMS (AWS KMS, GCP KMS for SaaS)
```

**3. LLM Provider** (new, critical)
```
Interface: LLMProvider
  - Cloud API (Anthropic Claude, OpenAI) -- highest capability
  - Local inference (Ollama/vLLM) -- highest privacy
  - Hybrid router -- routes by data sensitivity classification
```

**What stays the same across all deployments:**
- Auth model (user/team/role structure from M6-AUTH)
- Permission checks (RLS policies, RBAC)
- Audit logging (always on, storage location varies)
- Data classification rules (which data category, what sensitivity)
- Encryption at rest (always AES-256, key management varies by provider)
- API surface (same REST/WS endpoints regardless of deployment)

**What changes per deployment:**
- Where data physically lives (provider determines this)
- How secrets are stored and retrieved
- Which LLM processes queries
- Network boundaries (air-gapped = no outbound; cloud = full internet)
- Backup strategy (provider-specific)
- TLS certificate management

The 4-layer config system already in CONFIG-SYSTEM.md handles this naturally:
- **Platform layer:** Defines encryption requirements, audit requirements, minimum security standards
- **Template layer:** Locks compliance settings per vertical (HIPAA = true, locked)
- **Workspace layer:** Admin selects deployment mode and providers
- **User layer:** No privacy overrides allowed (this is a hard constraint)

---

## Question 2: Data Classification -- What Lives Where?

### Classification Taxonomy

Every piece of data in OpenVibe must be tagged with a sensitivity level. This determines where it CAN live.

| Category | Sensitivity | Examples | Cloud OK? | Local Required? |
|----------|-------------|----------|-----------|-----------------|
| **L0: Public** | None | Agent SOUL definitions, template configs | Yes | No |
| **L1: Internal** | Low | Team structure, workspace settings, non-sensitive thread metadata | Yes | No |
| **L2: Confidential** | Medium | General conversation content, agent memory, meeting summaries | Depends on industry | Depends on industry |
| **L3: Regulated** | High | Patient PHI, case details, privileged communications | Only with BAA + encryption | Required for some deployments |
| **L4: Restricted** | Critical | Encryption keys, auth tokens, API secrets, master passwords | Never in cloud plaintext | Always local or HSM |

### Per-Data-Type Analysis

**Conversation Content (Threads)**
- General enterprise: L2 (cloud OK with encryption)
- Medical clinic: L3 (cloud requires BAA, encryption, audit trail; many customers will want local)
- Law firm: L3 (cloud requires private AI + confidentiality agreement; strong preference for local)
- Construction: L2 (cloud OK; safety incidents may be L3 for liability reasons)

**Agent Memory**
- This is the hardest one. Memory accumulates sensitive data over time. A medical @FollowUp agent's memory contains patient names, conditions, treatment plans.
- Classification: inherits the HIGHEST sensitivity of any data it has ingested.
- Implication: Medical/Legal agent memory is ALWAYS L3, even if individual conversations might be L2.
- This means agent memory in regulated verticals must either be local or in a BAA-covered cloud environment.

**User Credentials**
- Always L4. Never stored in plaintext anywhere.
- Supabase Auth handles this today (bcrypt hashes for passwords, JWT for sessions).
- Self-hosted: credentials stay entirely within the customer's infrastructure.
- Cloud: Supabase handles; we need to ensure our own access is minimal.

**LLM Inference (The Hard One)**
- When a user sends a message and an agent processes it, the content goes to an LLM.
- Cloud LLMs (Claude API, GPT): The LLM provider sees the content. Even with BAA (Anthropic offers this for API with zero data retention), the data LEAVES the customer's boundary during inference.
- Local LLMs (Ollama + Llama 3): Data never leaves. But capabilities are weaker.
- This is the fundamental tension -- see Question 6 for deep analysis.

**Embeddings/Vectors**
- Vectors are mathematical representations of content. They are NOT directly reversible to plaintext, but research shows partial reconstruction is possible.
- Classification: Same as source data. Medical embeddings = L3.
- Cloud vector stores (pgvector on Supabase cloud) require same protections as source data.
- Local vector stores (sqlite-vec, local pgvector) keep everything within boundary.

### Key Insight: Classification Must Be Automatic

Manual classification won't work. A front desk person won't tag every message. The system needs:
1. **Vertical template defines default classification.** Medical-clinic template: all conversation content defaults to L3.
2. **Per-thread-type overrides.** A "patient-encounter" thread is always L3. A "staff-meeting" thread might be L2.
3. **Content scanning (optional).** Detect PHI/PII patterns and auto-escalate classification. This is useful for general enterprise verticals where not everything is sensitive.

---

## Question 3: Per-Industry Compliance Requirements

### HIPAA (Medical Clinics)

**What HIPAA actually requires for a conversation platform:**

| Requirement | What It Means for OpenVibe | Implementation |
|-------------|---------------------------|----------------|
| **Encryption at rest** | All stored PHI encrypted AES-256 | Supabase supports this; self-hosted needs explicit config |
| **Encryption in transit** | TLS 1.3 for all connections | Standard practice, enforce in platform config |
| **Access controls** | Role-based, minimum necessary | Already designed in M6-AUTH (physician/front-desk/billing roles) |
| **Audit trail** | Log ALL access to PHI | Every read/write to L3 data must be logged with who, when, what |
| **BAA with vendors** | Legal agreement with every sub-processor | Anthropic (API), Supabase, any cloud vendor must sign BAA |
| **Breach notification** | 60-day notification requirement | Need incident response procedure |
| **Data integrity** | Prevent unauthorized modification | RLS + audit log covers this |
| **MFA** | Multi-factor authentication | Mandatory in 2025 HIPAA updates; enforce in medical template |
| **Network segmentation** | Isolate PHI systems | Container isolation + network policies in K8s |
| **De-identification** | Remove identifiers when possible | Relevant for analytics/training; never use PHI for model training |

**2025 HIPAA Update Impact:** The proposed Security Rule changes eliminate the "addressable" loophole -- everything becomes mandatory. MFA, encryption, network segmentation are no longer optional. This actually simplifies our design: if we build for mandatory, we're compliant regardless of whether the rule passes.

**BAA Chain:** OpenVibe (us) -> Anthropic (LLM) -> Supabase (database) -> Cloud provider (infrastructure). Every link needs a BAA. For self-hosted, the chain collapses: customer runs everything, no BAA needed with us for the infrastructure.

**Practical Impact:** A medical clinic using cloud OpenVibe needs us to sign a BAA. We need Anthropic API (not Claude.ai) with zero data retention. We need Supabase's BAA. A medical clinic self-hosting just needs our software, which is pre-configured for HIPAA in the medical template.

### Attorney-Client Privilege (Law Firms)

**The legal standard is different from HIPAA. It's about "reasonable precautions."**

| Requirement | What It Means for OpenVibe | Risk Level |
|-------------|---------------------------|------------|
| **Confidentiality** | Communications must remain between attorney and client | HIGH -- cloud LLMs are "third parties" |
| **No waiver** | Sharing with third parties can waive privilege permanently | CRITICAL -- once waived, it's gone forever |
| **Reasonable precautions** | Lawyer must show they took reasonable steps | Need security certifications, encryption, access controls |
| **Metadata protection** | Even knowing a communication happened can be sensitive | Metadata must be protected, not just content |
| **Ethical obligations** | State bar rules on technology competence | Varies by state; California, New York, ABA Model Rules |

**The Cloud LLM Problem for Legal:**
Courts have not yet ruled definitively on whether sending privileged communications through a cloud LLM constitutes waiver. But the risk is real. The ABA has noted that "entering the contents of privileged attorney-client communications into public generative AI models could be deemed a failure to keep communications confidential."

**Key distinction:** Public AI (ChatGPT free tier, Claude.ai consumer) vs. Private AI (API with contractual protections, self-hosted models). Using a private API with explicit confidentiality agreements, zero data retention, and encryption is likely considered "reasonable precautions." But many law firms will want local inference to eliminate the argument entirely.

**Practical Impact:** Law firm vertical should strongly recommend self-hosted or at minimum API-only with zero data retention agreements. The template should default to local LLM inference for all case-related threads, with cloud LLM as opt-in only for non-privileged work.

### OSHA / Construction

**Much simpler requirements, but documentation-focused:**

| Requirement | What It Means for OpenVibe | Retention |
|-------------|---------------------------|-----------|
| **Injury/illness records** | OSHA 300/301 forms | 5 years after calendar year |
| **Exposure records** | Chemical, noise, pathogen documentation | 30 years after employment ends |
| **Training records** | Safety training completion | 1-3 years, varies by type |
| **Safety inspection records** | Site inspection documentation | Duration of project + retention |
| **Daily logs** | Weather, labor, equipment, activities | Project duration + varies |
| **Electronic submission** | Injury/illness data must be filed electronically | OSHA mandates digital |

**Practical Impact:** Construction is the easiest vertical for privacy. The concern is retention and auditability, not data residency. Cloud storage is fine. The template needs: strong retention policies (auto-archive, never auto-delete), searchable audit trails, and export capabilities for OSHA inspections.

**One edge case:** Safety incident threads may involve liability. If a worker is injured and the company is sued, all related communications become discoverable. The construction template should flag "safety-incident" thread types as L3 and retain them for the maximum period.

### General Enterprise

- Standard data protection (GDPR if EU customers, CCPA if California)
- No specific data residency requirements unless dictated by customer policy
- Cloud deployment is the default; self-hosted for customers who want it
- SOC 2 Type II certification is the table-stakes expectation

---

## Question 4: Trust Boundaries Per Runtime

### Current Runtime Analysis

OpenVibe inherits from OpenClaw's multi-runtime reality. Each runtime has fundamentally different trust properties.

#### OpenClaw via Telegram

| Aspect | Trust Level | Reality |
|--------|-------------|---------|
| **Message transport** | LOW | Telegram sees all message content. Telegram's servers are in multiple jurisdictions. |
| **User identity** | MEDIUM | Telegram accounts, not enterprise SSO. Phone number based. |
| **Data storage** | MEDIUM | Conversation data on Telegram's servers + OpenClaw's local storage. |
| **Encryption** | LOW-MEDIUM | Not E2E by default for bot interactions. Secret chats are E2E but bots can't use them. |
| **Compliance** | NONE | Cannot be HIPAA compliant. Cannot guarantee privilege. Not suitable for regulated data. |

**Recommendation:** OpenClaw via Telegram should be classified as an L0-L1 channel only. No regulated data should flow through it. It's fine for general notifications, casual team communication, personal assistant use. Not for patient data, case details, or safety incidents.

#### Claude Code CLI

| Aspect | Trust Level | Reality |
|--------|-------------|---------|
| **Execution** | HIGH | Runs locally on user's machine. Code execution is sandboxed. |
| **Data transport** | MEDIUM | Sends prompts to Anthropic API. Content goes to cloud for inference. |
| **User identity** | HIGH | Authenticated locally. Enterprise can use SSO. |
| **Data storage** | HIGH | Local file system. User controls storage. |
| **Compliance** | MEDIUM | Local execution is good. API calls mean data leaves boundary temporarily. With zero-retention API agreement, acceptable for most use cases. |

**Recommendation:** Claude Code CLI is suitable for L0-L3 data WITH appropriate API agreements (BAA/zero-retention). For L4 (keys, secrets), acceptable because secrets don't need to be sent to the LLM. For maximally sensitive legal work, pair with local LLM option.

#### Web UI (Cloud-Hosted)

| Aspect | Trust Level | Reality |
|--------|-------------|---------|
| **Data transport** | MEDIUM | HTTPS to OpenVibe servers. Standard web security. |
| **Data storage** | MEDIUM-HIGH | On our infrastructure (Supabase). We control the environment. |
| **User identity** | HIGH | Full auth system (Supabase Auth, OAuth, SSO). |
| **Compliance** | HIGH (achievable) | With BAA chain, encryption, audit logs, can be HIPAA compliant. |

**Recommendation:** Web UI is the primary channel for regulated industries when cloud deployment is used. Full control over the experience, auth, audit, and data handling.

#### Web UI (Self-Hosted)

| Aspect | Trust Level | Reality |
|--------|-------------|---------|
| **Everything** | HIGHEST | Customer controls all infrastructure. No data leaves their network. |
| **Compliance** | HIGHEST (achievable) | Customer is responsible for their own compliance, but the software makes it easy. |

**Recommendation:** Self-hosted Web UI is the gold standard for regulated industries. All L3 and L4 data stays within the customer's boundary.

### User Clarity: The Trust Dashboard

Users need to understand where their data goes. This is not a technical problem -- it's a UX problem.

**Proposal: Trust Indicators in the UI**

Each thread/channel should show a simple indicator:
- **Fully Local** (green lock): All data stays on your infrastructure. LLM inference is local.
- **Cloud w/ Protection** (blue shield): Data is encrypted, vendor has BAA, zero-retention API.
- **Cloud Standard** (gray): Standard cloud security. Not suitable for regulated data.
- **External Channel** (yellow): Data passes through third party (e.g., Telegram). Not for sensitive use.

This maps directly to the data classification:
- L0-L1: Any trust level
- L2: Cloud Standard or above
- L3: Cloud w/ Protection or Fully Local
- L4: Fully Local only

---

## Question 5: Open Source Strategy

### Options Explored

#### Option A: Fully Proprietary
- **Description:** Closed source. SaaS only.
- **Pros:** Maximum control. No competitors fork your code.
- **Cons:** Zero trust from regulated industries. "Trust us" is not enough for hospitals and law firms. Can't self-host. Dead on arrival for the target market.
- **Why rejected:** Fundamentally incompatible with OpenVibe's trust-building mission.

#### Option B: Open Core (like GitLab pre-2024)
- **Description:** Core platform open source (AGPL or MIT). Enterprise features (SSO, audit, compliance templates, advanced agent orchestration) are proprietary.
- **Pros:** Proven model. Community builds trust. Enterprise features justify pricing. Clear upgrade path.
- **Cons:** Constant tension about where the line is. Community resentment when features move to paid tier. "Open core" has become a pejorative in some circles.
- **Why considered but not primary:** Works, but the "what's free vs paid" line is hard to draw for a trust-focused product. If compliance features are paid-only, you're saying "trust is a premium feature," which undermines the message.

#### Option C: Source-Available (BSL / SSPL)
- **Description:** Source code visible but not technically "open source." BSL converts to open source after a delay. SSPL prevents cloud competitors.
- **Pros:** Prevents AWS/Google from offering "managed OpenVibe." Source transparency builds some trust.
- **Cons:** Not OSI-approved. Excluded from many Linux distributions. Community skepticism is high. HashiCorp's BSL switch in 2023 caused massive backlash. "Source available" is not "open source" and regulated industries' compliance teams know the difference.
- **Why rejected:** The trust argument falls flat. Law firms and hospitals want to audit the code AND deploy it freely. BSL/SSPL introduces friction that undermines the mission.

#### Option D: AGPL Core + Hosted Service (like Supabase model) -- Recommended
- **Description:** Full platform under AGPL-3.0. Everything is open source including compliance features. Revenue comes from: (1) Hosted SaaS with managed infrastructure, (2) Support & SLA agreements, (3) Vertical template marketplace (certified templates), (4) Professional services (deployment, customization), (5) Enterprise add-ons that are TOOLS not core features (e.g., managed Vault, managed monitoring, white-glove onboarding).
- **Pros:**
  - AGPL is a true open source license recognized by OSI.
  - AGPL's copyleft requirement means cloud competitors must also open-source their modifications. This is the "AWS protection" without being source-available.
  - Full code auditability builds genuine trust. A hospital's security team can audit every line.
  - Self-hosting is a first-class citizen, not an afterthought.
  - Community contributions improve the platform for everyone.
  - The "we make money from service, not from locking features" message resonates with trust-sensitive buyers.
- **Cons:**
  - Less revenue capture than open-core. Can't gate features behind paywall.
  - AGPL scares some companies (they worry about copyleft obligations). But these are not our target customers -- regulated industries with self-hosted needs are already comfortable with AGPL (PostgreSQL ecosystem, etc.).
  - Requires strong managed service to compete on convenience vs DIY.
- **Why adopted:** This is the Supabase/PostHog model adapted for trust-sensitive industries. Redis returned to AGPLv3 in 2025 with Redis 8, validating this approach. The key insight: in regulated industries, OPEN SOURCE IS THE PRODUCT FEATURE. It's not a marketing strategy -- it's a compliance requirement. Hospitals need to audit code. Law firms need to verify no data leaks. "Just trust us" doesn't work. "Read the code yourself" does.

#### Option E: Full FOSS + Services Only (like Red Hat)
- **Description:** Everything open source (Apache 2.0 or MIT). Revenue purely from support, training, certification.
- **Pros:** Maximum openness. No licensing concerns.
- **Cons:** Permissive licenses (MIT/Apache) don't prevent cloud competitors from offering managed versions. Red Hat model requires massive scale. OpenVibe doesn't have Red Hat's market position.
- **Why rejected:** Without copyleft protection, a cloud provider could offer "Managed OpenVibe" without contributing back. AGPL prevents this while still being genuinely open source.

### Recommendation: AGPL-3.0 + Managed Service

Revenue model breakdown:

| Revenue Stream | Description | Target Customer |
|----------------|-------------|-----------------|
| **Hosted SaaS** | Managed cloud OpenVibe. We handle infrastructure, updates, backups. | Small-medium teams, general enterprise |
| **Enterprise Support** | SLA, priority support, dedicated account manager | Self-hosted enterprises |
| **Vertical Templates** | Certified templates (medical, legal, construction). Free community templates exist, certified ones come with compliance guarantees. | Industry-specific customers |
| **Professional Services** | Deployment assistance, customization, compliance consulting | Regulated industries |
| **Managed Infrastructure Add-ons** | Managed Vault, managed monitoring, managed backups (for self-hosted customers who want some convenience) | Self-hosted customers who don't want full ops burden |

Why NOT gate compliance features: If HIPAA audit logging is paid-only, a clinic that self-hosts to save money can't be compliant. This defeats the purpose. Instead, the software is fully compliant out of the box. We charge for the SERVICE of managing it, not for the CAPABILITY.

---

## Question 6: LLM Privacy -- The Fundamental Tension

This is the hardest problem in R6. Every AI platform faces it. OpenVibe needs a clear position.

### The Tension

```
User types: "Patient John Smith, DOB 03/15/1985, diagnosed with..."
                                    |
                    +----- LOCAL LLM -----+------ CLOUD LLM ------+
                    |                     |                        |
                    | Data stays local    | Data goes to Anthropic |
                    | Llama 3 70B         | Claude Opus 4          |
                    | Good, not great     | Excellent reasoning    |
                    | 100% private        | BAA protects legally   |
                    | Needs GPU hardware  | Pay per token          |
                    |                     | Data SEEN by provider  |
                    +---------------------+------------------------+
```

### Options Explored

#### Option A: Cloud Only, Rely on BAA
- **Description:** Send everything to Claude API with BAA + zero data retention.
- **Pros:** Best AI capabilities. Simple architecture. Anthropic offers BAA for API.
- **Cons:** Data LEAVES the boundary during inference, even if not retained. Some customers (law firms especially) won't accept this. "Zero retention" still means the data was SEEN. A breach during transit is still a breach.
- **Why insufficient:** Works for some customers. Not for the most sensitive ones. Not a universal solution.

#### Option B: Local Only
- **Description:** All inference via Ollama/vLLM with local models (Llama 3, Mixtral, etc.).
- **Pros:** Maximum privacy. No data leaves boundary. Air-gapped compatible. Compliance teams love it.
- **Cons:** Significantly weaker capabilities, especially for complex reasoning, multi-step analysis, nuanced language. Requires GPU hardware ($5K-$30K per node). Not practical for small clinics or solo law offices. Model updates require manual deployment.
- **Why insufficient:** Quality gap is too large for many use cases. A medical @FollowUp agent needs excellent language understanding. A legal @Settlement agent needs strong reasoning. Local models in 2026 are good but not Claude/GPT-level for complex tasks.

#### Option C: Hybrid Router with Data Classification (Recommended)
- **Description:** Route inference requests based on data sensitivity classification. Sensitive data goes to local models. Complex reasoning with non-sensitive data goes to cloud. A "sanitize and route" layer sits between the application and LLM providers.
- **Architecture:**
  ```
  User Message
       |
       v
  [Data Classifier]  -- Checks thread type, vertical, content patterns
       |
       +--- L0-L1 (non-sensitive) --> Cloud LLM (full capability)
       |
       +--- L2 (confidential) --> Cloud LLM with BAA OR Local (admin choice)
       |
       +--- L3 (regulated) --> Local LLM (mandatory for some verticals)
       |                        OR Cloud with BAA + explicit consent
       |
       +--- L4 (restricted) --> Never sent to any LLM
  ```
- **Pros:**
  - Best of both worlds: privacy where needed, capability where possible.
  - Admin controls the routing policy through workspace config.
  - Vertical template can set defaults (medical: all patient threads -> local).
  - Progressive: as local models improve, more traffic routes locally.
  - Works with the existing config system (routing rules are configuration, not code).
- **Cons:**
  - Complexity. Two model backends to maintain.
  - Classification errors could route sensitive data to cloud. Need conservative defaults.
  - User experience varies: cloud responses are faster and better, local may be noticeably worse for some tasks. Users need to understand the tradeoff.
  - GPU hardware requirement for local inference adds to deployment cost.
- **Why adopted:** This is the only approach that serves ALL customer segments. A general enterprise team can use full cloud. A hospital can default to local with cloud for non-PHI tasks. A law firm can go fully local. The router is configurable, not hardcoded.

#### Option D: Sanitization / De-identification
- **Description:** Strip PHI/PII from prompts before sending to cloud LLM. Re-identify in the response.
- **Pros:** Uses cloud capabilities while protecting specific identifiers.
- **Cons:** Doesn't work for many use cases. "Patient [REDACTED] has [REDACTED] and needs [REDACTED]" is useless. Context matters -- you can't de-identify a medical discussion and still get meaningful AI responses. Also, re-identification is fragile and error-prone.
- **Why rejected as primary approach:** Useful as a supplementary technique for analytics and reporting, but not viable as the main privacy strategy for conversations. The content IS the sensitive data, not just the identifiers.

### Recommendation: Hybrid Router with Conservative Defaults

**Default routing by vertical template:**

| Vertical | Thread Type | Default Route | Admin Can Override To |
|----------|-------------|---------------|----------------------|
| Medical | patient-encounter | Local LLM | Cloud with BAA (explicit opt-in) |
| Medical | staff-meeting | Cloud with BAA | Local LLM |
| Medical | insurance-auth | Cloud with BAA | Local LLM |
| Legal | case-thread | Local LLM | Cannot override (locked) |
| Legal | negotiation | Local LLM | Cannot override (locked) |
| Legal | client-update | Local LLM | Cloud with BAA (explicit opt-in) |
| Construction | rfi-thread | Cloud | Local LLM |
| Construction | safety-incident | Local LLM | Cloud with BAA |
| Construction | daily-report | Cloud | Local LLM |
| General | any | Cloud | Local LLM |

The config system already supports this via the `locked` attribute on template-level settings.

**Local LLM Infrastructure:**
- Recommended: Ollama for development and small deployments, vLLM for production multi-user
- Minimum hardware: NVIDIA GPU with 24GB VRAM (RTX 4090) for 70B parameter models
- Recommended: 2x NVIDIA A100 or equivalent for production workloads
- Alternative: Apple Silicon Mac Studio (M2 Ultra, 192GB) for smaller deployments
- Model recommendations: Llama 3.1 70B or 405B for general use, specialized medical/legal fine-tuned models when available

---

## Question 7: Practical Hybrid Deployment Architecture

### Same Codebase, Different Configs

The deployment architecture follows the provider pattern from Question 1:

```
┌──────────────────────────────────────────────────────┐
│                  OpenVibe Core                        │
│                                                       │
│  Thread Engine | Agent Runtime | Memory System        │
│  Auth/Permissions | Config System | UI Components     │
│                                                       │
│  (Identical code in ALL deployment modes)             │
└───────────────────┬──────────────────────────────────┘
                    │
          ┌─────────┼─────────────────────┐
          │         │                     │
    ┌─────▼─────┐ ┌─▼─────────────┐ ┌────▼──────────┐
    │  Providers │ │   Providers   │ │   Providers   │
    │  (Cloud)   │ │  (Self-Host)  │ │   (Edge)      │
    │            │ │               │ │               │
    │ Supabase   │ │ Local PG      │ │ SQLite        │
    │ Cloud KMS  │ │ Vault/SOPS    │ │ File secrets  │
    │ Claude API │ │ Ollama/vLLM   │ │ Ollama        │
    │ S3 storage │ │ Local storage │ │ Local storage │
    └────────────┘ └───────────────┘ └───────────────┘
```

### Component Requirements by Deployment Mode

| Component | Cloud SaaS | VPS Self-Host | Container (K8s) | Local (Desktop) | Edge (Air-Gap) |
|-----------|-----------|---------------|------------------|-----------------|----------------|
| **Database** | Supabase (managed PG) | PostgreSQL (self-managed) | PostgreSQL (in cluster) | SQLite | SQLite |
| **Vector Store** | pgvector (Supabase) | pgvector (self-managed) | pgvector (in cluster) | sqlite-vec | sqlite-vec |
| **Auth** | Supabase Auth (managed) | GoTrue (self-hosted) | GoTrue (in cluster) | Local auth (simplified) | Local auth |
| **Realtime** | Supabase Realtime | Realtime server | Realtime server | WebSocket (local) | WebSocket (local) |
| **LLM** | Cloud API | Hybrid (cloud + local) | Hybrid (cloud + local) | Local (Ollama) | Local (Ollama) |
| **Secrets** | Cloud KMS | Vault or SOPS | Vault | SOPS or env vars | SOPS or env vars |
| **Storage** | S3/Supabase Storage | Local filesystem or S3 | PVC/S3 | Local filesystem | Local filesystem |
| **Monitoring** | Managed (Datadog/etc) | Self-hosted (Prometheus) | Prometheus/Grafana | Minimal logging | Minimal logging |
| **Backups** | Automated (Supabase) | Customer responsibility | Customer responsibility | User responsibility | User responsibility |
| **Updates** | We push automatically | Customer pulls | Customer pulls | Auto-update opt-in | Manual |

### What MUST Be Local vs What CAN Be Cloud

**MUST be local in every deployment:**
- Encryption keys (L4) -- never leave the deployment boundary
- Auth session management -- must work without internet
- Basic CRUD operations -- must work offline for edge/local modes
- Audit log writes -- must capture locally even if synced later

**CAN be cloud (with appropriate protections):**
- LLM inference (with BAA/zero-retention for regulated data)
- Backup storage (encrypted before upload)
- Analytics/telemetry (aggregated, de-identified)
- Template/plugin registry (read-only, no sensitive data)

**SHOULD be local for regulated verticals:**
- All conversation content (L3)
- Agent memory (inherits L3)
- Embeddings/vectors (inherits L3)
- LLM inference for regulated threads

### Sync Architecture: Local <-> Cloud

Some customers want hybrid: run locally but sync select data to cloud for backup, multi-site access, or mobile access.

**Sync Model:**
```
Local Instance                         Cloud Instance
┌─────────────┐                       ┌─────────────┐
│ Full data    │ ──── Encrypted ────> │ Encrypted    │
│ (L0-L4)     │      Sync           │ blob storage │
│              │                      │ (L0-L1 in    │
│              │ <─── Config/Updates  │  plaintext)  │
│              │                      │              │
└─────────────┘                       └─────────────┘
```

**Sync Rules:**
- L0-L1: Sync in readable form (for multi-device access, search)
- L2-L3: Sync as encrypted blobs only (cloud cannot read; keys stay local)
- L4: Never sync to cloud
- Sync is opt-in, not default
- Conflict resolution: last-write-wins with audit trail (not Git-like merging for sync -- that's for threads)

**Zero-Knowledge Sync Option:**
For the most paranoid customers (law firms), offer Bitwarden-style zero-knowledge sync:
- All data encrypted with a key derived from the user's master password
- Cloud stores only ciphertext
- We cannot decrypt even with full database access
- Trade-off: no server-side search on encrypted data. Client must download and decrypt locally for search.

---

## Open Questions

### Unresolved -- Needs Further Validation

1. **Local LLM quality threshold.** At what capability level is a local model "good enough" for medical/legal use cases? This needs real-world testing with actual workflows. Llama 3.1 405B is impressive but still below Claude Opus for complex reasoning. By the time OpenVibe ships, the gap may be smaller (or larger).

2. **GPU requirement accessibility.** Requiring a $5K+ GPU for local inference limits who can self-host with full AI capabilities. Apple Silicon is an alternative but not universal. Is there a viable "no-GPU" local inference option for basic agent tasks?

3. **Certification costs.** SOC 2 Type II, HITRUST, and similar certifications for the hosted service cost $50K-$200K+ per year. At what revenue level does this make sense? Can we partner with a compliance-as-a-service provider?

4. **AGPL compliance burden on customers.** Some enterprise legal departments are uncomfortable with AGPL even when they're not modifying the code. Need clear documentation / FAQ addressing common AGPL concerns for enterprise buyers.

5. **Multi-region deployment.** GDPR requires EU data to stay in EU. If we offer hosted service, we need EU and US instances at minimum. What's the infrastructure cost for multi-region?

6. **Anthropic BAA scope evolution.** Anthropic's BAA currently covers API with zero-retention. Will they expand to cover more products? Will they offer data residency guarantees (EU processing)?

7. **Agent memory classification drift.** An agent starts processing L1 data but gradually ingests L3 data through conversations. How do we handle reclassification of existing memory? Does all historical memory need to be migrated?

8. **Sync conflict resolution at scale.** The last-write-wins sync model is simple but may not work for multi-site medical clinics where two front desks modify the same patient thread. Need to think about this more.

9. **Vertical-specific compliance certification.** Medical clinics may want "HIPAA-certified" badge on the product. This is expensive and ongoing. Is the compliance template + self-hosted enough, or do customers expect formal certification?

10. **OpenClaw Telegram channel deprecation path.** If Telegram is L0-L1 only, what's the migration path for existing OpenClaw users who currently send sensitive data through it? This is a user communication challenge as much as a technical one.

---

## Rejected Approaches

### 1. Single Cloud-Only Deployment
- **What:** Only offer hosted SaaS, no self-hosted option.
- **Why rejected:** Regulated industries will not adopt. HIPAA and attorney-client privilege create hard requirements for data sovereignty.
- **Reconsider if:** The regulatory landscape changes to allow cloud-only solutions for all data types (unlikely in the near term).

### 2. Per-Message Encryption with Customer Keys (BYOK for Every Message)
- **What:** Encrypt each message with a customer-provided key before storage, even in our cloud.
- **Why rejected:** Prevents server-side search, RAG, embedding generation, and AI processing. The platform becomes a dumb encrypted blob store. Kills the Memory System value proposition.
- **Reconsider if:** Homomorphic encryption becomes practical for vector similarity search (academic research ongoing, not production-ready).

### 3. Federated Learning for Agent Training
- **What:** Train agents across multiple deployments without sharing data (like Google's Gboard approach).
- **Why rejected:** Overkill for current scale. Federated learning is designed for millions of devices. OpenVibe will have hundreds of deployments at most in the near term. The coordination overhead isn't justified. Also, the "agents" in OpenVibe are primarily prompt-driven, not trained models -- fine-tuning is not the primary customization mechanism.
- **Reconsider if:** OpenVibe reaches >1000 deployments and wants to improve base agent quality across all instances. Or if the architecture shifts toward fine-tuned models per vertical.

### 4. Building Our Own Auth System
- **What:** Replace Supabase Auth with a custom-built authentication system.
- **Why rejected:** Auth is not our competitive advantage. Supabase Auth (GoTrue) is open source, battle-tested, and self-hostable. Building our own adds risk and development time.
- **Reconsider if:** Supabase Auth doesn't support a critical authentication requirement (unlikely -- it already supports OAuth, SAML, MFA).

### 5. Data De-identification as Primary Privacy Strategy
- **What:** Strip all PII/PHI before cloud processing, re-identify locally.
- **Why rejected:** Doesn't work for conversation platforms. The CONTENT is the sensitive data. A medical conversation about symptoms is inherently PHI even without names. A legal strategy discussion is privileged even without case numbers.
- **Reconsider if:** Advances in context-preserving de-identification make it possible to strip identifiers while maintaining conversational coherence (research exists but not production-quality).

### 6. Separate Codebases for Cloud vs Self-Hosted
- **What:** Maintain two codebases optimized for each deployment model.
- **Why rejected:** Doubles engineering effort. Feature parity diverges. Bugs fixed in one aren't fixed in the other. This is exactly what Supabase's community complains about.
- **Reconsider if:** Never. This is an anti-pattern.

### 7. SSPL or BSL Licensing
- **What:** Source-available but not technically open source.
- **Why rejected:** Undermines trust with the exact audience that needs trust most. Not OSI-approved. Enterprise legal teams flag it. The AGPL provides equivalent "cloud competitor protection" while being genuinely open source.
- **Reconsider if:** A major cloud provider starts offering managed OpenVibe using our AGPL code and our revenue is significantly impacted. But AGPL's copyleft requirement should prevent this -- they'd have to open-source their entire managed service stack.

---

## Summary Recommendation

### The OpenVibe Privacy Architecture in One Page

**Principles:**
1. **Data classification drives everything.** L0-L4 sensitivity levels. Vertical templates set defaults. The system enforces where data can live.
2. **Provider pattern for deployment flexibility.** Same code, different backends. Configuration determines behavior.
3. **Conservative defaults for regulated verticals.** Medical and Legal templates default to local. General enterprise defaults to cloud. Admins can adjust within bounds.
4. **AGPL open source for trust.** Code auditability IS the trust mechanism. Not marketing -- a compliance feature.
5. **Hybrid LLM routing for the AI/privacy tension.** Route by classification. Local for sensitive, cloud for capability.
6. **Trust indicators in UI.** Users always know where their data is going.

**The MVP path for dogfood (Vibe internal):**
- Cloud deployment (Supabase hosted)
- Cloud LLM (Claude API)
- General enterprise template (L1-L2 data only)
- This is the simplest path that validates core product functionality

**The regulated industry path (Phase 5+):**
- Self-hosted deployment (Docker Compose or K8s)
- Hybrid LLM routing (local + cloud with BAA)
- Vertical-specific templates with locked compliance settings
- SOC 2 + HIPAA BAA for hosted option

**Key architectural decision for Phase 2 Design:** The provider interfaces (DataStore, SecretsProvider, LLMProvider) must be defined in Phase 2 even if only one implementation (cloud) is built for MVP. This prevents architectural debt that would make self-hosted a painful retrofit.

---

*Research completed: 2026-02-07*
*Researcher: privacy-hybrid-researcher*
*Next consumer: SYNTHESIS.md author, Phase 2 MVP designer*
