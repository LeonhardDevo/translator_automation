from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
from ..models.user import User
from ..models.pricing_models import UsageRecord, PricingPlan, UserSubscription
from ..schemas.pricing_schemas import (
    UserCreate,
    UserUpdate,
    PricingPlanCreate,
    PricingPlanUpdate,
    SubscriptionCreate
)

def create_user(db: Session, user: UserCreate):
    from ..auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    free_plan = db.query(PricingPlan).filter(PricingPlan.id == 1).first()
    if free_plan:
        free_subscription = UserSubscription(
            user_id=db_user.id,
            pricing_plan_id=free_plan.id,
            status="active"
        )
        db.add(free_subscription)
        db.commit()
    
    create_usage_record(db, db_user.id)
    
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        for field, value in user_update.model_dump(exclude_unset=True).items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_pricing_plan(db: Session, plan_id: int):
    return db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()

def get_pricing_plan_by_name(db: Session, name: str):
    return db.query(PricingPlan).filter(PricingPlan.name == name).first()

def get_pricing_plans(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True):
    query = db.query(PricingPlan)
    if active_only:
        query = query.filter(PricingPlan.is_active == True)
    return query.offset(skip).limit(limit).all()

def create_pricing_plan(db: Session, plan: PricingPlanCreate):
    db_plan = PricingPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def update_pricing_plan(db: Session, plan_id: int, plan_update: PricingPlanUpdate):
    db_plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
    if db_plan:
        for field, value in plan_update.model_dump(exclude_unset=True).items():
            setattr(db_plan, field, value)
        db_plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_plan)
    return db_plan

def delete_pricing_plan(db: Session, plan_id: int):
    db_plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).first()
    if db_plan:
        db.delete(db_plan)
        db.commit()
    return db_plan

def get_usage_record(db: Session, user_id: int):
    return (
        db.query(UsageRecord)
        .filter(UsageRecord.user_id == user_id)
        .order_by(UsageRecord.created_at.desc())
        .first()
    )

def get_usage_records(db: Session, user_id: int):
    return db.query(UsageRecord).filter(UsageRecord.user_id == user_id).all()

def create_usage_record(db: Session, user_id: int, reset_date: datetime = None):
    if reset_date is None:
        reset_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)
        reset_date = reset_date.replace(day=1)
    
    db_usage = UsageRecord(
        user_id=user_id,
        translation_count=0,
        reset_date=reset_date
    )
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage

def increment_usage_count(db: Session, user_id: int):
    usage_record = get_usage_record(db, user_id)
    if usage_record:
        usage_record.translation_count += 1
        db.commit()
        db.refresh(usage_record)
    return usage_record

def reset_usage_count(db: Session, user_id: int):
    usage_record = get_usage_record(db, user_id)
    if usage_record:
        usage_record.translation_count = 0
        db.commit()
        db.refresh(usage_record)
    return usage_record

def get_user_subscription(db: Session, user_id: int):
    return (
        db.query(UserSubscription)
        .filter(UserSubscription.user_id == user_id)
        .order_by(UserSubscription.created_at.desc())
        .first()
    )

def create_user_subscription(db: Session, user_id: int, subscription: SubscriptionCreate):
    db_subscription = UserSubscription(
        user_id=user_id,
        pricing_plan_id=subscription.pricing_plan_id,
        status=subscription.status
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def update_user_subscription(db: Session, user_id: int, status: str):
    subscription = get_user_subscription(db, user_id)
    if subscription:
        subscription.status = status
        db.commit()
        db.refresh(subscription)
    return subscription