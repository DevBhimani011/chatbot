import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Turbopack is default for 'next dev', but sometimes we need to be careful with config.
  // Removing experimental.turbo which causes build error.
};

export default nextConfig;
