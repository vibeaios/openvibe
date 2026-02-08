import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: [
    "@openvibe/core",
    "@openvibe/db",
    "@openvibe/ui",
    "@openvibe/thread-engine",
    "@openvibe/agent-runtime",
    "@openvibe/auth",
    "@openvibe/config",
  ],
};

export default nextConfig;
