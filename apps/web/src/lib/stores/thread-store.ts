"use client";

import { create } from "zustand";

interface ThreadState {
  openThreadId: string | null;
  openThread: (threadId: string) => void;
  closeThread: () => void;
}

export const useThreadStore = create<ThreadState>((set) => ({
  openThreadId: null,
  openThread: (threadId) => set({ openThreadId: threadId }),
  closeThread: () => set({ openThreadId: null }),
}));
