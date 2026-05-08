from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from ..database import get_session_context
from ..security import get_current_user, get_current_admin
from ..models.user import User
from ..models.pricing_models import PricingPlan, UserSubscription
from ..schemas.pricing_schemas import (
    User as UserSchema,
    PricingPlan as PricingPlanSchema,
    PricingPlanCreate,
    PricingPlanUpdate,
    UsageResponse,
    Token,
    SubscriptionCreate
)
from ..crud.pricing_crud import (
    get_user_by_email,
    get_pricing_plan,
    get_pricing_plans,
    create_pricing_plan,
    update_pricing_plan,
    delete_pricing_plan,
    get_usage_record,
    create_usage_record,
    increment_usage_count,
    reset_usage_count,
    get_user_subscription,
    create_user_subscription
)

router = APIRouter()

@router.get("/pricing-plans", response_model=List[PricingPlanSchema])
async def get_all_pricing_plans(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_session_context)
):
    """Get all pricing plans"""
    plans = get_pricing_plans(db, skip=skip, limit=limit, active_only=active_only)
    return plans

@router.post("/pricing-plans", response_model=PricingPlanSchema)
async def create_new_pricing_plan(
    plan: PricingPlanCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Create a new pricing plan (admin only)"""
    existing_plan = db.query(PricingPlan).filter(PricingPlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(status_code=400, detail="Pricing plan with this name already exists")
    
    new_plan = create_pricing_plan(db, plan)
    return new_plan

@router.put("/pricing-plans/{plan_id}", response_model=PricingPlanSchema)
async def update_existing_pricing_plan(
    plan_id: int,
    plan_update: PricingPlanUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Update an existing pricing plan (admin only)"""
    updated_plan = update_pricing_plan(db, plan_id, plan_update)
    if not updated_plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found")
    return updated_plan

@router.delete("/pricing-plans/{plan_id}")
async def delete_pricing_plan_endpoint(
    plan_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Delete a pricing plan (admin only)"""
    deleted_plan = delete_pricing_plan(db, plan_id)
    if not deleted_plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found")
    return {"message": "Pricing plan deleted successfully"}

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session_context)
):
    """Get current user's usage statistics"""
    subscription = get_user_subscription(db, current_user.id)
    if not subscription:
        free_plan = db.query(PricingPlan).filter(PricingPlan.name == "Free Trial").first()
        if not free_plan:
            free_plan = PricingPlan(
                name="Free Trial",
                max_translation_count=10,
                price_for_max_translation_per_counts=0,
                description="1-day free trial with limited translations",
                is_active=True
            )
            db.add(free_plan)
            db.commit()
    else:
        free_plan = db.query(PricingPlan).filter(PricingPlan.id == subscription.pricing_plan_id).first()
    
    current_usage = get_usage_record(db, current_user.id)
    
    if not current_usage:
        current_usage = create_usage_record(db, current_user.id)
    
    remaining = max(0, free_plan.max_translation_count - current_usage.translation_count)
    
    return UsageResponse(
        current_usage=current_usage.translation_count,
        limit=free_plan.max_translation_count,
        remaining=remaining,
        reset_date=current_usage.reset_date
    )

@router.post("/translate")
async def translate_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session_context)
):
    """Handle image translation with usage tracking"""
    current_usage = get_usage_record(db, current_user.id)
    subscription = get_user_subscription(db, current_user.id)
    
    if not subscription:
        user_plan = db.query(PricingPlan).filter(PricingPlan.name == "Free Trial").first()
        if not user_plan:
            user_plan = PricingPlan(
                name="Free Trial",
                max_translation_count=10,
                price_for_max_translation_per_counts=0,
                description="1-day free trial with limited translations",
                is_active=True
            )
            db.add(user_plan)
            db.commit()
    else:
        user_plan = db.query(PricingPlan).filter(PricingPlan.id == subscription.pricing_plan_id).first()
    
    if not current_usage:
        current_usage = create_usage_record(db, current_user.id)
    
    if current_usage.translation_count >= user_plan.max_translation_count:
        raise HTTPException(
            status_code=429,
            detail=f"Translation limit exceeded. You've used {current_usage.translation_count}/{user_plan.max_translation_count} translations."
        )
    
    updated_usage = increment_usage_count(db, current_user.id)
    
    return {
        "message": "Translation completed successfully",
        "translation_id": f"trans_{current_user.id}_{updated_usage.id}",
        "current_usage": updated_usage.translation_count,
        "remaining": user_plan.max_translation_count - updated_usage.translation_count
    }

@router.post("/select-plan/{plan_id}")
async def select_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session_context)
):
    """Allow user to select a pricing plan"""
    plan = db.query(PricingPlan).filter(PricingPlan.id == plan_id).filter(PricingPlan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found or inactive")
    
    existing_subscription = get_user_subscription(db, current_user.id)
    
    new_subscription = create_user_subscription(
        db,
        current_user.id,
        SubscriptionCreate(pricing_plan_id=plan_id, status="pending_payment")
    )
    
    return {
        "message": "Plan selected successfully. Waiting for admin approval.",
        "plan_name": plan.name,
        "status": "pending_payment"
    }

@router.get("/admin/purchase-requests")
async def get_purchase_requests(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Get all purchase requests (admin only)"""
    all_subscriptions = db.query(UserSubscription).order_by(
        UserSubscription.created_at.desc()
    ).all()
    
    results = []
    for subscription in all_subscriptions:
        user = db.query(User).filter(User.id == subscription.user_id).first()
        plan = db.query(PricingPlan).filter(PricingPlan.id == subscription.pricing_plan_id).first()
        
        if user and plan:
            results.append({
                "subscription_id": subscription.id,
                "user_id": user.id,
                "user_email": user.email,
                "plan_id": plan.id,
                "plan_name": plan.name,
                "request_date": subscription.created_at.isoformat() + "Z",
                "status": subscription.status
            })
    
    return results

@router.post("/admin/approve-subscription/{subscription_id}")
async def approve_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Approve a subscription request after payment verification (admin only)"""
    subscription = db.query(UserSubscription).filter(UserSubscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription request not found")
    
    if subscription.status != "pending_payment":
        raise HTTPException(status_code=400, detail="Subscription is not in pending payment status")
    
    subscription.status = "active"
    subscription.start_date = datetime.utcnow()
    subscription.end_date = subscription.start_date + timedelta(days=3650)
    
    active_subs = db.query(UserSubscription).filter(
        UserSubscription.user_id == subscription.user_id,
        UserSubscription.id != subscription_id,
        UserSubscription.status == "active"
    ).all()
    for sub in active_subs:
        sub.status = "superseded"

    db.commit()
    
    reset_usage_count(db, subscription.user_id)
    
    return {
        "message": "Subscription approved successfully",
        "subscription_id": subscription.id,
        "status": subscription.status
    }

@router.post("/admin/reject-subscription/{subscription_id}")
async def reject_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Reject a subscription request (admin only)"""
    subscription = db.query(UserSubscription).filter(UserSubscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription request not found")
    
    if subscription.status != "pending_payment":
        raise HTTPException(status_code=400, detail="Subscription is not in pending payment status")
    
    subscription.status = "rejected"
    
    db.commit()
    
    return {
        "message": "Subscription request rejected",
        "subscription_id": subscription.id,
        "status": subscription.status
    }

@router.get("/admin/users/{user_id}/usage")
async def get_user_usage(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Get specific user's usage (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from ..crud.pricing_crud import get_usage_records
    usage_records = get_usage_records(db, user_id)
    
    subscription = get_user_subscription(db, user_id)
    if subscription:
        plan = db.query(PricingPlan).filter(PricingPlan.id == subscription.pricing_plan_id).first()
    else:
        plan = None
    
    return {
        "user": user,
        "current_plan": plan,
        "usage_history": usage_records,
        "subscription_status": subscription.status if subscription else "none"
    }

@router.post("/admin/users/{user_id}/adjust-limit")
async def adjust_user_limit(
    user_id: int,
    new_limit: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Adjust a user's translation limit (admin only)"""
    custom_plan_name = f"Custom-{user_id}"
    pricing_plan = db.query(PricingPlan).filter(PricingPlan.name == custom_plan_name).first()
    
    if not pricing_plan:
        custom_plan = PricingPlan(
            name=custom_plan_name,
            max_translation_count=new_limit,
            price_for_max_translation_per_counts=0,  
            description=f"Custom plan for user {user_id}",
            is_active=True
        )
        db.add(custom_plan)
        db.commit()
        pricing_plan = custom_plan
    else:
        pricing_plan.max_translation_count = new_limit
        db.commit()
    
    from ..schemas.pricing_schemas import SubscriptionCreate
    from ..crud.pricing_crud import update_user_subscription
    
    subscription = get_user_subscription(db, user_id)
    if subscription:
        subscription.status = "superseded"
        db.commit()
    
    new_subscription = create_user_subscription(
        db,
        user_id,
        SubscriptionCreate(pricing_plan_id=pricing_plan.id, status="active")
    )
    
    return {"message": f"User limit adjusted to {new_limit}"}

@router.get("/admin/pricing-analytics")
async def get_pricing_analytics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_session_context)
):
    """Get analytics about pricing plans and usage (admin only)"""
    from sqlalchemy import func
    
    total_users = db.query(User).count()
    
    active_users = db.query(User).filter(User.is_active == True).count()
    
    subscription_stats = db.query(
        UserSubscription.status,
        func.count(UserSubscription.id).label('count')
    ).group_by(UserSubscription.status).all()
    
    plan_stats = db.query(
        PricingPlan.name,
        func.count(UserSubscription.id).label('subscriber_count')
    ).join(UserSubscription, PricingPlan.id == UserSubscription.pricing_plan_id).group_by(PricingPlan.name).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "subscription_status_breakdown": [
            {"status": stat[0], "count": stat[1]} for stat in subscription_stats
        ],
        "plan_breakdown": [
            {"plan_name": stat[0], "subscribers": stat[1]} for stat in plan_stats
        ]
    }