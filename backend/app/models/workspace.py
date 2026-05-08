from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class WorkspaceFolder(SQLModel, table=True):
    __tablename__ = "workspace_folders"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None
    status: str = Field(default="pending")  # pending, processing, completed, failed
