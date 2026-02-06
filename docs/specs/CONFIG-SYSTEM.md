# Configuration System Specification

> 4-Layer Configuration System + Admin Console

---

## Overview

The Vibe AI Workspace configuration system uses a 4-layer inheritance architecture, supporting progressive customization from Platform to User while ensuring that security and compliance constraints cannot be bypassed.

---

## 1. Configuration Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Platform Defaults                                   │
│ Defined by us, inherited by everyone                         │
│ Not modifiable                                               │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Industry Template                                   │
│ Industry template, e.g. medical-clinic                       │
│ Defined by template developers                               │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Workspace Config                                    │
│ Admin configuration, e.g. Downtown Clinic                    │
│ Admin configures within template-allowed boundaries          │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: User Preferences                                    │
│ Personal preferences                                         │
│ Configurable within Admin-allowed boundaries                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Why 4 Layers

| Layer | Responsibility | Typical Configurator | Example |
|------|------|-----------|------|
| **Platform** | Global security/performance constraints | Vibe engineers | Max token count, timeout limits |
| **Template** | Industry best practices | Industry experts/partners | HIPAA compliance requirements, locked workflows |
| **Workspace** | Organization customization | IT Admin | Enabled Agents, working hours |
| **User** | Personal preferences | End user | Theme, notification settings |

### 1.2 Layer Constraints

```
Platform ──┬── Defines immutable hard limits
           │
           ▼
Template ──┬── Can tighten Platform limits
           │   Cannot relax Platform limits
           │   Can lock configuration items
           │
           ▼
Workspace ─┬── Can tighten Template limits
           │   Cannot relax Template limits
           │   Can define User-selectable options
           │
           ▼
User ──────┴── Can only choose within Workspace-allowed range
```

---

## 2. Configuration Schema

### 2.1 Configuration Item Definition

```typescript
interface ConfigItem<T> {
  // Value
  value: T;

  // Who set it
  source: "platform" | "template" | "workspace" | "user";

  // Who can edit it
  editable_by: ("platform" | "template" | "admin" | "user")[];

  // Whether locked (lower layers cannot modify)
  locked: boolean;

  // User override policy
  user_override: "allowed" | "forbidden" | "within_options";

  // If within_options, available choices
  options?: T[];

  // Validation rules
  validation?: ConfigValidation;

  // Metadata
  description?: string;
  category?: string;
  sensitive?: boolean;
}

interface ConfigValidation {
  type: "string" | "number" | "boolean" | "array" | "object";
  min?: number;
  max?: number;
  pattern?: string;
  enum?: any[];
  custom?: (value: any) => boolean;
}
```

### 2.2 Complete Configuration Structure

```typescript
interface WorkspaceConfig {
  // === Basic Information ===
  workspace: {
    id: string;
    name: string;
    template: string;
    timezone: string;
    locale: string;
  };

  // === Agent Configuration ===
  agents: {
    // Available Agents (defined by Template)
    available: string[];

    // Enabled Agents (selected by Admin)
    enabled: string[];

    // Per-Agent configuration
    config: Record<string, AgentConfig>;

    // Global Agent settings
    global: {
      maxConcurrent: number;
      timeoutSec: number;
      defaultModel: string;
    };
  };

  // === Memory Configuration ===
  memory: {
    retentionDays: number;
    maxSizeGb: number;
    encryptionEnabled: boolean;

    // Zoom levels
    zoomLevels: {
      default: number;
      byRole: Record<string, number>;
    };
  };

  // === Thread Configuration ===
  threads: {
    maxBranches: number;
    autoArchiveDays: number;

    // Thread types (defined by Template)
    types: ThreadType[];
  };

  // === Permission Configuration ===
  permissions: {
    // Role definitions
    roles: Record<string, RoleConfig>;

    // Default role
    defaultRole: string;

    // Invite policy
    invitePolicy: "admin_only" | "members" | "open";
  };

  // === Device Configuration ===
  devices: {
    autoRegister: boolean;
    requireApproval: boolean;

    // Device default configuration
    defaults: Record<DeviceType, DeviceConfig>;
  };

  // === Integration Configuration ===
  integrations: {
    enabled: string[];
    config: Record<string, IntegrationConfig>;
  };

  // === Workflow Configuration ===
  workflows: {
    // Workflows defined by Template
    available: WorkflowDefinition[];

    // Locked workflows (not modifiable)
    locked: string[];

    // Admin custom workflows
    custom: WorkflowDefinition[];
  };

  // === Compliance Configuration ===
  compliance: {
    hipaa?: boolean;
    gdpr?: boolean;
    soc2?: boolean;
    auditLog: boolean;
    dataResidency?: string;
  };

  // === UI Configuration ===
  ui: {
    theme: "light" | "dark" | "system";
    branding?: {
      logo?: string;
      primaryColor?: string;
    };

    // User-customizable items
    userCustomizable: {
      theme: boolean;
      language: boolean;
      notifications: boolean;
    };
  };
}
```

---

## 3. Configuration File Format

### 3.1 Layer 1: Platform Defaults

```yaml
# config/platform/defaults.yaml
# Defined by Vibe, not modifiable

platform:
  version: "1.0"

agents:
  global:
    maxConcurrent:
      value: 10
      locked: true
      description: "Maximum concurrent agent tasks"
    timeoutSec:
      value: 300
      max: 600
      description: "Agent task timeout"

memory:
  retentionDays:
    value: 365
    min: 30
    max: 3650
    description: "Memory retention period"
  maxSizeGb:
    value: 100
    max: 1000
    description: "Maximum memory size per workspace"

security:
  mfaRequired:
    value: false
    editable_by: ["template", "admin"]
  sessionTimeoutMin:
    value: 60
    min: 15
    max: 480
  apiRateLimit:
    value: 1000
    locked: true
    description: "API calls per minute"
```

### 3.2 Layer 2: Industry Template

```yaml
# verticals/medical-clinic/config.yaml
# Medical clinic industry template

vertical:
  name: "medical-clinic"
  displayName: "Medical Clinic"
  extends: "_base"
  version: "1.0"

agents:
  available:
    - "@Scheduler"
    - "@FollowUp"
    - "@Insurance"
    - "@Concierge"

  default_enabled:
    - "@Scheduler"
    - "@Concierge"

  config:
    "@Scheduler":
      editable_by: ["admin"]
      user_override: "forbidden"
      defaults:
        working_hours: "08:00-17:00"
        appointment_duration: 30
        buffer_time: 10

    "@Insurance":
      editable_by: ["admin"]
      user_override: "forbidden"

threads:
  types:
    - id: "patient-encounter"
      name: "Patient Encounter"
      locked: true

    - id: "insurance-auth"
      name: "Insurance Authorization"
      locked: true

workflows:
  locked:
    - "patient-check-in"
    - "prescription-refill"

  definitions:
    - id: "patient-check-in"
      name: "Patient Check-in"
      locked: true
      steps:
        - type: "verify_identity"
        - type: "update_info"
        - type: "collect_copay"
        - type: "notify_provider"

compliance:
  hipaa:
    value: true
    locked: true
    description: "HIPAA compliance is mandatory for medical clinics"

  auditLog:
    value: true
    locked: true

  dataResidency:
    value: "us"
    options: ["us"]
    locked: true

roles:
  definitions:
    physician:
      displayName: "Physician"
      zoomLevel: 3
      agents: ["@Scheduler", "@FollowUp", "@Insurance"]
      permissions:
        - "memory:read:all"
        - "memory:write"
        - "thread:create"
        - "thread:branch"

    front_desk:
      displayName: "Front Desk"
      zoomLevel: 2
      agents: ["@Scheduler", "@Concierge"]
      permissions:
        - "memory:read:limited"
        - "thread:create"

    billing:
      displayName: "Billing Staff"
      zoomLevel: 2
      agents: ["@Insurance"]
      permissions:
        - "memory:read:billing"

ui:
  userCustomizable:
    theme: true
    language: true
    notifications: true
    agents: false  # Users cannot select agents
```

### 3.3 Layer 3: Workspace Config

```yaml
# workspaces/downtown-clinic/config.yaml
# Admin configuration

workspace:
  id: "clinic-downtown"
  name: "Downtown Medical Clinic"
  template: "medical-clinic"
  timezone: "America/Denver"
  locale: "en-US"

agents:
  enabled:
    - "@Scheduler"
    - "@Concierge"
    - "@Insurance"  # Additionally enabled by Admin

  config:
    "@Scheduler":
      working_hours: "07:30-18:00"  # Override default
      appointment_duration: 20

    "@Concierge":
      greeting: "Welcome to Downtown Medical Clinic"
      languages: ["en", "es"]

memory:
  retentionDays: 730  # 2 years
  zoomLevels:
    byRole:
      physician: 3
      front_desk: 2
      billing: 2

devices:
  autoRegister: false
  requireApproval: true

  defaults:
    vibe-bot:
      transcription:
        language: ["en-US", "es-ES"]
        hipaaMode: true

integrations:
  enabled:
    - "epic-ehr"
    - "stripe"

  config:
    epic-ehr:
      endpoint: "https://epic.downtownclinic.com"
      apiKey: "${EPIC_API_KEY}"

roles:
  custom:
    nurse:
      extends: "front_desk"
      displayName: "Nurse"
      zoomLevel: 3
      agents: ["@Scheduler", "@FollowUp", "@Concierge"]

permissions:
  invitePolicy: "admin_only"

ui:
  branding:
    logo: "/assets/downtown-clinic-logo.png"
    primaryColor: "#2563eb"

  userCustomizable:
    theme: true
    language: true
    notifications: true
```

### 3.4 Layer 4: User Preferences

```yaml
# users/dr-smith/preferences.yaml

user:
  id: "dr-smith"
  role: "physician"

preferences:
  ui:
    theme: "dark"
    language: "en-US"

  notifications:
    email: true
    push: true
    digest: "daily"

  agents:
    pinned: ["@Scheduler", "@FollowUp"]

  workspace:
    defaultSpace: "exam-room-1"
    defaultThreadType: "patient-encounter"
```

---

## 4. Configuration Merge Logic

### 4.1 Merge Algorithm

```typescript
function mergeConfigs(
  platform: Config,
  template: Config,
  workspace: Config,
  user: Config
): ResolvedConfig {
  const result: ResolvedConfig = {};

  for (const key of Object.keys(platform)) {
    const platformItem = platform[key];
    const templateItem = template[key];
    const workspaceItem = workspace[key];
    const userItem = user[key];

    // 1. Check locks
    if (platformItem.locked) {
      result[key] = platformItem.value;
      continue;
    }

    if (templateItem?.locked) {
      result[key] = templateItem.value;
      continue;
    }

    if (workspaceItem?.locked) {
      result[key] = workspaceItem.value;
      continue;
    }

    // 2. Check user override policy
    if (userItem !== undefined) {
      const override = workspaceItem?.user_override ?? templateItem?.user_override ?? "allowed";

      if (override === "forbidden") {
        result[key] = workspaceItem?.value ?? templateItem?.value ?? platformItem.value;
      } else if (override === "within_options") {
        const options = workspaceItem?.options ?? templateItem?.options ?? [];
        if (options.includes(userItem)) {
          result[key] = userItem;
        } else {
          result[key] = workspaceItem?.value ?? templateItem?.value ?? platformItem.value;
        }
      } else {
        result[key] = userItem;
      }
      continue;
    }

    // 3. Walk up layers to find value
    result[key] = workspaceItem?.value ?? templateItem?.value ?? platformItem.value;
  }

  return result;
}
```

### 4.2 Validation Logic

```typescript
function validateConfig(config: Config, layer: ConfigLayer): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  for (const [key, item] of Object.entries(config)) {
    const schema = getConfigSchema(key);

    // 1. Check type
    if (!matchesType(item.value, schema.type)) {
      errors.push({
        key,
        message: `Expected ${schema.type}, got ${typeof item.value}`
      });
    }

    // 2. Check range
    if (schema.min !== undefined && item.value < schema.min) {
      errors.push({
        key,
        message: `Value ${item.value} is below minimum ${schema.min}`
      });
    }

    // 3. Check lock constraints
    const parentLocked = isLockedByParent(key, layer);
    if (parentLocked && item.value !== getParentValue(key, layer)) {
      errors.push({
        key,
        message: `Cannot override locked value from ${parentLocked}`
      });
    }

    // 4. Check permissions
    if (!item.editable_by?.includes(layer)) {
      errors.push({
        key,
        message: `Layer ${layer} cannot edit this config`
      });
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}
```

---

## 5. Admin Console

### 5.1 Overview

The Admin Console is a command-line interface for Workspace administrators to configure the system, similar to how Claude Code interacts.

### 5.2 Command Structure

```
┌──────────────────────────────────────────────────────────┐
│                    Admin Console                          │
│                                                           │
│  > workspace show                                        │
│  > agent enable @Insurance                               │
│  > role create nurse --base front_desk                   │
│  > config set agents.@Scheduler.working_hours "08:00-18:00"│
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 5.3 Command Categories

#### Workspace Management

```bash
# View workspace information
> workspace show
> workspace status

# Switch workspace (multi-workspace admin)
> workspace list
> workspace switch clinic-123

# Export/import configuration
> workspace export --format yaml > config.yaml
> workspace import config.yaml --dry-run
> workspace import config.yaml --apply
```

#### Agent Management

```bash
# List agents
> agent list
> agent list --available
> agent list --enabled

# Enable/disable agent
> agent enable @Insurance
> agent disable @Concierge

# Configure agent
> agent config @Scheduler
> agent config @Scheduler --set working_hours="08:00-18:00"
> agent config @Scheduler --set appointment_duration=20
> agent config @Scheduler --reset working_hours

# Test agent
> agent test @Scheduler "Schedule an appointment for tomorrow"
```

#### Role Management

```bash
# List roles
> role list
> role show physician

# Create role
> role create nurse --base front_desk
> role create nurse --interactive

# Modify role
> role grant nurse --agent @FollowUp
> role revoke nurse --agent @Insurance
> role set nurse --zoom-level 3
> role set nurse --permission memory:read:all

# Delete role
> role delete nurse
```

#### User Management

```bash
# List users
> user list
> user list --role physician

# Invite user
> user invite jane@clinic.com --role nurse
> user invite --batch users.csv

# Modify user
> user set jane@clinic.com --role physician
> user set jane@clinic.com --zoom-level 3

# Disable/enable user
> user disable jane@clinic.com
> user enable jane@clinic.com

# Remove user
> user remove jane@clinic.com
```

#### Device Management

```bash
# List devices
> device list
> device list --type vibe-bot --status online

# Device details
> device show bot-001
> device status bot-001

# Assign device
> device assign bot-001 --to space:waiting-room
> device assign dot-001 --to user:dr-smith
> device unassign bot-001

# Configure device
> device config bot-001 --set transcription.language=en-US

# Device commands
> device command bot-001 restart
> device command bot-001 start_capture --mode meeting
```

#### Configuration Management

```bash
# View configuration
> config show
> config show agents
> config show agents.@Scheduler

# Modify configuration
> config set agents.@Scheduler.working_hours "08:00-18:00"
> config set memory.retentionDays 730

# Reset configuration
> config reset agents.@Scheduler.working_hours

# Validate configuration
> config validate
> config validate --strict

# Configuration history
> config history
> config history --key agents.@Scheduler
> config rollback --to 2026-02-01
```

#### Memory Management

```bash
# Statistics
> memory stats
> memory stats --by-space

# Search
> memory search "patient complaint"
> memory search "patient complaint" --space complaints --limit 10

# Export
> memory export --from 2026-01-01 --to 2026-02-01 --format json

# Cleanup
> memory cleanup --older-than 365d --dry-run
> memory cleanup --older-than 365d --apply
```

#### Audit

```bash
# View audit logs
> audit log
> audit log --user jane@clinic.com
> audit log --action config.change
> audit log --last 7d

# Export audit logs
> audit export --from 2026-01-01 --format csv
```

#### Integration Management

```bash
# List integrations
> integration list
> integration list --enabled

# Enable/disable integration
> integration enable epic-ehr
> integration disable stripe

# Configure integration
> integration config epic-ehr --set endpoint="https://epic.clinic.com"

# Test integration
> integration test epic-ehr
> integration test epic-ehr --verbose
```

### 5.4 Console Implementation

```typescript
// services/config/admin/console.ts

interface Command {
  name: string;
  description: string;
  args: ArgDefinition[];
  options: OptionDefinition[];
  handler: (args: Args, options: Options) => Promise<CommandResult>;
}

const commands: Record<string, Command> = {
  "workspace.show": {
    name: "workspace show",
    description: "Display workspace information",
    args: [],
    options: [],
    handler: async () => {
      const config = await getWorkspaceConfig();
      return { output: formatWorkspaceInfo(config) };
    }
  },

  "agent.enable": {
    name: "agent enable",
    description: "Enable an agent",
    args: [{ name: "agentId", required: true }],
    options: [],
    handler: async ({ agentId }) => {
      // 1. Check if agent is available
      const available = await getAvailableAgents();
      if (!available.includes(agentId)) {
        throw new Error(`Agent ${agentId} is not available in this template`);
      }

      // 2. Enable it
      await updateConfig({
        path: "agents.enabled",
        operation: "append",
        value: agentId
      });

      return { output: `Agent ${agentId} enabled` };
    }
  },

  "config.set": {
    name: "config set",
    description: "Set a configuration value",
    args: [
      { name: "path", required: true },
      { name: "value", required: true }
    ],
    options: [],
    handler: async ({ path, value }) => {
      // 1. Validate path
      const schema = getConfigSchema(path);
      if (!schema) {
        throw new Error(`Unknown config path: ${path}`);
      }

      // 2. Validate value
      const parsed = parseValue(value, schema.type);
      const validation = validateValue(parsed, schema);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // 3. Check lock
      if (isLocked(path)) {
        throw new Error(`Config ${path} is locked by template`);
      }

      // 4. Update
      await updateConfig({ path, operation: "set", value: parsed });

      // 5. Record audit log
      await auditLog({
        action: "config.change",
        path,
        oldValue: getOldValue(path),
        newValue: parsed
      });

      return { output: `Set ${path} = ${value}` };
    }
  }
};

// Console main loop
async function runConsole() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: "> "
  });

  rl.prompt();

  for await (const line of rl) {
    try {
      const { command, args, options } = parseCommand(line);
      const result = await executeCommand(command, args, options);
      console.log(result.output);
    } catch (error) {
      console.error(`Error: ${error.message}`);
    }
    rl.prompt();
  }
}
```

---

## 6. API

### 6.1 Configuration API

```typescript
// Get merged configuration
GET /api/config
Authorization: Bearer <token>

Response:
{
  workspace: { ... },
  agents: { ... },
  memory: { ... },
  // ... complete configuration
}

// Get specific path
GET /api/config/agents.@Scheduler

// Update configuration (Admin)
PATCH /api/config
{
  "path": "agents.@Scheduler.working_hours",
  "value": "08:00-18:00"
}

// Batch update
POST /api/config/batch
{
  "updates": [
    { "path": "agents.enabled", "operation": "append", "value": "@Insurance" },
    { "path": "memory.retentionDays", "value": 730 }
  ]
}

// Validate configuration
POST /api/config/validate
{
  "config": { ... }
}

Response:
{
  "valid": true,
  "errors": [],
  "warnings": []
}

// Export configuration
GET /api/config/export?format=yaml

// Import configuration
POST /api/config/import
Content-Type: multipart/form-data

{
  "file": <yaml-file>,
  "dryRun": true
}
```

### 6.2 Configuration History API

```typescript
// Get configuration history
GET /api/config/history
  ?path=agents.@Scheduler
  &from=2026-01-01
  &to=2026-02-07

Response:
{
  "changes": [
    {
      "id": "ch-123",
      "path": "agents.@Scheduler.working_hours",
      "oldValue": "08:00-17:00",
      "newValue": "08:00-18:00",
      "changedBy": "admin@clinic.com",
      "changedAt": "2026-02-05T10:00:00Z"
    }
  ]
}

// Rollback configuration
POST /api/config/rollback
{
  "changeId": "ch-123"
}
```

---

## 7. Security Considerations

### 7.1 Sensitive Configuration

```yaml
# Sensitive configuration is not stored in plaintext
integrations:
  config:
    epic-ehr:
      apiKey: "${EPIC_API_KEY}"  # Environment variable reference

# Or using a secrets service
integrations:
  config:
    epic-ehr:
      apiKey:
        _secret: "epic-api-key"  # Retrieved from secrets service
```

### 7.2 Configuration Permissions

```typescript
const CONFIG_PERMISSIONS = {
  "config:read": ["admin", "manager"],
  "config:write": ["admin"],
  "config:export": ["admin"],
  "config:import": ["admin"],
  "config:rollback": ["admin"]
};
```

### 7.3 Audit Log

```typescript
interface ConfigAuditLog {
  id: string;
  workspaceId: string;

  action: "read" | "write" | "export" | "import" | "rollback";
  path: string;

  oldValue?: any;
  newValue?: any;

  userId: string;
  userEmail: string;
  userRole: string;

  ip: string;
  userAgent: string;

  timestamp: Date;
}
```

---

*Last updated: 2026-02-07*
