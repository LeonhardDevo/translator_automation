from sqlmodel import Session, select
from typing import List, Optional
from backend.app.models.api_key import GeminiApiKey as GeminiApiKeyModel
from backend.app.schemas.api_key import GeminiApiKeyCreate, GeminiApiKeyUpdate
from datetime import datetime
import hashlib


def create_api_key(db: Session, api_key: GeminiApiKeyCreate) -> GeminiApiKeyModel:
    """Create a new API key entry"""
    hashed_key = hashlib.sha256(api_key.key.encode()).hexdigest()
    
    db_api_key = GeminiApiKeyModel(
        key=hashed_key,
        description=api_key.description,
        is_active=api_key.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_used=None,
        usage_count=0
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key


def get_api_key(db: Session, api_key_id: int) -> Optional[GeminiApiKeyModel]:
    """Get an API key by ID"""
    return db.get(GeminiApiKeyModel, api_key_id)


def get_api_key_by_hashed_key(db: Session, hashed_key: str) -> Optional[GeminiApiKeyModel]:
    """Get an API key by its hashed value"""
    statement = select(GeminiApiKeyModel).where(GeminiApiKeyModel.key == hashed_key)
    return db.exec(statement).first()


def get_api_keys(db: Session, skip: int = 0, limit: int = 100) -> List[GeminiApiKeyModel]:
    """Get all API keys with pagination"""
    statement = select(GeminiApiKeyModel).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_active_api_keys(db: Session) -> List[GeminiApiKeyModel]:
    """Get all active API keys"""
    statement = select(GeminiApiKeyModel).where(GeminiApiKeyModel.is_active == True)
    return db.exec(statement).all()


def update_api_key(db: Session, api_key_id: int, api_key_update: GeminiApiKeyUpdate) -> Optional[GeminiApiKeyModel]:
    """Update an existing API key"""
    db_api_key = db.get(GeminiApiKeyModel, api_key_id)
    if db_api_key:
        update_data = api_key_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_api_key, field, value)
        
        db_api_key.updated_at = datetime.utcnow()
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
    return db_api_key


def delete_api_key(db: Session, api_key_id: int) -> bool:
    """Delete an API key"""
    db_api_key = db.get(GeminiApiKeyModel, api_key_id)
    if db_api_key:
        db.delete(db_api_key)
        db.commit()
        return True
    return False


def increment_usage_count(db: Session, api_key_id: int) -> Optional[GeminiApiKeyModel]:
    """Increment the usage count for an API key"""
    db_api_key = db.get(GeminiApiKeyModel, api_key_id)
    if db_api_key:
        db_api_key.usage_count += 1
        db_api_key.last_used = datetime.utcnow()
        db_api_key.updated_at = datetime.utcnow()
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
    return db_api_key


def validate_api_key(db: Session, raw_key: str) -> Optional[GeminiApiKeyModel]:
    """Validate an API key by checking if it exists and is active"""
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = get_api_key_by_hashed_key(db, hashed_key)
    
    if api_key and api_key.is_active:
        increment_usage_count(db, api_key.id)
        return api_key
    
    return None