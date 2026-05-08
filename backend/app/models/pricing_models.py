from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .pricing_models import PricingPlan

class PricingPlanBase(SQLModel):
    name: str = Field(sa_column_kwargs={"unique": True}, nullable=False)
    max_translation_count: int = Field(nullable=False)
    price_for_max_translation_per_counts: int = Field(nullable=False)
    description: str = Field(nullable=False)
    is_active: bool = Field(default=True)

class PricingPlan(PricingPlanBase, table=True):
    __tablename__ = "pricing_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UsageRecordBase(SQLModel):
    translation_count: int = Field(default=0)
    reset_date: Optional[datetime] = Field(default=None)

class UsageRecord(UsageRecordBase, table=True):
    __tablename__ = "usage_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional["User"] = Relationship(back_populates="usage_records")

class UserSubscriptionBase(SQLModel):
    status: str = Field(default="active")
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = Field(default=None)

class UserSubscription(UserSubscriptionBase, table=True):
    __tablename__ = "user_subscriptions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    pricing_plan_id: int = Field(foreign_key="pricing_plans.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional["User"] = Relationship(back_populates="subscriptions")
    pricing_plan: Optional["PricingPlan"] = Relationship()