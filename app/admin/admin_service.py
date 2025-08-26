from sqlalchemy.orm import Session
from app.database import engine, Base
from app.models import User, Job, Application, BusinessProfile

class AdminService:
    def __init__(self, db: Session):
        self.db = db
    
    def reset_database(self):
        """
        Reset the database by dropping and recreating all tables.
        This will delete all existing data!
        """
        try:
            # Drop all tables
            Base.metadata.drop_all(bind=engine)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            return True
        except Exception as e:
            raise Exception(f"Failed to reset database: {str(e)}")
    
    def get_database_stats(self):
        """
        Get database statistics for admin dashboard
        """
        try:
            user_count = self.db.query(User).count()
            job_count = self.db.query(Job).count()
            application_count = self.db.query(Application).count()
            business_profile_count = self.db.query(BusinessProfile).count()
            
            return {
                "users": user_count,
                "jobs": job_count,
                "applications": application_count,
                "business_profiles": business_profile_count
            }
        except Exception as e:
            raise Exception(f"Failed to get database stats: {str(e)}")
