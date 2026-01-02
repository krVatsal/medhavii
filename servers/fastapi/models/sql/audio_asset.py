from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import JSON, Column, DateTime, LargeBinary, ForeignKey
from sqlmodel import Field, SQLModel

from utils.datetime_utils import get_current_utc_datetime


class AudioAsset(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, default=get_current_utc_datetime
        ),
    )
    user_id: Optional[uuid.UUID] = Field(
        sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True),
        default=None
    )
    is_uploaded: bool = Field(default=False)
    path: Optional[str] = None  # Kept for backward compatibility, but deprecated
    binary_data: Optional[bytes] = Field(sa_column=Column(LargeBinary), default=None)
    filename: Optional[str] = None  # Store original filename
    content_type: Optional[str] = "audio/wav"  # MIME type (wav, mp3, etc.)
    file_size: Optional[int] = None  # Size in bytes
    language_code: Optional[str] = None  # For TTS audio
    extras: Optional[dict] = Field(sa_column=Column(JSON), default=None)
