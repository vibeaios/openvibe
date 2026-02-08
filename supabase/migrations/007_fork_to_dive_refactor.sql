-- Migration: Fork → Dive terminology refactor
-- Date: 2026-02-08
-- Purpose: Rename fork-related tables, columns, and enums to dive terminology
-- See: docs/design/PRODUCT-CORE-REFRAME.md

-- ============================================================
-- 1. Rename forks table to dives
-- ============================================================
ALTER TABLE forks RENAME TO dives;

-- ============================================================
-- 2. Rename columns in dives table
-- ============================================================
ALTER TABLE dives RENAME COLUMN description TO topic;
ALTER TABLE dives RENAME COLUMN resolution TO result;
ALTER TABLE dives RENAME COLUMN resolved_at TO published_at;

-- ============================================================
-- 3. Update status enum values in dives table
-- Drop and recreate the check constraint with new values
-- ============================================================
ALTER TABLE dives DROP CONSTRAINT IF EXISTS forks_status_check;
ALTER TABLE dives ADD CONSTRAINT dives_status_check 
  CHECK (status IN ('active', 'published', 'discarded'));

-- Migrate existing data status values
UPDATE dives SET status = 'published' WHERE status = 'resolved';
UPDATE dives SET status = 'discarded' WHERE status = 'abandoned';

-- ============================================================
-- 4. Rename foreign key column in messages table
-- ============================================================
ALTER TABLE messages RENAME COLUMN fork_id TO dive_id;

-- ============================================================
-- 5. Rename foreign key constraint and index
-- ============================================================
ALTER TABLE messages DROP CONSTRAINT IF EXISTS fk_messages_fork;
ALTER TABLE messages ADD CONSTRAINT fk_messages_dive
  FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE;

DROP INDEX IF EXISTS idx_messages_fork;
CREATE INDEX idx_messages_dive ON messages(dive_id, created_at);

-- ============================================================
-- 6. Rename indexes on dives table
-- ============================================================
DROP INDEX IF EXISTS idx_forks_thread;
CREATE INDEX idx_dives_thread ON dives(thread_id);

DROP INDEX IF EXISTS idx_forks_status;
CREATE INDEX idx_dives_status ON dives(thread_id, status);

-- ============================================================
-- 7. Rename column in tasks table
-- ============================================================
ALTER TABLE tasks RENAME COLUMN fork_id TO dive_id;

-- ============================================================
-- 8. Update Supabase Realtime publication
-- Remove old table, add renamed table
-- ============================================================
ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS forks;
ALTER PUBLICATION supabase_realtime ADD TABLE dives;

-- ============================================================
-- 9. Update RLS policies for dives table
-- ============================================================
DROP POLICY IF EXISTS "forks_select" ON dives;
DROP POLICY IF EXISTS "forks_insert" ON dives;
DROP POLICY IF EXISTS "forks_update_own" ON dives;
DROP POLICY IF EXISTS "forks_delete_own" ON dives;

-- SELECT: any workspace member can see dives
CREATE POLICY "dives_select" ON dives FOR SELECT
  USING (thread_id IN (
    SELECT t.id FROM threads t
    JOIN channels c ON t.channel_id = c.id
    JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
    WHERE wm.user_id = auth.uid()
  ));

-- INSERT: any workspace member can create dives
CREATE POLICY "dives_insert" ON dives FOR INSERT
  WITH CHECK (
    created_by = auth.uid()
    AND thread_id IN (
      SELECT t.id FROM threads t
      JOIN channels c ON t.channel_id = c.id
      JOIN workspace_members wm ON c.workspace_id = wm.workspace_id
      WHERE wm.user_id = auth.uid()
    )
  );

-- UPDATE: creator can update their own dives
CREATE POLICY "dives_update_own" ON dives FOR UPDATE
  USING (created_by = auth.uid());

-- DELETE: only creator can delete their dives
CREATE POLICY "dives_delete_own" ON dives FOR DELETE
  USING (created_by = auth.uid());

-- ============================================================
-- Comments
-- ============================================================
COMMENT ON TABLE dives IS 'Deep dives: AI-assisted exploration of conversation points. Formerly named "forks".';
COMMENT ON COLUMN dives.topic IS 'What the user is exploring in this deep dive (formerly "description")';
COMMENT ON COLUMN dives.result IS 'AI-generated structured result from the deep dive (formerly "resolution")';
COMMENT ON COLUMN dives.status IS 'active = in progress, published = result posted to main thread, discarded = abandoned';
COMMENT ON COLUMN dives.published_at IS 'When the dive result was published to the main thread (formerly "resolved_at")';
