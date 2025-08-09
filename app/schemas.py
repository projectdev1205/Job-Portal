from pydantic import BaseModel
from typing import Optional, List, Dict


# Reusable sub-models
class JobLocation(BaseModel):
    street: Optional[str]
    city: str
    state: Optional[str]
    zip: Optional[str]


class CompanyInfo(BaseModel):
    name: str
    address: Optional[str]
    description: Optional[str]


# Input model for creating a job
class JobCreate(BaseModel):
    title: str
    company: CompanyInfo
    type: List[str]
    location: JobLocation
    tags: List[str]
    applicants: Optional[int] = 0
    posted_date: Optional[str] = None  # Format: "MM/DD/YYYY"
    description: str
    key_responsibilities: List[str]
    requirements_qualifications: List[str]
    offerings: List[str]
    job_details: Dict


# Output model for job summary (used in job listings)
class JobSummary(BaseModel):
    id: int
    title: str
    company: str
    type: List[str]
    location: JobLocation
    tags: List[str]
    applicants: int
    posted: str  # e.g. "2 days ago"


# Output model for detailed job view
class JobDetail(BaseModel):
    id: int
    title: str
    company: CompanyInfo
    type: List[str]
    location: JobLocation
    posted_date: str
    applicants: int
    tags: List[str]
    description: str
    key_responsibilities: List[str]
    requirements_qualifications: List[str]
    offerings: List[str]
    job_details: Dict
    apply: Dict
