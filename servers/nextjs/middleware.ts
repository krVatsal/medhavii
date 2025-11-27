import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Proxy static assets (icons, images, fonts, exports) to FastAPI during development
  if (
    pathname.startsWith('/static/') ||
    pathname.startsWith('/exports/') ||
    pathname.startsWith('/app_data/fonts/')
  ) {
    // Rewrite to FastAPI backend
    const fastApiUrl = new URL(pathname, 'http://localhost:8000');
    fastApiUrl.search = request.nextUrl.search; // Preserve query params
    
    return NextResponse.rewrite(fastApiUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match static assets that should be proxied to FastAPI
    '/static/:path*',
    '/exports/:path*',
    '/app_data/fonts/:path*',
  ],
};
