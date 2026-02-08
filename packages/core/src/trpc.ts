import { initTRPC } from "@trpc/server";
import type { SupabaseClient } from "@supabase/supabase-js";

export type Context = {
  userId: string | null;
  supabase: SupabaseClient;
};

const t = initTRPC.context<Context>().create();

export const router = t.router;
export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(async ({ ctx, next }) => {
  if (!ctx.userId) {
    throw new Error("Unauthorized");
  }
  return next({
    ctx: { ...ctx, userId: ctx.userId, supabase: ctx.supabase },
  });
});
