from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, UniqueConstraint, DateTime, Boolean, Numeric
from app.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Job(Base):
    __tablename__ = "business"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    
    # Add foreign key to track who posted the job
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Basic job info
    job_type = Column(String(255), nullable=True)  # comma-separated: "part-time,full-time"
    business_category = Column(String(100), nullable=True)
    work_format = Column(String(50), nullable=True)  # "remote", "in-person", "hybrid"
    minimum_age_required = Column(Integer, nullable=True)
    
    # Company info (from business profile but can be overridden)
    company_name = Column(String(100), nullable=False)
    company_address = Column(String(255), nullable=True)
    company_description = Column(Text, nullable=True)

    # Location
    location_street = Column(String(255), nullable=True)
    location_city = Column(String(100), nullable=True)
    location_state = Column(String(50), nullable=True)
    location_zip = Column(String(20), nullable=True)

    # Job content
    description = Column(Text, nullable=True)
    key_responsibilities = Column(Text, nullable=True)           # JSON string list
    requirements_qualifications = Column(Text, nullable=True)    # JSON string list
    
    # Compensation & Schedule
    compensation_type = Column(String(20), nullable=True)  # "salary", "hourly"
    compensation_amount = Column(Numeric(10, 2), nullable=True)
    compensation_currency = Column(String(10), default="USD")
    duration = Column(String(50), nullable=True)  # "ongoing", "3 months", etc.
    schedule = Column(String(255), nullable=True)  # "Mon-Fri 9-5", "flexible", etc.
    
    # Application deadline
    application_deadline = Column(Date, nullable=True)
    
    # Contact
    contact_email = Column(String(255), nullable=True)
    
    # Special options
    high_school_students_welcome = Column(Boolean, default=False)
    after_school_hours_available = Column(Boolean, default=False)
    previous_experience_required = Column(Boolean, default=True)
    
    # Legacy fields for backward compatibility
    tags = Column(String(255), nullable=True)      # comma-separated string
    offerings = Column(Text, nullable=True)        # JSON string list
    job_details = Column(Text, nullable=True)      # JSON string (dict)

    # Metadata
    applicants = Column(Integer, default=0)
    posted_date = Column(Date, nullable=True)
    status = Column(String(20), default="draft")  # "draft", "active", "archived"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    poster = relationship("User", back_populates="jobs_posted")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # "business" or "applicant"
    
    # Applicant-specific fields
    date_of_birth = Column(Date, nullable=True)
    
    # User address (optional for applicants)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Preferences
    email_notifications = Column(Boolean, default=True)
    terms_accepted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business_profile = relationship("BusinessProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    jobs_posted = relationship("Job", back_populates="poster", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="applicant", cascade="all, delete-orphan")

class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Business-specific info
    business_name = Column(String(200), nullable=False)
    business_category = Column(String(100), nullable=True)
    business_description = Column(Text, nullable=True)
    
    # Business address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="business_profile")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String(30), default="applied")  # applied, shortlisted, hired, rejected
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Application form data
    cover_letter = Column(Text, nullable=True)
    resume_filename = Column(String(255), nullable=True)
    
    # Additional application information
    relevant_experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    availability = Column(String(255), nullable=True)
    references = Column(Text, nullable=True)
    
    # Consent tracking
    terms_accepted = Column(Boolean, default=False)
    contact_permission = Column(Boolean, default=False)

    # Relationships
    applicant = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job_once"),
    )
