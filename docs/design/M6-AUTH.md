> **SUPERSEDED**: This document is from the initial design phase. For implementation, refer to:
> - [`BACKEND-MINIMUM-SCOPE.md`](../research/phase-1.5/BACKEND-MINIMUM-SCOPE.md) — Auth procedures
> - [`BDD-IMPLEMENTATION-PLAN.md`](../research/phase-1.5/BDD-IMPLEMENTATION-PLAN.md) — Auth specs

# M6: Auth & Permissions (Access Control)

> Status: Draft | Priority: Medium | Dependency: None

## Overview

Authentication (who are you) + Authorization (what can you do). Keep it simple for the MVP phase, extensible later.

## User Model

```typescript
interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: Role;
  teamId: string;
  createdAt: Date;
  lastActiveAt: Date;
}

type Role = 'owner' | 'admin' | 'member' | 'guest';

interface Team {
  id: string;
  name: string;
  slug: string;  // URL-friendly
  ownerId: string;
  plan: 'free' | 'pro' | 'enterprise';
  settings: TeamSettings;
  createdAt: Date;
}

interface TeamSettings {
  maxAgents: number;
  maxChannels: number;
  features: string[];
}
```

## Authentication

### MVP: Supabase Auth

Using Supabase built-in authentication, supporting:
- Email/Password
- Google OAuth
- GitHub OAuth (developer-friendly)

```typescript
// Login
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: `${window.location.origin}/auth/callback`
  }
});

// Check session
const { data: { session } } = await supabase.auth.getSession();

// Get user info
const { data: { user } } = await supabase.auth.getUser();
```

### Future: Enterprise SSO

- SAML 2.0
- OpenID Connect
- Add when needed

## Authorization Model

### Role Permission Matrix

| Operation | Owner | Admin | Member | Guest |
|-----------|-------|-------|--------|-------|
| Manage Team settings | Yes | Yes | No | No |
| Invite members | Yes | Yes | No | No |
| Manage Agents | Yes | Yes | No | No |
| Create Channel | Yes | Yes | Yes | No |
| Send messages | Yes | Yes | Yes | Yes |
| Create Branch | Yes | Yes | Yes | No |
| Merge Branch | Yes | Yes | Yes | No |
| Delete messages | Yes | Yes | Own only | No |
| Read Memory | Yes | Yes | Yes | Limited |
| Write Memory | Yes | Yes | Yes | No |
| View Agent logs | Yes | Yes | No | No |

### Channel-level Permissions

```typescript
interface ChannelPermission {
  channelId: string;
  userId: string;

  canRead: boolean;
  canWrite: boolean;
  canManage: boolean;  // edit/delete channel
}

// Private channel
interface PrivateChannel {
  id: string;
  name: string;
  isPrivate: true;
  allowedUserIds: string[];
}
```

## Implementation

### Middleware (API)

```typescript
// Next.js middleware
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs';

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const supabase = createMiddlewareClient({ req, res });

  const { data: { session } } = await supabase.auth.getSession();

  // Not logged in → redirect to login page
  if (!session && !isPublicRoute(req.nextUrl.pathname)) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  return res;
}
```

### API Permission Checks

```typescript
// Decorator style
async function createChannel(req: Request) {
  const user = await getUser(req);

  // Permission check
  if (!hasPermission(user, 'channel:create')) {
    throw new ForbiddenError('No permission to create channel');
  }

  // Execute operation
  // ...
}

// Permission check function
function hasPermission(user: User, action: string): boolean {
  const rolePermissions = {
    owner: ['*'],  // All permissions
    admin: ['channel:*', 'agent:*', 'member:invite', ...],
    member: ['channel:create', 'message:*', 'branch:*'],
    guest: ['message:read', 'message:send']
  };

  const permissions = rolePermissions[user.role];
  return matchesPermission(permissions, action);
}
```

### Row Level Security (Supabase)

```sql
-- Users can only read their own team's data
CREATE POLICY "Users can view own team data"
ON messages FOR SELECT
USING (
  team_id IN (
    SELECT team_id FROM users
    WHERE id = auth.uid()
  )
);

-- Users can only edit their own messages
CREATE POLICY "Users can edit own messages"
ON messages FOR UPDATE
USING (author_id = auth.uid());

-- Channel permissions
CREATE POLICY "Users can view permitted channels"
ON channels FOR SELECT
USING (
  NOT is_private
  OR id IN (
    SELECT channel_id FROM channel_permissions
    WHERE user_id = auth.uid()
  )
);
```

## Invitation System

### Invitation Flow

```
1. Admin creates invitation
   POST /api/invites
   { email: "new@user.com", role: "member" }

2. System sends email
   Contains invite link: /join?token=xxx

3. User clicks link
   a. Existing account → Directly joins team
   b. New user → Registers then joins team

4. Invitation expiry: 7 days
```

### Invite Code

```typescript
interface Invite {
  id: string;
  teamId: string;
  email?: string;      // Specific email or universal code
  role: Role;
  code: string;        // Unique invite code
  usedBy?: string;
  expiresAt: Date;
  createdBy: string;
}

// Generate invite code
function generateInviteCode(): string {
  return nanoid(12);  // e.g., "V1StGXR8_Z5j"
}
```

## API Key (Agent Authentication)

Agent containers need authentication to call APIs:

```typescript
interface ApiKey {
  id: string;
  teamId: string;
  name: string;
  keyHash: string;  // bcrypt hash
  prefix: string;   // First few characters for identification, e.g., "vibe_"
  permissions: string[];
  lastUsedAt?: Date;
  expiresAt?: Date;
  createdBy: string;
}

// Usage
// Header: Authorization: Bearer vibe_xxxxxxxxxxxxx

// Validation
async function validateApiKey(key: string): Promise<ApiKey | null> {
  const prefix = key.slice(0, 5);
  const candidates = await getKeysByPrefix(prefix);

  for (const candidate of candidates) {
    if (await bcrypt.compare(key, candidate.keyHash)) {
      await updateLastUsed(candidate.id);
      return candidate;
    }
  }

  return null;
}
```

## Database Schema

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT NOT NULL,
  name TEXT,
  avatar TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_active_at TIMESTAMPTZ
);

-- Teams
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  owner_id UUID REFERENCES users(id),
  plan TEXT DEFAULT 'free',
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team members
CREATE TABLE team_members (
  team_id UUID REFERENCES teams(id),
  user_id UUID REFERENCES users(id),
  role TEXT NOT NULL DEFAULT 'member',
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (team_id, user_id)
);

-- Invitations
CREATE TABLE invites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id),
  email TEXT,
  role TEXT NOT NULL,
  code TEXT UNIQUE NOT NULL,
  used_by UUID REFERENCES users(id),
  expires_at TIMESTAMPTZ NOT NULL,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id),
  name TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  prefix TEXT NOT NULL,
  permissions TEXT[] DEFAULT '{}',
  last_used_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## MVP Scope

**Phase 1 (Must have)**:
- [ ] Supabase Auth integration
- [ ] Google OAuth
- [ ] Basic roles (owner, member)
- [ ] Team creation

**Phase 2 (Important)**:
- [ ] Invitation system
- [ ] API Key management
- [ ] Channel permissions
- [ ] Admin role

**Phase 3 (Advanced)**:
- [ ] Guest role
- [ ] Full RLS coverage
- [ ] Audit logging
- [ ] SSO integration

## Security Considerations

1. **Passwords**: Using Supabase built-in, no need to handle ourselves
2. **Sessions**: JWT, short-lived, periodically refreshed
3. **API Keys**: bcrypt hashed, never stored in plaintext
4. **HTTPS**: Enforced HTTPS
5. **Rate Limiting**: Protection against brute force attacks

## Open Questions

1. **Free tier limits**: How many users/agents?
2. **Personal vs Team**: Support a personal mode?
3. **Account deletion**: GDPR-compliant data deletion?
4. **Multiple Teams**: One user across multiple teams?

---

*To be refined after Charles confirms*
