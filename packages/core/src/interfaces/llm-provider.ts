export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMResponse {
  content: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
}

export interface LLMProvider {
  complete(messages: LLMMessage[], options?: { model?: string; maxTokens?: number }): Promise<LLMResponse>;
}
