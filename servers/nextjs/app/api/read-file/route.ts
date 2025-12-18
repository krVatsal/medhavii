import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';


export async function POST(request: Request) {
  try {
    const { filePath } = await request.json();
    console.log('Attempting to read file:', filePath);

    if (!filePath) {
      return NextResponse.json({ error: 'File path is required' }, { status: 400 });
    }
   
      // Remove null bytes to prevent null byte injection attacks
      const sanitizedFilePath = filePath.replace(/\0/g, '');
      const normalizedPath = path.normalize(sanitizedFilePath);
      
      // Check if file exists before trying to resolve it
      if (!fs.existsSync(normalizedPath)) {
        console.error('File not found:', normalizedPath);
        return NextResponse.json({ error: 'File not found' }, { status: 404 });
      }

      const allowedBaseDirs = [
        process.env.APP_DATA_DIRECTORY || '/app/user_data',
        process.env.TEMP_DIRECTORY || '/tmp',
        '/app/user_data',
        '/tmp',
        'C:\\tmp',
        'C:\\temp'
      ];
      
      let resolvedPath;
      try {
        resolvedPath = fs.realpathSync(path.resolve(normalizedPath));
      } catch (e) {
        console.error('Error resolving path:', e);
        return NextResponse.json({ error: 'Invalid file path' }, { status: 400 });
      }
      
      const isPathAllowed = allowedBaseDirs.some(baseDir => {
        try {
          const resolvedBaseDir = fs.realpathSync(path.resolve(baseDir));
          // Check if the file is inside the base directory
          // We add a separator to ensure we don't match partial folder names (e.g. /tmp/foo matching /tmp/foobar)
          return resolvedPath.startsWith(resolvedBaseDir + path.sep) || resolvedPath === resolvedBaseDir;
        } catch (e) {
          // Directory doesn't exist, so it can't contain the file
          return false;
        }
      });

    if (!isPathAllowed) {
      console.error('Unauthorized file access attempt:', resolvedPath);
      return NextResponse.json(
        { error: 'Access denied: File path not allowed' },
        { status: 403 }
      );
    }
    const content=  fs.readFileSync(resolvedPath, 'utf-8');
    
    return NextResponse.json({ content });
  } catch (error) {
    console.error('Error reading file:', error);
    return NextResponse.json(
      { error: 'Failed to read file' },
      { status: 500 }
    );
  }
} 