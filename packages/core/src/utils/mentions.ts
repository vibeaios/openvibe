const MENTION_REGEX = /@(\w+)/g;

export function parseMentions(content: string): string[] {
  const matches = content.matchAll(MENTION_REGEX);
  return [...matches].map(m => m[1].toLowerCase());
}

export function hasMention(content: string, slug: string): boolean {
  return parseMentions(content).includes(slug.toLowerCase());
}
