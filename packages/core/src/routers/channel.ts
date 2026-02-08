import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const channelRouter = router({
  list: protectedProcedure
    .input(z.object({ workspaceId: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const { data, error } = await ctx.supabase
        .from("channels")
        .select("id, workspace_id, name, description, is_private, created_by, created_at")
        .eq("workspace_id", input.workspaceId)
        .order("name", { ascending: true });

      if (error) throw new Error(`Failed to list channels: ${error.message}`);

      return (data ?? []).map((c: any) => ({
        id: c.id,
        workspaceId: c.workspace_id,
        name: c.name,
        description: c.description,
        isPrivate: c.is_private,
        createdBy: c.created_by,
        createdAt: c.created_at,
      }));
    }),

  getBySlug: protectedProcedure
    .input(
      z.object({
        workspaceId: z.string().uuid(),
        slug: z.string(),
      })
    )
    .query(async ({ ctx, input }) => {
      const { data, error } = await ctx.supabase
        .from("channels")
        .select("id, workspace_id, name, description, is_private, created_by, created_at")
        .eq("workspace_id", input.workspaceId)
        .eq("name", input.slug)
        .single();

      if (error) throw new Error(`Channel not found: ${error.message}`);

      return {
        id: data.id,
        workspaceId: data.workspace_id,
        name: data.name,
        description: data.description,
        isPrivate: data.is_private,
        createdBy: data.created_by,
        createdAt: data.created_at,
      };
    }),

  create: protectedProcedure
    .input(
      z.object({
        workspaceId: z.string().uuid(),
        name: z.string().min(1).max(80),
        description: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { data, error } = await ctx.supabase
        .from("channels")
        .insert({
          workspace_id: input.workspaceId,
          name: input.name,
          description: input.description ?? null,
          created_by: ctx.userId,
        })
        .select("id, workspace_id, name, description, is_private, created_by, created_at")
        .single();

      if (error) throw new Error(`Failed to create channel: ${error.message}`);

      return {
        id: data.id,
        workspaceId: data.workspace_id,
        name: data.name,
        description: data.description,
        isPrivate: data.is_private,
        createdBy: data.created_by,
        createdAt: data.created_at,
      };
    }),
});
