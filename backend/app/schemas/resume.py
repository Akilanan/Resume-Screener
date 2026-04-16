from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ResumeResponse(BaseModel):
    id: str
    filename: str
    status: str
    score: Optional[float] = None
    match_summary: Optional[str] = None
    skills_matched: Optional[str] = None
    skills_missing: Optional[str] = None
    red_flags: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        use_enum_values = True
