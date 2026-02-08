"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { trpc } from "@/lib/trpc";
import { useWorkspaceStore } from "@/lib/stores/workspace-store";

export function Sidebar() {
  const pathname = usePathname();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const workspaceName = useWorkspaceStore((s) => s.workspaceName);

  const { data: channels } = trpc.channel.list.useQuery(
    { workspaceId: workspaceId! },
    { enabled: !!workspaceId }
  );

  return (
    <aside className="flex w-60 flex-col border-r border-border bg-sidebar">
      {/* Workspace header */}
      <div className="flex h-12 items-center border-b border-border px-4">
        <h1 className="text-base font-semibold text-foreground">
          {workspaceName ?? "OpenVibe"}
        </h1>
      </div>

      {/* Channel list */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <div className="mb-2 px-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Channels
        </div>
        <ul className="space-y-0.5">
          {channels?.map((channel) => {
            const href = `/${channel.name}`;
            const isActive = pathname === href;

            return (
              <li key={channel.id}>
                <Link
                  href={href}
                  className={clsx(
                    "flex items-center rounded-md px-2 py-1.5 text-sm transition-colors",
                    isActive
                      ? "bg-sidebar-active-bg text-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-hover hover:text-foreground"
                  )}
                >
                  <span
                    className={clsx(
                      "mr-1.5 text-xs",
                      isActive ? "text-primary" : "text-muted-foreground"
                    )}
                  >
                    #
                  </span>
                  {channel.name}
                </Link>
              </li>
            );
          })}
          {!channels && (
            <li className="px-2 py-1.5 text-sm text-muted-foreground">Loading...</li>
          )}
        </ul>
      </nav>
    </aside>
  );
}
