from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import JobCreate, JobSummary, JobDetail
from app.jobs.jobs_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=dict)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    service = JobService(db)
    job = service.create_job(payload)
    return {"message": "Job created", "job_id": job.id}

@router.get("/", response_model=List[JobSummary])
def list_jobs(db: Session = Depends(get_db)):
    service = JobService(db)
    return service.get_all_jobs()

@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: int, db: Session = Depends(get_db)):
    service = JobService(db)
    job = service.get_job_detail(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=dict)
def update_job(job_id: int, payload: JobCreate, db: Session = Depends(get_db)):
    service = JobService(db)
    updated_job = service.update_job(job_id, payload)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job updated", "job_id": updated_job.id}

@router.delete("/{job_id}", response_model=dict)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    service = JobService(db)
    success = service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted", "job_id": job_id}

