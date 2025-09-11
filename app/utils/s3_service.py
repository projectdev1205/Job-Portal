import boto3
import uuid
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.aws_region
        self.folder_prefix = settings.s3_folder_prefix
        
        # Initialize S3 client
        if settings.use_s3:
            try:
                if settings.aws_access_key_id and settings.aws_secret_access_key:
                    # Use explicit credentials
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.aws_access_key_id,
                        aws_secret_access_key=settings.aws_secret_access_key,
                        region_name=self.region
                    )
                else:
                    # Use IAM role or default credentials
                    self.s3_client = boto3.client('s3', region_name=self.region)
                
                # Test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"S3 service initialized successfully with bucket: {self.bucket_name}")
                
            except NoCredentialsError:
                logger.error("AWS credentials not found")
                raise HTTPException(status_code=500, detail="AWS credentials not configured")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    logger.error(f"S3 bucket '{self.bucket_name}' not found")
                    raise HTTPException(status_code=500, detail=f"S3 bucket '{self.bucket_name}' not found")
                else:
                    logger.error(f"S3 error: {e}")
                    raise HTTPException(status_code=500, detail="S3 service unavailable")
        else:
            self.s3_client = None
            logger.info("S3 service disabled, using local file storage")

    def upload_file(self, file_content: bytes, file_extension: str, folder: str = "resumes") -> Optional[str]:
        """
        Upload file to S3 and return the S3 key/path
        
        Args:
            file_content: File content as bytes
            file_extension: File extension (e.g., 'pdf', 'docx')
            folder: S3 folder name (e.g., 'resumes', 'cover-letters')
            
        Returns:
            S3 key/path if successful, None if S3 is disabled
        """
        if not settings.use_s3 or not self.s3_client:
            return None
            
        try:
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            s3_key = f"{self.folder_prefix}{folder}/{unique_filename}"
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(file_extension)
            )
            
            logger.info(f"File uploaded to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")

    def get_file_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for file access
        
        Args:
            s3_key: S3 key/path of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL for file access
        """
        if not settings.use_s3 or not self.s3_client:
            # Return local file path if S3 is disabled
            return f"/files/{s3_key}"
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate file URL")

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 key/path of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not settings.use_s3 or not self.s3_client:
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

    def _get_content_type(self, file_extension: str) -> str:
        """Get MIME type based on file extension"""
        content_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')

    def validate_file(self, file_content: bytes, content_type: str, max_size_mb: int = None) -> bool:
        """
        Validate file before upload
        
        Args:
            file_content: File content as bytes
            content_type: MIME type of the file
            max_size_mb: Maximum file size in MB
            
        Returns:
            True if valid, raises HTTPException if invalid
        """
        # Check file size
        max_size = max_size_mb or settings.max_file_size_mb
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size must be less than {max_size}MB"
            )
        
        # Check file type
        allowed_types = [
            "application/pdf",
            "application/msword", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ]
        
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOC, DOCX, and TXT files are allowed"
            )
        
        return True


# Global S3 service instance
s3_service = S3Service()
