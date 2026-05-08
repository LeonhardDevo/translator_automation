"""Database models registry to avoid duplicate table definitions"""

from sqlmodel import SQLModel
from typing import cast

class ModelRegistry:
    _initialized = False
    
    @classmethod
    def initialize_models(cls):
        if cls._initialized:
            return
            
        from .user import User
        from .document import Document
        from .api_key import GeminiApiKey
        
        cls._initialized = True

ModelRegistry.initialize_models()

from .user import User, UserBase, UserCreate, UserUpdate, UserPublic
from .document import Document
from .api_key import GeminiApiKey

__all__ = [
    "User", "UserBase", "UserCreate", "UserUpdate", "UserPublic",
    "Document", 
    "GeminiApiKey"
]