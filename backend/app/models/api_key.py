from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class GeminiApiKey(SQLModel, table=True):
    __tablename__ = "gemini_api_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    last_used: Optional[datetime] = Field(default=None)
    usage_count: int = Field(default=0)