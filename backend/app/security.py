from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from .config import settings
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from .database import get_session_context
from .models.user import User
import re
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

pwd = PasswordHash([Argon2Hasher()])

limiter = Limiter(key_func=get_remote_address)

def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")
    
    return pwd.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    return pwd.verify(password, hashed)

def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    if not subject or not role:
        raise ValueError("Subject and role are required")
    
    to_encode = {"sub": subject, "role": role}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

security = HTTPBearer()

def get_current_user_or_admin(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session_context)):
    """
    Returns (user, role) where role is either 'user' or 'admin'
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        
        if not email or not role:
            raise credentials_exception
            
        if not validate_email(email):
            raise credentials_exception
            
        if role == "user":
            user = session.exec(select(User).where(User.email == email)).first()
            if user is None:
                raise credentials_exception
            return user, role
        elif role == "admin":
            user_admin = session.exec(select(User).where(User.email == email)).first()
            if user_admin and user_admin.role == "admin":
                return user_admin, role
                
            raise credentials_exception
        else:
            raise credentials_exception

    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session_context)):
    user, role = get_current_user_or_admin(credentials, session)
    if role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return user

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session_context)):
    user, role = get_current_user_or_admin(credentials, session)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return user

def validate_file_extension(filename: str) -> bool:
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in settings.ALLOWED_FILE_EXTENSIONS

def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[\\/]', '', filename)
    sanitized = re.sub(r'\.\.', '', sanitized)
    return sanitized
