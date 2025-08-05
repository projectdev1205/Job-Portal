from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Create job
@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(
        title=job.title,
        description=job.description,
        company=job.company,
        location=job.location,
        skills_required=job.skills_required
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

# List all jobs
@router.get("/", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()

# Get job by ID
@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
