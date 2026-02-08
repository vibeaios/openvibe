-- OpenVibe MVP Schema
-- 12 tables for the fork/resolve thread model

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Workspaces
CREATE TABLE workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (mirrors auth.users with app-specific fields)
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_active_at TIMESTAMPTZ
);

-- Workspace members
CREATE TABLE workspace_members (
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member')),
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (workspace_id, user_id)
);

-- Channels
CREATE TABLE channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  is_private BOOLEAN DEFAULT FALSE,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (workspace_id, name)
);
CREATE INDEX idx_channels_workspace ON channels(workspace_id);

-- Threads
CREATE TABLE threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  root_message_id UUID,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'archived')),
  title TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_threads_channel ON threads(channel_id);
CREATE INDEX idx_threads_status ON threads(channel_id, status);

-- Messages (created before forks to allow parent_message_id reference)
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
  fork_id UUID, -- will add FK after forks table
  parent_id UUID REFERENCES messages(id),
  author_id UUID NOT NULL,
  author_type TEXT NOT NULL CHECK (author_type IN ('human', 'agent', 'system')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_messages_thread ON messages(thread_id, created_at);
CREATE INDEX idx_messages_author ON messages(author_id);

-- Full-text search on messages
ALTER TABLE messages ADD COLUMN fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
CREATE INDEX idx_messages_fts ON messages USING GIN(fts);

-- Forks
CREATE TABLE forks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
  parent_message_id UUID NOT NULL REFERENCES messages(id),
  description TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'abandoned')),
  resolution TEXT,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);
CREATE INDEX idx_forks_thread ON forks(thread_id);
CREATE INDEX idx_forks_status ON forks(thread_id, status);

-- Add FK from messages to forks (deferred creation due to circular dependency)
ALTER TABLE messages ADD CONSTRAINT fk_messages_fork
  FOREIGN KEY (fork_id) REFERENCES forks(id) ON DELETE CASCADE;
CREATE INDEX idx_messages_fork ON messages(fork_id, created_at);

-- Add FK from threads to root message
ALTER TABLE threads ADD CONSTRAINT fk_threads_root_message
  FOREIGN KEY (root_message_id) REFERENCES messages(id);

-- Agent configs
CREATE TABLE agent_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  display_name TEXT NOT NULL,
  description TEXT,
  model TEXT DEFAULT 'claude-sonnet-4-5',
  system_prompt TEXT,
  capabilities JSONB DEFAULT '[]',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (workspace_id, slug)
);

-- Tasks (agent task queue)
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id),
  thread_id UUID REFERENCES threads(id),
  fork_id UUID REFERENCES forks(id),
  trigger_message_id UUID REFERENCES messages(id),
  agent_config_id UUID NOT NULL REFERENCES agent_configs(id),
  status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
  task_type TEXT DEFAULT 'message_response',
  input JSONB DEFAULT '{}',
  output JSONB DEFAULT '{}',
  token_usage JSONB DEFAULT '{}',
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);
CREATE INDEX idx_tasks_status ON tasks(status) WHERE status IN ('queued', 'running');
CREATE INDEX idx_tasks_workspace ON tasks(workspace_id, created_at DESC);
CREATE INDEX idx_tasks_agent ON tasks(agent_config_id, status);

-- UI configs
CREATE TABLE ui_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  config_key TEXT NOT NULL,
  config_value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (workspace_id, config_key)
);

-- API keys
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  prefix TEXT NOT NULL,
  permissions TEXT[] DEFAULT '{}',
  last_used_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Context items (minimal, for future context bus)
CREATE TABLE context_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('discovery', 'decision', 'status', 'note', 'thread_summary')),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  summary TEXT,
  scope TEXT DEFAULT 'global' CHECK (scope IN ('task', 'thread', 'channel', 'global')),
  relevance_tags TEXT[] DEFAULT '{}',
  source_runtime TEXT,
  source_thread_id UUID REFERENCES threads(id),
  source_task_id UUID REFERENCES tasks(id),
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ
);
ALTER TABLE context_items ADD COLUMN fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || content)) STORED;
CREATE INDEX idx_context_fts ON context_items USING GIN(fts);
CREATE INDEX idx_context_workspace ON context_items(workspace_id, scope);
CREATE INDEX idx_context_tags ON context_items USING GIN(relevance_tags);
