from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import Set

load_dotenv()

_jwt_secret = os.getenv("JWT_SECRET_KEY")
if not _jwt_secret or len(_jwt_secret) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required and must be at least 32 characters. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./translation_app.db")
    JWT_SECRET_KEY: str = _jwt_secret
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    API_RATE_LIMIT: str = os.getenv("API_RATE_LIMIT", "100/hour")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "True").lower() == "true"
    
    class Config:
        extra = "allow"


settings = Settings()

allowed_extensions_str = os.getenv("ALLOWED_FILE_EXTENSIONS", "jpg,jpeg,png,gif,webp")
settings.ALLOWED_FILE_EXTENSIONS: Set[str] = set(allowed_extensions_str.split(",")) if allowed_extensions_str else set()
