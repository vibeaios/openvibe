"use client";

interface ThreadPanelProps {
  open?: boolean;
  onClose?: () => void;
}

export function ThreadPanel({ open = false, onClose }: ThreadPanelProps) {
  if (!open) return null;

  return (
    <aside className="flex w-96 flex-col border-l border-border bg-background">
      {/* Thread header */}
      <div className="flex h-12 items-center justify-between border-b border-border px-4">
        <h2 className="text-sm font-semibold text-foreground">Thread</h2>
        <button
          onClick={onClose}
          className="rounded p-1 text-secondary transition-colors hover:bg-hover hover:text-foreground"
          aria-label="Close thread"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 4L4 12M4 4l8 8"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>

      {/* Thread content placeholder */}
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">No thread selected</p>
      </div>
    </aside>
  );
}
