"use client";

import { use } from "react";
import { trpc } from "@/lib/trpc";
import { useWorkspaceStore } from "@/lib/stores/workspace-store";
import { MessageList } from "@/components/channel/message-list";
import { MessageComposer } from "@/components/channel/message-composer";

interface ChannelPageProps {
  params: Promise<{ channelSlug: string }>;
}

export default function ChannelPage({ params }: ChannelPageProps) {
  const { channelSlug } = use(params);
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);

  const { data: channel, isLoading } = trpc.channel.getBySlug.useQuery(
    { workspaceId: workspaceId!, slug: channelSlug },
    { enabled: !!workspaceId }
  );

  if (!workspaceId || isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!channel) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Channel not found</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <MessageList channelId={channel.id} />
      <MessageComposer channelId={channel.id} channelName={channel.name} />
    </div>
  );
}
