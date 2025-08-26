from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User
from app.schemas import (
    DashboardResponse, DashboardMetrics, DashboardJobSummary, 
    JobStatusUpdate
)
from app.auth.auth_deps import require_role
from app.dashboard.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Get dashboard data for business user"""
    service = DashboardService(db)
    return service.get_dashboard_data(current_user.id)


@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Get dashboard metrics only"""
    service = DashboardService(db)
    return service._get_metrics(current_user.id)


@router.get("/jobs", response_model=List[DashboardJobSummary])
def get_dashboard_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business")),
    search: Optional[str] = None,
    status: Optional[str] = None
):
    """Get job listings for dashboard with optional filtering"""
    service = DashboardService(db)
    return service.get_filtered_jobs(current_user.id, search=search, status=status)


@router.put("/jobs/{job_id}/status", response_model=dict)
def update_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Update job status (active/archived)"""
    service = DashboardService(db)
    success = service.update_job_status(job_id, current_user.id, payload.status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to update it")
    
    return {"message": f"Job status updated to {payload.status}", "job_id": job_id}


@router.post("/jobs/{job_id}/archive", response_model=dict)
def archive_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Archive a job"""
    service = DashboardService(db)
    success = service.update_job_status(job_id, current_user.id, "archived")
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to archive it")
    
    return {"message": "Job archived successfully", "job_id": job_id}


@router.post("/jobs/{job_id}/unarchive", response_model=dict)
def unarchive_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("business"))
):
    """Unarchive a job"""
    service = DashboardService(db)
    success = service.update_job_status(job_id, current_user.id, "active")
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or you don't have permission to unarchive it")
    
    return {"message": "Job unarchived successfully", "job_id": job_id}
