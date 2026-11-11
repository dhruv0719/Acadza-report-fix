/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const rawUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL;
    let target = (rawUrl || '').trim();

    if (!target) {
      target =
        process.env.NODE_ENV === 'production'
          ? 'https://acadza-report-fix.onrender.com/api'
          : 'http://127.0.0.1:8000/api';
    }

    // Strip trailing /api and slashes to isolate the backend origin base
    const base = target.replace(/\/api\/?$/, '').replace(/\/+$/, '');

    return [
      {
        source: '/api/:path*',
        destination: `${base}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
