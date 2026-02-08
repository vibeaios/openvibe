import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const agentRouter = router({
  list: protectedProcedure.query(async () => {
    // TODO: Sprint 2
    return [];
  }),

  invoke: protectedProcedure
    .input(
      z.object({
        agentId: z.string().uuid(),
        messageId: z.string().uuid(),
        channelId: z.string().uuid(),
      })
    )
    .mutation(async ({ input }) => {
      // TODO: Sprint 2
      return null;
    }),
});
