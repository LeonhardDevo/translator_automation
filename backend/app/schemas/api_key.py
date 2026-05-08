from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GeminiApiKeyBase(BaseModel):
    key: str
    description: Optional[str] = None
    is_active: bool = True


class GeminiApiKeyCreate(GeminiApiKeyBase):
    pass


class GeminiApiKeyUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None


class GeminiApiKey(GeminiApiKeyBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0

    class Config:
        from_attributes = True


class GeminiApiKeyUsage(BaseModel):
    id: int
    key_preview: str
    description: Optional[str]
    is_active: bool
    usage_count: int
    last_used: Optional[datetime]
    created_at: datetime