from pydantic import BaseModel
from typing import Optional

class UserStats(BaseModel):
    email: str
    submitted: int
    translated: int

class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    password: str
