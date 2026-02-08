import { describe, it, expect, beforeEach } from "vitest";
import { useThreadStore } from "./thread-store";

describe("useThreadStore", () => {
  beforeEach(() => {
    useThreadStore.setState({ openThreadId: null });
  });

  it("has null initial openThreadId", () => {
    expect(useThreadStore.getState().openThreadId).toBeNull();
  });

  it("opens a thread", () => {
    useThreadStore.getState().openThread("thread-1");
    expect(useThreadStore.getState().openThreadId).toBe("thread-1");
  });

  it("closes a thread", () => {
    useThreadStore.getState().openThread("thread-1");
    useThreadStore.getState().closeThread();
    expect(useThreadStore.getState().openThreadId).toBeNull();
  });

  it("switches thread by opening a different one", () => {
    useThreadStore.getState().openThread("thread-1");
    useThreadStore.getState().openThread("thread-2");
    expect(useThreadStore.getState().openThreadId).toBe("thread-2");
  });

  it("closing already-closed thread is a no-op", () => {
    useThreadStore.getState().closeThread();
    expect(useThreadStore.getState().openThreadId).toBeNull();
  });
});
