"use client";

import { useState, useRef, useCallback } from "react";
import { trpc } from "@/lib/trpc";

interface MessageComposerProps {
  channelId: string;
  channelName: string;
}

export function MessageComposer({
  channelId,
  channelName,
}: MessageComposerProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const utils = trpc.useUtils();

  const sendMessage = trpc.message.send.useMutation({
    onSuccess: () => {
      setContent("");
      utils.message.list.invalidate({ channelId });
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    },
  });

  const handleSubmit = useCallback(() => {
    const trimmed = content.trim();
    if (!trimmed || sendMessage.isPending) return;
    sendMessage.mutate({ channelId, content: trimmed });
  }, [content, channelId, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <div className="border-t border-border px-4 py-3">
      <div className="flex items-end rounded-lg border border-divider bg-input px-3 py-2">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={`Message #${channelName}`}
          rows={1}
          className="max-h-[200px] flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
        />
        <button
          onClick={handleSubmit}
          disabled={!content.trim() || sendMessage.isPending}
          className="ml-2 rounded p-1 text-secondary transition-colors hover:text-foreground disabled:opacity-30"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19V5m0 0l-7 7m7-7l7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
