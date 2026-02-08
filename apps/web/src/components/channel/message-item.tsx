"use client";

import clsx from "clsx";

interface MessageItemProps {
  id: string;
  content: string;
  authorName: string | null;
  authorType: string;
  avatarUrl?: string | null;
  createdAt: string;
}

export function MessageItem({
  content,
  authorName,
  authorType,
  createdAt,
}: MessageItemProps) {
  const time = new Date(createdAt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const displayName = authorName ?? "Unknown";
  const isAgent = authorType === "agent";

  return (
    <div
      className={clsx(
        "group flex gap-3 px-4 py-2 transition-colors hover:bg-hover",
        isAgent && "bg-agent"
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-medium",
          isAgent
            ? "bg-primary-muted text-primary"
            : "bg-elevated text-foreground"
        )}
      >
        {isAgent ? "AI" : displayName.charAt(0).toUpperCase()}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold text-foreground">
            {displayName}
          </span>
          {isAgent && (
            <span className="rounded bg-primary-muted px-1.5 py-0.5 text-[10px] font-medium text-primary">
              BOT
            </span>
          )}
          <span className="text-xs text-secondary">{time}</span>
        </div>
        <div className="mt-0.5 whitespace-pre-wrap text-sm leading-relaxed text-foreground">
          {content}
        </div>
      </div>
    </div>
  );
}
