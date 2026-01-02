from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from services.database import get_async_session
from services.auth_service import AuthService
from middlewares.auth_middleware import require_auth
import uuid


AUTH_ROUTER = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleLoginRequest(BaseModel):
    """Google OAuth login request"""
    id_token: str  # Google ID token from frontend


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    user: dict


@AUTH_ROUTER.post("/google/login", response_model=LoginResponse)
async def google_login(
    request: GoogleLoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user with Google OAuth
    Frontend sends Google ID token, we verify it and create/update user
    """
    try:
        # Verify Google ID token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={request.id_token}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            google_data = response.json()
        
        # Extract user info from Google token
        google_id = google_data.get("sub")
        email = google_data.get("email")
        name = google_data.get("name")
        picture = google_data.get("picture")
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data"
            )
        
        # Get or create user
        user = await AuthService.get_or_create_user(
            session=session,
            google_id=google_id,
            email=email,
            name=name,
            picture=picture
        )
        
        # Create access token
        access_token = AuthService.create_access_token(user.id, user.email)
        
        return LoginResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@AUTH_ROUTER.get("/me")
async def get_current_user_info(
    user_id: uuid.UUID = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current authenticated user info"""
    user = await AuthService.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    }


@AUTH_ROUTER.post("/logout")
async def logout():
    """Logout user (client should delete token)"""
    return JSONResponse(
        content={"message": "Logged out successfully"},
        status_code=200
    )
