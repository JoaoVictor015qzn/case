import type { NextConfig } from "next";

// Configuração do Next: build standalone para a imagem Docker.
const nextConfig: NextConfig = {
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
