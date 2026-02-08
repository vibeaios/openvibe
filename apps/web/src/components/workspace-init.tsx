"use client";

import { useEffect } from "react";
import { trpc } from "@/lib/trpc";
import { useWorkspaceStore } from "@/lib/stores/workspace-store";

export function WorkspaceInit() {
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);

  const { data: workspaces, error, isLoading } = trpc.workspace.list.useQuery();

  useEffect(() => {
    if (error) {
      console.error("[WorkspaceInit] Error fetching workspaces:", error.message);
      return;
    }
    if (!workspaces) return;

    if (workspaces.length > 0) {
      console.log("[WorkspaceInit] Found workspace:", workspaces[0].name, workspaces[0].id);
      setWorkspace(workspaces[0].id, workspaces[0].name);
      return;
    }

    console.log("[WorkspaceInit] No workspaces found, will not auto-create (seed data expected)");
  }, [workspaces, error]);

  if (error) {
    return (
      <div className="fixed bottom-4 right-4 z-50 rounded-lg bg-destructive/80 px-4 py-2 text-sm text-destructive-foreground">
        Auth error: {error.message}
      </div>
    );
  }

  return null;
}
