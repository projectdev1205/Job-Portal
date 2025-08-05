from pydantic import BaseModel
from typing import Optional

class JobCreate(BaseModel):
    title: str
    description: str
    company: str
    location: Optional[str] = None
    skills_required: Optional[str] = None

class JobResponse(JobCreate):
    id: int

    class Config:
        orm_mode = True
