import { describe, it, expect, beforeEach } from "vitest";
import { appRouter } from "./index";
import {
  createMockSupabase,
  createSequentialMockSupabase,
} from "../__test__/mock-supabase";

const TEST_USER_ID = "user-001";

describe("workspaceRouter", () => {
  describe("list", () => {
    it("returns mapped workspaces for the current user", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "ws-1",
          name: "Vibe",
          slug: "vibe",
          owner_id: TEST_USER_ID,
          settings: { theme: "dark" },
          created_at: "2026-01-01T00:00:00Z",
          workspace_members: [{ user_id: TEST_USER_ID }],
        },
      ]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.workspace.list();

      expect(result).toEqual([
        {
          id: "ws-1",
          name: "Vibe",
          slug: "vibe",
          ownerId: TEST_USER_ID,
          settings: { theme: "dark" },
          createdAt: "2026-01-01T00:00:00Z",
        },
      ]);
    });

    it("returns empty array when no workspaces", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.workspace.list();
      expect(result).toEqual([]);
    });

    it("defaults settings to empty object when null", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "ws-1",
          name: "Test",
          slug: "test",
          owner_id: TEST_USER_ID,
          settings: null,
          created_at: "2026-01-01T00:00:00Z",
          workspace_members: [],
        },
      ]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.workspace.list();
      expect(result[0].settings).toEqual({});
    });

    it("throws on Supabase error", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("connection refused");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(caller.workspace.list()).rejects.toThrow(
        "Failed to list workspaces"
      );
    });

    it("rejects unauthenticated calls", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({
        userId: null,
        supabase,
      });
      await expect(caller.workspace.list()).rejects.toThrow("Unauthorized");
    });
  });

  describe("getById", () => {
    const VALID_WS_ID = "550e8400-e29b-41d4-a716-446655440000";

    it("returns a single workspace", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: VALID_WS_ID,
        name: "Vibe",
        slug: "vibe",
        owner_id: TEST_USER_ID,
        settings: {},
        created_at: "2026-01-01T00:00:00Z",
      });

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const result = await caller.workspace.getById({ id: VALID_WS_ID });
      expect(result.id).toBe(VALID_WS_ID);
      expect(result.name).toBe("Vibe");
    });

    it("throws when workspace not found", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("Row not found");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.workspace.getById({ id: "550e8400-e29b-41d4-a716-446655440000" })
      ).rejects.toThrow("Workspace not found");
    });

    it("rejects invalid UUID input", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      await expect(
        caller.workspace.getById({ id: "not-a-uuid" })
      ).rejects.toThrow();
    });
  });

  describe("create", () => {
    it("creates workspace, user record, and membership", async () => {
      const mock = createSequentialMockSupabase();
      // 1. upsert user
      mock.pushResult({ id: TEST_USER_ID });
      // 2. insert workspace
      mock.pushResult({
        id: "ws-new",
        name: "New Space",
        slug: "new-space",
        owner_id: TEST_USER_ID,
        settings: null,
        created_at: "2026-02-01T00:00:00Z",
      });
      // 3. insert workspace_member
      mock.pushResult({ workspace_id: "ws-new", user_id: TEST_USER_ID });

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      const result = await caller.workspace.create({
        name: "New Space",
        slug: "new-space",
      });

      expect(result.id).toBe("ws-new");
      expect(result.name).toBe("New Space");
      expect(result.slug).toBe("new-space");
      expect(result.settings).toEqual({});
    });

    it("throws when user upsert fails", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushError("user upsert failed");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      await expect(
        caller.workspace.create({ name: "Test", slug: "test" })
      ).rejects.toThrow("Failed to ensure user record");
    });

    it("throws when workspace insert fails", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushResult({ id: TEST_USER_ID }); // user upsert ok
      mock.pushError("duplicate slug");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      await expect(
        caller.workspace.create({ name: "Test", slug: "test" })
      ).rejects.toThrow("Failed to create workspace");
    });

    it("throws when member insert fails", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushResult({ id: TEST_USER_ID }); // user upsert ok
      mock.pushResult({
        // workspace insert ok
        id: "ws-x",
        name: "X",
        slug: "x",
        owner_id: TEST_USER_ID,
        settings: null,
        created_at: "2026-01-01T00:00:00Z",
      });
      mock.pushError("member insert failed");

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase: mock.supabase,
      });
      await expect(
        caller.workspace.create({ name: "X", slug: "x" })
      ).rejects.toThrow("Failed to add workspace member");
    });
  });
});
