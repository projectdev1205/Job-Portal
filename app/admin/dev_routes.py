from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.admin.admin_service import AdminService
from app.config import settings

router = APIRouter(prefix="/dev", tags=["Development"])

@router.post("/reset-database", status_code=status.HTTP_200_OK)
async def reset_database_dev(
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """
    Development endpoint to reset the database.
    Only available in development environment.
    This will delete all existing data!
    
    Args:
        confirm: Must be True to confirm the reset operation
        db: Database session
    
    Returns:
        Success message
    """
    # Only allow in development environment
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
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
            "status": "success",
            "environment": settings.environment
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset database: {str(e)}"
        )

@router.get("/database-stats", status_code=status.HTTP_200_OK)
async def get_database_stats_dev(
    db: Session = Depends(get_db)
):
    """
    Development endpoint to get database statistics.
    Only available in development environment.
    """
    # Only allow in development environment
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
        )
    
    try:
        admin_service = AdminService(db)
        stats = admin_service.get_database_stats()
        return {
            "stats": stats,
            "environment": settings.environment
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database stats: {str(e)}"
        )

@router.post("/create-admin", status_code=status.HTTP_201_CREATED)
async def create_admin_dev(
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
    db: Session = Depends(get_db)
):
    """
    Development endpoint to create an admin user.
    Only available in development environment.
    """
    # Only allow in development environment
    if settings.environment != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
        )
    
    try:
        from app.auth.auth_service import AuthService
        from app.schemas import AdminRegisterIn
        
        # Create admin registration payload
        admin_data = AdminRegisterIn(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            admin_code="ADMIN_SECRET_2024",
            terms_accepted=True
        )
        
        auth_service = AuthService(db)
        admin_user = auth_service.register_admin(admin_data)
        
        return {
            "message": "Admin user created successfully",
            "user": {
                "id": admin_user.id,
                "email": admin_user.email,
                "name": f"{admin_user.first_name or ''} {admin_user.last_name or ''}".strip() or "Unknown User",
                "role": admin_user.role
            },
            "environment": settings.environment
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin user: {str(e)}"
        )
