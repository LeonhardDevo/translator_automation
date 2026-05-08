from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

if TYPE_CHECKING:
    from .pricing_models import UsageRecord, UserSubscription


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = True
    role: str = Field(default=UserRole.USER)
    daily_translation_count: int = Field(default=0)
    daily_translation_reset: datetime = Field(default_factory=datetime.utcnow)
    max_daily_translations: int = Field(default=100)
    max_daily_images: int = Field(default=10)
    account_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deactivated_at: Optional[datetime] = None
    cancelled_user_id: Optional[int] = Field(default=None)

    usage_records: list["UsageRecord"] = Relationship(back_populates="user")
    subscriptions: list["UserSubscription"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    max_daily_translations: Optional[int] = None
    max_daily_images: Optional[int] = None
    account_expires: Optional[datetime] = None


class UserPublic(UserBase):
    id: int
    is_active: bool
    role: str
    daily_translation_count: int
    max_daily_translations: int
    max_daily_images: int
    account_expires: Optional[datetime]
    created_at: datetime