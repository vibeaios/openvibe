/**
 * BDD Feature: Authentication & Authorization
 *
 * Feature: User Authentication
 *   As a Vibe team member
 *   I want to access OpenVibe with proper authentication
 *   So that my data is protected and I can collaborate securely
 */
import { describe, it, expect } from "vitest";
import { appRouter } from "../routers/index";
import { createMockSupabase } from "./mock-supabase";

const TEST_USER_ID = "auth-user-001";
const TEST_WORKSPACE_ID = "550e8400-e29b-41d4-a716-446655440000";

describe("Feature: User Authentication", () => {
  describe("Scenario: Authenticated user can access workspace data", () => {
    it("Given an authenticated user who is a workspace member", async () => {
      // Setup: user is authenticated and workspace exists
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: TEST_WORKSPACE_ID,
          name: "Vibe Team",
          slug: "vibe",
          owner_id: TEST_USER_ID,
          settings: { theme: "dark" },
          created_at: "2026-01-01T00:00:00Z",
          workspace_members: [
            {
              user_id: TEST_USER_ID,
              role: "admin",
              joined_at: "2026-01-01T00:00:00Z",
            },
          ],
        },
      ]);

      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });

      // When they list workspaces
      const workspaces = await caller.workspace.list();

      // Then they should see their workspace
      expect(workspaces).toHaveLength(1);
      expect(workspaces[0].name).toBe("Vibe Team");
      expect(workspaces[0].slug).toBe("vibe");
    });
  });

  describe("Scenario: Unauthenticated user is rejected", () => {
    it("Given no authentication token", async () => {
      const { supabase } = createMockSupabase();

      // When an unauthenticated user tries to access workspace
      const caller = appRouter.createCaller({
        userId: null,
        supabase,
      });

      // Then the request should be rejected with Unauthorized
      await expect(caller.workspace.list()).rejects.toThrow("Unauthorized");
    });

    it("Given no auth, channel listing is also rejected", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: null, supabase });

      await expect(
        caller.channel.list({ workspaceId: TEST_WORKSPACE_ID })
      ).rejects.toThrow("Unauthorized");
    });

    it("Given no auth, sending messages is rejected", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: null, supabase });

      await expect(
        caller.message.send({
          channelId: TEST_WORKSPACE_ID,
          content: "Hello!",
        })
      ).rejects.toThrow("Unauthorized");
    });
  });

  describe("Scenario: First-time user creates a workspace", () => {
    it("Given a new authenticated user with no workspace", async () => {
      const { supabase, mockResult } = createMockSupabase();

      // When they list workspaces, they see none
      mockResult([]);
      const caller = appRouter.createCaller({
        userId: TEST_USER_ID,
        supabase,
      });
      const workspaces = await caller.workspace.list();

      // Then the list is empty
      expect(workspaces).toHaveLength(0);
    });
  });
});
