import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const diveRouter = router({
  create: protectedProcedure
    .input(
      z.object({
        sourceMessageId: z.string().uuid(),
        title: z.string().min(1).max(200),
      })
    )
    .mutation(async ({ input }) => {
      // TODO: Sprint 3
      return null;
    }),

  list: protectedProcedure
    .input(z.object({ channelId: z.string().uuid() }))
    .query(async ({ input }) => {
      // TODO: Sprint 3
      return [];
    }),

  publish: protectedProcedure
    .input(z.object({ diveId: z.string().uuid() }))
    .mutation(async ({ input }) => {
      // TODO: Sprint 3
      return null;
    }),
});
