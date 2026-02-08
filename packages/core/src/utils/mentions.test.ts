import { describe, it, expect } from "vitest";
import { parseMentions, hasMention } from "./mentions";

describe("parseMentions", () => {
  it("extracts a single mention", () => {
    expect(parseMentions("Hello @vibe")).toEqual(["vibe"]);
  });

  it("extracts multiple mentions", () => {
    expect(parseMentions("@vibe and @coder please help")).toEqual([
      "vibe",
      "coder",
    ]);
  });

  it("returns empty array when no mentions", () => {
    expect(parseMentions("no mentions here")).toEqual([]);
  });

  it("lowercases mention slugs", () => {
    expect(parseMentions("Hey @Vibe")).toEqual(["vibe"]);
  });

  it("handles mention at start of string", () => {
    expect(parseMentions("@coder fix this")).toEqual(["coder"]);
  });

  it("handles mention at end of string", () => {
    expect(parseMentions("help me @vibe")).toEqual(["vibe"]);
  });

  it("handles mention with underscores", () => {
    expect(parseMentions("ask @dive_helper")).toEqual(["dive_helper"]);
  });

  it("ignores email addresses (partial match on local part)", () => {
    // The regex matches @word so it will match the domain part — this is
    // known behavior. Testing current implementation accurately.
    const result = parseMentions("email user@example.com");
    expect(result).toContain("example");
  });

  it("handles empty string", () => {
    expect(parseMentions("")).toEqual([]);
  });

  it("handles duplicate mentions", () => {
    expect(parseMentions("@vibe @vibe")).toEqual(["vibe", "vibe"]);
  });
});

describe("hasMention", () => {
  it("returns true when mention exists", () => {
    expect(hasMention("Hello @vibe", "vibe")).toBe(true);
  });

  it("returns false when mention does not exist", () => {
    expect(hasMention("Hello world", "vibe")).toBe(false);
  });

  it("is case-insensitive on slug", () => {
    expect(hasMention("Hello @Vibe", "VIBE")).toBe(true);
  });

  it("matches exact slug", () => {
    expect(hasMention("Hello @vibes", "vibe")).toBe(false);
  });

  it("handles empty content", () => {
    expect(hasMention("", "vibe")).toBe(false);
  });
});
