from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    folder_id: Optional[int] = Field(default=None, foreign_key="workspace_folders.id")
    filename: str  # Original filename
    filepath: str  # Path to stored file
    output_filepath: Optional[str] = None  # Path to translated file
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    is_translated: bool = False
    status: str = Field(default="pending")  # pending, processing, completed, failed
    error_message: Optional[str] = None
    target_language: str = Field(default="Turkmen")  # Target language for translation
