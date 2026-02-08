import { describe, it, expect } from "vitest";
import { router, publicProcedure, protectedProcedure } from "../trpc";
import { createMockSupabase } from "../__test__/mock-supabase";

// Build a minimal test router to verify middleware behavior
const testRouter = router({
  publicEndpoint: publicProcedure.query(() => "public-ok"),
  protectedEndpoint: protectedProcedure.query(({ ctx }) => ({
    userId: ctx.userId,
  })),
});

describe("tRPC middleware", () => {
  describe("publicProcedure", () => {
    it("allows unauthenticated access", async () => {
      const { supabase } = createMockSupabase();
      const caller = testRouter.createCaller({ userId: null, supabase });
      const result = await caller.publicEndpoint();
      expect(result).toBe("public-ok");
    });

    it("allows authenticated access", async () => {
      const { supabase } = createMockSupabase();
      const caller = testRouter.createCaller({
        userId: "user-1",
        supabase,
      });
      const result = await caller.publicEndpoint();
      expect(result).toBe("public-ok");
    });
  });

  describe("protectedProcedure", () => {
    it("allows authenticated access and passes userId in ctx", async () => {
      const { supabase } = createMockSupabase();
      const caller = testRouter.createCaller({
        userId: "user-1",
        supabase,
      });
      const result = await caller.protectedEndpoint();
      expect(result).toEqual({ userId: "user-1" });
    });

    it("rejects unauthenticated access", async () => {
      const { supabase } = createMockSupabase();
      const caller = testRouter.createCaller({ userId: null, supabase });
      await expect(caller.protectedEndpoint()).rejects.toThrow("Unauthorized");
    });
  });
});
