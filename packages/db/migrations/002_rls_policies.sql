-- Row Level Security Policies

-- Enable RLS on all tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE forks ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ui_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_items ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "users_read_own" ON users FOR SELECT
  USING (id = auth.uid());

-- Users can update their own profile
CREATE POLICY "users_update_own" ON users FOR UPDATE
  USING (id = auth.uid());

-- Workspace isolation: members can see their workspaces
CREATE POLICY "workspace_member_access" ON workspaces FOR SELECT
  USING (id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

-- Workspace members: can see co-members
CREATE POLICY "workspace_members_read" ON workspace_members FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

-- Channels: workspace members can access
CREATE POLICY "channels_workspace_access" ON channels FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

CREATE POLICY "channels_workspace_insert" ON channels FOR INSERT
  WITH CHECK (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

-- Threads: accessible via channel workspace membership
CREATE POLICY "threads_access" ON threads FOR ALL
  USING (channel_id IN (
    SELECT c.id FROM channels c
    JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
    WHERE wm.user_id = auth.uid()
  ));

-- Messages: workspace isolation via thread
CREATE POLICY "messages_access" ON messages FOR SELECT
  USING (thread_id IN (
    SELECT t.id FROM threads t
    JOIN channels c ON t.channel_id = c.id
    JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
    WHERE wm.user_id = auth.uid()
  ));

CREATE POLICY "messages_insert" ON messages FOR INSERT
  WITH CHECK (thread_id IN (
    SELECT t.id FROM threads t
    JOIN channels c ON t.channel_id = c.id
    JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
    WHERE wm.user_id = auth.uid()
  ));

-- Forks: accessible via thread
CREATE POLICY "forks_access" ON forks FOR ALL
  USING (thread_id IN (
    SELECT t.id FROM threads t
    JOIN channels c ON t.channel_id = c.id
    JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
    WHERE wm.user_id = auth.uid()
  ));

-- Tasks: workspace isolation
CREATE POLICY "tasks_access" ON tasks FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

-- Agent configs: workspace members can read, admins can write
CREATE POLICY "agent_configs_read" ON agent_configs FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

CREATE POLICY "agent_configs_admin" ON agent_configs FOR ALL
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

-- UI configs: workspace members can read
CREATE POLICY "ui_configs_read" ON ui_configs FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

-- Service role bypass for agent operations
-- (Agent tasks are created/updated by the server using the service role key,
--  which bypasses RLS. No explicit policy needed for server-side operations.)
