/**
 * BDD Feature: Channel Management
 *
 * Feature: Channel CRUD
 *   As a workspace member
 *   I want to create and browse channels
 *   So that I can organize conversations by topic
 */
import { describe, it, expect } from "vitest";
import { appRouter } from "../routers/index";
import { createMockSupabase } from "./mock-supabase";

const USER_ID = "user-001";
const WORKSPACE_ID = "550e8400-e29b-41d4-a716-446655440000";

describe("Feature: Channel Management", () => {
  describe("Scenario: User sees channel list in sidebar", () => {
    it("Given workspace has channels, When user opens sidebar, Then they see all channels sorted by name", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([
        {
          id: "ch-1",
          workspace_id: WORKSPACE_ID,
          name: "engineering",
          description: "Engineering discussions",
          is_private: false,
          created_by: USER_ID,
          created_at: "2026-01-01T00:00:00Z",
        },
        {
          id: "ch-2",
          workspace_id: WORKSPACE_ID,
          name: "general",
          description: "General chat",
          is_private: false,
          created_by: USER_ID,
          created_at: "2026-01-01T00:00:00Z",
        },
        {
          id: "ch-3",
          workspace_id: WORKSPACE_ID,
          name: "product",
          description: null,
          is_private: false,
          created_by: USER_ID,
          created_at: "2026-01-02T00:00:00Z",
        },
      ]);

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const channels = await caller.channel.list({
        workspaceId: WORKSPACE_ID,
      });

      expect(channels).toHaveLength(3);
      expect(channels[0].name).toBe("engineering");
      expect(channels[1].name).toBe("general");
      expect(channels[2].name).toBe("product");
    });
  });

  describe("Scenario: User navigates to a specific channel", () => {
    it("Given channel 'general' exists, When user clicks it, Then they see channel details", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: "ch-2",
        workspace_id: WORKSPACE_ID,
        name: "general",
        description: "General chat",
        is_private: false,
        created_by: USER_ID,
        created_at: "2026-01-01T00:00:00Z",
      });

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const channel = await caller.channel.getBySlug({
        workspaceId: WORKSPACE_ID,
        slug: "general",
      });

      expect(channel.name).toBe("general");
      expect(channel.description).toBe("General chat");
      expect(channel.isPrivate).toBe(false);
    });
  });

  describe("Scenario: User creates a new channel", () => {
    it("Given user is a workspace member, When they create channel 'design', Then channel appears in list", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult({
        id: "ch-new",
        workspace_id: WORKSPACE_ID,
        name: "design",
        description: "Design discussions",
        is_private: false,
        created_by: USER_ID,
        created_at: "2026-02-07T00:00:00Z",
      });

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const channel = await caller.channel.create({
        workspaceId: WORKSPACE_ID,
        name: "design",
        description: "Design discussions",
      });

      expect(channel.name).toBe("design");
      expect(channel.description).toBe("Design discussions");
      expect(channel.createdBy).toBe(USER_ID);
    });
  });

  describe("Scenario: Channel creation with invalid input", () => {
    it("Given empty name, When user creates channel, Then validation error is thrown", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: USER_ID, supabase });

      await expect(
        caller.channel.create({
          workspaceId: WORKSPACE_ID,
          name: "",
        })
      ).rejects.toThrow();
    });

    it("Given name exceeds 80 chars, When user creates channel, Then validation error is thrown", async () => {
      const { supabase } = createMockSupabase();
      const caller = appRouter.createCaller({ userId: USER_ID, supabase });

      await expect(
        caller.channel.create({
          workspaceId: WORKSPACE_ID,
          name: "x".repeat(81),
        })
      ).rejects.toThrow();
    });
  });

  describe("Scenario: Empty workspace has no channels", () => {
    it("Given a new workspace, When user lists channels, Then the list is empty", async () => {
      const { supabase, mockResult } = createMockSupabase();
      mockResult([]);

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });
      const channels = await caller.channel.list({
        workspaceId: WORKSPACE_ID,
      });

      expect(channels).toHaveLength(0);
    });
  });

  describe("Scenario: Channel not found", () => {
    it("Given nonexistent channel slug, When user navigates to it, Then error is thrown", async () => {
      const { supabase, mockError } = createMockSupabase();
      mockError("Row not found");

      const caller = appRouter.createCaller({ userId: USER_ID, supabase });

      await expect(
        caller.channel.getBySlug({
          workspaceId: WORKSPACE_ID,
          slug: "nonexistent",
        })
      ).rejects.toThrow("Channel not found");
    });
  });
});
