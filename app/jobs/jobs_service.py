import json
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Job
from app.schemas import JobCreate, JobDetail, JobSummary, JobLocation, CompanyInfo


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def _days_ago(self, date_obj):
        delta = datetime.utcnow().date() - date_obj
        return f"{delta.days} days ago" if delta.days > 0 else "Today"

    def create_job(self, payload: JobCreate) -> Job:
        posted_date = (
            datetime.strptime(payload.posted_date, "%m/%d/%Y").date()
            if payload.posted_date
            else datetime.utcnow().date()
        )

        db_job = Job(
            title=payload.title,
            company_name=payload.company.name,
            company_address=payload.company.address,
            company_description=payload.company.description,
            job_type=",".join(payload.type),
            tags=",".join(payload.tags),
            location_street=payload.location.street,
            location_city=payload.location.city,
            location_state=payload.location.state,
            location_zip=payload.location.zip,
            applicants=payload.applicants,
            posted_date=posted_date,
            description=payload.description,
            key_responsibilities=json.dumps(payload.key_responsibilities),
            requirements_qualifications=json.dumps(payload.requirements_qualifications),
            offerings=json.dumps(payload.offerings),
            job_details=json.dumps(payload.job_details),
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def get_all_jobs(self) -> List[JobSummary]:
        jobs = self.db.query(Job).all()
        return [
            JobSummary(
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
                posted=self._days_ago(job.posted_date)
                if job.posted_date
                else "N/A",
            )
            for job in jobs
        ]

    def get_job_detail(self, job_id: int) -> JobDetail:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        return JobDetail(
            id=job.id,
            title=job.title,
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
            posted_date=job.posted_date.strftime("%m/%d/%Y")
            if job.posted_date
            else "N/A",
            applicants=job.applicants or 0,
            tags=job.tags.split(",") if job.tags else [],
            description=job.description or "",
            key_responsibilities=json.loads(job.key_responsibilities or "[]"),
            requirements_qualifications=json.loads(
                job.requirements_qualifications or "[]"
            ),
            offerings=json.loads(job.offerings or "[]"),
            job_details=json.loads(job.job_details or "{}"),
            apply={
                "button_text": "Apply Now",
                "estimated_submission_time": "less than 5 minutes",
            },
        )

    def update_job(self, job_id: int, payload: JobCreate) -> Job | None:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        posted_date = (
            datetime.strptime(payload.posted_date, "%m/%d/%Y").date()
            if payload.posted_date
            else job.posted_date or datetime.utcnow().date()
        )

        job.title = payload.title
        job.company_name = payload.company.name
        job.company_address = payload.company.address
        job.company_description = payload.company.description
        job.job_type = ",".join(payload.type)
        job.tags = ",".join(payload.tags)
        job.location_street = payload.location.street
        job.location_city = payload.location.city
        job.location_state = payload.location.state
        job.location_zip = payload.location.zip
        job.applicants = payload.applicants or 0
        job.posted_date = posted_date
        job.description = payload.description
        job.key_responsibilities = json.dumps(payload.key_responsibilities)
        job.requirements_qualifications = json.dumps(payload.requirements_qualifications)
        job.offerings = json.dumps(payload.offerings)
        job.job_details = json.dumps(payload.job_details)

        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: int) -> bool:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False

        self.db.delete(job)
        self.db.commit()
        return True
