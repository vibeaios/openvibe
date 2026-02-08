// Strip `secure` flag in development (HTTP over LAN)
export function fixCookieOptions(
  options?: Record<string, unknown>
): Record<string, unknown> {
  if (process.env.NODE_ENV === "development" && options) {
    const { secure, ...rest } = options;
    return rest;
  }
  return options ?? {};
}
