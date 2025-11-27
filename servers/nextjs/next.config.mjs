
const nextConfig = {
  reactStrictMode: false,
  distDir: ".next-build",
  
  // Prevent Next from treating static assets as pages
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdx'],

  // Rewrites for development - proxy requests to FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/v1/ppt/:path*',
        destination: 'http://localhost:8000/api/v1/ppt/:path*',
      },
      {
        // Proxy static asset requests (icons, images) to FastAPI backend
        source: '/static/:path*',
        destination: 'http://localhost:8000/static/:path*',
      },
      {
        source: '/app_data/fonts/:path*',
        destination: 'http://localhost:8000/app_data/fonts/:path*',
      },
      {
        // Proxy exports directory for generated PDFs, narrations, etc
        source: '/exports/:path*',
        destination: 'http://localhost:8000/exports/:path*',
      },
    ];
  },

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "pub-7c765f3726084c52bcd5d180d51f1255.r2.dev",
      },
      {
        protocol: "https",
        hostname: "pptgen-public.ap-south-1.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "pptgen-public.s3.ap-south-1.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "img.icons8.com",
      },
      {
        protocol: "https",
        hostname: "present-for-me.s3.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "yefhrkuqbjcblofdcpnr.supabase.co",
      },
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "picsum.photos",
      },
      {
        protocol: "https",
        hostname: "unsplash.com",
      },
    ],
  },
  
};

export default nextConfig;
