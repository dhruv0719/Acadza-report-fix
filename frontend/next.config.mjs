/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL;
    if (backendUrl && !backendUrl.includes('127.0.0.1') && !backendUrl.includes('localhost')) {
      const base = backendUrl.replace(/\/api\/?$/, '');
      return [
        {
          source: '/api/:path*',
          destination: `${base}/api/:path*`,
        },
      ];
    }
    // In local development only, proxy to local FastAPI backend
    if (process.env.NODE_ENV !== 'production') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://127.0.0.1:8000/api/:path*',
        },
      ];
    }
    // In production without explicit backend proxy, let client fetch NEXT_PUBLIC_API_URL directly
    return [];
  },
};

export default nextConfig;
