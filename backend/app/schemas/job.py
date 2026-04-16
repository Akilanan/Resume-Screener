from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobCreate(BaseModel):
    title: str
    description: str


class JobResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True
