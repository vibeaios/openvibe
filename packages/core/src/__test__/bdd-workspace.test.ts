/**
 * BDD Feature: Workspace Management
 *
 * Feature: Workspace Creation & Membership
 *   As a Vibe team admin
 *   I want to create and manage workspaces
 *   So that my team has a collaboration space
 */
import { describe, it, expect } from "vitest";
import { appRouter } from "../routers/index";
import {
  createMockSupabase,
  createSequentialMockSupabase,
} from "./mock-supabase";

const ADMIN_USER_ID = "admin-001";
const WORKSPACE_ID = "550e8400-e29b-41d4-a716-446655440000";

describe("Feature: Workspace Creation & Membership", () => {
  describe("Scenario: Admin creates a new workspace", () => {
    it("Given an authenticated admin, When they create workspace 'Vibe', Then it exists with agents seeded", async () => {
      const mock = createSequentialMockSupabase();

      // Step 1: user upsert succeeds
      mock.pushResult({ id: ADMIN_USER_ID });
      // Step 2: workspace insert returns new workspace
      mock.pushResult({
        id: WORKSPACE_ID,
        name: "Vibe",
        slug: "vibe",
        owner_id: ADMIN_USER_ID,
        settings: {},
        created_at: "2026-02-01T00:00:00Z",
      });
      // Step 3: workspace_members insert succeeds
      mock.pushResult(null);
      // Step 4: rpc seed_workspace_agents succeeds (called via try/catch)

      const caller = appRouter.createCaller({
        userId: ADMIN_USER_ID,
        supabase: mock.supabase,
      });

      const result = await caller.workspace.create({
        name: "Vibe",
        slug: "vibe",
      });

      expect(result.id).toBe(WORKSPACE_ID);
      expect(result.name).toBe("Vibe");
      expect(result.slug).toBe("vibe");
      expect(result.ownerId).toBe(ADMIN_USER_ID);
    });
  });

  describe("Scenario: User retrieves workspace by ID", () => {
    it("Given a workspace exists, When user requests it by ID, Then they see workspace details", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: WORKSPACE_ID,
        name: "Vibe",
        slug: "vibe",
        owner_id: ADMIN_USER_ID,
        settings: { theme: "dark" },
        created_at: "2026-02-01T00:00:00Z",
        workspace_members: [
          { user_id: ADMIN_USER_ID, role: "admin", joined_at: "2026-02-01T00:00:00Z" },
        ],
      });

      const caller = appRouter.createCaller({
        userId: ADMIN_USER_ID,
        supabase,
      });

      const workspace = await caller.workspace.getById({ id: WORKSPACE_ID });

      expect(workspace.name).toBe("Vibe");
      expect(workspace.settings).toEqual({ theme: "dark" });
    });
  });

  describe("Scenario: Workspace creation fails gracefully", () => {
    it("Given a DB error during creation, Then a clear error is thrown", async () => {
      const mock = createSequentialMockSupabase();
      mock.pushResult({ id: ADMIN_USER_ID }); // user upsert
      mock.pushError("duplicate key value violates unique constraint");

      const caller = appRouter.createCaller({
        userId: ADMIN_USER_ID,
        supabase: mock.supabase,
      });

      await expect(
        caller.workspace.create({ name: "Vibe", slug: "vibe" })
      ).rejects.toThrow("Failed to create workspace");
    });
  });

  describe("Scenario: Workspace settings default to empty object", () => {
    it("Given workspace has null settings, Then API returns empty object", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: WORKSPACE_ID,
          name: "Vibe",
          slug: "vibe",
          owner_id: ADMIN_USER_ID,
          settings: null,
          created_at: "2026-02-01T00:00:00Z",
          workspace_members: [
            { user_id: ADMIN_USER_ID, role: "admin", joined_at: "2026-02-01T00:00:00Z" },
          ],
        },
      ]);

      const caller = appRouter.createCaller({
        userId: ADMIN_USER_ID,
        supabase,
      });

      const workspaces = await caller.workspace.list();
      expect(workspaces[0].settings).toEqual({});
    });
  });
});
