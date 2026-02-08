import { z } from 'zod';

export const createMessageSchema = z.object({
  threadId: z.string().uuid(),
  diveId: z.string().uuid().optional(),
  content: z.string().min(1).max(50000),
});

export const createChannelSchema = z.object({
  workspaceId: z.string().uuid(),
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  isPrivate: z.boolean().optional().default(false),
});

export const createDiveSchema = z.object({
  threadId: z.string().uuid(),
  parentMessageId: z.string().uuid(),
  topic: z.string().max(200).optional(),
});

export const publishDiveSchema = z.object({
  diveId: z.string().uuid(),
});
