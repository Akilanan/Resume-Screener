"""
S3 Storage Service for Resume Files
Supports AWS S3 and S3-compatible services (MinIO)
"""
import os
import uuid
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

from app.core.config import settings


class S3StorageError(Exception):
    """S3 storage operation failed"""
    pass


class S3Service:
    def __init__(self):
        self.s3_client = None
        self.bucket = settings.AWS_S3_BUCKET
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.region = settings.AWS_REGION
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client with proper credentials"""
        if not self.bucket:
            logger.warning("AWS_S3_BUCKET not configured. S3 storage disabled.")
            return
        
        try:
            kwargs = {
                'region_name': self.region,
                'service_name': 's3'
            }
            
            # Use custom endpoint for MinIO/local S3
            if self.endpoint_url:
                kwargs['endpoint_url'] = self.endpoint_url
            
            # Check for credentials
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
                kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
            else:
                logger.warning("AWS credentials not configured, attempting IAM role")
            
            self.s3_client = boto3.client(**kwargs)
            
            # Test connection
            if self.endpoint_url:
                self.s3_client.list_buckets()
                logger.info(f"S3 connected to custom endpoint: {self.endpoint_url}")
            else:
                logger.info(f"S3 connected to AWS region: {self.region}")
                
        except NoCredentialsError:
            logger.warning("No AWS credentials found. S3 storage may not work.")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {e}")
    
    def is_available(self) -> bool:
        """Check if S3 storage is available"""
        return self.s3_client is not None and bool(self.bucket)
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = "application/pdf") -> Optional[str]:
        """
        Upload file to S3 and return the S3 URI
        """
        if not self.is_available():
            raise S3StorageError("S3 storage not configured")
        
        # Generate unique filename to prevent collisions
        ext = os.path.splitext(filename)[1] or '.pdf'
        unique_filename = f"resumes/{uuid.uuid4()}{ext}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=unique_filename,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )
            
            s3_uri = f"s3://{self.bucket}/{unique_filename}"
            logger.info(f"Uploaded file to S3: {s3_uri}")
            return s3_uri
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise S3StorageError(f"S3 upload failed: {e}")
    
    def delete_file(self, s3_uri: str) -> bool:
        """Delete file from S3"""
        if not self.is_available():
            return False
        
        try:
            # Parse s3://bucket/key
            if s3_uri.startswith("s3://"):
                uri_parts = s3_uri[5:].split("/", 1)
                bucket = uri_parts[0]
                key = uri_parts[1] if len(uri_parts) > 1 else ""
            else:
                return False
            
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted file from S3: {s3_uri}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False
    
    def generate_presigned_url(self, s3_uri: str, expires_in: int = 3600) -> Optional[str]:
        """Generate presigned URL for downloading file"""
        if not self.is_available():
            return None
        
        try:
            if s3_uri.startswith("s3://"):
                uri_parts = s3_uri[5:].split("/", 1)
                bucket = uri_parts[0]
                key = uri_parts[1] if len(uri_parts) > 1 else ""
            else:
                return None
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None


# Singleton instance
s3_service = S3Service()


def is_s3_configured() -> bool:
    """Check if S3 is properly configured"""
    return s3_service.is_available()


def upload_to_s3(file_content: bytes, filename: str, content_type: str = "application/pdf") -> str:
    """Convenience function for uploading files"""
    return s3_service.upload_file(file_content, filename, content_type)