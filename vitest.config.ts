import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    include: ["packages/**/*.test.ts", "apps/**/*.test.ts", "apps/**/*.test.tsx"],
    exclude: ["**/node_modules/**", "**/dist/**", "**/.next/**"],
    environment: "node",
  },
  resolve: {
    alias: {
      "@openvibe/core": path.resolve(__dirname, "packages/core/src/index.ts"),
      "@openvibe/db": path.resolve(__dirname, "packages/db/src/index.ts"),
    },
  },
});
