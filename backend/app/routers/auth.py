from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select
from datetime import timedelta
from ..database import get_session_context
from ..security import create_access_token, verify_password, validate_email
from ..models.user import User
from ..schemas.auth import UserLogin
from ..config import settings

router = APIRouter()
security = HTTPBearer()

@router.post("/login")
def login(login_request: UserLogin, session: Session = Depends(get_session_context)):
    if not validate_email(login_request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    user = session.exec(
        select(User).where(User.email == login_request.email)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    user_role = "user"
    authenticated_user = user
    
    if user.role == "admin":
        user_role = "admin"

    if not verify_password(login_request.password, authenticated_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if hasattr(authenticated_user, 'is_active') and not authenticated_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )
    
    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    if login_request.remember_me:
        expire_minutes = 30 * 24 * 60
        
    access_token_expires = timedelta(minutes=expire_minutes)
    access_token = create_access_token(
        subject=authenticated_user.email,
        role=user_role,
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}