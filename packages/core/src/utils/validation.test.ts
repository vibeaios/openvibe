import { describe, it, expect } from "vitest";
import {
  createMessageSchema,
  createChannelSchema,
  createDiveSchema,
  publishDiveSchema,
} from "./validation";

describe("createMessageSchema", () => {
  const validUUID = "550e8400-e29b-41d4-a716-446655440000";

  it("accepts valid input", () => {
    const result = createMessageSchema.safeParse({
      threadId: validUUID,
      content: "Hello world",
    });
    expect(result.success).toBe(true);
  });

  it("rejects missing threadId", () => {
    const result = createMessageSchema.safeParse({ content: "Hello" });
    expect(result.success).toBe(false);
  });

  it("rejects invalid threadId (not UUID)", () => {
    const result = createMessageSchema.safeParse({
      threadId: "not-a-uuid",
      content: "Hello",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty content", () => {
    const result = createMessageSchema.safeParse({
      threadId: validUUID,
      content: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects content over 50000 chars", () => {
    const result = createMessageSchema.safeParse({
      threadId: validUUID,
      content: "a".repeat(50001),
    });
    expect(result.success).toBe(false);
  });

  it("accepts content at 50000 chars", () => {
    const result = createMessageSchema.safeParse({
      threadId: validUUID,
      content: "a".repeat(50000),
    });
    expect(result.success).toBe(true);
  });

  it("accepts optional diveId", () => {
    const result = createMessageSchema.safeParse({
      threadId: validUUID,
      diveId: validUUID,
      content: "Hello",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid diveId", () => {
    const result = createMessageSchema.safeParse({
      threadId: validUUID,
      diveId: "not-uuid",
      content: "Hello",
    });
    expect(result.success).toBe(false);
  });
});

describe("createChannelSchema", () => {
  const validUUID = "550e8400-e29b-41d4-a716-446655440000";

  it("accepts valid input", () => {
    const result = createChannelSchema.safeParse({
      workspaceId: validUUID,
      name: "general",
    });
    expect(result.success).toBe(true);
  });

  it("defaults isPrivate to false", () => {
    const result = createChannelSchema.safeParse({
      workspaceId: validUUID,
      name: "general",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.isPrivate).toBe(false);
    }
  });

  it("rejects empty name", () => {
    const result = createChannelSchema.safeParse({
      workspaceId: validUUID,
      name: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects name over 100 chars", () => {
    const result = createChannelSchema.safeParse({
      workspaceId: validUUID,
      name: "a".repeat(101),
    });
    expect(result.success).toBe(false);
  });

  it("rejects description over 500 chars", () => {
    const result = createChannelSchema.safeParse({
      workspaceId: validUUID,
      name: "general",
      description: "a".repeat(501),
    });
    expect(result.success).toBe(false);
  });

  it("accepts optional description", () => {
    const result = createChannelSchema.safeParse({
      workspaceId: validUUID,
      name: "general",
      description: "A general channel",
    });
    expect(result.success).toBe(true);
  });
});

describe("createDiveSchema", () => {
  const validUUID = "550e8400-e29b-41d4-a716-446655440000";

  it("accepts valid input", () => {
    const result = createDiveSchema.safeParse({
      threadId: validUUID,
      parentMessageId: validUUID,
    });
    expect(result.success).toBe(true);
  });

  it("accepts optional topic", () => {
    const result = createDiveSchema.safeParse({
      threadId: validUUID,
      parentMessageId: validUUID,
      topic: "Exploring alternative",
    });
    expect(result.success).toBe(true);
  });

  it("rejects topic over 200 chars", () => {
    const result = createDiveSchema.safeParse({
      threadId: validUUID,
      parentMessageId: validUUID,
      topic: "a".repeat(201),
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing threadId", () => {
    const result = createDiveSchema.safeParse({
      parentMessageId: validUUID,
    });
    expect(result.success).toBe(false);
  });
});

describe("publishDiveSchema", () => {
  const validUUID = "550e8400-e29b-41d4-a716-446655440000";

  it("accepts valid diveId", () => {
    const result = publishDiveSchema.safeParse({ diveId: validUUID });
    expect(result.success).toBe(true);
  });

  it("rejects invalid diveId", () => {
    const result = publishDiveSchema.safeParse({ diveId: "bad" });
    expect(result.success).toBe(false);
  });

  it("rejects missing diveId", () => {
    const result = publishDiveSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});
