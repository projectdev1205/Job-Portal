from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import json

from app.database import get_db
from app.schemas import JobSummary, JobDetail, ApplicationOut, ApplicationFormCreate
from app.applicant.applicant_service import ApplicantJobService
from app.auth.auth_deps import require_role
from app.models import User
from app.utils.s3_service import s3_service
from app.config import settings

router = APIRouter(prefix="/applicant", tags=["Applicant Jobs"])


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
    """List all active business with filtering and pagination (for applicants to browse)"""
    service = ApplicantJobService(db)
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
    """Get detailed job information (only active business)"""
    service = ApplicantJobService(db)
    job = service.get_job_detail(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def create_application_form(
    job_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    street_address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    cover_letter: Optional[str] = Form(None),
    relevant_experience: Optional[str] = Form(None),
    education: Optional[str] = Form(None),
    availability: Optional[str] = Form(None),
    references: Optional[str] = Form(None),
    terms_accepted: bool = Form(...),
    contact_permission: bool = Form(False),
    resume: Optional[UploadFile] = File(None)
) -> ApplicationFormCreate:
    """Dependency to create ApplicationFormCreate from form data"""
    if not terms_accepted:
        raise HTTPException(status_code=400, detail="Terms and conditions must be accepted")
    
    # Handle resume upload if provided
    resume_filename = None
    if resume and resume.filename:
        # Read file content
        content = resume.file.read()
        resume.file.seek(0)  # Reset file pointer
        
        # Validate file using S3 service
        s3_service.validate_file(content, resume.content_type, settings.max_file_size_mb)
        
        # Get file extension
        file_extension = resume.filename.split('.')[-1] if '.' in resume.filename else 'pdf'
        
        if settings.use_s3:
            # Upload to S3 in resumes folder
            resume_filename = s3_service.upload_file(content, file_extension, "resumes")
        else:
            # Fallback to local storage
            resume_filename = f"{uuid.uuid4()}.{file_extension}"
            upload_dir = "uploads/resumes"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, resume_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(content)
    
    return ApplicationFormCreate(
        job_id=job_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        street_address=street_address,
        city=city,
        state=state,
        zip_code=zip_code,
        resume_filename=resume_filename,
        cover_letter=cover_letter,
        relevant_experience=relevant_experience,
        education=education,
        availability=availability,
        references=references,
        terms_accepted=terms_accepted,
        contact_permission=contact_permission
    )


@router.post("/{job_id}/apply", response_model=dict)
def apply_to_job(
    job_id: int,
    form_data: ApplicationFormCreate = Depends(create_application_form),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("applicant"))
):
    """Apply to a job with comprehensive form data and resume upload (matches UI form)"""
    service = ApplicantJobService(db)
    application = service.apply_to_job(job_id, current_user.id, form_data)
    if not application:
        raise HTTPException(status_code=400, detail="Unable to apply (job not found or already applied)")
    return {"message": "Application submitted successfully", "application_id": application.id}




@router.get("/applications/my", response_model=List[ApplicationOut])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("applicant")),
    skip: int = 0,
    limit: int = 20
):
    """Get current user's applications"""
    service = ApplicantJobService(db)
    return service.get_user_applications(current_user.id, skip=skip, limit=limit)


@router.get("/files/{file_path:path}")
def get_file_url(file_path: str):
    """Get file URL (S3 presigned URL or local file path)"""
    if settings.use_s3:
        # Generate presigned URL for S3 file
        try:
            url = s3_service.get_file_url(file_path)
            return {"url": url}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        # Return local file path
        return {"url": f"/files/{file_path}"}
