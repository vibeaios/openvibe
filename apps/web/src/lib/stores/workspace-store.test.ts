import { describe, it, expect, beforeEach } from "vitest";
import { useWorkspaceStore } from "./workspace-store";

describe("useWorkspaceStore", () => {
  beforeEach(() => {
    // Reset store to initial state between tests
    useWorkspaceStore.setState({
      workspaceId: null,
      workspaceName: null,
    });
  });

  it("has null initial state", () => {
    const state = useWorkspaceStore.getState();
    expect(state.workspaceId).toBeNull();
    expect(state.workspaceName).toBeNull();
  });

  it("sets workspace id and name", () => {
    useWorkspaceStore.getState().setWorkspace("ws-1", "Vibe");
    const state = useWorkspaceStore.getState();
    expect(state.workspaceId).toBe("ws-1");
    expect(state.workspaceName).toBe("Vibe");
  });

  it("overwrites previous workspace", () => {
    useWorkspaceStore.getState().setWorkspace("ws-1", "First");
    useWorkspaceStore.getState().setWorkspace("ws-2", "Second");
    const state = useWorkspaceStore.getState();
    expect(state.workspaceId).toBe("ws-2");
    expect(state.workspaceName).toBe("Second");
  });
});
