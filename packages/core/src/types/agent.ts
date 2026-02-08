import { z } from 'zod';

export const TaskStatus = z.enum(['queued', 'running', 'completed', 'failed']);
export type TaskStatus = z.infer<typeof TaskStatus>;

export const TaskType = z.enum(['message_response', 'dive_publish', 'thread_summary']);
export type TaskType = z.infer<typeof TaskType>;

export interface AgentConfig {
  id: string;
  workspaceId: string;
  name: string;
  slug: string;
  displayName: string;
  description: string | null;
  model: string;
  systemPrompt: string | null;
  capabilities: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AgentTask {
  id: string;
  workspaceId: string;
  threadId: string | null;
  diveId: string | null;
  triggerMessageId: string | null;
  agentConfigId: string;
  status: TaskStatus;
  taskType: TaskType;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  tokenUsage: { input_tokens?: number; output_tokens?: number; model?: string };
  retryCount: number;
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
}
