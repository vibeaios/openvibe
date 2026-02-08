export interface UIConfig {
  id: string;
  workspaceId: string;
  configKey: string;
  configValue: Record<string, unknown>;
  updatedAt: string;
}

export interface ContextItem {
  id: string;
  workspaceId: string;
  type: 'discovery' | 'decision' | 'status' | 'note' | 'thread_summary';
  title: string;
  content: string;
  summary: string | null;
  scope: 'task' | 'thread' | 'channel' | 'global';
  relevanceTags: string[];
  sourceRuntime: string | null;
  sourceThreadId: string | null;
  sourceTaskId: string | null;
  createdAt: string;
  expiresAt: string | null;
}
