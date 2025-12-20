import { NextRequest, NextResponse } from 'next/server';

export const maxDuration = 300; // 5 minutes for Vercel/serverless
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward to FastAPI backend with extended timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes
    
    const response = await fetch('http://localhost:8000/api/v1/ppt/narration/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
      // @ts-ignore - Node.js fetch options
      keepalive: true,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: errorText || 'Narration generation failed' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error: any) {
    console.error('Narration proxy error:', error);
    
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Narration generation timed out after 5 minutes' },
        { status: 504 }
      );
    }
    
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
