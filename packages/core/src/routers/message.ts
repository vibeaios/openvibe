import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const messageRouter = router({
  list: protectedProcedure
    .input(
      z.object({
        channelId: z.string().uuid(),
        cursor: z.string().optional(),
        limit: z.number().min(1).max(100).default(50),
      })
    )
    .query(async ({ ctx, input }) => {
      // Get root thread messages for a channel (one thread per top-level message).
      // We join threads -> messages where the message is the root of the thread,
      // then join the author info from users table.
      let query = ctx.supabase
        .from("messages")
        .select(
          `
          id, thread_id, dive_id, parent_id,
          author_id, author_type, content, metadata,
          created_at, updated_at,
          users!messages_author_id_fkey (id, name, avatar_url),
          threads!inner (id, channel_id)
          `
        )
        .eq("threads.channel_id", input.channelId)
        .is("parent_id", null)
        .order("created_at", { ascending: false })
        .limit(input.limit + 1); // fetch one extra to determine nextCursor

      if (input.cursor) {
        query = query.lt("created_at", input.cursor);
      }

      const { data, error } = await query;

      if (error)
        throw new Error(`Failed to list messages: ${error.message}`);

      const rows = data ?? [];
      const hasMore = rows.length > input.limit;
      const messages = rows.slice(0, input.limit).map((m: any) => ({
        id: m.id,
        threadId: m.thread_id,
        diveId: m.dive_id,
        parentId: m.parent_id,
        authorId: m.author_id,
        authorType: m.author_type,
        content: m.content,
        metadata: m.metadata ?? {},
        createdAt: m.created_at,
        updatedAt: m.updated_at,
        author: m.users
          ? {
              id: m.users.id,
              name: m.users.name,
              avatarUrl: m.users.avatar_url,
            }
          : null,
      }));

      return {
        messages,
        nextCursor: hasMore ? messages[messages.length - 1]?.createdAt ?? null : null,
      };
    }),

  send: protectedProcedure
    .input(
      z.object({
        channelId: z.string().uuid(),
        content: z.string().min(1),
        parentId: z.string().uuid().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      let threadId: string;

      if (input.parentId) {
        // Reply to existing message: find its thread
        const { data: parentMsg, error: parentError } = await ctx.supabase
          .from("messages")
          .select("thread_id")
          .eq("id", input.parentId)
          .single();

        if (parentError)
          throw new Error(`Parent message not found: ${parentError.message}`);

        threadId = parentMsg.thread_id;
      } else {
        // New top-level message: create a thread first
        const { data: thread, error: threadError } = await ctx.supabase
          .from("threads")
          .insert({
            channel_id: input.channelId,
            status: "active",
          })
          .select("id")
          .single();

        if (threadError)
          throw new Error(`Failed to create thread: ${threadError.message}`);

        threadId = thread.id;
      }

      // Insert the message
      const { data: message, error: msgError } = await ctx.supabase
        .from("messages")
        .insert({
          thread_id: threadId,
          parent_id: input.parentId ?? null,
          author_id: ctx.userId,
          author_type: "human",
          content: input.content,
        })
        .select(
          `
          id, thread_id, dive_id, parent_id,
          author_id, author_type, content, metadata,
          created_at, updated_at
          `
        )
        .single();

      if (msgError)
        throw new Error(`Failed to send message: ${msgError.message}`);

      // If this is a new top-level message, set it as the thread's root_message_id
      if (!input.parentId) {
        const { error: updateError } = await ctx.supabase
          .from("threads")
          .update({ root_message_id: message.id })
          .eq("id", threadId);

        if (updateError)
          throw new Error(
            `Failed to set root message on thread: ${updateError.message}`
          );
      }

      return {
        id: message.id,
        threadId: message.thread_id,
        diveId: message.dive_id,
        parentId: message.parent_id,
        authorId: message.author_id,
        authorType: message.author_type,
        content: message.content,
        metadata: message.metadata ?? {},
        createdAt: message.created_at,
        updatedAt: message.updated_at,
      };
    }),
});
