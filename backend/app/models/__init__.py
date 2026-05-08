"""Models registry to avoid duplicate table definitions"""

from .user import User
from .workspace import WorkspaceFolder
from .document import Document
from .api_key import GeminiApiKey
from .pricing_models import PricingPlan, UsageRecord, UserSubscription

__all__ = ["User", "WorkspaceFolder", "Document", "GeminiApiKey", "PricingPlan", "UsageRecord", "UserSubscription"]

def metadata_init():
    """Initialize all model metadata to ensure proper registration"""
    from .user import User
    from .workspace import WorkspaceFolder
    from .document import Document
    from .api_key import GeminiApiKey
    from .pricing_models import PricingPlan, UsageRecord, UserSubscription