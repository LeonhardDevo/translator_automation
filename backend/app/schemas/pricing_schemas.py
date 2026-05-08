from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    
    class Config:
        orm_mode = True

class UsageRecordBase(BaseModel):
    translation_count: int
    reset_date: Optional[datetime]

class UsageRecordCreate(UsageRecordBase):
    user_id: int

class UsageRecord(UsageRecordBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class PricingPlanBase(BaseModel):
    name: str
    max_translation_count: int
    price_for_max_translation_per_counts: int
    description: str
    is_active: Optional[bool] = True

class PricingPlanCreate(PricingPlanBase):
    pass

class PricingPlanUpdate(BaseModel):
    name: Optional[str] = None
    max_translation_count: Optional[int] = None
    price_for_max_translation_per_counts: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PricingPlan(PricingPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class UsageResponse(BaseModel):
    current_usage: int
    limit: int
    remaining: int
    reset_date: datetime

class SubscriptionBase(BaseModel):
    pricing_plan_id: int
    status: str

class SubscriptionCreate(SubscriptionBase):
    pass

class Subscription(SubscriptionBase):
    id: int
    user_id: int
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None