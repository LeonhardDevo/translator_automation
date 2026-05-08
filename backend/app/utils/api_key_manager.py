from sqlmodel import Session
from typing import Optional
from backend.app.crud.api_key import validate_api_key, get_active_api_keys
from backend.app.models.api_key import GeminiApiKey as GeminiApiKeyModel
import logging

logger = logging.getLogger(__name__)


class ApiKeyManager:
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def get_valid_api_key(self) -> Optional[GeminiApiKeyModel]:
        """
        Get a valid, active API key with the lowest usage count
        This helps distribute usage across available keys
        """
        active_keys = get_active_api_keys(self.db)
        
        if not active_keys:
            logger.warning("No active API keys available")
            return None
            
        sorted_keys = sorted(active_keys, key=lambda k: k.usage_count)
        return sorted_keys[0]
    
    def validate_and_use_key(self, raw_key: str) -> bool:
        """
        Validate a specific API key and increment its usage count
        """
        api_key = validate_api_key(self.db, raw_key)
        return api_key is not None
    
    def get_available_keys_count(self) -> int:
        """
        Get the count of active API keys
        """
        active_keys = get_active_api_keys(self.db)
        return len(active_keys)
    
    def get_total_usage_count(self) -> int:
        """
        Get the total usage count across all API keys
        """
        active_keys = get_active_api_keys(self.db)
        return sum(key.usage_count for key in active_keys)


def get_translation_api_key(db: Session) -> Optional[str]:
    """
    Get an appropriate API key for translation tasks from the database.

    Returns the raw key string of the active Gemini API key with the lowest
    usage count, or None if no active keys exist.
    """
    manager = ApiKeyManager(db)
    api_key = manager.get_valid_api_key()
    return api_key.key if api_key else None

def get_all_active_translation_api_keys(db: Session) -> list[str]:
    """
    Get ALL active API keys from the database for translation tasks
    Returns a list of actual API key strings (not hashed)
    """
    from sqlmodel import select
    from backend.app.models.api_key import GeminiApiKey
    
    statement = select(GeminiApiKey).where(GeminiApiKey.is_active == True)
    active_keys = db.exec(statement).all()
    
    if not active_keys:
        logger.warning("No active API keys found in database")
        return []
    
    return [key.key for key in active_keys]