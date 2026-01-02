from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from utils.datetime_utils import get_current_utc_datetime


class User(SQLModel, table=True):
    """User model for authentication and ownership tracking"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, default=get_current_utc_datetime
        ),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, default=get_current_utc_datetime, onupdate=get_current_utc_datetime
        ),
    )
    
    # Google OAuth fields
    google_id: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    email: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    name: Optional[str] = Field(sa_column=Column(String(255)), default=None)
    picture: Optional[str] = Field(sa_column=Column(String(500)), default=None)
    
    # Account status
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True)), default=None
    )
