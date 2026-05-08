from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from ..database import get_session_context
from ..security import get_current_admin
from ..models.user import User
from ..models.document import Document
from ..models.api_key import GeminiApiKey
from ..models.pricing_models import UserSubscription, PricingPlan
from ..utils.logging_util import log_api_call, log_database_operation, log_error
import json
import secrets
import random
from datetime import timedelta
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()

class JWTConfigUpdate(BaseModel):
    access_token_expire_minutes: int = None
    refresh_token_expire_days: int = None
    max_concurrent_sessions: int = None
    enforce_strong_auth: bool = None

class JWTSessionInfo(BaseModel):
    current_access_token_expire_minutes: int
    current_refresh_token_expire_days: int
    current_max_concurrent_sessions: int
    enforce_strong_auth: bool
    total_active_sessions: int
    active_sessions: list

@router.get("/jwt-session-config")
def get_jwt_session_config(current_admin=Depends(get_current_admin)):
    """Get current JWT session configuration (admin only)"""
    from ..config import settings
    
    config = {
        "current_access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "current_refresh_token_expire_days": 30,
        "current_max_concurrent_sessions": 5,
        "enforce_strong_auth": False,
        "total_active_sessions": 0,
        "active_sessions": []
    }
    
    return config

@router.post("/jwt-session-config")
def update_jwt_session_config(config_update: JWTConfigUpdate, current_admin=Depends(get_current_admin)):
    """Update JWT session configuration (admin only)"""
    from ..config import settings
    
    updates = {}
    
    if config_update.access_token_expire_minutes is not None:
        updates["access_token_expire_minutes"] = config_update.access_token_expire_minutes
    
    if config_update.refresh_token_expire_days is not None:
        updates["refresh_token_expire_days"] = config_update.refresh_token_expire_days
    
    if config_update.max_concurrent_sessions is not None:
        updates["max_concurrent_sessions"] = config_update.max_concurrent_sessions
    
    if config_update.enforce_strong_auth is not None:
        updates["enforce_strong_auth"] = config_update.enforce_strong_auth
    
    return {
        "message": "JWT session configuration updated successfully",
        "updated_values": updates
    }

@router.get("/jwt-sessions")
def get_active_sessions(current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Get information about active JWT sessions (admin only)"""
    active_sessions = []
    
    return {
        "total_active_sessions": len(active_sessions),
        "sessions": active_sessions
    }

@router.post("/invalidate-user-sessions/{user_id}")
def invalidate_user_sessions(user_id: int, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Invalidate all sessions for a specific user (admin only)"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": f"All sessions invalidated for user {user.email}",
        "user_id": user_id
    }

@router.get("/users")
def get_all_users(current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)) -> List[dict]:
    """Get all users (admin only) with their usage and quota information"""
    try:
        log_api_call("/admin/users", "GET", current_admin.id, {}, 200)
        
        users = session.exec(select(User)).all()
        result = []
        for user in users:
            today = datetime.utcnow().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            daily_usage = session.exec(
                select(func.count(Document.id)).where(
                    Document.user_id == user.id,
                    Document.submitted_at >= start_of_day
                )
            ).one()
            
            total_usage = session.exec(
                select(func.count(Document.id)).where(Document.user_id == user.id)
            ).one()
            
            subscription = session.exec(
                select(UserSubscription).where(
                    UserSubscription.user_id == user.id,
                    UserSubscription.status == "active"
                ).order_by(UserSubscription.created_at.desc())
            ).first()
            
            plan_name = "No Plan"
            plan_total_limit = 0
            if subscription:
                plan = session.exec(
                    select(PricingPlan).where(PricingPlan.id == subscription.pricing_plan_id)
                ).first()
                if plan:
                    plan_name = plan.name
                    plan_total_limit = plan.max_translation_count
            
            result.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "daily_usage": daily_usage,
                "daily_limit": 500,
                "total_usage": total_usage,
                "plan_name": plan_name,
                "plan_total_limit": plan_total_limit,
                "account_expires": user.account_expires,
                "created_at": user.created_at,
                "deactivated_at": user.deactivated_at,
                "cancelled_user_id": user.cancelled_user_id
            })
        
        log_database_operation("read", "user", None, current_admin.id, True, None)
        return result
    except Exception as e:
        log_error("get_all_users", e, current_admin.id)
        raise

@router.post("/users")
def create_user(user_data: dict, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)) -> dict:
    """Create a new user (admin only)"""
    from ..security import hash_password
    
    try:
        log_api_call("/admin/users", "POST", current_admin.id, user_data, 200)
        
        if "email" not in user_data or not user_data["email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        if "password" not in user_data or not user_data["password"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
        
        existing_user = session.exec(select(User).where(User.email == user_data["email"])).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        try:
            hashed_password = hash_password(user_data["password"])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid password: {str(e)}"
            )
        
        user = User(
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            hashed_password=hashed_password,
            role=user_data.get("role", "user"),
            max_daily_translations=500,
            max_daily_images=500
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        from ..models.pricing_models import UserSubscription, PricingPlan
        from ..crud.pricing_crud import create_usage_record
        
        free_plan = session.exec(select(PricingPlan).where(PricingPlan.name == "Free Trial")).first()
        if not free_plan:
            free_plan = PricingPlan(
                name="Free Trial",
                max_translation_count=10,
                price_for_max_translation_per_counts=0,
                description="1-day free trial with limited translations",
                is_active=True
            )
            session.add(free_plan)
            session.commit()
            session.refresh(free_plan)
            
        free_subscription = UserSubscription(
            user_id=user.id,
            pricing_plan_id=free_plan.id,
            status="active"
        )
        session.add(free_subscription)
        session.commit()
        
        create_usage_record(session, user.id)
        
        log_database_operation("create", "user", user.id, current_admin.id, True, None)
        
        return {"id": user.id, "email": user.email, "full_name": user.full_name, "is_active": user.is_active}
    except Exception as e:
        log_error("create_user", e, current_admin.id, user_data)
        raise

@router.put("/users/{user_id}")
def update_user(user_id: int, user_update: dict, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)) -> dict:
    """Update a user (admin only) - allows modification of quotas and user info"""
    try:
        log_api_call(f"/admin/users/{user_id}", "PUT", current_admin.id, user_update, 200)
        
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if "full_name" in user_update:
            user.full_name = user_update["full_name"]
        if "email" in user_update:
            existing_user = session.exec(select(User).where(
                User.email == user_update["email"],
                User.id != user_id
            )).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken by another user"
                )
            user.email = user_update["email"]
        if "account_expires" in user_update:
            if user_update["account_expires"] == "" or user_update["account_expires"] is None:
                user.account_expires = None
            else:
                user.account_expires = user_update["account_expires"]
        if "is_active" in user_update:
            user.is_active = user_update["is_active"]
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        log_database_operation("update", "user", user.id, current_admin.id, True, None)
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "daily_limit": 500,
            "account_expires": user.account_expires,
            "cancelled_user_id": user.cancelled_user_id
        }
    except Exception as e:
        log_error("update_user", e, current_admin.id, {"user_id": user_id, "update_data": user_update})
        raise

@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Deactivate a user (admin only)"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.deactivated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    
    return {"message": "User deactivated successfully"}

@router.post("/users/{user_id}/activate")
def activate_user(user_id: int, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Activate a user (admin only)"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.deactivated_at = None
    session.add(user)
    session.commit()
    
    return {"message": "User activated successfully"}

@router.get("/stats")
def get_system_stats(current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Get system statistics (admin only)"""
    total_users = session.exec(select(func.count(User.id))).one()
    active_users = session.exec(select(func.count(User.id)).where(User.is_active == True)).one()
    total_docs = session.exec(select(func.count(Document.id))).one()
    completed_docs = session.exec(select(func.count(Document.id)).where(Document.status == "completed")).one()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_documents": total_docs,
        "completed_documents": completed_docs,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/user-stats/{user_id}")
def get_user_stats(user_id: int, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Get detailed statistics for a specific user"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    total_docs = session.exec(select(func.count(Document.id)).where(Document.user_id == user_id)).one()
    completed_docs = session.exec(select(func.count(Document.id)).where(
        Document.user_id == user_id,
        Document.status == "completed"
    )).one()
    
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    daily_usage = session.exec(
        select(func.count(Document.id)).where(
            Document.user_id == user_id,
            Document.submitted_at >= start_of_day
        )
    ).one()
    
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "daily_usage": daily_usage,
        "daily_limit": 500,
        "total_documents": total_docs,
        "completed_documents": completed_docs,
        "account_status": "active" if user.is_active else "inactive",
        "created_at": user.created_at,
        "usage_percentage": (daily_usage / 500 * 100)
    }

@router.post("/users/{user_id}/reset-daily-count")
def reset_user_daily_count(user_id: int, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Reset a user's daily translation counter"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.daily_translation_count = 0
    user.daily_translation_reset = datetime.utcnow()
    
    session.add(user)
    session.commit()
    
    return {
        "message": "Daily translation count reset successfully",
        "user_id": user.id,
        "new_count": user.daily_translation_count,
        "reset_time": user.daily_translation_reset
    }

@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, password_data: dict, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Reset a user's password (admin only)"""
    from ..security import hash_password
    
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if "password" not in password_data or not password_data["password"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required"
            )
    
    try:
        hashed_password = hash_password(password_data["password"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid password: {str(e)}"
        )
    
    user.hashed_password = hashed_password
    
    session.add(user)
    session.commit()
    
    return {"message": "Password reset successfully"}

@router.delete("/users/{user_id}/soft-delete")
def soft_delete_user(user_id: int, current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Soft delete a user by setting a cancelled flag (admin only)"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.deactivated_at = datetime.utcnow()
    user.cancelled_user_id = current_admin.id
    
    session.add(user)
    session.commit()
    
    return {"message": "User soft deleted successfully"}

@router.get("/usage-analytics")
def get_usage_analytics(current_admin=Depends(get_current_admin), session: Session = Depends(get_session_context)):
    """Get system-wide usage analytics for daily, weekly, monthly periods"""
    now = datetime.utcnow()
    
    seven_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    daily_stats = session.exec(
        select(
            func.date(Document.submitted_at).label('date'),
            func.count(Document.id).label('count')
        )
        .where(Document.submitted_at >= seven_days_ago)
        .group_by(func.date(Document.submitted_at))
        .order_by(func.date(Document.submitted_at))
    ).all()
    
    four_weeks_ago = now - timedelta(weeks=4)
    weekly_stats = session.exec(
        select(
            func.date_part('week', Document.submitted_at).label('week_number'),
            func.count(Document.id).label('count')
        )
        .where(Document.submitted_at >= four_weeks_ago)
        .group_by(func.date_part('week', Document.submitted_at))
        .order_by(func.date_part('week', Document.submitted_at))
    ).all()
    
    six_months_ago = now - timedelta(days=180)
    monthly_stats = session.exec(
        select(
            func.date_part('month', Document.submitted_at).label('month_number'),
            func.date_part('year', Document.submitted_at).label('year'),
            func.count(Document.id).label('count')
        )
        .where(Document.submitted_at >= six_months_ago)
        .group_by(func.date_part('month', Document.submitted_at), func.date_part('year', Document.submitted_at))
        .order_by(func.date_part('year', Document.submitted_at), func.date_part('month', Document.submitted_at))
    ).all()
    
    daily_formatted = [{"date": str(row[0]), "count": row[1]} for row in daily_stats]
    weekly_formatted = [{"week": f"Week {int(row[0])}", "count": row[1]} for row in weekly_stats]
    monthly_formatted = [{"month": f"{int(row[1])}-{int(row[0]):02d}", "count": row[2]} for row in monthly_stats]
    
    return {
        "daily_usage": daily_formatted,
        "weekly_usage": weekly_formatted,
        "monthly_usage": monthly_formatted,
        "timestamp": now.isoformat(),
        "summary": {
            "total_documents_processed": sum([row[1] for row in daily_stats]),
            "active_days_count": len(daily_stats),
            "active_weeks_count": len(weekly_stats),
            "active_months_count": len(monthly_stats)
        }
    }


from sqlmodel import Session, select
from typing import Dict, Any


@router.get("/gemini-api-keys")
def get_gemini_api_keys(current_admin=Depends(get_current_admin), db: Session = Depends(get_session_context)):
    """Get all Gemini API keys (with masked values for security)"""
    try:
        api_keys = db.exec(select(GeminiApiKey)).all()
        
        result = []
        for key in api_keys:
            masked_key = "..." + key.key[-4:] if len(key.key) > 7 else key.key
            result.append({
                "id": key.id,
                "key": masked_key,
                "description": key.description or f"Gemini API Key #{key.id}",
                "is_active": key.is_active,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "last_used": key.last_used.isoformat() if key.last_used else None,
                "usage_count": key.usage_count
            })
        
        return result
    except Exception as e:
        print(f"Error fetching API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch API keys")


@router.post("/gemini-api-keys")
def add_gemini_api_key(new_key: Dict[str, Any], current_admin=Depends(get_current_admin), db: Session = Depends(get_session_context)):
    """Add a new Gemini API key to the database"""
    try:
        key_value = new_key.get("key", "").strip()
        description = new_key.get("description", "").strip()
        
        if not key_value:
            raise HTTPException(status_code=400, detail="API key is required")
        
        if not key_value.startswith("AIza"):
            raise HTTPException(status_code=400, detail="Invalid API key format. Must start with 'AIza'")
        
        existing_key = db.exec(select(GeminiApiKey).where(GeminiApiKey.key == key_value)).first()
        if existing_key:
            raise HTTPException(status_code=400, detail="API key already exists")
        
        new_api_key = GeminiApiKey(
            key=key_value,
            description=description or f"Added on {datetime.utcnow().strftime('%Y-%m-%d')}",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(new_api_key)
        db.commit()
        db.refresh(new_api_key)
        
        masked_key = "..." + new_api_key.key[-4:]
        return {
            "id": new_api_key.id,
            "key": masked_key,
            "description": new_api_key.description,
            "message": "API key added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding API key: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add API key")


@router.delete("/gemini-api-keys/{key_id}")
def remove_gemini_api_key(key_id: int, current_admin=Depends(get_current_admin), db: Session = Depends(get_session_context)):
    """Remove a Gemini API key by ID"""
    try:
        api_key = db.exec(select(GeminiApiKey).where(GeminiApiKey.id == key_id)).first()
        
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        db.delete(api_key)
        db.commit()
        
        return {
            "message": "API key removed successfully",
            "removed_key_id": key_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing API key: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove API key")