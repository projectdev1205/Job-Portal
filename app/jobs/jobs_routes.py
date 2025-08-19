from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas import JobCreate, JobSummary, JobDetail, ApplicationCreate, ApplicationOut, ApplicationDetail
from app.jobs.jobs_service import JobService
from app.auth.auth_deps import get_current_user, require_role
from app.models import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=dict)
def create_job(
    payload: JobCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Create a new job posting with all UI fields"""
    service = JobService(db)
    job = service.create_job(payload, user_id=current_user.id)
    return {"message": "Job created", "job_id": job.id}

@router.get("/", response_model=List[JobSummary])
def list_jobs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    job_type: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    business_category: Optional[str] = None,
    work_format: Optional[str] = None,
    compensation_type: Optional[str] = None
):
    """List jobs with comprehensive filtering and all UI fields"""
    service = JobService(db)
    return service.get_all_jobs(
        skip=skip, 
        limit=limit, 
        search=search, 
        job_type=job_type, 
        location=location, 
        company=company,
        business_category=business_category,
        work_format=work_format,
        compensation_type=compensation_type
    )

@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: int, db: Session = Depends(get_db)):
    service = JobService(db)
    job = service.get_job_detail(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=dict)
def update_job(
    job_id: int, 
    payload: JobCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    service = JobService(db)
    updated_job = service.update_job(job_id, payload, user_id=current_user.id)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to update it")
    return {"message": "Job updated", "job_id": updated_job.id}

@router.delete("/{job_id}", response_model=dict)
def delete_job(
    job_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    service = JobService(db)
    success = service.delete_job(job_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to delete it")
    return {"message": "Job deleted", "job_id": job_id}



# Application endpoints
@router.post("/{job_id}/apply", response_model=dict)
def apply_to_job(
    job_id: int,
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("applicant"))
):
    if payload.job_id != job_id:
        raise HTTPException(status_code=400, detail="Job ID mismatch")
    
    service = JobService(db)
    application = service.apply_to_job(job_id, current_user.id, payload.cover_letter)
    if not application:
        raise HTTPException(status_code=400, detail="Unable to apply (job not found or already applied)")
    return {"message": "Application submitted successfully", "application_id": application.id}

@router.get("/applications/my", response_model=List[ApplicationOut])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    service = JobService(db)
    return service.get_user_applications(current_user.id, skip=skip, limit=limit)

@router.get("/{job_id}/applications", response_model=List[ApplicationDetail])
def get_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business")),
    skip: int = 0,
    limit: int = 20
):
    service = JobService(db)
    applications = service.get_job_applications(job_id, current_user.id, skip=skip, limit=limit)
    if applications is None:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to view applications")
    return applications

@router.put("/applications/{application_id}/status", response_model=dict)
def update_application_status(
    application_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    if status not in ["applied", "shortlisted", "hired", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    service = JobService(db)
    success = service.update_application_status(application_id, status, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found or you don't have permission to update it")
    return {"message": "Application status updated successfully"}

