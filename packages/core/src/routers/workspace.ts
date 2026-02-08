import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const workspaceRouter = router({
  list: protectedProcedure.query(async ({ ctx }) => {
    const { data, error } = await ctx.supabase
      .from("workspaces")
      .select(
        `
        id, name, slug, owner_id, settings, created_at,
        workspace_members!inner (user_id, role, joined_at)
        `
      )
      .eq("workspace_members.user_id", ctx.userId);

    if (error) throw new Error(`Failed to list workspaces: ${error.message}`);

    return (data ?? []).map((w: any) => ({
      id: w.id,
      name: w.name,
      slug: w.slug,
      ownerId: w.owner_id,
      settings: w.settings ?? {},
      createdAt: w.created_at,
    }));
  }),

  getById: protectedProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ ctx, input }) => {
      const { data, error } = await ctx.supabase
        .from("workspaces")
        .select(
          `
          id, name, slug, owner_id, settings, created_at,
          workspace_members!inner (user_id, role, joined_at)
          `
        )
        .eq("id", input.id)
        .eq("workspace_members.user_id", ctx.userId)
        .single();

      if (error) throw new Error(`Workspace not found: ${error.message}`);

      return {
        id: data.id,
        name: data.name,
        slug: data.slug,
        ownerId: data.owner_id,
        settings: data.settings ?? {},
        createdAt: data.created_at,
      };
    }),

  create: protectedProcedure
    .input(
      z.object({
        name: z.string().min(1).max(100),
        slug: z.string().min(1).max(100),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Ensure user record exists (mirrors auth.users)
      const { error: userError } = await ctx.supabase
        .from("users")
        .upsert(
          { id: ctx.userId, email: "" },
          { onConflict: "id", ignoreDuplicates: true }
        );

      if (userError)
        throw new Error(`Failed to ensure user record: ${userError.message}`);

      // Create workspace
      const { data: workspace, error: wsError } = await ctx.supabase
        .from("workspaces")
        .insert({
          name: input.name,
          slug: input.slug,
          owner_id: ctx.userId,
        })
        .select("id, name, slug, owner_id, settings, created_at")
        .single();

      if (wsError)
        throw new Error(`Failed to create workspace: ${wsError.message}`);

      // Add creator as admin member
      const { error: memberError } = await ctx.supabase
        .from("workspace_members")
        .insert({
          workspace_id: workspace.id,
          user_id: ctx.userId,
          role: "admin",
        });

      if (memberError)
        throw new Error(
          `Failed to add workspace member: ${memberError.message}`
        );

      // Seed default agents (@Vibe, @Coder) for the new workspace.
      // Non-blocking: workspace creation succeeds even if seeding fails.
      try {
        await ctx.supabase.rpc("seed_workspace_agents", {
          ws_id: workspace.id,
        });
      } catch {
        // Agent seeding is best-effort; log but don't fail workspace creation
      }

      return {
        id: workspace.id,
        name: workspace.name,
        slug: workspace.slug,
        ownerId: workspace.owner_id,
        settings: workspace.settings ?? {},
        createdAt: workspace.created_at,
      };
    }),
});
