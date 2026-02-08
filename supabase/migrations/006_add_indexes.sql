-- Additional indexes identified in Phase 1 review

-- Agent configs: frequent workspace-scoped reads
CREATE INDEX IF NOT EXISTS idx_agent_configs_workspace ON agent_configs(workspace_id);

-- Context items: time-based queries for memory retrieval
CREATE INDEX IF NOT EXISTS idx_context_items_created ON context_items(workspace_id, created_at DESC);

-- Workspace members: find all workspaces for a user (reverse lookup)
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);
