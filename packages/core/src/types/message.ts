import { z } from 'zod';

export const AuthorType = z.enum(['human', 'agent', 'system']);
export type AuthorType = z.infer<typeof AuthorType>;

export const ThreadStatus = z.enum(['active', 'resolved', 'archived']);
export type ThreadStatus = z.infer<typeof ThreadStatus>;

export const DiveStatus = z.enum(['active', 'published', 'discarded']);
export type DiveStatus = z.infer<typeof DiveStatus>;

export interface Channel {
  id: string;
  workspaceId: string;
  name: string;
  description: string | null;
  isPrivate: boolean;
  createdBy: string;
  createdAt: string;
}

export interface Thread {
  id: string;
  channelId: string;
  rootMessageId: string | null;
  status: ThreadStatus;
  title: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Dive {
  id: string;
  threadId: string;
  parentMessageId: string;
  topic: string | null;
  status: DiveStatus;
  result: string | null;
  createdBy: string;
  createdAt: string;
  publishedAt: string | null;
}

export interface MessageAuthor {
  id: string;
  name: string | null;
  avatarUrl: string | null;
}

export interface Message {
  id: string;
  threadId: string;
  diveId: string | null;
  parentId: string | null;
  authorId: string;
  authorType: AuthorType;
  content: string;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface MessageWithAuthor extends Message {
  author: MessageAuthor | null;
}
