from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Literal
from datetime import date, datetime
from decimal import Decimal


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


# Job Creation Schema (supports all UI fields)
class JobCreate(BaseModel):
    # Action field - mandatory
    action: str  # "save", "save_and_publish"
    
    # Basic job details
    title: str
    job_type: Optional[List[str]] = None  # ["part-time", "full-time", etc.]
    business_category: Optional[str] = None
    work_format: Optional[str] = None  # "remote", "in-person", "hybrid"
    minimum_age_required: Optional[int] = None
    
    # Job location
    location_street: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_zip: Optional[str] = None
    
    # Job content
    description: str
    key_responsibilities: List[str]
    requirements_qualifications: List[str]
    
    # Compensation & Schedule
    compensation_type: Optional[str] = None  # "salary", "hourly"
    compensation_amount: Optional[Decimal] = None
    duration: Optional[str] = None  # "ongoing", "3 months", etc.
    schedule: Optional[str] = None  # "Mon-Fri 9-5", "flexible", etc.
    application_deadline: Optional[date] = None
    
    # Contact
    contact_email: Optional[str] = None
    
    # Special options
    high_school_students_welcome: Optional[bool] = False
    after_school_hours_available: Optional[bool] = False
    previous_experience_required: Optional[bool] = True
    
    # Legacy fields for backward compatibility
    company: Optional[CompanyInfo] = None
    type: Optional[List[str]] = None
    location: Optional[JobLocation] = None
    tags: Optional[List[str]] = None
    applicants: Optional[int] = 0
    posted_date: Optional[str] = None  # Format: "MM/DD/YYYY"
    offerings: Optional[List[str]] = None
    job_details: Optional[Dict] = None


# Job Summary Schema (supports all UI fields)
class JobSummary(BaseModel):
    id: int
    title: str
    company: str
    job_type: List[str]
    business_category: Optional[str]
    work_format: Optional[str]
    location: JobLocation
    compensation_type: Optional[str]
    compensation_amount: Optional[Decimal]
    applicants: int
    posted: str  # e.g. "2 days ago"
    application_deadline: Optional[str]
    
    # Legacy fields for backward compatibility
    type: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class JobDetail(BaseModel):
    id: int
    title: str
    company_name: str
    job_type: List[str]
    business_category: Optional[str]
    work_format: Optional[str]
    minimum_age_required: Optional[int]
    
    # Location
    location_street: Optional[str]
    location_city: str
    location_state: Optional[str]
    location_zip: Optional[str]
    
    # Content
    description: str
    key_responsibilities: List[str]
    requirements_qualifications: List[str]
    
    # Compensation & Schedule
    compensation_type: Optional[str]
    compensation_amount: Optional[Decimal]
    duration: Optional[str]
    schedule: Optional[str]
    application_deadline: Optional[str]
    
    # Contact
    contact_email: Optional[str]
    
    # Special options
    high_school_students_welcome: bool
    after_school_hours_available: bool
    previous_experience_required: bool
    
    # Metadata
    applicants: int
    posted_date: str
    apply: Dict
    
    # Legacy fields for backward compatibility
    company: Optional[CompanyInfo] = None
    type: Optional[List[str]] = None
    location: Optional[JobLocation] = None
    tags: Optional[List[str]] = None
    offerings: Optional[List[str]] = None
    job_details: Optional[Dict] = None

# Address schema for reuse
class AddressInfo(BaseModel):
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

# Business Profile schema
class BusinessProfileCreate(BaseModel):
    business_name: str
    business_category: Optional[str] = None
    business_description: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

class BusinessProfileOut(BaseModel):
    id: int
    business_name: str
    business_category: Optional[str]
    business_description: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    
    class Config:
        from_attributes = True

# Business Registration Schema (matches UI Screen 1)
class BusinessRegisterIn(BaseModel):
    # Personal info
    email: EmailStr
    phone_number: Optional[str] = None
    password: str
    
    # Business info
    business_name: str
    business_category: Optional[str] = None
    business_description: Optional[str] = None
    
    # Business address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Preferences
    email_notifications: Optional[bool] = True
    terms_accepted: bool = True

    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v

# Applicant Registration Schema (matches UI Screen 2)
class ApplicantRegisterIn(BaseModel):
    # Personal info
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    password: str
    
    # Optional address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Preferences
    email_notifications: Optional[bool] = True
    terms_accepted: bool = True

    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v

# Admin Registration Schema
class AdminRegisterIn(BaseModel):
    # Personal info
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    password: str
    
    # Admin-specific fields
    admin_code: str  # Secret code to verify admin registration
    
    # Preferences
    email_notifications: Optional[bool] = True
    terms_accepted: bool = True

    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v

    @validator('admin_code')
    def validate_admin_code(cls, v):
        # You can change this to any secret code you want
        if v != "ADMIN_SECRET_2024":
            raise ValueError('Invalid admin code')
        return v

# Legacy registration for backward compatibility
class RegisterIn(BaseModel):
    name: str  # Will be split into first_name, last_name
    email: EmailStr
    password: str
    role: Literal["business", "applicant", "admin"]

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone_number: Optional[str]
    role: str
    date_of_birth: Optional[date]
    email_notifications: bool
    business_profile: Optional[BusinessProfileOut] = None

    class Config:
        from_attributes = True

# Legacy user output for backward compatibility
class UserOutLegacy(BaseModel):
    id: int
    name: str  # Combined first_name + last_name
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ApplicationFormCreate(BaseModel):
    job_id: int
    
    # Personal Information
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    
    # Address
    street_address: str
    city: str
    state: str
    zip_code: str
    
    resume_filename: Optional[str] = None
    
    # Cover Letter
    cover_letter: Optional[str] = None
    
    # Additional Information
    relevant_experience: Optional[str] = None
    education: Optional[str] = None
    availability: Optional[str] = None
    references: Optional[str] = None
    
    # Consent
    terms_accepted: bool = False
    contact_permission: bool = False

class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    applied_at: str  # formatted datetime
    job_title: str
    company_name: str
    
    class Config:
        from_attributes = True

class ApplicationDetail(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: str
    applied_at: str
    updated_at: str
    cover_letter: Optional[str]
    resume_filename: Optional[str]
    job: JobSummary
    applicant: UserOut
    
    class Config:
        from_attributes = True

# Dashboard schemas
class DashboardMetrics(BaseModel):
    active_jobs: int
    total_applications: int
    new_applications_this_month: int
    average_response_rate: float

class DashboardJobSummary(BaseModel):
    id: int
    title: str
    job_type: List[str]
    business_category: Optional[str]
    location_city: Optional[str]
    location_state: Optional[str]
    location_zip: Optional[str]
    posted_date: str  # Format: "MM/DD/YYYY"
    description: str
    applicants: int
    status: str  # "active" or "archived"
    
    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    jobs: List[DashboardJobSummary]

class JobStatusUpdate(BaseModel):
    status: str  # "active" or "archived"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_role: str
    user_name: str

class LogoutResponse(BaseModel):
    message: str
    status: str

# Admin Migration Schemas
class DatabaseStatus(BaseModel):
    connection_status: str
    connection_error: Optional[str] = None
    missing_columns: List[str]
    needs_migration: bool
    timestamp: datetime

class MigrationResponse(BaseModel):
    success: bool
    message: str
    missing_columns: List[str]
    timestamp: datetime