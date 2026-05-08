"""Metadata configuration to handle duplicate table definitions"""

from sqlmodel import SQLModel

SQLModel.metadata.info['extend_existing'] = True

from .user import User
from .workspace import WorkspaceFolder
from .document import Document
from .api_key import GeminiApiKey
from .pricing_models import UsageRecord, UserSubscription

__all__ = ["User", "WorkspaceFolder", "Document", "GeminiApiKey", "UsageRecord", "UserSubscription"]