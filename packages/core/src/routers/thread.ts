import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const threadRouter = router({
  getReplies: protectedProcedure
    .input(
      z.object({
        messageId: z.string().uuid(),
        cursor: z.string().optional(),
      })
    )
    .query(async ({ input }) => {
      // TODO: Sprint 2
      return { replies: [], nextCursor: null };
    }),
});
