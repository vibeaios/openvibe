import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const searchRouter = router({
  query: protectedProcedure
    .input(
      z.object({
        q: z.string().min(1),
        workspaceId: z.string().uuid(),
        limit: z.number().min(1).max(50).default(20),
      })
    )
    .query(async ({ input }) => {
      // TODO: Sprint 4
      return [];
    }),
});
