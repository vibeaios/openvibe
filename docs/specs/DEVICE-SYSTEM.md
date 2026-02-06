# Device System Specification

> Device as First-Class Entity

---

## Overview

Vibe's hardware devices (Bot, Dot, Board) are not just data sources -- they are first-class entities in the system with their own identity, capabilities, and state.

---

## 1. Why Device as Entity

### 1.1 Problems with the Traditional Approach

```
Traditional:
  Device -> Recording -> Data enters system -> Device disappears

Problems:
  - Cannot trace data origin
  - Cannot manage device state
  - Cannot assign permissions per device
  - Cannot support multi-device collaboration
```

### 1.2 Our Approach

```
Vibe AI:
  Device = A participant with identity
         = Can be assigned to a Space/User/Location
         = Has capability declarations and status reporting
         = Data produced is associated with the device
         = Can receive commands
```

### 1.3 Business Value

| Scenario | Traditional | Device as Entity |
|------|------|------------------|
| Device management | Manual tracking | Centralized management panel |
| Data attribution | Unclear | Clear provenance |
| Permission control | Per user | Per device + user |
| Troubleshooting | Difficult | Status monitoring |
| Billing | Per user | Can be per device |

---

## 2. Data Model

### 2.1 Device Entity

```typescript
interface Device {
  // Unique identifier
  id: string;                      // "device-bot-001"
  type: DeviceType;

  // Identity information
  name: string;                    // "Conference Room A Bot"
  serial?: string;                 // Hardware serial number
  firmwareVersion?: string;        // Firmware version

  // Ownership
  workspaceId: string;
  assignedTo?: DeviceAssignment;

  // Capabilities
  capabilities: DeviceCapability[];

  // Status
  status: DeviceStatus;

  // Location
  location?: DeviceLocation;

  // Network
  network?: DeviceNetwork;

  // Configuration
  config?: DeviceConfig;

  // Metadata
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
  lastActiveAt: Date;
}
```

### 2.2 Device Types

```typescript
type DeviceType =
  | "vibe-bot"      // Vibe Bot meeting device
  | "vibe-dot"      // Vibe Dot note-taking device
  | "vibe-board"    // Vibe Board whiteboard
  | "external";     // Third-party device

interface DeviceTypeInfo {
  type: DeviceType;
  displayName: string;
  icon: string;
  defaultCapabilities: DeviceCapability[];
  configSchema: JSONSchema;
}

const DEVICE_TYPES: Record<DeviceType, DeviceTypeInfo> = {
  "vibe-bot": {
    displayName: "Vibe Bot",
    icon: "bot",
    defaultCapabilities: [
      "audio_capture",
      "video_capture",
      "transcription",
      "speaker_id",
      "meeting_summary"
    ],
    configSchema: { /* ... */ }
  },
  "vibe-dot": {
    displayName: "Vibe Dot",
    icon: "dot",
    defaultCapabilities: [
      "audio_capture",
      "transcription",
      "meeting_summary"
    ],
    configSchema: { /* ... */ }
  },
  // ...
};
```

### 2.3 Device Capabilities

```typescript
type DeviceCapability =
  // Capture capabilities
  | "audio_capture"        // Audio recording
  | "video_capture"        // Video recording
  | "screen_share"         // Screen sharing
  | "whiteboard"           // Whiteboard capture

  // Processing capabilities
  | "transcription"        // Transcription
  | "speaker_id"           // Speaker identification
  | "realtime_translate"   // Real-time translation
  | "meeting_summary"      // Meeting summarization

  // Interaction capabilities
  | "display"              // Display screen
  | "touch"                // Touch input
  | "voice_command"        // Voice commands

  // Scenario-specific capabilities
  | "check_in"             // Check-in (medical)
  | "safety_alert"         // Safety alerts (construction)
  | "attendance";          // Attendance tracking

interface CapabilityDefinition {
  id: DeviceCapability;
  name: string;
  description: string;
  requiredConfig?: string[];
  dataTypes: string[];      // Types of data produced
}
```

### 2.4 Device Status

```typescript
interface DeviceStatus {
  // Connection status
  online: boolean;
  lastSeen: Date;
  connectionType?: "wifi" | "ethernet" | "cellular";

  // Health status
  health: "healthy" | "degraded" | "offline" | "error";
  healthDetails?: {
    issue?: string;
    since?: Date;
    severity?: "low" | "medium" | "high";
  };

  // Activity status
  activity: "idle" | "capturing" | "processing" | "syncing";
  currentSession?: {
    id: string;
    startedAt: Date;
    type: string;
  };

  // Resource metrics
  metrics?: {
    cpu?: number;           // 0-100
    memory?: number;        // 0-100
    storage?: number;       // 0-100
    temperature?: number;   // Celsius
    battery?: number;       // 0-100 (if applicable)
  };

  // Sync status
  sync?: {
    lastSyncAt: Date;
    pendingItems: number;
    syncStatus: "synced" | "syncing" | "pending" | "error";
  };
}
```

### 2.5 Device Assignment

```typescript
interface DeviceAssignment {
  type: "space" | "user" | "location" | "pool";
  id: string;

  // Assignment configuration
  exclusive?: boolean;      // Whether exclusive
  schedulable?: boolean;    // Whether schedulable
  priority?: number;        // Scheduling priority

  // Time range
  validFrom?: Date;
  validUntil?: Date;

  // Assigned by
  assignedBy: string;
  assignedAt: Date;
}

// Examples
const assignments: DeviceAssignment[] = [
  // Bot assigned to a conference room
  {
    type: "location",
    id: "room-a",
    exclusive: true,
    schedulable: true
  },
  // Dot assigned to an individual
  {
    type: "user",
    id: "dr-smith",
    exclusive: true
  },
  // Bot placed in a shared pool
  {
    type: "pool",
    id: "shared-bots",
    exclusive: false,
    schedulable: true,
    priority: 1
  }
];
```

### 2.6 Device Location

```typescript
interface DeviceLocation {
  // Hierarchical location
  building?: string;
  floor?: string;
  room?: string;
  desk?: string;

  // Exact coordinates (optional)
  coordinates?: {
    lat: number;
    lng: number;
  };

  // Indoor positioning (optional)
  indoor?: {
    x: number;
    y: number;
    mapId: string;
  };

  // Location tags
  tags?: string[];      // ["lobby", "customer-facing"]

  // Location description
  description?: string; // "Front desk, left side"
}
```

---

## 3. API Design

### 3.1 Device Registration

```typescript
// Device self-registration (called from device side)
POST /api/devices/register
{
  type: "vibe-bot",
  serial: "VB-2026-001234",
  firmwareVersion: "2.1.0",
  capabilities: ["audio_capture", "transcription"],
  network: {
    mac: "AA:BB:CC:DD:EE:FF",
    ip: "192.168.1.100"
  }
}

Response:
{
  id: "device-bot-001",
  token: "eyJhbGciOiJIUzI1NiIs...",  // Device token
  config: { ... }
}

// Admin adds device
POST /api/devices
{
  type: "vibe-bot",
  name: "Conference Room A Bot",
  serial: "VB-2026-001234",
  location: {
    building: "HQ",
    floor: "2F",
    room: "Conference Room A"
  },
  assignedTo: {
    type: "space",
    id: "space-meetings"
  }
}
```

### 3.2 Device Queries

```typescript
// List devices
GET /api/devices
  ?type=vibe-bot
  &status=online
  &assignedTo=space:meetings
  &location.building=HQ

Response:
{
  devices: Device[],
  total: number,
  page: number
}

// Get single device
GET /api/devices/:deviceId

// Get device status
GET /api/devices/:deviceId/status

// Get device history
GET /api/devices/:deviceId/history
  ?from=2026-02-01
  &to=2026-02-07
```

### 3.3 Device Management

```typescript
// Update device
PATCH /api/devices/:deviceId
{
  name: "Conference Room B Bot",
  location: { room: "Conference Room B" }
}

// Assign device
POST /api/devices/:deviceId/assign
{
  type: "user",
  id: "dr-smith",
  exclusive: true
}

// Unassign device
DELETE /api/devices/:deviceId/assign

// Send command
POST /api/devices/:deviceId/command
{
  command: "start_capture",
  params: {
    mode: "meeting",
    duration: 3600
  }
}

// Update configuration
PUT /api/devices/:deviceId/config
{
  transcription: {
    language: "en-US",
    speakerId: true
  }
}
```

### 3.4 Device Status Reporting (Device Side)

```typescript
// Heartbeat
POST /api/devices/:deviceId/heartbeat
Authorization: Bearer <device-token>
{
  status: {
    online: true,
    health: "healthy",
    activity: "idle",
    metrics: {
      cpu: 15,
      memory: 42,
      temperature: 38
    }
  }
}

// Event reporting
POST /api/devices/:deviceId/events
{
  events: [
    {
      type: "session_started",
      timestamp: "2026-02-07T10:00:00Z",
      data: { sessionId: "sess-123" }
    },
    {
      type: "capture_completed",
      timestamp: "2026-02-07T11:30:00Z",
      data: {
        sessionId: "sess-123",
        duration: 5400,
        size: 102400000
      }
    }
  ]
}
```

### 3.5 Data Upload (Device Side)

```typescript
// Upload captured data
POST /api/devices/:deviceId/upload
Content-Type: multipart/form-data

{
  sessionId: "sess-123",
  type: "audio",
  file: <binary>,
  metadata: {
    startTime: "2026-02-07T10:00:00Z",
    endTime: "2026-02-07T11:30:00Z",
    participants: ["user-1", "user-2"]
  }
}

// Streaming upload (real-time)
WebSocket /api/devices/:deviceId/stream
{
  type: "audio_chunk",
  data: <base64>,
  timestamp: 1234567890
}
```

---

## 4. Database Schema

```sql
-- Devices table
CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id),

  -- Type and identity
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  serial TEXT UNIQUE,
  firmware_version TEXT,

  -- Capabilities
  capabilities TEXT[] DEFAULT '{}',

  -- Status (JSON for extensibility)
  status JSONB DEFAULT '{}',

  -- Location
  location JSONB,

  -- Network
  network JSONB,

  -- Configuration
  config JSONB DEFAULT '{}',

  -- Metadata
  metadata JSONB DEFAULT '{}',

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_active_at TIMESTAMPTZ,

  -- Indexes
  CONSTRAINT devices_workspace_name UNIQUE (workspace_id, name)
);

-- Indexes
CREATE INDEX idx_devices_workspace ON devices(workspace_id);
CREATE INDEX idx_devices_type ON devices(type);
CREATE INDEX idx_devices_serial ON devices(serial);
CREATE INDEX idx_devices_status ON devices USING GIN(status);
CREATE INDEX idx_devices_location ON devices USING GIN(location);

-- Device assignments table
CREATE TABLE device_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

  -- Assignment target
  target_type TEXT NOT NULL,  -- 'space' | 'user' | 'location' | 'pool'
  target_id TEXT NOT NULL,

  -- Assignment configuration
  exclusive BOOLEAN DEFAULT true,
  schedulable BOOLEAN DEFAULT false,
  priority INT DEFAULT 0,

  -- Time range
  valid_from TIMESTAMPTZ,
  valid_until TIMESTAMPTZ,

  -- Audit
  assigned_by UUID REFERENCES users(id),
  assigned_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure a device has only one active assignment at a time (if exclusive)
  CONSTRAINT device_assignments_exclusive
    EXCLUDE USING gist (
      device_id WITH =,
      tstzrange(valid_from, valid_until) WITH &&
    ) WHERE (exclusive = true)
);

-- Device event log
CREATE TABLE device_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

  event_type TEXT NOT NULL,
  event_data JSONB,

  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Time-series data with TimescaleDB (optional)
-- SELECT create_hypertable('device_events', 'timestamp');

CREATE INDEX idx_device_events_device ON device_events(device_id);
CREATE INDEX idx_device_events_type ON device_events(event_type);
CREATE INDEX idx_device_events_time ON device_events(timestamp DESC);

-- Device tokens
CREATE TABLE device_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

  token_hash TEXT NOT NULL,  -- bcrypt
  token_prefix TEXT NOT NULL, -- First few characters for identification

  permissions TEXT[] DEFAULT '{}',

  expires_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_device_tokens_device ON device_tokens(device_id);
CREATE INDEX idx_device_tokens_prefix ON device_tokens(token_prefix);
```

---

## 5. Industry Scenarios

### 5.1 Medical Clinic

```yaml
# Front Desk Bot
device:
  id: bot-frontdesk
  type: vibe-bot
  name: "Front Desk Bot"
  location:
    room: "Front Desk"
  assignedTo:
    type: space
    id: waiting-room
  capabilities:
    - audio_capture
    - transcription
    - check_in
  config:
    check_in:
      enabled: true
      workflow: patient-check-in
    transcription:
      language: ["en-US", "es-ES"]
      speakerId: true
      hipaaMode: true  # Sensitive information handling

# Doctor's Dot
device:
  id: dot-dr-smith
  type: vibe-dot
  name: "Dr. Smith's Dot"
  assignedTo:
    type: user
    id: dr-smith
  capabilities:
    - audio_capture
    - transcription
    - meeting_summary
  config:
    autoStart: true
    transcription:
      hipaaMode: true
```

### 5.2 Construction Site

```yaml
# Job Site Trailer Bot
device:
  id: bot-trailer
  type: vibe-bot
  name: "Site Trailer Bot"
  location:
    building: "Job Site 123"
    room: "Site Trailer"
  assignedTo:
    type: location
    id: job-site-123
  capabilities:
    - audio_capture
    - transcription
    - safety_alert
  config:
    safety:
      keywords: ["accident", "injury", "hazard"]
      alertTo: ["safety-channel"]
    environment:
      dustResistant: true
      temperatureRange: [-10, 45]
```

### 5.3 Law Firm

```yaml
# Conference Room Bot
device:
  id: bot-conf-1
  type: vibe-bot
  name: "Conference Room 1 Bot"
  location:
    room: "Conference Room 1"
  assignedTo:
    type: space
    id: client-meetings
  capabilities:
    - audio_capture
    - video_capture
    - transcription
    - meeting_summary
  config:
    transcription:
      legalMode: true  # Optimized for legal terminology
      confidentialityWarning: true
    recording:
      retention: 365  # days
      encrypted: true
```

---

## 6. Admin Console Commands

```bash
# List devices
> device list
> device list --type vibe-bot --status online

# Device details
> device show bot-001
> device status bot-001

# Add device
> device add --type vibe-bot --name "Conference Room A Bot" --serial VB-2026-001

# Assign device
> device assign bot-001 --to space:meetings
> device assign dot-001 --to user:dr-smith --exclusive

# Unassign device
> device unassign bot-001

# Device configuration
> device config bot-001 --set transcription.language=en-US
> device config bot-001 --get

# Device commands
> device command bot-001 start_capture --mode meeting
> device command bot-001 stop_capture

# Device history
> device history bot-001 --last 7d
> device events bot-001 --type session_started

# Batch operations
> device update-firmware --type vibe-bot --version 2.1.1
> device restart --location "HQ/2F/*"
```

---

## 7. UI Components

### 7.1 Device Panel

```tsx
// libs/ui/device/DevicePanel.tsx
interface DevicePanelProps {
  deviceId: string;
  showStatus?: boolean;
  showLocation?: boolean;
  showActions?: boolean;
}

function DevicePanel({ deviceId, ...props }: DevicePanelProps) {
  const device = useDevice(deviceId);

  return (
    <Card>
      <DeviceHeader device={device} />
      {props.showStatus && <DeviceStatus status={device.status} />}
      {props.showLocation && <DeviceLocation location={device.location} />}
      {props.showActions && <DeviceActions device={device} />}
    </Card>
  );
}
```

### 7.2 Device List

```tsx
// libs/ui/device/DeviceList.tsx
interface DeviceListProps {
  filters?: DeviceFilters;
  onSelect?: (device: Device) => void;
  layout?: "grid" | "list";
}

function DeviceList({ filters, onSelect, layout = "grid" }: DeviceListProps) {
  const { devices, loading } = useDevices(filters);

  return (
    <div className={layout === "grid" ? "grid grid-cols-3" : "space-y-2"}>
      {devices.map(device => (
        <DeviceCard
          key={device.id}
          device={device}
          onClick={() => onSelect?.(device)}
        />
      ))}
    </div>
  );
}
```

### 7.3 Device Status Badge

```tsx
// libs/ui/device/DeviceStatusBadge.tsx
function DeviceStatusBadge({ status }: { status: DeviceStatus }) {
  const colors = {
    healthy: "bg-green-500",
    degraded: "bg-yellow-500",
    offline: "bg-gray-500",
    error: "bg-red-500"
  };

  return (
    <span className={`px-2 py-1 rounded ${colors[status.health]}`}>
      {status.online ? "Online" : "Offline"}
      {status.activity !== "idle" && ` · ${status.activity}`}
    </span>
  );
}
```

---

## 8. Security Considerations

### 8.1 Device Authentication

```typescript
// Device token generation
async function generateDeviceToken(deviceId: string): Promise<string> {
  const token = `vibe_dev_${nanoid(32)}`;
  const hash = await bcrypt.hash(token, 10);

  await db.deviceTokens.create({
    deviceId,
    tokenHash: hash,
    tokenPrefix: token.slice(0, 12)
  });

  return token;
}

// Device authentication middleware
async function authenticateDevice(req: Request): Promise<Device> {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token?.startsWith("vibe_dev_")) {
    throw new UnauthorizedError("Invalid device token");
  }

  const prefix = token.slice(0, 12);
  const candidates = await db.deviceTokens.findByPrefix(prefix);

  for (const candidate of candidates) {
    if (await bcrypt.compare(token, candidate.tokenHash)) {
      return db.devices.findById(candidate.deviceId);
    }
  }

  throw new UnauthorizedError("Device token not found");
}
```

### 8.2 Data Encryption

```yaml
# Sensitive scenario configuration
device:
  config:
    encryption:
      atRest: true           # Encryption at rest
      inTransit: true        # Encryption in transit
      keyRotation: 30        # Key rotation (days)

    privacy:
      anonymizeAudio: false  # Whether to anonymize
      retentionDays: 90      # Retention period in days
      gdprCompliant: true    # GDPR compliant
```

### 8.3 Access Control

```typescript
// Device operation permissions
const DEVICE_PERMISSIONS = {
  "device:read": ["admin", "manager", "user"],
  "device:write": ["admin", "manager"],
  "device:command": ["admin", "manager"],
  "device:assign": ["admin"],
  "device:delete": ["admin"]
};

// Permission check
function canAccessDevice(user: User, device: Device, action: string): boolean {
  // 1. Check user role
  if (!DEVICE_PERMISSIONS[action].includes(user.role)) {
    return false;
  }

  // 2. Check Workspace ownership
  if (device.workspaceId !== user.workspaceId) {
    return false;
  }

  // 3. Check Space permissions (if device is assigned to a Space)
  if (device.assignedTo?.type === "space") {
    return user.spaces.includes(device.assignedTo.id);
  }

  // 4. Check personal assignment (if device is assigned to a user)
  if (device.assignedTo?.type === "user") {
    return device.assignedTo.id === user.id || user.role === "admin";
  }

  return true;
}
```

---

*Last updated: 2026-02-07*
