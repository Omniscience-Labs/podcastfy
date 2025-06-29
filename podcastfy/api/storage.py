"""
Storage management for podcast files.

This module handles file storage using S3-compatible storage (AWS S3, MinIO, etc.).
"""

import os
import io
from typing import Optional, BinaryIO, Union
from datetime import datetime, timedelta
import mimetypes

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class StorageManager:
    """Manage file storage in S3-compatible storage."""
    
    def __init__(self):
        """Initialize storage manager with S3 client."""
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'podcastfy')
        self.endpoint_url = os.getenv('S3_ENDPOINT_URL')  # None for AWS S3
        self.region_name = os.getenv('AWS_REGION', 'us-east-1')
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.public_url_base = os.getenv('S3_PUBLIC_URL_BASE')
        
        # Create S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4')
        )
        
        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    if self.endpoint_url:  # MinIO or custom S3
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:  # AWS S3
                        if self.region_name == 'us-east-1':
                            self.s3_client.create_bucket(Bucket=self.bucket_name)
                        else:
                            self.s3_client.create_bucket(
                                Bucket=self.bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': self.region_name}
                            )
                    logger.info(f"Created bucket {self.bucket_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {str(create_error)}")
                    raise
            else:
                logger.error(f"Error checking bucket: {str(e)}")
                raise
    
    def upload_file(self, file_path: str, object_name: str, 
                   content_type: Optional[str] = None) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_path: Path to local file
            object_name: S3 object name
            content_type: MIME type of the file
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Upload file
            extra_args = {
                'ContentType': content_type,
                'CacheControl': 'max-age=86400'  # Cache for 24 hours
            }
            
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                object_name,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{object_name}")
            
            # Return public URL
            return self.get_public_url(object_name)
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except NoCredentialsError:
            logger.error("S3 credentials not available")
            raise
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise
    
    def upload_fileobj(self, file_obj: BinaryIO, object_name: str,
                      content_type: str = 'application/octet-stream') -> str:
        """
        Upload a file object to S3.
        
        Args:
            file_obj: File-like object
            object_name: S3 object name
            content_type: MIME type of the file
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'max-age=86400'
                }
            )
            
            logger.info(f"Uploaded file object to s3://{self.bucket_name}/{object_name}")
            return self.get_public_url(object_name)
            
        except Exception as e:
            logger.error(f"Failed to upload file object: {str(e)}")
            raise
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download a file from S3.
        
        Args:
            object_name: S3 object name
            file_path: Local file path to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(
                self.bucket_name,
                object_name,
                file_path
            )
            logger.info(f"Downloaded s3://{self.bucket_name}/{object_name} to {file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file: {str(e)}")
            return False
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            object_name: S3 object name or full URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract object name if full URL provided
            if object_name.startswith('http'):
                object_name = object_name.split('/')[-1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"Deleted s3://{self.bucket_name}/{object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            object_name: S3 object name
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return True
        except ClientError:
            return False
    
    def get_public_url(self, object_name: str) -> str:
        """
        Get public URL for an S3 object.
        
        Args:
            object_name: S3 object name
            
        Returns:
            Public URL
        """
        if self.public_url_base:
            # Use custom public URL base (e.g., CloudFront)
            return f"{self.public_url_base.rstrip('/')}/{object_name}"
        elif self.endpoint_url:
            # MinIO or custom S3
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
        else:
            # AWS S3
            return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{object_name}"
    
    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            object_name: S3 object name
            expiration: Time in seconds for URL to remain valid
            
        Returns:
            Presigned URL
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> list:
        """
        List files in S3 bucket.
        
        Args:
            prefix: Filter results to objects beginning with prefix
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object names
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
            
        except ClientError as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        try:
            # Get bucket size
            total_size = 0
            total_count = 0
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
                        total_count += 1
            
            return {
                'bucket_name': self.bucket_name,
                'total_files': total_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                'bucket_name': self.bucket_name,
                'error': str(e)
            }
    
    def health_check(self) -> bool:
        """
        Check if storage is accessible.
        
        Returns:
            True if storage is healthy, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.error(f"Storage health check failed: {str(e)}")
            return False 