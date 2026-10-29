/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Transpile the workspace package consumed as TypeScript source.
  transpilePackages: ["@stdevsec/shared-contracts"],
};

export default nextConfig;
