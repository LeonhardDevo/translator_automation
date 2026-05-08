from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_session_context as get_db
from backend.app.models.user import User
from backend.app.security import get_current_admin
from backend.app.schemas.api_key import (
    GeminiApiKey as GeminiApiKeySchema,
    GeminiApiKeyCreate,
    GeminiApiKeyUpdate,
    GeminiApiKeyUsage
)
from backend.app.crud.api_key import (
    create_api_key,
    get_api_key,
    get_api_keys,
    get_active_api_keys,
    update_api_key,
    delete_api_key,
    validate_api_key
)
import secrets
import hashlib

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("/", response_model=GeminiApiKeySchema)
async def create_new_api_key(
    api_key: GeminiApiKeyCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    if not api_key.key or len(api_key.key.strip()) == 0:
        api_key.key = f"gmi-{secrets.token_urlsafe(32)}"
    
    if not api_key.key.startswith("gmi-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key must start with 'gmi-' prefix"
        )
    
    db_api_key = create_api_key(db, api_key)
    response_key = db_api_key.copy()
    response_key.key = api_key.key
    return response_key


@router.get("/{api_key_id}", response_model=GeminiApiKeySchema)
async def read_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get an API key by ID"""
    db_api_key = get_api_key(db, api_key_id)
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    response_key = db_api_key.copy()
    response_key.key = f"****{db_api_key.key[-4:]}"
    return response_key


@router.get("/", response_model=List[GeminiApiKeySchema])
async def read_api_keys(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all API keys"""
    api_keys = get_api_keys(db, skip=skip, limit=limit)
    masked_keys = []
    for key in api_keys:
        masked_key = key.copy()
        masked_key.key = f"****{key.key[-4:]}"
        masked_keys.append(masked_key)
    return masked_keys


@router.put("/{api_key_id}", response_model=GeminiApiKeySchema)
async def update_existing_api_key(
    api_key_id: int,
    api_key_update: GeminiApiKeyUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an existing API key"""
    db_api_key = update_api_key(db, api_key_id, api_key_update)
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    response_key = db_api_key.copy()
    response_key.key = f"****{db_api_key.key[-4:]}"
    return response_key


@router.delete("/{api_key_id}")
async def delete_api_key_entry(
    api_key_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    success = delete_api_key(db, api_key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return {"message": "API key deleted successfully"}


@router.get("/active/", response_model=List[GeminiApiKeySchema])
async def read_active_api_keys(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all active API keys"""
    api_keys = get_active_api_keys(db)
    masked_keys = []
    for key in api_keys:
        masked_key = key.copy()
        masked_key.key = f"****{key.key[-4:]}"
        masked_keys.append(masked_key)
    return masked_keys


@router.post("/validate/{api_key_id}")
async def validate_specific_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Validate a specific API key by ID"""
    db_api_key = get_api_key(db, api_key_id)
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return {
        "valid": db_api_key.is_active,
        "id": db_api_key.id,
        "description": db_api_key.description,
        "usage_count": db_api_key.usage_count,
        "last_used": db_api_key.last_used
    }


@router.get("/usage-stats/", response_model=List[GeminiApiKeyUsage])
async def get_api_key_usage_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get usage statistics for all API keys"""
    api_keys = get_api_keys(db)
    usage_stats = []
    
    for key in api_keys:
        usage_stat = GeminiApiKeyUsage(
            id=key.id,
            key_preview=f"****{key.key[-4:]}",
            description=key.description,
            is_active=key.is_active,
            usage_count=key.usage_count,
            last_used=key.last_used,
            created_at=key.created_at
        )
        usage_stats.append(usage_stat)
    
    return usage_stats