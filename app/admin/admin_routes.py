from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.auth.auth_deps import get_current_user
from app.models import User
from app.admin.admin_service import AdminService
from app.schemas import MigrationResponse, DatabaseStatus
import subprocess
import os
import psycopg2
from datetime import datetime

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

@router.get("/database/status", response_model=DatabaseStatus)
async def get_database_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get database connection status and schema information
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )
    
    try:
        # Test database connection
        connection_status = "connected"
        connection_error = None
        
        try:
            # Test basic connection
            db.execute(text("SELECT 1"))
        except Exception as e:
            connection_status = "disconnected"
            connection_error = str(e)
        
        # Check for missing columns in applications table
        missing_columns = []
        try:
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'applications' 
                AND table_schema = 'public'
                AND column_name IN ('relevant_experience', 'education', 'availability', 'references', 'terms_accepted', 'contact_permission')
                ORDER BY column_name;
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            required_columns = ['relevant_experience', 'education', 'availability', 'references', 'terms_accepted', 'contact_permission']
            missing_columns = list(set(required_columns) - set(existing_columns))
            
        except Exception as e:
            missing_columns = ["Unable to check columns"]
        
        return DatabaseStatus(
            connection_status=connection_status,
            connection_error=connection_error,
            missing_columns=missing_columns,
            needs_migration=len(missing_columns) > 0,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database status: {str(e)}"
        )

@router.post("/database/migrate", response_model=MigrationResponse)
async def run_database_migration(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run database migration to add missing columns
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )
    
    try:
        # Check if migration is needed
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'applications' 
            AND table_schema = 'public'
            AND column_name IN ('relevant_experience', 'education', 'availability', 'references', 'terms_accepted', 'contact_permission')
            ORDER BY column_name;
        """))
        
        existing_columns = [row[0] for row in result.fetchall()]
        required_columns = ['relevant_experience', 'education', 'availability', 'references', 'terms_accepted', 'contact_permission']
        missing_columns = list(set(required_columns) - set(existing_columns))
        
        if not missing_columns:
            return MigrationResponse(
                success=True,
                message="No migration needed - all columns already exist",
                missing_columns=[],
                timestamp=datetime.utcnow()
            )
        
        # Run the migration
        migration_sql = []
        
        if 'relevant_experience' in missing_columns:
            migration_sql.append("ALTER TABLE applications ADD COLUMN relevant_experience TEXT;")
        
        if 'education' in missing_columns:
            migration_sql.append("ALTER TABLE applications ADD COLUMN education TEXT;")
        
        if 'availability' in missing_columns:
            migration_sql.append("ALTER TABLE applications ADD COLUMN availability VARCHAR(255);")
        
        if 'references' in missing_columns:
            migration_sql.append('ALTER TABLE applications ADD COLUMN "references" TEXT;')
        
        if 'terms_accepted' in missing_columns:
            migration_sql.append("ALTER TABLE applications ADD COLUMN terms_accepted BOOLEAN DEFAULT FALSE;")
        
        if 'contact_permission' in missing_columns:
            migration_sql.append("ALTER TABLE applications ADD COLUMN contact_permission BOOLEAN DEFAULT FALSE;")
        
        # Execute migration
        for sql in migration_sql:
            db.execute(text(sql))
        
        db.commit()
        
        return MigrationResponse(
            success=True,
            message=f"Migration completed successfully. Added {len(missing_columns)} columns.",
            missing_columns=missing_columns,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )

@router.post("/database/backup")
async def create_database_backup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a database backup using SQL dump
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint"
        )
    
    try:
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}.sql"
        
        # Get database connection info from the existing connection
        from app.config import settings
        
        # Extract connection details from database URL
        db_url = settings.database_url
        if not db_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database URL not configured"
            )
        
        # Parse the database URL to get connection details
        # Format: postgresql+psycopg://user:password@host:port/database
        import urllib.parse as urlparse
        
        # Remove the +psycopg part for parsing
        clean_url = db_url.replace("postgresql+psycopg://", "postgresql://")
        parsed = urlparse.urlparse(clean_url)
        
        db_host = parsed.hostname
        db_port = parsed.port or 5432
        db_name = parsed.path.lstrip('/')
        db_user = parsed.username
        db_password = parsed.password
        
        if not all([db_host, db_name, db_user, db_password]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not extract database connection information from URL"
            )
        
        # Try to run pg_dump first
        try:
            dump_cmd = [
                "pg_dump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
                "--create",
                f"--file={backup_file}"
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password
            
            result = subprocess.run(
                dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Backup created successfully: {backup_file}",
                    "backup_file": backup_file,
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Fallback: Create a simple SQL backup using the existing connection
            return await create_simple_backup(db, backup_file)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )

async def create_simple_backup(db: Session, backup_file: str):
    """
    Create a simple backup using SQL queries (fallback when pg_dump is not available)
    """
    try:
        backup_content = []
        backup_content.append("-- Simple Database Backup")
        backup_content.append(f"-- Created: {datetime.utcnow()}")
        backup_content.append("-- This is a simplified backup created via SQL queries")
        backup_content.append("")
        
        # Get all table names
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        for table in tables:
            backup_content.append(f"-- Table: {table}")
            backup_content.append(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
            # Get table structure
            result = db.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            if columns:
                column_defs = []
                for col in columns:
                    col_name, data_type, is_nullable, default = col
                    col_def = f"{col_name} {data_type}"
                    if is_nullable == 'NO':
                        col_def += " NOT NULL"
                    if default:
                        col_def += f" DEFAULT {default}"
                    column_defs.append(col_def)
                
                backup_content.append(f"CREATE TABLE {table} ({', '.join(column_defs)});")
                
                # Get table data
                result = db.execute(text(f"SELECT * FROM {table};"))
                rows = result.fetchall()
                
                if rows:
                    backup_content.append(f"-- Data for table {table}")
                    for row in rows:
                        values = []
                        for value in row:
                            if value is None:
                                values.append("NULL")
                            elif isinstance(value, str):
                                values.append(f"'{value.replace("'", "''")}'")
                            else:
                                values.append(str(value))
                        backup_content.append(f"INSERT INTO {table} VALUES ({', '.join(values)});")
                
                backup_content.append("")
        
        # Write backup file
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(backup_content))
        
        return {
            "success": True,
            "message": f"Simple backup created successfully: {backup_file}",
            "backup_file": backup_file,
            "backup_type": "simple_sql",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise Exception(f"Simple backup failed: {str(e)}")