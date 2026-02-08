import { describe, it, expect } from "vitest";
import { appRouter } from "./index";
import {
  createMockSupabase,
  createSequentialMockSupabase,
} from "../__test__/mock-supabase";

const TEST_USER_ID = "user-001";
const TEST_CHANNEL_ID = "550e8400-e29b-41d4-a716-446655440000";
const TEST_THREAD_ID = "660e8400-e29b-41d4-a716-446655440000";

describe("messageRouter", () => {
  describe("list", () => {
    it("returns messages with author info and pagination", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "msg-1",
          thread_id: TEST_THREAD_ID,
          dive_id: null,
          parent_id: null,
          author_id: TEST_USER_ID,
          author_type: "human",
          content: "Hello world",
          metadata: { key: "value" },
          created_at: "2026-01-01T12:00:00Z",
          updated_at: "2026-01-01T12:00:00Z",
          users: { id: TEST_USER_ID, name: "Alice", avatar_url: null },
          threads: { id: TEST_THREAD_ID, channel_id: TEST_CHANNEL_ID },
        },
      ]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.message.list({
        channelId: TEST_CHANNEL_ID,
      });

      expect(result.messages).toHaveLength(1);
      expect(result.messages[0]).toEqual({
        id: "msg-1",
        threadId: TEST_THREAD_ID,
        diveId: null,
        parentId: null,
        authorId: TEST_USER_ID,
        authorType: "human",
        content: "Hello world",
        metadata: { key: "value" },
        createdAt: "2026-01-01T12:00:00Z",
        updatedAt: "2026-01-01T12:00:00Z",
        author: { id: TEST_USER_ID, name: "Alice", avatarUrl: null },
      });
      expect(result.nextCursor).toBeNull();
    });

    it("returns nextCursor when more messages exist", async () => {
      const { supabase, mockResult } = createMockSupabase();
      // Return limit+1 items to trigger hasMore
      const messages = Array.from({ length: 3 }, (_, i) => ({
        id: `msg-${i}`,
        thread_id: TEST_THREAD_ID,
        dive_id: null,
        parent_id: null,
        author_id: TEST_USER_ID,
        author_type: "human",
        content: `Message ${i}`,
        metadata: null,
        created_at: `2026-01-01T${String(12 - i).padStart(2, "0")}:00:00Z`,
        updated_at: `2026-01-01T${String(12 - i).padStart(2, "0")}:00:00Z`,
        users: null,
        threads: { id: TEST_THREAD_ID, channel_id: TEST_CHANNEL_ID },
      }));

      mockResult(messages);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.message.list({
        channelId: TEST_CHANNEL_ID,
        limit: 2,
      });

      expect(result.messages).toHaveLength(2);
      expect(result.nextCursor).toBe("2026-01-01T11:00:00Z");
    });

    it("handles null metadata", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "msg-1",
          thread_id: TEST_THREAD_ID,
          dive_id: null,
          parent_id: null,
          author_id: TEST_USER_ID,
          author_type: "human",
          content: "test",
          metadata: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          users: null,
          threads: { id: TEST_THREAD_ID, channel_id: TEST_CHANNEL_ID },
        },
      ]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.message.list({
        channelId: TEST_CHANNEL_ID,
      });

      expect(result.messages[0].metadata).toEqual({});
      expect(result.messages[0].author).toBeNull();
    });

    it("throws on Supabase error", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("connection lost");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.message.list({ channelId: TEST_CHANNEL_ID })
      ).rejects.toThrow("Failed to list messages");
    });

    it("rejects unauthenticated calls", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: null, supabase });
      await expect(
        caller.message.list({ channelId: TEST_CHANNEL_ID })
      ).rejects.toThrow("Unauthorized");
    });
  });

  describe("send", () => {
    it("creates thread + message for new top-level message", async () => {
      const mock = createSequentialMockSupabase();
      // 1. insert thread
      mock.pushResult({ id: TEST_THREAD_ID });
      // 2. insert message
      mock.pushResult({
        id: "msg-new",
        thread_id: TEST_THREAD_ID,
        dive_id: null,
        parent_id: null,
        author_id: TEST_USER_ID,
        author_type: "human",
        content: "Hello!",
        metadata: null,
        created_at: "2026-02-01T00:00:00Z",
        updated_at: "2026-02-01T00:00:00Z",
      });
      // 3. update thread root_message_id
      mock.pushResult(null);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      const result = await caller.message.send({
        channelId: TEST_CHANNEL_ID,
        content: "Hello!",
      });

      expect(result.id).toBe("msg-new");
      expect(result.threadId).toBe(TEST_THREAD_ID);
      expect(result.content).toBe("Hello!");
      expect(result.authorType).toBe("human");
    });

    it("uses parent's thread for replies", async () => {
      const mock = createSequentialMockSupabase();
      // 1. select parent message thread_id
      mock.pushResult({ thread_id: TEST_THREAD_ID });
      // 2. insert reply message
      mock.pushResult({
        id: "msg-reply",
        thread_id: TEST_THREAD_ID,
        dive_id: null,
        parent_id: "msg-parent",
        author_id: TEST_USER_ID,
        author_type: "human",
        content: "Reply here",
        metadata: {},
        created_at: "2026-02-01T01:00:00Z",
        updated_at: "2026-02-01T01:00:00Z",
      });

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      const result = await caller.message.send({
        channelId: TEST_CHANNEL_ID,
        content: "Reply here",
        parentId: "550e8400-e29b-41d4-a716-446655440001",
      });

      expect(result.id).toBe("msg-reply");
      expect(result.parentId).toBe("msg-parent");
    });

    it("throws when parent message not found", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushError("Row not found");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      await expect(
        caller.message.send({
          channelId: TEST_CHANNEL_ID,
          content: "orphan reply",
          parentId: "550e8400-e29b-41d4-a716-446655440099",
        })
      ).rejects.toThrow("Parent message not found");
    });

    it("throws when thread creation fails", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushError("insert failed");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      await expect(
        caller.message.send({
          channelId: TEST_CHANNEL_ID,
          content: "test",
        })
      ).rejects.toThrow("Failed to create thread");
    });

    it("throws when message insert fails", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushResult({ id: TEST_THREAD_ID }); // thread ok
      mock.pushError("message insert failed");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      await expect(
        caller.message.send({
          channelId: TEST_CHANNEL_ID,
          content: "test",
        })
      ).rejects.toThrow("Failed to send message");
    });

    it("rejects empty content", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.message.send({
          channelId: TEST_CHANNEL_ID,
          content: "",
        })
      ).rejects.toThrow();
    });
  });
});
