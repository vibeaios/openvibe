import type { AgentConfig, AgentTask } from '../types/agent';

export interface AgentRuntimeInput {
  task: AgentTask;
  config: AgentConfig;
  contextMessages: Array<{ role: string; content: string; authorType: string }>;
}

export interface AgentRuntimeOutput {
  content: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
}

export interface AgentRuntime {
  execute(input: AgentRuntimeInput): Promise<AgentRuntimeOutput>;
}
