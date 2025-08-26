from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.auth_deps import get_current_user
from app.models import User
from app.admin.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reset-database", status_code=status.HTTP_200_OK)
async def reset_database(
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset the database by dropping and recreating all tables.
    This will delete all existing data!
    
    Args:
        confirm: Must be True to confirm the reset operation
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Success message
    """
    # Check if user is admin (you can modify this logic as needed)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can reset the database"
        )
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must set confirm=True to reset the database"
        )
    
    try:
        admin_service = AdminService(db)
        admin_service.reset_database()
        return {
            "message": "Database reset successfully",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset database: {str(e)}"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def admin_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin health check endpoint
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )
    
    return {
        "status": "healthy",
        "user": current_user.email,
        "role": current_user.role
    }
