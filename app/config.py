from typing import List
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    db_user: str = os.getenv("DB_USER", "")
    db_pass: str = os.getenv("DB_PASS", "")
    db_host: str = os.getenv("DB_HOST", "")
    db_name: str = os.getenv("DB_NAME", "")

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.db_user}:{self.db_pass}@{self.db_host}/{self.db_name}"

    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    frontend_url: Optional[str] = None
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080"
    )

    @property
    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-2")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "worklyst-files")
    s3_folder_prefix: str = os.getenv("S3_FOLDER_PREFIX", "uploads/")
    
    # File storage settings
    use_s3: bool = os.getenv("USE_S3", "false").lower() == "true"
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
    
    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "detailed")  # detailed, simple, json

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "",
        "extra": "ignore"
    }

settings = Settings()