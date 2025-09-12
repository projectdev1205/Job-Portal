from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import JobCreate, JobSummary, JobDetail
from app.business.business_service import JobService
from app.auth.auth_deps import require_role
from app.models import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=dict)
def create_job(
    payload: JobCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Create a new job posting with specified action (Save, Save & Publish)"""
    service = JobService(db)
    
    # Create the job with appropriate status
    job = service.create_job(payload, user_id=current_user.id)
    
    if payload.action == "save_and_publish":
        return {
            "message": "Job saved and published successfully",
            "job_id": job.id,
            "status": job.status,
            "action": "save_and_publish"
        }
    else:  # action == "save"
        return {
            "message": "Job saved as draft",
            "job_id": job.id,
            "status": job.status,
            "action": "save"
        }


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
    compensation_type: Optional[str] = None,
    status: Optional[str] = None
):
    """List business with comprehensive filtering and all UI fields"""
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
        compensation_type=compensation_type,
        status=status
    )


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get detailed job information"""
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
    """Update an existing job with specified action (Save, Save & Publish)"""
    service = JobService(db)
    
    # Update the job with appropriate status
    updated_job = service.update_job(job_id, payload, user_id=current_user.id)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to update it")
    
    if payload.action == "save_and_publish":
        return {
            "message": "Job updated and published successfully",
            "job_id": updated_job.id,
            "status": updated_job.status,
            "action": "save_and_publish"
        }
    else:  # action == "save"
        return {
            "message": "Job updated and saved as draft",
            "job_id": updated_job.id,
            "status": updated_job.status,
            "action": "save"
        }


@router.delete("/{job_id}", response_model=dict)
def delete_job(
    job_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Delete a job"""
    service = JobService(db)
    success = service.delete_job(job_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to delete it")
    return {"message": "Job deleted", "job_id": job_id}