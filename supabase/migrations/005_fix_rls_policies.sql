-- Fix missing RLS policies identified in Phase 1 review
-- Addresses: api_keys, context_items, messages UPDATE/DELETE, workspaces UPDATE/DELETE, forks DELETE

-- ============================================================
-- 1. Workspaces: admin UPDATE/DELETE
-- ============================================================
CREATE POLICY "workspace_admin_update" ON workspaces FOR UPDATE
  USING (id IN (
    SELECT workspace_id FROM workspace_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

CREATE POLICY "workspace_admin_delete" ON workspaces FOR DELETE
  USING (owner_id = auth.uid());

-- ============================================================
-- 2. Messages: author UPDATE/DELETE, admin DELETE
-- ============================================================
CREATE POLICY "messages_update_own" ON messages FOR UPDATE
  USING (
    author_id = auth.uid()
    AND author_type = 'human'
  );

CREATE POLICY "messages_delete_own" ON messages FOR DELETE
  USING (
    author_id = auth.uid()
    AND author_type = 'human'
  );

-- ============================================================
-- 3. Forks: replace overly permissive FOR ALL
--    Drop existing policy and create granular ones
-- ============================================================
DROP POLICY IF EXISTS "forks_access" ON forks;

-- SELECT: any workspace member can see forks
CREATE POLICY "forks_select" ON forks FOR SELECT
  USING (thread_id IN (
    SELECT t.id FROM threads t
    JOIN channels c ON t.channel_id = c.id
    JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
    WHERE wm.user_id = auth.uid()
  ));

-- INSERT: any workspace member can create forks
CREATE POLICY "forks_insert" ON forks FOR INSERT
  WITH CHECK (
    created_by = auth.uid()
    AND thread_id IN (
      SELECT t.id FROM threads t
      JOIN channels c ON t.channel_id = c.id
      JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
      WHERE wm.user_id = auth.uid()
    )
  );

-- UPDATE: creator can update their own forks
CREATE POLICY "forks_update_own" ON forks FOR UPDATE
  USING (created_by = auth.uid());

-- DELETE: only creator can delete their forks
CREATE POLICY "forks_delete_own" ON forks FOR DELETE
  USING (created_by = auth.uid());

-- ============================================================
-- 4. API Keys: workspace-scoped SELECT, admin-only write
-- ============================================================
CREATE POLICY "api_keys_workspace_read" ON api_keys FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

CREATE POLICY "api_keys_admin_insert" ON api_keys FOR INSERT
  WITH CHECK (
    created_by = auth.uid()
    AND workspace_id IN (
      SELECT workspace_id FROM workspace_members
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "api_keys_admin_update" ON api_keys FOR UPDATE
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

CREATE POLICY "api_keys_admin_delete" ON api_keys FOR DELETE
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

-- ============================================================
-- 5. Context Items: workspace-scoped with scope visibility
-- ============================================================
CREATE POLICY "context_items_workspace_read" ON context_items FOR SELECT
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

CREATE POLICY "context_items_insert" ON context_items FOR INSERT
  WITH CHECK (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

CREATE POLICY "context_items_update" ON context_items FOR UPDATE
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
  ));

CREATE POLICY "context_items_admin_delete" ON context_items FOR DELETE
  USING (workspace_id IN (
    SELECT workspace_id FROM workspace_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

-- ============================================================
-- 6. Users: allow workspace members to see each other
-- ============================================================
CREATE POLICY "users_workspace_members_read" ON users FOR SELECT
  USING (id IN (
    SELECT wm2.user_id FROM workspace_members wm1
    JOIN workspace_members wm2 ON wm1.workspace_id = wm2.workspace_id
    WHERE wm1.user_id = auth.uid()
  ));
