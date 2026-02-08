"use client";

import { useEffect, useRef } from "react";
import { trpc } from "@/lib/trpc";
import { createClient } from "@/lib/supabase/client";
import { MessageItem } from "./message-item";

interface MessageListProps {
  channelId: string;
}

export function MessageList({ channelId }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const utils = trpc.useUtils();

  const { data, isLoading } = trpc.message.list.useQuery({
    channelId,
    limit: 50,
  });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data?.messages?.length]);

  // Supabase Realtime subscription for live updates
  useEffect(() => {
    const supabase = createClient();

    const realtimeChannel = supabase
      .channel(`channel-messages:${channelId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
        },
        () => {
          utils.message.list.invalidate({ channelId });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(realtimeChannel);
    };
  }, [channelId, utils]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading messages...</p>
      </div>
    );
  }

  const messages = data?.messages ?? [];

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">
          No messages yet. Start the conversation!
        </p>
      </div>
    );
  }

  // Messages come newest-first from API, reverse for display
  const displayMessages = [...messages].reverse();

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <div className="mt-auto">
        {displayMessages.map((msg) => (
          <MessageItem
            key={msg.id}
            id={msg.id}
            content={msg.content}
            authorName={msg.author?.name ?? null}
            authorType={msg.authorType}
            avatarUrl={msg.author?.avatarUrl ?? null}
            createdAt={msg.createdAt}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
