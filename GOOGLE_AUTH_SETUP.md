# Google Authentication Setup Guide

This guide explains how to set up Google Authentication for your Medhavi application.

## Prerequisites

- Google Cloud Platform account
- Cloud PostgreSQL database configured

## Step 1: Create Google OAuth Credentials

### 1.1 Go to Google Cloud Console
Visit: https://console.cloud.google.com/apis/credentials

### 1.2 Create OAuth 2.0 Client ID
1. Click "Create Credentials" → "OAuth client ID"
2. Select "Web application"
3. Name it (e.g., "Medhavi Web App")
4. Add Authorized JavaScript origins:
   - `http://localhost:3000` (for development)
   - `https://yourdomain.com` (for production)
5. Add Authorized redirect URIs:
   - `http://localhost:3000` (for development)
   - `https://yourdomain.com` (for production)
6. Click "Create"
7. Copy the **Client ID** (you'll need this)

## Step 2: Run Database Migrations

Run both migration scripts on your cloud PostgreSQL database:

```bash
# First migration (binary storage)
psql "postgresql://username:password@your-host:5432/database" -f servers/fastapi/migrations/001_add_binary_storage.sql

# Second migration (authentication)
psql "postgresql://username:password@your-host:5432/database" -f servers/fastapi/migrations/002_add_authentication.sql
```

Or use your cloud provider's query console to run the SQL from both files.

## Step 3: Configure Backend (.env)

Edit `servers/fastapi/.env` and add:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://username:password@your-cloud-host:5432/your_database

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

**Important**: Generate a strong JWT secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Configure Frontend (.env.local)

Edit `servers/nextjs/.env.local` and add:

```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

Use the Client ID you copied from Google Cloud Console in Step 1.

## Step 5: Install Dependencies

### Backend:
```bash
cd servers/fastapi
pip install python-jose[cryptography] httpx
```

### Frontend:
```bash
cd servers/nextjs
npm install @react-oauth/google
```

## Step 6: Update auth_service.py

Edit `servers/fastapi/services/auth_service.py` and update:

```python
# Load from environment variables
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
```

## Step 7: Restart Your Application

```bash
# Backend
cd servers/fastapi
uvicorn server:app --reload

# Frontend
cd servers/nextjs
npm run dev
```

## Step 8: Test Authentication

1. Open your app in browser: `http://localhost:3000`
2. Click on any protected action (e.g., generate image)
3. Auth popup should appear
4. Click "Sign in with Google"
5. Complete Google OAuth flow
6. You should be logged in!

## How It Works

### Flow:
1. **User clicks login** → Google OAuth popup appears
2. **User authorizes** → Google returns ID token
3. **Frontend sends token** to backend `/api/v1/ppt/auth/google/login`
4. **Backend verifies token** with Google's tokeninfo API
5. **Backend creates/updates user** in database
6. **Backend generates JWT** for subsequent requests
7. **Frontend stores JWT** in localStorage
8. **Protected routes** require `Authorization: Bearer <token>` header

### Protected Endpoints:
- `/api/v1/ppt/images/generate` - Generate images (requires auth)
- `/api/v1/ppt/images/upload` - Upload images (requires auth)
- `/api/v1/ppt/images/uploaded` - Get user's uploaded images
- `/api/v1/ppt/images/generated` - Get user's generated images
- `/api/v1/ppt/videos/*` - All video endpoints (requires auth)
- `/api/v1/ppt/audio/*` - All audio endpoints (requires auth)

### Public Endpoints:
- `/api/v1/ppt/auth/google/login` - Login endpoint
- `/api/v1/ppt/images/{id}/data` - Serve image binary (no auth needed for now)
- `/api/v1/ppt/videos/{id}/data` - Serve video binary (no auth needed for now)

## Frontend Integration

### Wrap your app with AuthProvider:

```tsx
// app/layout.tsx or _app.tsx
import { AuthProvider } from "@/lib/auth-context";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

### Show auth popup when needed:

```tsx
"use client";
import { useState } from "react";
import { AuthPopup } from "@/components/AuthPopup";
import { useAuth } from "@/lib/auth-context";

export function MyComponent() {
  const [showAuthPopup, setShowAuthPopup] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();

  const handleGenerateImage = () => {
    if (!isAuthenticated) {
      setShowAuthPopup(true);
      return;
    }
    // Proceed with generation...
  };

  return (
    <>
      <button onClick={handleGenerateImage}>
        Generate Image
      </button>

      {isAuthenticated ? (
        <div>
          <img src={user.picture} alt={user.name} />
          <span>{user.name}</span>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={() => setShowAuthPopup(true)}>
          Sign In
        </button>
      )}

      <AuthPopup
        isOpen={showAuthPopup}
        onClose={() => setShowAuthPopup(false)}
        onLoginSuccess={(user) => {
          console.log("Logged in:", user);
        }}
      />
    </>
  );
}
```

### Make authenticated API requests:

```tsx
import { useAuth, getAuthHeaders } from "@/lib/auth-context";

const { token } = useAuth();

const response = await fetch("/api/v1/ppt/images/generate?prompt=sunset", {
  headers: {
    ...getAuthHeaders(token),
  },
});
```

## User Data Management

All media (images, videos, audio) is now linked to users:
- Each user only sees their own generated/uploaded content
- When a user is deleted, all their media is automatically deleted (CASCADE)
- User info includes: email, name, profile picture from Google

## Security Notes

1. **JWT Secret**: Use a strong, random secret key (min 32 characters)
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiry**: Default is 7 days, adjust as needed
4. **CORS**: Configure CORS properly for your domain
5. **Rate Limiting**: Consider adding rate limiting to auth endpoints

## Troubleshooting

### "Invalid Google token"
- Check your Google Client ID is correct
- Ensure authorized origins are configured in Google Console
- Token might be expired (they expire after 1 hour)

### "Invalid or expired token" (JWT)
- User needs to log in again
- Clear localStorage and retry
- Check JWT_SECRET_KEY matches between sessions

### "User not found"
- Database migration might not have run
- Check user table exists: `SELECT * FROM "user" LIMIT 1;`

### CORS errors
- Add frontend domain to FastAPI CORS middleware
- Check Authorization header is allowed in CORS

## Production Checklist

- [ ] Set strong JWT_SECRET_KEY (min 32 chars)
- [ ] Configure production Google OAuth redirect URIs
- [ ] Use HTTPS for all requests
- [ ] Set up proper CORS configuration
- [ ] Enable rate limiting on auth endpoints
- [ ] Set up monitoring for failed login attempts
- [ ] Configure session timeout appropriately
- [ ] Test with multiple users
- [ ] Verify data isolation between users
