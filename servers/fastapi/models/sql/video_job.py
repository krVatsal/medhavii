"""Video generation job tracking model."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlmodel import Field, SQLModel


class VideoJobStatus(str, Enum):
    """Video generation job status."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    EMBEDDING = "EMBEDDING"
    EMBEDDED = "EMBEDDED"
    FAILED = "FAILED"


class VideoJob(SQLModel, table=True):
    """Track video generation jobs to prevent duplicates and loops."""
    
    __tablename__ = "video_jobs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    presentation_id: uuid.UUID = Field(index=True)
    
    slide_index: int = Field()
    
    video_path: str = Field()
    
    prompt: str = Field(sa_column=Column(Text))
    
    status: str = Field(default=VideoJobStatus.PENDING, index=True)
    
    video_asset_id: Optional[uuid.UUID] = Field(default=None)
    
    error_message: Optional[str] = Field(sa_column=Column(Text), default=None)
    
    created_at: datetime = Field(sa_column=Column(DateTime, default=datetime.utcnow))
    
    started_at: Optional[datetime] = Field(sa_column=Column(DateTime), default=None)
    
    completed_at: Optional[datetime] = Field(sa_column=Column(DateTime), default=None)
    
    retry_count: int = Field(default=0)
    
    max_retries: int = Field(default=3)
