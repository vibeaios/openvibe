import { z } from 'zod';

export const MemberRole = z.enum(['admin', 'member']);
export type MemberRole = z.infer<typeof MemberRole>;

export interface User {
  id: string;
  email: string;
  name: string | null;
  avatarUrl: string | null;
  createdAt: string;
  lastActiveAt: string | null;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  ownerId: string;
  settings: Record<string, unknown>;
  createdAt: string;
}

export interface WorkspaceMember {
  workspaceId: string;
  userId: string;
  role: MemberRole;
  joinedAt: string;
}
