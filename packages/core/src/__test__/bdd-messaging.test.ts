/**
 * BDD Feature: Messaging
 *
 * Feature: Send & Receive Messages
 *   As a workspace member
 *   I want to send messages in channels
 *   So that I can communicate with my team and AI agents
 */
import { describe, it, expect } from "vitest";
import { appRouter } from "../routers/index";
import {
  createMockSupabase,
  createSequentialMockSupabase,
} from "./mock-supabase";

const USER_ID = "user-001";
const CHANNEL_ID = "550e8400-e29b-41d4-a716-446655440000";
const THREAD_ID = "660e8400-e29b-41d4-a716-446655440000";

describe("Feature: Send & Receive Messages", () => {
  describe("Scenario: User sends a new message to a channel", () => {
    it("Given user is in #general, When they send 'Hello team!', Then message appears with author info", async () => {
      const mock = createSequentialMockSupabase();

      // Step 1: create thread (new top-level message)
      mock.pushResult({ id: THREAD_ID });
      // Step 2: insert message
      mock.pushResult({
        id: "msg-1",
        thread_id: THREAD_ID,
        dive_id: null,
        parent_id: null,
        author_id: USER_ID,
        author_type: "human",
        content: "Hello team!",
        metadata: {},
        created_at: "2026-02-07T10:00:00Z",
        updated_at: "2026-02-07T10:00:00Z",
      });
      // Step 3: update thread root_message_id
      mock.pushResult(null);

      const caller = appRouter.createCaller({
        userId: USER_ID,
        supabase: mock.supabase,
      });

      const msg = await caller.message.send({
        channelId: CHANNEL_ID,
        content: "Hello team!",
      });

      expect(msg.content).toBe("Hello team!");
      expect(msg.authorId).toBe(USER_ID);
      expect(msg.authorType).toBe("human");
      expect(msg.threadId).toBe(THREAD_ID);
      expect(msg.parentId).toBeNull();
    });
  });

  describe("Scenario: User replies to an existing message", () => {
    it("Given a message exists in a thread, When user replies, Then reply is linked to parent", async () => {
      const mock = createSequentialMockSupabase();
      const PARENT_MSG_ID = "550e8400-e29b-41d4-a716-446655440001";

      // Step 1: find parent message's thread
      mock.pushResult({ thread_id: THREAD_ID });
      // Step 2: insert reply
      mock.pushResult({
        id: "msg-reply",
        thread_id: THREAD_ID,
        dive_id: null,
        parent_id: PARENT_MSG_ID,
        author_id: USER_ID,
        author_type: "human",
        content: "Great point!",
        metadata: {},
        created_at: "2026-02-07T10:05:00Z",
        updated_at: "2026-02-07T10:05:00Z",
      });

      const caller = appRouter.createCaller({
        userId: USER_ID,
        supabase: mock.supabase,
      });

      const reply = await caller.message.send({
        channelId: CHANNEL_ID,
        content: "Great point!",
        parentId: PARENT_MSG_ID,
      });

      expect(reply.content).toBe("Great point!");
      expect(reply.parentId).toBe(PARENT_MSG_ID);
      expect(reply.threadId).toBe(THREAD_ID);
    });
  });

  describe("Scenario: User views message history with pagination", () => {
    it("Given 5 messages exist, When user requests limit=2, Then they get 2 messages + nextCursor", async () => {
      const { supabase, mockResult } = createMockSupabase();

      // Return 3 items (limit+1) to indicate more exist
      const messages = Array.from({ length: 3 }, (_, i) => ({
        id: `msg-${i}`,
        thread_id: THREAD_ID,
        dive_id: null,
        parent_id: null,
        author_id: USER_ID,
        author_type: "human",
        content: `Message ${i}`,
        metadata: null,
        created_at: `2026-02-07T${String(12 - i).padStart(2, "0")}:00:00Z`,
        updated_at: `2026-02-07T${String(12 - i).padStart(2, "0")}:00:00Z`,
        users: { id: USER_ID, name: "Alice", avatar_url: null },
        threads: { id: THREAD_ID, channel_id: CHANNEL_ID },
      }));
      mockResult(messages);

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const result = await caller.message.list({
        channelId: CHANNEL_ID,
        limit: 2,
      });

      expect(result.messages).toHaveLength(2);
      expect(result.nextCursor).not.toBeNull();
      expect(result.nextCursor).toBe("2026-02-07T11:00:00Z");
    });

    it("Given fewer messages than limit, Then nextCursor is null", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "msg-0",
          thread_id: THREAD_ID,
          dive_id: null,
          parent_id: null,
          author_id: USER_ID,
          author_type: "human",
          content: "Only message",
          metadata: {},
          created_at: "2026-02-07T12:00:00Z",
          updated_at: "2026-02-07T12:00:00Z",
          users: { id: USER_ID, name: "Alice", avatar_url: null },
          threads: { id: THREAD_ID, channel_id: CHANNEL_ID },
        },
      ]);

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const result = await caller.message.list({
        channelId: CHANNEL_ID,
        limit: 50,
      });

      expect(result.messages).toHaveLength(1);
      expect(result.nextCursor).toBeNull();
    });
  });

  describe("Scenario: Messages include author information", () => {
    it("Given a human message with user record, Then author name and avatar are included", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "msg-1",
          thread_id: THREAD_ID,
          dive_id: null,
          parent_id: null,
          author_id: USER_ID,
          author_type: "human",
          content: "Hello",
          metadata: {},
          created_at: "2026-02-07T12:00:00Z",
          updated_at: "2026-02-07T12:00:00Z",
          users: {
            id: USER_ID,
            name: "Charles",
            avatar_url: "https://example.com/avatar.jpg",
          },
          threads: { id: THREAD_ID, channel_id: CHANNEL_ID },
        },
      ]);

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const result = await caller.message.list({ channelId: CHANNEL_ID });

      const msg = result.messages[0];
      expect(msg.author).not.toBeNull();
      expect(msg.author!.name).toBe("Charles");
      expect(msg.author!.avatarUrl).toBe("https://example.com/avatar.jpg");
    });

    it("Given a message with no user record, Then author is null", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "msg-1",
          thread_id: THREAD_ID,
          dive_id: null,
          parent_id: null,
          author_id: "agent-001",
          author_type: "agent",
          content: "I can help with that",
          metadata: {},
          created_at: "2026-02-07T12:00:00Z",
          updated_at: "2026-02-07T12:00:00Z",
          users: null,
          threads: { id: THREAD_ID, channel_id: CHANNEL_ID },
        },
      ]);

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const result = await caller.message.list({ channelId: CHANNEL_ID });

      expect(result.messages[0].author).toBeNull();
      expect(result.messages[0].authorType).toBe("agent");
    });
  });

  describe("Scenario: Message validation", () => {
    it("Given empty content, When user sends message, Then validation error", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: USER_ID, supabase });

      await expect(
        caller.message.send({ channelId: CHANNEL_ID, content: "" })
      ).rejects.toThrow();
    });

    it("Given invalid channelId format, When user sends message, Then validation error", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: USER_ID, supabase });

      await expect(
        caller.message.send({ channelId: "not-a-uuid", content: "Hello" })
      ).rejects.toThrow();
    });
  });

  describe("Scenario: Database error handling", () => {
    it("Given DB is unavailable, When user lists messages, Then clear error is thrown", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("connection refused");

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });

      await expect(
        caller.message.list({ channelId: CHANNEL_ID })
      ).rejects.toThrow("Failed to list messages");
    });

    it("Given parent message not found, When user replies, Then clear error is thrown", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushError("Row not found");

      const caller = appRouter.createCaller({
        userId: USER_ID,
        supabase: mock.supabase,
      });

      await expect(
        caller.message.send({
          channelId: CHANNEL_ID,
          content: "reply",
          parentId: "550e8400-e29b-41d4-a716-446655440099",
        })
      ).rejects.toThrow("Parent message not found");
    });
  });
});
