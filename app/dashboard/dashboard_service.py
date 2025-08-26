from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date

from app.models import User, Job, Application
from app.schemas import (
    DashboardResponse, DashboardMetrics, DashboardJobSummary, 
    JobStatusUpdate
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_data(self, business_user_id: int) -> DashboardResponse:
        """Get dashboard metrics and job listings for a business user"""
        
        # Get metrics
        metrics = self._get_metrics(business_user_id)
        
        # Get job listings
        jobs = self._get_job_listings(business_user_id)
        
        return DashboardResponse(metrics=metrics, jobs=jobs)
    
    def _get_metrics(self, business_user_id: int) -> DashboardMetrics:
        """Calculate dashboard metrics"""
        
        # Active jobs count
        active_jobs = self.db.query(Job).filter(
            Job.posted_by == business_user_id,
            Job.status == "active"
        ).count()
        
        # Total applications across all jobs
        total_applications = self.db.query(Application).join(Job).filter(
            Job.posted_by == business_user_id
        ).count()
        
        # New applications this month
        first_day_of_month = date.today().replace(day=1)
        new_applications_this_month = self.db.query(Application).join(Job).filter(
            Job.posted_by == business_user_id,
            Application.applied_at >= first_day_of_month
        ).count()
        
        # Average response rate (simplified calculation)
        # For now, we'll calculate as percentage of applications that have been reviewed
        total_apps = self.db.query(Application).join(Job).filter(
            Job.posted_by == business_user_id
        ).count()
        
        reviewed_apps = self.db.query(Application).join(Job).filter(
            Job.posted_by == business_user_id,
            Application.status.in_(["shortlisted", "hired", "rejected"])
        ).count()
        
        average_response_rate = (reviewed_apps / total_apps * 100) if total_apps > 0 else 0
        
        return DashboardMetrics(
            active_jobs=active_jobs,
            total_applications=total_applications,
            new_applications_this_month=new_applications_this_month,
            average_response_rate=round(average_response_rate, 1)
        )
    
    def _get_job_listings(self, business_user_id: int) -> List[DashboardJobSummary]:
        """Get job listings for dashboard"""
        
        jobs = self.db.query(Job).filter(
            Job.posted_by == business_user_id
        ).order_by(Job.created_at.desc()).all()
        
        job_summaries = []
        for job in jobs:
            # Parse job_type from comma-separated string to list
            job_types = job.job_type.split(',') if job.job_type else []
            job_types = [jt.strip() for jt in job_types if jt.strip()]
            
            # Format posted date
            posted_date = job.posted_date.strftime("%m/%d/%Y") if job.posted_date else job.created_at.strftime("%m/%d/%Y")
            
            # Get applicant count
            applicant_count = self.db.query(Application).filter(
                Application.job_id == job.id
            ).count()
            
            job_summary = DashboardJobSummary(
                id=job.id,
                title=job.title,
                job_type=job_types,
                business_category=job.business_category,
                location_city=job.location_city,
                location_state=job.location_state,
                location_zip=job.location_zip,
                posted_date=posted_date,
                description=job.description or "",
                applicants=applicant_count,
                status=job.status
            )
            job_summaries.append(job_summary)
        
        return job_summaries
    
    def get_filtered_jobs(self, business_user_id: int, search: Optional[str] = None, status: Optional[str] = None) -> List[DashboardJobSummary]:
        """Get job listings with optional filtering"""
        jobs = self._get_job_listings(business_user_id)
        
        # Apply filters
        if search:
            search_lower = search.lower()
            jobs = [job for job in jobs if search_lower in job.title.lower() or search_lower in job.description.lower()]
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        return jobs
    
    def update_job_status(self, job_id: int, business_user_id: int, status: str) -> bool:
        """Update job status (active/archived)"""
        
        if status not in ["active", "archived"]:
            return False
        
        job = self.db.query(Job).filter(
            Job.id == job_id,
            Job.posted_by == business_user_id
        ).first()
        
        if not job:
            return False
        
        job.status = status
        self.db.commit()
        return True
