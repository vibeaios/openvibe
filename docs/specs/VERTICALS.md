# Vertical Adaptation Specification

> Industry Template System Design

---

## Overview

Vibe AI Workspace adapts to different industries through Vertical Templates, achieving "one codebase + different configuration packages = different industry solutions."

---

## 1. Why Verticals Are Needed

### 1.1 Industry Differences

| Dimension | Medical Clinic | PI Lawyer | Construction |
|------|----------------|-----------|--------------|
| **Core Unit** | Patient / Encounter | Case | Project / Phase |
| **Key Agents** | @Scheduler, @Insurance | @Intake, @Settlement | @RFI, @DailyLog |
| **Compliance** | HIPAA (strict) | Attorney-Client Privilege | OSHA / Safety |
| **Workflows** | Locked examination process | Flexible | Document-driven |
| **Hardware Scenarios** | Front desk Check-in | Client meeting recording | Job site Trailer |
| **External Systems** | EHR (Epic, Cerner) | Legal CRM (Clio) | PM (Procore) |

### 1.2 Shared vs Custom

```
┌───────────────────────────────────────────────────────────┐
│                    Shared Layer (80%)                       │
│                                                            │
│  Memory System │ Thread Engine │ Agent Runtime             │
│  Device System │ Auth/IAM │ UI Components                  │
└───────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Medical (20%)  │ │  Legal (20%)    │ │ Construction    │
│                 │ │                 │ │     (20%)       │
│ • Agents        │ │ • Agents        │ │ • Agents        │
│ • Skills        │ │ • Skills        │ │ • Skills        │
│ • Workflows     │ │ • Workflows     │ │ • Workflows     │
│ • Thread Types  │ │ • Thread Types  │ │ • Thread Types  │
│ • Integrations  │ │ • Integrations  │ │ • Integrations  │
│ • Compliance    │ │ • Compliance    │ │ • Compliance    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2. Template Structure

### 2.1 Directory Structure

```
verticals/
├── _base/                        # Base template (inherited by all industries)
│   ├── agents/
│   │   ├── assistant.md          # General assistant
│   │   └── summarizer.md         # General summarizer
│   ├── skills/
│   │   ├── calendar/
│   │   ├── email/
│   │   └── search/
│   ├── thread-types/
│   │   ├── general.yaml
│   │   └── meeting.yaml
│   └── config.yaml
│
├── medical-clinic/               # Medical Clinic
│   ├── agents/
│   │   ├── scheduler.md
│   │   ├── followup.md
│   │   ├── insurance.md
│   │   └── concierge.md
│   ├── skills/
│   │   ├── ehr-integration/
│   │   ├── hipaa-guard/
│   │   └── appointment/
│   ├── thread-types/
│   │   ├── patient-encounter.yaml
│   │   ├── insurance-auth.yaml
│   │   └── followup-sequence.yaml
│   ├── roles/
│   │   ├── physician.yaml
│   │   ├── nurse.yaml
│   │   ├── front-desk.yaml
│   │   └── billing.yaml
│   ├── workflows/
│   │   ├── patient-check-in.yaml
│   │   ├── prescription-refill.yaml
│   │   └── insurance-verification.yaml
│   ├── integrations/
│   │   ├── epic.yaml
│   │   └── cerner.yaml
│   └── config.yaml
│
├── pi-lawyer/                    # Personal Injury Law Firm
│   ├── agents/
│   │   ├── intake.md
│   │   ├── client-comm.md
│   │   ├── medical-records.md
│   │   └── settlement.md
│   ├── skills/
│   │   ├── legal-research/
│   │   ├── lien-calculator/
│   │   └── demand-generator/
│   ├── thread-types/
│   │   ├── case-thread.yaml
│   │   ├── negotiation.yaml
│   │   └── client-update.yaml
│   ├── roles/
│   │   ├── attorney.yaml
│   │   ├── paralegal.yaml
│   │   └── intake-specialist.yaml
│   ├── workflows/
│   │   ├── new-case-intake.yaml
│   │   └── settlement-negotiation.yaml
│   └── config.yaml
│
└── construction/                 # Construction
    ├── agents/
    │   ├── rfi.md
    │   ├── daily-log.md
    │   ├── sub-coordinator.md
    │   ├── doc-search.md
    │   └── safety.md
    ├── skills/
    │   ├── procore-integration/
    │   ├── drawing-lookup/
    │   └── schedule-impact/
    ├── thread-types/
    │   ├── rfi-thread.yaml
    │   ├── daily-report.yaml
    │   └── safety-incident.yaml
    ├── roles/
    │   ├── project-manager.yaml
    │   ├── superintendent.yaml
    │   └── safety-officer.yaml
    ├── workflows/
    │   ├── rfi-submission.yaml
    │   └── safety-report.yaml
    └── config.yaml
```

---

## 3. Template Components

### 3.1 Agents

Each Agent is a Markdown file (similar to SOUL.md):

```markdown
# verticals/medical-clinic/agents/scheduler.md

# @Scheduler Agent

## Identity

You are the Scheduling Agent for a medical clinic. You help patients and staff manage appointments efficiently.

## Capabilities

- Schedule new appointments
- Reschedule existing appointments
- Send appointment reminders
- Check provider availability
- Handle cancellations

## Knowledge

You have access to:
- Provider schedules and availability
- Patient appointment history
- Appointment types and durations
- Clinic policies (no-shows, cancellation rules)

## Constraints

- Never double-book providers
- Respect provider preferences for appointment types
- Maintain required buffer time between appointments
- Follow HIPAA guidelines for patient information

## Integrations

- Calendar system (read/write)
- EHR (read patient info, appointment types)
- SMS/Email for confirmations and reminders

## Example Interactions

**Patient:** "I need to see Dr. Smith next week."
**Agent:** "I can help with that. Dr. Smith has availability on Tuesday at 10am or Thursday at 2pm. Which works better for you?"

**Staff:** "What's Dr. Johnson's schedule tomorrow?"
**Agent:** "Dr. Johnson has 6 appointments tomorrow: [lists appointments]. There are two open slots at 11am and 3pm."
```

### 3.2 Skills

Skills are capability modules that Agents can invoke:

```yaml
# verticals/medical-clinic/skills/ehr-integration/skill.yaml

skill:
  id: "ehr-integration"
  name: "EHR Integration"
  description: "Connect to Electronic Health Record systems"
  version: "1.0"

providers:
  - id: "epic"
    name: "Epic"
    config_schema:
      type: object
      properties:
        endpoint:
          type: string
        clientId:
          type: string
        clientSecret:
          type: string
          sensitive: true

  - id: "cerner"
    name: "Cerner"
    config_schema:
      # ...

actions:
  - id: "get_patient"
    name: "Get Patient Information"
    description: "Retrieve patient demographics and history"
    input:
      type: object
      properties:
        patientId:
          type: string
        fields:
          type: array
          items:
            enum: ["demographics", "appointments", "medications", "allergies"]
    output:
      type: object

  - id: "get_schedule"
    name: "Get Provider Schedule"
    description: "Get a provider's schedule for a date range"
    input:
      type: object
      properties:
        providerId:
          type: string
        startDate:
          type: string
          format: date
        endDate:
          type: string
          format: date

  - id: "create_appointment"
    name: "Create Appointment"
    description: "Schedule a new appointment"
    input:
      type: object
      properties:
        patientId:
          type: string
        providerId:
          type: string
        dateTime:
          type: string
          format: date-time
        appointmentType:
          type: string
        notes:
          type: string

permissions:
  required:
    - "ehr:read"
  optional:
    - "ehr:write"
    - "ehr:schedule"

compliance:
  hipaa: true
  audit_log: true
```

### 3.3 Thread Types

Thread Types define the structure of conversations:

```yaml
# verticals/medical-clinic/thread-types/patient-encounter.yaml

thread_type:
  id: "patient-encounter"
  name: "Patient Encounter"
  description: "Thread for a patient visit"

structure:
  # Required fields
  required:
    - patientId
    - providerId
    - encounterDate

  # Metadata
  metadata:
    patientId:
      type: string
      label: "Patient"
      lookup: "patients"
    providerId:
      type: string
      label: "Provider"
      lookup: "providers"
    encounterDate:
      type: date
      label: "Visit Date"
    encounterType:
      type: string
      label: "Visit Type"
      options: ["routine", "follow-up", "urgent", "new-patient"]
    chiefComplaint:
      type: string
      label: "Chief Complaint"

phases:
  - id: "pre-visit"
    name: "Pre-Visit"
    description: "Before the patient arrives"
    tasks:
      - "Verify insurance"
      - "Review previous notes"
      - "Prepare forms"

  - id: "check-in"
    name: "Check-In"
    description: "Patient arrival"
    tasks:
      - "Confirm identity"
      - "Update demographics"
      - "Collect copay"

  - id: "exam"
    name: "Examination"
    description: "Provider encounter"
    tasks:
      - "Vitals"
      - "Chief complaint"
      - "Examination"
      - "Assessment/Plan"

  - id: "checkout"
    name: "Checkout"
    description: "After the visit"
    tasks:
      - "Schedule follow-up"
      - "Print instructions"
      - "Submit claims"

agents:
  allowed:
    - "@Scheduler"
    - "@FollowUp"
    - "@Insurance"
  primary: "@FollowUp"

compliance:
  hipaa: true
  retention_days: 2555  # 7 years

ui:
  icon: "stethoscope"
  color: "#10b981"
```

### 3.4 Workflows

Workflows define locked business processes:

```yaml
# verticals/medical-clinic/workflows/patient-check-in.yaml

workflow:
  id: "patient-check-in"
  name: "Patient Check-In"
  description: "Standard patient check-in process"

  # Whether locked (Admin cannot modify)
  locked: true

  # Trigger conditions
  trigger:
    type: "event"
    event: "patient.arrived"
    conditions:
      - "appointment.status == 'scheduled'"

steps:
  - id: "verify-identity"
    name: "Verify Identity"
    type: "task"
    agent: "@Concierge"
    action:
      skill: "identity-verification"
      input:
        method: ["id-check", "photo-match"]
    next: "update-demographics"
    on_failure: "escalate-to-staff"

  - id: "update-demographics"
    name: "Update Demographics"
    type: "form"
    form: "patient-demographics"
    required: false
    next: "verify-insurance"

  - id: "verify-insurance"
    name: "Verify Insurance"
    type: "task"
    agent: "@Insurance"
    action:
      skill: "insurance-verification"
      input:
        realtime: true
    next:
      - condition: "result.eligible == true"
        goto: "collect-copay"
      - condition: "result.eligible == false"
        goto: "insurance-issue"

  - id: "collect-copay"
    name: "Collect Copay"
    type: "task"
    agent: "@Concierge"
    action:
      skill: "payment-collection"
      input:
        amount: "${insurance.copay}"
        methods: ["card", "cash", "check"]
    next: "notify-provider"

  - id: "notify-provider"
    name: "Notify Provider"
    type: "notification"
    target: "${appointment.providerId}"
    message: "Patient ${patient.name} checked in for ${appointment.time} appointment"
    next: "complete"

  - id: "complete"
    name: "Check-In Complete"
    type: "end"
    result: "success"

  - id: "insurance-issue"
    name: "Insurance Issue"
    type: "escalation"
    escalate_to: "front-desk"
    message: "Insurance verification failed for ${patient.name}"

  - id: "escalate-to-staff"
    name: "Escalate to Staff"
    type: "escalation"
    escalate_to: "front-desk"
    message: "Identity verification failed for appointment ${appointment.id}"

sla:
  max_duration_minutes: 15
  alert_at_minutes: 10

metrics:
  - "completion_rate"
  - "average_duration"
  - "escalation_rate"
```

### 3.5 Roles

Roles define role-based permissions:

```yaml
# verticals/medical-clinic/roles/physician.yaml

role:
  id: "physician"
  name: "Physician"
  description: "Medical doctor or provider"

permissions:
  # Memory permissions
  memory:
    read: "all"
    write: true
    delete: false

  # Zoom level
  zoom_level: 3  # Full access

  # Agents
  agents:
    access:
      - "@Scheduler"
      - "@FollowUp"
      - "@Insurance"
    configure: false

  # Threads
  threads:
    create: true
    branch: true
    merge: true
    delete: false
    types: "all"

  # Spaces
  spaces:
    access: "assigned"
    create: false
    manage: false

  # Devices
  devices:
    view: true
    assign: false
    command: true

  # Integrations
  integrations:
    use:
      - "ehr"
      - "calendar"
    configure: false

ui:
  dashboard: "provider-dashboard"
  default_space: "exam-rooms"

workflows:
  # Workflows that can be triggered
  trigger:
    - "prescription-refill"
    - "referral-request"
```

---

## 4. Detailed Industry Design

### 4.1 Medical Clinic

#### Value Proposition

```
Before Vibe AI:
  - Front desk uses 5 systems (EHR, calendar, phone, insurance, payments)
  - Doctors write notes manually, often delayed
  - Follow-ups rely on memory, frequently missed
  - Insurance verification is slow, patients wait a long time

After Vibe AI:
  - One interface integrates everything
  - Bot handles automatic check-in at the front desk
  - Dot records and auto-generates visit notes
  - @FollowUp automatically schedules follow-ups
  - @Insurance verifies insurance in real time
```

#### Agent Definitions

| Agent | Responsibility | Key Skills |
|-------|------|------------|
| **@Scheduler** | Appointment management | calendar, appointment, provider-availability |
| **@FollowUp** | Follow-up management | patient-outreach, reminder, task-tracking |
| **@Insurance** | Insurance verification | eligibility-check, prior-auth, claims |
| **@Concierge** | Patient services | check-in, payment, patient-communication |

#### Hardware Scenarios

| Device | Location | Purpose |
|------|------|------|
| **Bot** | Front desk | Check-in, inquiries |
| **Bot** | Waiting room | Patient notifications |
| **Dot** | Exam room | Record and generate notes |
| **Board** | Conference room | Multidisciplinary discussions |

#### Integrations

| System | Integration Method | Data Flow |
|------|----------|--------|
| **Epic/Cerner** | FHIR API | Bidirectional sync of patients and appointments |
| **Stripe** | API | Payment processing |
| **Twilio** | API | SMS reminders |
| **Zoom** | API | Telemedicine |

---

### 4.2 Personal Injury Lawyer

#### Value Proposition

```
Before Vibe AI:
  - Intake relies on phone calls, information often incomplete
  - Case status tracked via Excel
  - Clients keep asking for updates, attorneys have no time to respond
  - Medical records organized manually

After Vibe AI:
  - @Intake accepts cases 24/7
  - Case status updates automatically
  - @ClientComm sends progress updates automatically
  - @MedicalRecords requests and organizes records automatically
```

#### Agent Definitions

| Agent | Responsibility | Key Skills |
|-------|------|------------|
| **@Intake** | Case intake | questionnaire, conflict-check, case-evaluation |
| **@ClientComm** | Client communication | status-update, appointment, question-answer |
| **@MedicalRecords** | Medical records | records-request, treatment-summary, timeline |
| **@Settlement** | Settlement negotiation | demand-letter, offer-analysis, lien-calculation |

#### Thread Types

| Thread Type | Purpose | Lifecycle |
|-------------|------|----------|
| **Case Thread** | Main case | From signing to closure |
| **Negotiation** | Settlement negotiation | From demand to agreement |
| **Client Update** | Client communication | Ongoing |
| **Medical Records** | Records collection | Until collection complete |

---

### 4.3 Construction

#### Value Proposition

```
Before Vibe AI:
  - RFI emails scattered everywhere, hard to find
  - Daily reports handwritten, often incomplete
  - Subcontractor coordination relies on phone calls
  - Drawing update notifications unreliable

After Vibe AI:
  - @RFI provides unified management with automatic tracking
  - Bot in the job site trailer records automatically
  - @SubCoordinator coordinates subcontractors
  - @DocSearch finds any document instantly
```

#### Agent Definitions

| Agent | Responsibility | Key Skills |
|-------|------|------------|
| **@RFI** | RFI management | submission, tracking, routing |
| **@DailyLog** | Daily reports | weather, labor, equipment, activities |
| **@SubCoordinator** | Subcontractor coordination | scheduling, communication, compliance |
| **@DocSearch** | Document search | drawing-lookup, spec-search, submittal-find |
| **@Safety** | Safety management | incident-report, inspection, training |

#### Hardware Scenarios

| Device | Location | Purpose |
|------|------|------|
| **Bot** | Job site Trailer | Meeting recording, daily reports |
| **Dot** | Carried by foreman | Field notes |
| **Board** | Project office | Drawing discussions, progress meetings |

#### Integrations

| System | Integration Method | Data Flow |
|------|----------|--------|
| **Procore** | API | RFI, daily reports, documents |
| **PlanGrid** | API | Drawing management |
| **Bluebeam** | File sync | Markup sync |

---

## 5. Template Development

### 5.1 Creating a New Template

```bash
# Using Nx generators
nx g @vibe/vertical --name=dental-clinic --base=medical-clinic

# Generated structure
verticals/dental-clinic/
├── agents/
│   ├── scheduler.md      # Inherited from medical-clinic
│   └── treatment-plan.md # New addition
├── skills/
│   ├── dental-imaging/   # New addition
│   └── treatment-codes/  # New addition
├── thread-types/
│   └── treatment-plan.yaml
├── roles/
│   ├── dentist.yaml
│   └── hygienist.yaml
└── config.yaml
```

### 5.2 Inheritance and Overrides

```yaml
# verticals/dental-clinic/config.yaml

vertical:
  name: "dental-clinic"
  displayName: "Dental Clinic"
  extends: "medical-clinic"  # Inherits from medical template
  version: "1.0"

agents:
  # Inherit agents from medical-clinic
  inherit:
    - "@Scheduler"
    - "@Insurance"

  # Remove unneeded agents
  remove:
    - "@FollowUp"  # Not needed for dental

  # Add new agents
  add:
    - "@TreatmentPlan"

  # Override configuration
  config:
    "@Scheduler":
      defaults:
        appointment_duration: 60  # Dental appointments are longer

thread_types:
  inherit: true
  add:
    - "treatment-plan"

roles:
  # Map to dental roles
  map:
    physician: "dentist"
    nurse: "hygienist"

  add:
    - "dental-assistant"
```

### 5.3 Template Publishing

```bash
# Validate template
nx run dental-clinic:validate

# Build template package
nx run dental-clinic:build

# Publish to registry
nx run dental-clinic:publish

# After publishing, other workspaces can use it
> workspace create --template dental-clinic --name "Smile Dental"
```

---

## 6. Template Marketplace

### 6.1 Template Registry

```typescript
interface TemplateRegistry {
  // List available templates
  listTemplates(filters?: TemplateFilters): Promise<TemplateSummary[]>;

  // Get template details
  getTemplate(id: string, version?: string): Promise<TemplateManifest>;

  // Install template
  installTemplate(id: string, version: string): Promise<void>;

  // Publish template (partners)
  publishTemplate(manifest: TemplateManifest, files: TemplateFiles): Promise<void>;
}

interface TemplateSummary {
  id: string;
  name: string;
  description: string;
  industry: string;
  author: string;
  version: string;
  downloads: number;
  rating: number;
  certified: boolean;  // Vibe certified
}
```

### 6.2 Business Model

| Template Type | Pricing | Example |
|--------------|------|------|
| **Free** | Free | enterprise-general |
| **Certified** | Included in subscription | medical-clinic, pi-lawyer |
| **Partner** | Revenue share | dental-clinic (partner-developed) |
| **Custom** | Custom development fee | specific-hospital (custom-built) |

---

*Last updated: 2026-02-07*
