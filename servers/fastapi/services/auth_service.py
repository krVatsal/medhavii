"""
Authentication service for Google OAuth and JWT token management
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.sql.user import User
from utils.datetime_utils import get_current_utc_datetime


# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # Should be in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class AuthService:
    """Service for handling authentication"""
    
    @staticmethod
    def create_access_token(user_id: uuid.UUID, email: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        google_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None
    ) -> User:
        """Get existing user or create new one from Google OAuth data"""
        # Try to find existing user
        result = await session.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update last login and info
            user.last_login = get_current_utc_datetime()
            user.name = name or user.name
            user.picture = picture or user.picture
            user.updated_at = get_current_utc_datetime()
        else:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
                last_login=get_current_utc_datetime()
            )
            session.add(user)
        
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return await session.get(User, user_id)
