import { describe, it, expect } from "vitest";
import { appRouter } from "./index";
import { createMockSupabase } from "../__test__/mock-supabase";

const TEST_USER_ID = "user-001";
const TEST_WS_ID = "550e8400-e29b-41d4-a716-446655440000";

describe("channelRouter", () => {
  describe("list", () => {
    it("returns mapped channels for a workspace", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "ch-1",
          workspace_id: TEST_WS_ID,
          name: "general",
          description: "General discussion",
          is_private: false,
          created_by: TEST_USER_ID,
          created_at: "2026-01-01T00:00:00Z",
        },
        {
          id: "ch-2",
          workspace_id: TEST_WS_ID,
          name: "dev",
          description: null,
          is_private: true,
          created_by: TEST_USER_ID,
          created_at: "2026-01-02T00:00:00Z",
        },
      ]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.channel.list({ workspaceId: TEST_WS_ID });

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual({
        id: "ch-1",
        workspaceId: TEST_WS_ID,
        name: "general",
        description: "General discussion",
        isPrivate: false,
        createdBy: TEST_USER_ID,
        createdAt: "2026-01-01T00:00:00Z",
      });
      expect(result[1].isPrivate).toBe(true);
    });

    it("returns empty array when no channels", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.channel.list({ workspaceId: TEST_WS_ID });
      expect(result).toEqual([]);
    });

    it("throws on Supabase error", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("permission denied");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.channel.list({ workspaceId: TEST_WS_ID })
      ).rejects.toThrow("Failed to list channels");
    });

    it("rejects unauthenticated calls", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: null, supabase });
      await expect(
        caller.channel.list({ workspaceId: TEST_WS_ID })
      ).rejects.toThrow("Unauthorized");
    });
  });

  describe("getBySlug", () => {
    it("returns a single channel by slug", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: "ch-1",
        workspace_id: TEST_WS_ID,
        name: "general",
        description: "The general channel",
        is_private: false,
        created_by: TEST_USER_ID,
        created_at: "2026-01-01T00:00:00Z",
      });

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.channel.getBySlug({
        workspaceId: TEST_WS_ID,
        slug: "general",
      });

      expect(result.id).toBe("ch-1");
      expect(result.name).toBe("general");
    });

    it("throws when channel not found", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("Row not found");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.channel.getBySlug({
          workspaceId: TEST_WS_ID,
          slug: "nonexistent",
        })
      ).rejects.toThrow("Channel not found");
    });
  });

  describe("create", () => {
    it("creates a channel and returns mapped result", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: "ch-new",
        workspace_id: TEST_WS_ID,
        name: "design",
        description: "Design discussions",
        is_private: false,
        created_by: TEST_USER_ID,
        created_at: "2026-02-01T00:00:00Z",
      });

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.channel.create({
        workspaceId: TEST_WS_ID,
        name: "design",
        description: "Design discussions",
      });

      expect(result.id).toBe("ch-new");
      expect(result.name).toBe("design");
      expect(result.createdBy).toBe(TEST_USER_ID);
    });

    it("creates a channel without description", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: "ch-new",
        workspace_id: TEST_WS_ID,
        name: "random",
        description: null,
        is_private: false,
        created_by: TEST_USER_ID,
        created_at: "2026-02-01T00:00:00Z",
      });

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.channel.create({
        workspaceId: TEST_WS_ID,
        name: "random",
      });

      expect(result.description).toBeNull();
    });

    it("throws on Supabase error", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("duplicate name");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.channel.create({
          workspaceId: TEST_WS_ID,
          name: "general",
        })
      ).rejects.toThrow("Failed to create channel");
    });

    it("rejects name over 80 chars", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.channel.create({
          workspaceId: TEST_WS_ID,
          name: "a".repeat(81),
        })
      ).rejects.toThrow();
    });
  });
});
