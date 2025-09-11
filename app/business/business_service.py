import json
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime

from app.models import Job, Application, User
from app.schemas import JobCreate, JobDetail, JobSummary, JobLocation, CompanyInfo, ApplicationOut, ApplicationDetail, UserOut


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def _days_ago(self, date_obj):
        if not date_obj:
            return "N/A"
        # Convert datetime to date if needed
        if hasattr(date_obj, 'date'):
            date_obj = date_obj.date()
        delta = datetime.utcnow().date() - date_obj
        return f"{delta.days} days ago" if delta.days > 0 else "Today"

    def create_job(self, payload: JobCreate, user_id: int) -> Job:
        """Create a new job posting"""
        # Handle both new and legacy field formats
        posted_date = (
            datetime.strptime(payload.posted_date, "%m/%d/%Y").date()
            if payload.posted_date
            else datetime.utcnow().date()
        )

        # Use new fields if available, fall back to legacy fields
        job_type = payload.job_type if payload.job_type else (payload.type or [])
        company_name = payload.company.name if payload.company else "Company"
        company_address = payload.company.address if payload.company else None
        company_description = payload.company.description if payload.company else None
        tags = payload.tags or []
        
        # Location handling
        location_street = payload.location_street
        location_city = payload.location_city
        location_state = payload.location_state
        location_zip = payload.location_zip
        
        if payload.location:
            location_street = payload.location.street
            location_city = payload.location.city
            location_state = payload.location.state
            location_zip = payload.location.zip

        db_job = Job(
            title=payload.title,
            posted_by=user_id,
            company_name=company_name,
            company_address=company_address,
            company_description=company_description,
            job_type=",".join(job_type),
            business_category=payload.business_category,
            work_format=payload.work_format,
            minimum_age_required=payload.minimum_age_required,
            tags=",".join(tags),
            location_street=location_street,
            location_city=location_city,
            location_state=location_state,
            location_zip=location_zip,
            applicants=payload.applicants or 0,
            posted_date=posted_date,
            status="active" if payload.action == "save_and_publish" else ("preview" if payload.action == "preview" else "draft"),  # Set status based on action
            description=payload.description,
            key_responsibilities=json.dumps(payload.key_responsibilities),
            requirements_qualifications=json.dumps(payload.requirements_qualifications),
            compensation_type=payload.compensation_type,
            compensation_amount=payload.compensation_amount,
            duration=payload.duration,
            schedule=payload.schedule,
            application_deadline=payload.application_deadline,
            contact_email=payload.contact_email,
            high_school_students_welcome=payload.high_school_students_welcome,
            after_school_hours_available=payload.after_school_hours_available,
            previous_experience_required=payload.previous_experience_required,
            offerings=json.dumps(payload.offerings or []),
            job_details=json.dumps(payload.job_details or {}),
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def get_all_jobs(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        search: Optional[str] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        business_category: Optional[str] = None,
        work_format: Optional[str] = None,
        compensation_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[JobSummary]:
        """Get all business with filtering"""
        query = self.db.query(Job)
        
        # Filter by status - if no status specified, default to active for public listings
        if status:
            query = query.filter(Job.status == status)
        else:
            query = query.filter(Job.status == "active")  # Default to active business for public listings
        
        # Apply filters
        if search:
            search_filter = or_(
                Job.title.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%"),
                Job.company_name.ilike(f"%{search}%"),
                Job.tags.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if job_type:
            query = query.filter(Job.job_type.ilike(f"%{job_type}%"))
        
        if location:
            location_filter = or_(
                Job.location_city.ilike(f"%{location}%"),
                Job.location_state.ilike(f"%{location}%")
            )
            query = query.filter(location_filter)
        
        if company:
            query = query.filter(Job.company_name.ilike(f"%{company}%"))
        
        if business_category:
            query = query.filter(Job.business_category == business_category)
        
        if work_format:
            query = query.filter(Job.work_format == work_format)
        
        if compensation_type:
            query = query.filter(Job.compensation_type == compensation_type)
        
        # Apply pagination and ordering
        jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            JobSummary(
                id=job.id,
                title=job.title,
                company=job.company_name or "Company",
                job_type=job.job_type.split(",") if job.job_type else [],
                business_category=job.business_category,
                work_format=job.work_format,
                location=JobLocation(
                    street=job.location_street,
                    city=job.location_city,
                    state=job.location_state,
                    zip=job.location_zip,
                ),
                compensation_type=job.compensation_type,
                compensation_amount=job.compensation_amount,
                applicants=job.applicants or 0,
                posted=self._days_ago(job.created_at) if job.created_at else "N/A",
                application_deadline=job.application_deadline.strftime("%Y-%m-%d") if job.application_deadline else None,
                # Legacy fields for backward compatibility
                type=job.job_type.split(",") if job.job_type else [],
                tags=job.tags.split(",") if job.tags else [],
            )
            for job in jobs
        ]

    def get_job_detail(self, job_id: int) -> Optional[JobDetail]:
        """Get detailed job information"""
        job = self.db.query(Job).filter(Job.id == job_id, Job.status == "active").first()
        if not job:
            return None

        return JobDetail(
            id=job.id,
            title=job.title,
            company_name=job.company_name or "Company",
            job_type=job.job_type.split(",") if job.job_type else [],
            business_category=job.business_category,
            work_format=job.work_format,
            minimum_age_required=job.minimum_age_required,
            location_street=job.location_street,
            location_city=job.location_city,
            location_state=job.location_state,
            location_zip=job.location_zip,
            description=job.description or "",
            key_responsibilities=json.loads(job.key_responsibilities or "[]"),
            requirements_qualifications=json.loads(
                job.requirements_qualifications or "[]"
            ),
            compensation_type=job.compensation_type,
            compensation_amount=job.compensation_amount,
            duration=job.duration,
            schedule=job.schedule,
            application_deadline=job.application_deadline.strftime("%Y-%m-%d") if job.application_deadline else None,
            contact_email=job.contact_email,
            high_school_students_welcome=job.high_school_students_welcome or False,
            after_school_hours_available=job.after_school_hours_available or False,
            previous_experience_required=job.previous_experience_required or True,
            applicants=job.applicants or 0,
            posted_date=job.created_at.strftime("%Y-%m-%d") if job.created_at else "N/A",
            apply={"job_id": job.id, "title": job.title},
            # Legacy fields for backward compatibility
            company=CompanyInfo(
                name=job.company_name,
                address=job.company_address,
                description=job.company_description,
            ),
            type=job.job_type.split(",") if job.job_type else [],
            location=JobLocation(
                street=job.location_street,
                city=job.location_city,
                state=job.location_state,
                zip=job.location_zip,
            ),
            tags=job.tags.split(",") if job.tags else [],
            offerings=json.loads(job.offerings or "[]"),
            job_details=json.loads(job.job_details or "{}"),
        )

    def update_job(self, job_id: int, payload: JobCreate, user_id: int) -> Optional[Job]:
        """Update an existing job"""
        job = self.db.query(Job).filter(
            and_(Job.id == job_id, Job.posted_by == user_id)
        ).first()
        if not job:
            return None

        posted_date = (
            datetime.strptime(payload.posted_date, "%m/%d/%Y").date()
            if payload.posted_date
            else job.posted_date or datetime.utcnow().date()
        )

        job.title = payload.title
        
        # Handle company info (legacy or new format)
        if payload.company:
            job.company_name = payload.company.name
            job.company_address = payload.company.address
            job.company_description = payload.company.description
        
        # Handle job type (new or legacy format)
        job_type = payload.job_type if payload.job_type else (payload.type or [])
        job.job_type = ",".join(job_type)
        
        # Handle tags (legacy format)
        if payload.tags:
            job.tags = ",".join(payload.tags)
        
        # Handle location (new or legacy format)
        if payload.location:
            job.location_street = payload.location.street
            job.location_city = payload.location.city
            job.location_state = payload.location.state
            job.location_zip = payload.location.zip
        else:
            job.location_street = payload.location_street
            job.location_city = payload.location_city
            job.location_state = payload.location_state
            job.location_zip = payload.location_zip
        
        # New fields
        job.business_category = payload.business_category
        job.work_format = payload.work_format
        job.minimum_age_required = payload.minimum_age_required
        job.compensation_type = payload.compensation_type
        job.compensation_amount = payload.compensation_amount
        job.duration = payload.duration
        job.schedule = payload.schedule
        job.application_deadline = payload.application_deadline
        job.contact_email = payload.contact_email
        job.high_school_students_welcome = payload.high_school_students_welcome
        job.after_school_hours_available = payload.after_school_hours_available
        job.previous_experience_required = payload.previous_experience_required
        
        # Legacy fields
        job.applicants = payload.applicants or 0
        job.posted_date = posted_date
        job.description = payload.description
        job.key_responsibilities = json.dumps(payload.key_responsibilities)
        job.requirements_qualifications = json.dumps(payload.requirements_qualifications)
        job.offerings = json.dumps(payload.offerings or [])
        job.job_details = json.dumps(payload.job_details or {})
        
        # Update status based on action
        if payload.action == "save_and_publish":
            job.status = "active"
        elif payload.action == "preview":
            job.status = "preview"
        elif payload.action == "save":
            job.status = "draft"

        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: int, user_id: int) -> bool:
        """Delete a job"""
        job = self.db.query(Job).filter(
            and_(Job.id == job_id, Job.posted_by == user_id)
        ).first()
        if not job:
            return False

        self.db.delete(job)
        self.db.commit()
        return True

    # Application methods
    def apply_to_job(self, job_id: int, user_id: int, cover_letter: Optional[str] = None) -> Optional[Application]:
        """Apply to a job"""
        # Check if job exists
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None
        
        # Check if user already applied
        existing_application = self.db.query(Application).filter(
            and_(Application.job_id == job_id, Application.user_id == user_id)
        ).first()
        if existing_application:
            return None
        
        # Create application
        application = Application(
            user_id=user_id,
            job_id=job_id,
            cover_letter=cover_letter,
            status="applied"
        )
        self.db.add(application)
        
        # Update job applicant count
        job.applicants = (job.applicants or 0) + 1
        
        self.db.commit()
        self.db.refresh(application)
        return application

    def get_user_applications(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ApplicationOut]:
        """Get applications for a specific user"""
        applications = (
            self.db.query(Application)
            .join(Job)
            .filter(Application.user_id == user_id)
            .order_by(Application.applied_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [
            ApplicationOut(
                id=app.id,
                job_id=app.job_id,
                status=app.status,
                applied_at=app.applied_at.strftime("%Y-%m-%d %H:%M:%S"),
                job_title=app.job.title,
                company_name=app.job.company_name
            )
            for app in applications
        ]

    def get_job_applications(self, job_id: int, business_user_id: int, skip: int = 0, limit: int = 20) -> Optional[List[ApplicationDetail]]:
        """Get applications for a specific job (business user only)"""
        # Verify that the business user owns this job
        job = self.db.query(Job).filter(
            and_(Job.id == job_id, Job.posted_by == business_user_id)
        ).first()
        if not job:
            return None
        
        applications = (
            self.db.query(Application)
            .join(User, Application.user_id == User.id)
            .filter(Application.job_id == job_id)
            .order_by(Application.applied_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [
            ApplicationDetail(
                id=app.id,
                job_id=app.job_id,
                user_id=app.user_id,
                status=app.status,
                applied_at=app.applied_at.strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=app.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                cover_letter=app.cover_letter,
                resume_filename=app.resume_filename,
                job=JobSummary(
                    id=job.id,
                    title=job.title,
                    company=job.company_name,
                    type=job.job_type.split(",") if job.job_type else [],
                    location=JobLocation(
                        street=job.location_street,
                        city=job.location_city,
                        state=job.location_state,
                        zip=job.location_zip,
                    ),
                    tags=job.tags.split(",") if job.tags else [],
                    applicants=job.applicants or 0,
                    posted=self._days_ago(job.posted_date) if job.posted_date else "N/A",
                ),
                applicant=UserOut(
                    id=app.applicant.id,
                    first_name=app.applicant.first_name,
                    last_name=app.applicant.last_name,
                    email=app.applicant.email,
                    role=app.applicant.role
                )
            )
            for app in applications
        ]

    def update_application_status(self, application_id: int, status: str, business_user_id: int) -> bool:
        """Update application status (business user only)"""
        # Verify that the business user owns the job for this application
        application = (
            self.db.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(
                and_(
                    Application.id == application_id,
                    Job.posted_by == business_user_id
                )
            )
            .first()
        )
        
        if not application:
            return False
        
        application.status = status
        self.db.commit()
        return True


