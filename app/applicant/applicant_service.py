import json
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime

from app.models import Job, Application, User
from app.schemas import JobDetail, JobSummary, JobLocation, CompanyInfo, ApplicationOut, ApplicationFormCreate


class ApplicantJobService:
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
        compensation_type: Optional[str] = None
    ) -> List[JobSummary]:
        """Get all active business with filtering (for applicants to browse)"""
        query = self.db.query(Job).filter(Job.status == "active")  # Only show active business to applicants
        
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
        """Get detailed job information (only active business for applicants)"""
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

    def apply_to_job(self, job_id: int, user_id: int, payload: ApplicationFormCreate) -> Optional[Application]:
        """Apply to a job with comprehensive form data"""
        # Check if job exists and is active
        job = self.db.query(Job).filter(Job.id == job_id, Job.status == "active").first()
        if not job:
            return None
        
        # Check if user already applied
        existing_application = self.db.query(Application).filter(
            and_(Application.job_id == job_id, Application.user_id == user_id)
        ).first()
        if existing_application:
            return None
        
        # Create application with form data
        application = Application(
            user_id=user_id,
            job_id=job_id,
            cover_letter=payload.cover_letter,
            resume_filename=payload.resume_filename,
            relevant_experience=payload.relevant_experience,
            education=payload.education,
            availability=payload.availability,
            references=payload.references,
            terms_accepted=payload.terms_accepted,
            contact_permission=payload.contact_permission,
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
