"use client";

import { create } from "zustand";

interface WorkspaceState {
  workspaceId: string | null;
  workspaceName: string | null;
  setWorkspace: (id: string, name: string) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspaceId: null,
  workspaceName: null,
  setWorkspace: (id, name) => set({ workspaceId: id, workspaceName: name }),
}));
