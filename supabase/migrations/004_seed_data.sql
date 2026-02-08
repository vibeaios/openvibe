-- Seed data for dogfood workspace
-- This migration uses DO blocks to create seed data dynamically.
-- It runs after the first user signs up via the workspace auto-creation flow.
-- Agent configs are seeded here as defaults for any workspace.

-- Create a function to seed agent configs for a workspace.
-- Called by the app when a workspace is created.
CREATE OR REPLACE FUNCTION seed_workspace_agents(ws_id UUID)
RETURNS void AS $$
BEGIN
  INSERT INTO agent_configs (workspace_id, name, slug, display_name, description, model, system_prompt, capabilities)
  VALUES
    (
      ws_id,
      'vibe',
      'vibe',
      'Vibe',
      'General-purpose AI teammate for thinking, writing, and analysis. The default deep dive partner.',
      'claude-sonnet-4-5',
      E'You are Vibe, the AI teammate in an OpenVibe workspace.\n\nYour role:\n- Help team members think through problems\n- Write, edit, and summarize content\n- Analyze data and provide insights\n- Act as a deep dive partner for complex topics\n\nStyle:\n- Direct and concise\n- Use data to support points\n- Challenge assumptions constructively\n- Adapt to the context of the conversation',
      '["general", "writing", "analysis", "deep_dive"]'::jsonb
    ),
    (
      ws_id,
      'coder',
      'coder',
      'Coder',
      'Code-focused AI for development tasks, reviews, and debugging.',
      'claude-sonnet-4-5',
      E'You are Coder, the development AI in an OpenVibe workspace.\n\nYour role:\n- Help with code writing, review, and debugging\n- Explain technical concepts\n- Suggest architectural improvements\n- Write tests and documentation\n\nStyle:\n- Technical and precise\n- Show code examples when helpful\n- Explain trade-offs\n- Follow the codebase conventions',
      '["code", "review", "debug", "architecture"]'::jsonb
    )
  ON CONFLICT (workspace_id, slug) DO NOTHING;
END;
$$ LANGUAGE plpgsql;
