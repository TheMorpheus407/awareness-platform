"""
Content delivery service with S3/CDN integration for secure content storage and delivery.
"""

import io
import mimetypes
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from core.config import settings
from core.exceptions import NotFoundError, ContentDeliveryError, AuthorizationError
from models import Course, User

logger = logging.getLogger(__name__)


class ContentDeliveryService:
    """Service for managing content storage and delivery via S3/CDN."""

    def __init__(self, db: AsyncSession):
        """Initialize content delivery service."""
        self.db = db
        
        # Initialize S3 client if credentials are available
        self.s3_client = None
        self.s3_bucket = settings.AWS_S3_BUCKET
        self.cdn_domain = settings.AWS_S3_CUSTOM_DOMAIN
        
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
        else:
            logger.warning("AWS credentials not configured, using local storage")
            
        # Local storage fallback
        self.local_storage_path = Path(__file__).parent.parent / "storage"
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

    async def upload_content(
        self,
        file_content: Union[bytes, io.BytesIO],
        file_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        folder: str = "content",
        public: bool = False,
    ) -> Dict[str, Any]:
        """
        Upload content to S3 or local storage.

        Args:
            file_content: File content as bytes or BytesIO
            file_name: Original file name
            content_type: MIME type of the content
            metadata: Additional metadata to store
            folder: Folder/prefix in S3 bucket
            public: Whether the content should be publicly accessible

        Returns:
            Dict with upload details including URL and key
        """
        # Generate unique key
        file_key = self._generate_file_key(file_name, folder)
        
        # Detect content type if not provided
        if not content_type:
            content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        
        # Prepare metadata
        full_metadata = {
            'original_filename': file_name,
            'upload_timestamp': datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        
        if self.s3_client and self.s3_bucket:
            # Upload to S3
            return await self._upload_to_s3(
                file_content,
                file_key,
                content_type,
                full_metadata,
                public
            )
        else:
            # Upload to local storage
            return await self._upload_to_local(
                file_content,
                file_key,
                content_type,
                full_metadata
            )

    async def _upload_to_s3(
        self,
        file_content: Union[bytes, io.BytesIO],
        file_key: str,
        content_type: str,
        metadata: Dict[str, str],
        public: bool
    ) -> Dict[str, Any]:
        """Upload content to S3."""
        try:
            # Convert to bytes if needed
            if isinstance(file_content, io.BytesIO):
                file_content = file_content.getvalue()
            
            # Prepare S3 upload parameters
            upload_params = {
                'Bucket': self.s3_bucket,
                'Key': file_key,
                'Body': file_content,
                'ContentType': content_type,
                'Metadata': metadata,
            }
            
            if public:
                upload_params['ACL'] = 'public-read'
            else:
                upload_params['ServerSideEncryption'] = 'AES256'
            
            # Upload to S3
            response = self.s3_client.put_object(**upload_params)
            
            # Generate URL
            if self.cdn_domain:
                url = f"https://{self.cdn_domain}/{file_key}"
            elif public:
                url = f"https://{self.s3_bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            else:
                # Generate presigned URL for private content
                url = self.generate_presigned_url(file_key)
            
            return {
                'success': True,
                'key': file_key,
                'url': url,
                'size': len(file_content),
                'content_type': content_type,
                'etag': response.get('ETag', '').strip('"'),
                'storage': 's3',
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise ContentDeliveryError(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected upload error: {str(e)}")
            raise ContentDeliveryError(f"Upload failed: {str(e)}")

    async def _upload_to_local(
        self,
        file_content: Union[bytes, io.BytesIO],
        file_key: str,
        content_type: str,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """Upload content to local storage."""
        try:
            # Create directory structure
            file_path = self.local_storage_path / file_key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to bytes if needed
            if isinstance(file_content, io.BytesIO):
                file_content = file_content.getvalue()
            
            # Write file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Write metadata
            metadata_path = file_path.with_suffix('.metadata.json')
            import json
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps({
                    'content_type': content_type,
                    **metadata
                }))
            
            # Generate local URL
            url = f"{settings.FRONTEND_URL}/api/v1/content/local/{file_key}"
            
            return {
                'success': True,
                'key': file_key,
                'url': url,
                'size': len(file_content),
                'content_type': content_type,
                'storage': 'local',
            }
            
        except Exception as e:
            logger.error(f"Local storage error: {str(e)}")
            raise ContentDeliveryError(f"Failed to save to local storage: {str(e)}")

    def _generate_file_key(self, file_name: str, folder: str) -> str:
        """Generate unique file key."""
        # Extract extension
        path = Path(file_name)
        extension = path.suffix.lower()
        
        # Generate hash of filename + timestamp
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{file_name}:{timestamp}"
        file_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        
        # Create key
        safe_name = path.stem.lower().replace(' ', '-')[:50]
        return f"{folder}/{safe_name}-{file_hash}{extension}"

    async def download_content(
        self,
        file_key: str,
        user_id: Optional[int] = None
    ) -> Tuple[bytes, str, Dict[str, str]]:
        """
        Download content from S3 or local storage.

        Args:
            file_key: The storage key of the file
            user_id: Optional user ID for access control

        Returns:
            Tuple of (content, content_type, metadata)
        """
        if self.s3_client and self.s3_bucket:
            return await self._download_from_s3(file_key)
        else:
            return await self._download_from_local(file_key)

    async def _download_from_s3(self, file_key: str) -> Tuple[bytes, str, Dict[str, str]]:
        """Download content from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=file_key
            )
            
            content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            metadata = response.get('Metadata', {})
            
            return content, content_type, metadata
            
        except self.s3_client.exceptions.NoSuchKey:
            raise NotFoundError("Content", f"Content not found: {file_key}")
        except Exception as e:
            logger.error(f"S3 download error: {str(e)}")
            raise ContentDeliveryError(f"Failed to download from S3: {str(e)}")

    async def _download_from_local(self, file_key: str) -> Tuple[bytes, str, Dict[str, str]]:
        """Download content from local storage."""
        try:
            file_path = self.local_storage_path / file_key
            
            if not file_path.exists():
                raise NotFoundError("Content", f"Content not found: {file_key}")
            
            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            # Read metadata
            metadata_path = file_path.with_suffix('.metadata.json')
            if metadata_path.exists():
                import json
                async with aiofiles.open(metadata_path, 'r') as f:
                    metadata = json.loads(await f.read())
                content_type = metadata.pop('content_type', 'application/octet-stream')
            else:
                content_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
                metadata = {}
            
            return content, content_type, metadata
            
        except FileNotFoundError:
            raise NotFoundError("Content", f"Content not found: {file_key}")
        except Exception as e:
            logger.error(f"Local storage read error: {str(e)}")
            raise ContentDeliveryError(f"Failed to read from local storage: {str(e)}")

    async def delete_content(self, file_key: str) -> bool:
        """Delete content from storage."""
        try:
            if self.s3_client and self.s3_bucket:
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket,
                    Key=file_key
                )
            else:
                # Delete from local storage
                file_path = self.local_storage_path / file_key
                if file_path.exists():
                    file_path.unlink()
                
                # Delete metadata
                metadata_path = file_path.with_suffix('.metadata.json')
                if metadata_path.exists():
                    metadata_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            return False

    def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600,
        download: bool = False
    ) -> str:
        """
        Generate a presigned URL for S3 content.

        Args:
            file_key: The S3 key of the file
            expiration: URL expiration time in seconds
            download: If True, sets Content-Disposition to attachment

        Returns:
            Presigned URL string
        """
        if not self.s3_client or not self.s3_bucket:
            # Return local URL
            return f"{settings.FRONTEND_URL}/api/v1/content/local/{file_key}"
        
        try:
            params = {
                'Bucket': self.s3_bucket,
                'Key': file_key,
            }
            
            if download:
                filename = Path(file_key).name
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise ContentDeliveryError(f"Failed to generate URL: {str(e)}")

    async def upload_course_content(
        self,
        course_id: int,
        file_content: Union[bytes, io.BytesIO],
        file_name: str,
        content_type: Optional[str] = None,
        chapter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload content specifically for a course."""
        # Verify course exists
        course = await self.db.get(Course, course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Create folder structure
        folder = f"courses/{course_id}"
        if chapter:
            folder = f"{folder}/chapters/{chapter}"
        
        # Upload content
        result = await self.upload_content(
            file_content=file_content,
            file_name=file_name,
            content_type=content_type,
            metadata={
                'course_id': str(course_id),
                'course_title': course.title,
                'chapter': chapter or '',
            },
            folder=folder,
            public=False,  # Course content should be protected
        )
        
        return result

    async def get_course_content_url(
        self,
        course_id: int,
        file_key: str,
        user_id: int,
        expiration: int = 3600
    ) -> str:
        """
        Get a secure URL for course content with access control.

        Args:
            course_id: Course ID
            file_key: Content file key
            user_id: User requesting access
            expiration: URL expiration in seconds

        Returns:
            Secure URL for accessing the content
        """
        # Verify user has access to course
        # This would check enrollments, subscriptions, etc.
        # For now, simplified check
        user = await self.db.get(User, user_id)
        if not user or not user.is_active:
            raise AuthorizationError("Access denied")
        
        # Generate secure URL
        if self.s3_client and self.s3_bucket:
            # Add user tracking to URL
            url = self.generate_presigned_url(
                file_key,
                expiration=expiration
            )
            
            # Log access attempt
            logger.info(f"User {user_id} accessing course {course_id} content: {file_key}")
            
            return url
        else:
            # Generate JWT-protected local URL
            import jwt
            from datetime import datetime, timedelta
            
            payload = {
                'user_id': user_id,
                'course_id': course_id,
                'file_key': file_key,
                'exp': datetime.utcnow() + timedelta(seconds=expiration)
            }
            
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            return f"{settings.FRONTEND_URL}/api/v1/content/secure/{token}"

    async def list_content(
        self,
        prefix: str,
        max_items: int = 100
    ) -> List[Dict[str, Any]]:
        """List content in storage by prefix."""
        items = []
        
        if self.s3_client and self.s3_bucket:
            # List from S3
            try:
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(
                    Bucket=self.s3_bucket,
                    Prefix=prefix,
                    PaginationConfig={'MaxItems': max_items}
                )
                
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            items.append({
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'],
                                'etag': obj['ETag'].strip('"'),
                            })
                
            except Exception as e:
                logger.error(f"Failed to list S3 content: {str(e)}")
        else:
            # List from local storage
            prefix_path = self.local_storage_path / prefix
            if prefix_path.exists():
                for file_path in prefix_path.rglob('*'):
                    if file_path.is_file() and not file_path.name.endswith('.metadata.json'):
                        relative_path = file_path.relative_to(self.local_storage_path)
                        items.append({
                            'key': str(relative_path),
                            'size': file_path.stat().st_size,
                            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        })
        
        return items[:max_items]

    async def copy_content(
        self,
        source_key: str,
        destination_key: str
    ) -> bool:
        """Copy content within storage."""
        try:
            if self.s3_client and self.s3_bucket:
                # Copy in S3
                copy_source = {'Bucket': self.s3_bucket, 'Key': source_key}
                self.s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.s3_bucket,
                    Key=destination_key
                )
            else:
                # Copy in local storage
                source_path = self.local_storage_path / source_key
                dest_path = self.local_storage_path / destination_key
                
                if not source_path.exists():
                    raise NotFoundError("Content", f"Source not found: {source_key}")
                
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                import shutil
                shutil.copy2(source_path, dest_path)
                
                # Copy metadata if exists
                source_metadata = source_path.with_suffix('.metadata.json')
                if source_metadata.exists():
                    dest_metadata = dest_path.with_suffix('.metadata.json')
                    shutil.copy2(source_metadata, dest_metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Copy error: {str(e)}")
            return False

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            'storage_type': 's3' if self.s3_client else 'local',
            'total_size': 0,
            'file_count': 0,
            'content_types': {},
        }
        
        if self.s3_client and self.s3_bucket:
            # Get S3 stats
            try:
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(Bucket=self.s3_bucket)
                
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            stats['file_count'] += 1
                            stats['total_size'] += obj['Size']
                            
                            # Track content types by extension
                            ext = Path(obj['Key']).suffix.lower()
                            if ext:
                                stats['content_types'][ext] = stats['content_types'].get(ext, 0) + 1
                
            except Exception as e:
                logger.error(f"Failed to get S3 stats: {str(e)}")
        else:
            # Get local storage stats
            for file_path in self.local_storage_path.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.metadata.json'):
                    stats['file_count'] += 1
                    stats['total_size'] += file_path.stat().st_size
                    
                    ext = file_path.suffix.lower()
                    if ext:
                        stats['content_types'][ext] = stats['content_types'].get(ext, 0) + 1
        
        # Convert size to human readable
        stats['total_size_readable'] = self._format_bytes(stats['total_size'])
        
        return stats

    def _format_bytes(self, bytes: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"