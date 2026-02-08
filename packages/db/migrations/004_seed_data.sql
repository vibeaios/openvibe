-- OpenVibe Dogfood Seed Data
-- Run this in Supabase SQL Editor AFTER at least one user has logged in via Google OAuth.
-- It picks the first auth.users entry as the owner.

DO $$
DECLARE
  v_user_id UUID;
  v_user_email TEXT;
  v_workspace_id UUID;
  v_ch_general UUID;
  v_ch_engineering UUID;
  v_ch_design UUID;
  v_ch_random UUID;
  v_ch_product UUID;
  v_thread_id UUID;
  v_agent_vibe UUID;
  v_agent_coder UUID;
BEGIN
  -- Get first user from auth.users
  SELECT id, email INTO v_user_id, v_user_email FROM auth.users LIMIT 1;
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'No users found. Log in via Google OAuth first.';
  END IF;

  RAISE NOTICE 'Seeding for user: % (%)', v_user_email, v_user_id;

  -- Ensure user record exists in public.users
  INSERT INTO users (id, email, name, avatar_url)
  VALUES (v_user_id, v_user_email, split_part(v_user_email, '@', 1), NULL)
  ON CONFLICT (id) DO NOTHING;

  -- Create Vibe workspace
  INSERT INTO workspaces (id, name, slug, owner_id)
  VALUES (gen_random_uuid(), 'Vibe', 'vibe', v_user_id)
  RETURNING id INTO v_workspace_id;

  -- Add owner as admin member
  INSERT INTO workspace_members (workspace_id, user_id, role)
  VALUES (v_workspace_id, v_user_id, 'admin');

  -- Create channels
  INSERT INTO channels (id, workspace_id, name, description, created_by)
  VALUES (gen_random_uuid(), v_workspace_id, 'general', 'Team-wide announcements and conversation', v_user_id)
  RETURNING id INTO v_ch_general;

  INSERT INTO channels (id, workspace_id, name, description, created_by)
  VALUES (gen_random_uuid(), v_workspace_id, 'engineering', 'Engineering discussions, code reviews, architecture', v_user_id)
  RETURNING id INTO v_ch_engineering;

  INSERT INTO channels (id, workspace_id, name, description, created_by)
  VALUES (gen_random_uuid(), v_workspace_id, 'design', 'Design reviews, UX discussions, mockups', v_user_id)
  RETURNING id INTO v_ch_design;

  INSERT INTO channels (id, workspace_id, name, description, created_by)
  VALUES (gen_random_uuid(), v_workspace_id, 'random', 'Non-work chatter, memes, fun stuff', v_user_id)
  RETURNING id INTO v_ch_random;

  INSERT INTO channels (id, workspace_id, name, description, created_by)
  VALUES (gen_random_uuid(), v_workspace_id, 'product', 'Product roadmap, feature discussions, user feedback', v_user_id)
  RETURNING id INTO v_ch_product;

  -- Create agent configs
  INSERT INTO agent_configs (id, workspace_id, name, slug, display_name, description, model, system_prompt, capabilities)
  VALUES (
    gen_random_uuid(), v_workspace_id, 'vibe', 'vibe', '@Vibe',
    'General-purpose AI teammate for thinking, writing, and analysis',
    'claude-sonnet-4-5',
    'You are Vibe, an AI teammate at Vibe (the company). You help with thinking through problems, writing, analysis, and general questions. Be concise and direct. Use a collaborative tone — you are a peer, not an assistant. When uncertain, say so. Challenge assumptions when appropriate.',
    '["general", "writing", "analysis", "brainstorm"]'::jsonb
  ) RETURNING id INTO v_agent_vibe;

  INSERT INTO agent_configs (id, workspace_id, name, slug, display_name, description, model, system_prompt, capabilities)
  VALUES (
    gen_random_uuid(), v_workspace_id, 'coder', 'coder', '@Coder',
    'Code-focused AI for development, reviews, debugging, and architecture',
    'claude-sonnet-4-5',
    'You are Coder, a senior engineer AI teammate at Vibe. You help with code reviews, debugging, architecture decisions, and implementation. Write clean, minimal code. Prefer simplicity over cleverness. Point out potential issues proactively. When reviewing code, focus on correctness and maintainability.',
    '["code", "review", "debug", "architecture"]'::jsonb
  ) RETURNING id INTO v_agent_coder;

  -- Seed messages in #general
  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_general, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'Welcome to OpenVibe! This is our new team collaboration space.', NOW() - INTERVAL '2 hours');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_general, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'We are dogfooding this to replace Slack. Key difference: AI agents are first-class participants, and we have fork/resolve for research threads.', NOW() - INTERVAL '1 hour 50 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_general, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'Try mentioning @Vibe or @Coder in any channel to invoke the AI agents. They will respond in the thread.', NOW() - INTERVAL '1 hour 45 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  -- Seed messages in #engineering
  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_engineering, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'Tech stack for OpenVibe: Next.js 15, tRPC v11, Supabase (Postgres + Realtime + Auth), Tailwind v4, Zustand. Monorepo with Nx.', NOW() - INTERVAL '1 hour 30 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_engineering, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'DB schema: 12 tables. Messages use tsvector for full-text search. RLS policies enforce workspace isolation. Supabase Realtime publishes message/fork/task changes.', NOW() - INTERVAL '1 hour 20 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  -- Seed messages in #product
  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_product, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'Sprint 2 focus: thread replies, @mention detection, and AI agent invocation pipeline. The core differentiator is fork/resolve — coming in Sprint 3.', NOW() - INTERVAL '1 hour');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_product, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'Core thesis: the real pain is copy-paste between AI tools. Fork/resolve formalizes the "AI research loop" inside the conversation. Moat = behavioral habits + accumulated data.', NOW() - INTERVAL '50 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  -- Seed messages in #design
  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_design, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'UI direction: Discord-like 4-zone layout. Dark theme. Considering Geist Pixel font for branding. Focus Mode + Fork Sidebar for managing parallel research.', NOW() - INTERVAL '40 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  -- Seed messages in #random
  INSERT INTO threads (id, channel_id, status) VALUES (gen_random_uuid(), v_ch_random, 'active') RETURNING id INTO v_thread_id;
  INSERT INTO messages (thread_id, author_id, author_type, content, created_at)
  VALUES (v_thread_id, v_user_id, 'human', 'First message in #random. This channel is the official home for off-topic conversations, memes, and celebrating small wins.', NOW() - INTERVAL '30 minutes');
  UPDATE threads SET root_message_id = (SELECT id FROM messages WHERE thread_id = v_thread_id LIMIT 1) WHERE id = v_thread_id;

  RAISE NOTICE 'Seed complete! Workspace: %, Channels: 5, Agents: 2, Messages: 10', v_workspace_id;
END $$;
