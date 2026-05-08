from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select
from sqlalchemy import and_, func, or_
from typing import List
from ..database import get_session_context
from ..security import get_current_user, get_current_user_or_admin
from ..models.user import User
from ..models.document import Document
from ..models.pricing_models import UserSubscription, PricingPlan
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

DAILY_LIMIT = 500


def count_successful_translations(session: Session, user_id: int, subscription: UserSubscription | None = None) -> int:
    filters = [
        Document.user_id == user_id,
        Document.status == "completed",
    ]

    if subscription:
        period_start = subscription.start_date or subscription.created_at
        filters.append(
            or_(
                Document.completed_at >= period_start,
                and_(Document.completed_at.is_(None), Document.submitted_at >= period_start),
            )
        )

    return session.exec(select(func.count(Document.id)).where(*filters)).one()

@router.get("/dashboard")
def get_user_dashboard(current_user_or_admin = Depends(get_current_user_or_admin), session: Session = Depends(get_session_context)):
    """Get user dashboard data (for both regular users and admins)"""
    # Get the actual user (could be admin or regular user)
    if isinstance(current_user_or_admin, tuple):
        current_user, role = current_user_or_admin
    else:
        current_user = current_user_or_admin
        role = 'user'
    total_docs = session.exec(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    ).one()
    
    completed_docs = count_successful_translations(session, current_user.id)
    
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    
    todays_docs = session.exec(
        select(func.count(Document.id)).where(
            Document.user_id == current_user.id,
            Document.submitted_at >= start_of_day
        )
    ).one()
    
    subscription = session.exec(
        select(UserSubscription).where(
            UserSubscription.user_id == current_user.id,
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
    
    plan_usage = count_successful_translations(session, current_user.id, subscription) if subscription else 0
    
    return {
        "user_info": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "daily_usage": todays_docs,
            "daily_limit": DAILY_LIMIT,
            "total_usage": plan_usage,
            "total_translated_images": completed_docs,
            "plan_name": plan_name,
            "plan_total_limit": plan_total_limit,
            "account_expires": current_user.account_expires,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "language": current_user.language,
            "theme": current_user.theme
        },
        "stats": {
            "submitted": total_docs,
            "translated": completed_docs
        }
    }

@router.get("/documents")
def get_user_documents(current_user=Depends(get_current_user), session: Session = Depends(get_session_context)) -> List[dict]:
    """Get user's documents"""
    documents = session.exec(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.submitted_at.desc())
    ).all()
    
    return [{"id": doc.id, "filename": doc.filename, "status": doc.status, "submitted_at": doc.submitted_at} for doc in documents]

@router.get("/documents/{document_id}")
def get_user_document(document_id: int, current_user=Depends(get_current_user), session: Session = Depends(get_session_context)):
    """Get specific user document"""
    document = session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {"document": document}

@router.put("/language")
def update_user_language(
    language: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Update user's language preference"""
    # Validate language
    valid_languages = ["en", "ru", "tk"]
    if language not in valid_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
        )
    
    current_user.language = language
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {"message": "Language updated successfully", "language": current_user.language}

@router.put("/theme")
def update_user_theme(
    theme: str,
    current_user_or_admin = Depends(get_current_user_or_admin),
    session: Session = Depends(get_session_context)
):
    """Update user's theme preference (for both regular users and admins)"""
    # Get the actual user (could be admin or regular user)
    if isinstance(current_user_or_admin, tuple):
        user, role = current_user_or_admin
    else:
        user = current_user_or_admin
        role = 'user'
    
    # Validate theme
    valid_themes = ["dark", "light"]
    if theme not in valid_themes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid theme. Must be one of: {', '.join(valid_themes)}"
        )
    
    user.theme = theme
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"message": "Theme updated successfully", "theme": user.theme}
