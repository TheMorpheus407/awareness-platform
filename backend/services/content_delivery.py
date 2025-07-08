"""Content delivery service for course materials."""

from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import mimetypes
import hashlib
import re
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import urllib.parse

from backend.core.config import get_settings
from backend.models import CourseContent, ContentType

settings = get_settings()


class ContentDeliveryService:
    """Handle secure delivery of course content."""
    
    def __init__(self):
        """Initialize content delivery service."""
        self.s3_client = None
        self.cloudfront_client = None
        
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            # Initialize CloudFront client if distribution ID is set
            if hasattr(settings, 'CLOUDFRONT_DISTRIBUTION_ID'):
                self.cloudfront_client = boto3.client(
                    'cloudfront',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
        
        # Local storage fallback
        self.local_storage_path = Path(settings.UPLOAD_DIR) / "course_content"
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    def upload_content(
        self,
        file_path: str,
        content_type: ContentType,
        course_id: int,
        lesson_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload content to storage and return access information."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate unique key
        file_hash = self._calculate_file_hash(file_path)
        file_extension = file_path.suffix
        storage_key = f"courses/{course_id}/lessons/{lesson_id}/{file_hash}{file_extension}"
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        result = {
            "storage_key": storage_key,
            "mime_type": mime_type,
            "file_size": file_path.stat().st_size,
            "file_hash": file_hash
        }
        
        if self.s3_client:
            # Upload to S3
            try:
                extra_args = {
                    'ContentType': mime_type or 'application/octet-stream',
                    'Metadata': metadata or {}
                }
                
                # Add caching headers for static content
                if content_type in [ContentType.DOCUMENT, ContentType.PRESENTATION]:
                    extra_args['CacheControl'] = 'max-age=86400'  # 1 day
                
                self.s3_client.upload_file(
                    str(file_path),
                    settings.S3_BUCKET_NAME,
                    storage_key,
                    ExtraArgs=extra_args
                )
                
                result["storage_type"] = "s3"
                result["bucket"] = settings.S3_BUCKET_NAME
                
            except ClientError as e:
                raise Exception(f"Failed to upload to S3: {str(e)}")
        else:
            # Use local storage
            local_path = self.local_storage_path / storage_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to local storage
            import shutil
            shutil.copy2(file_path, local_path)
            
            result["storage_type"] = "local"
            result["local_path"] = str(local_path)
        
        return result
    
    def get_content_url(
        self,
        content: CourseContent,
        user_id: int,
        expires_in: int = 3600
    ) -> str:
        """Get secure URL for accessing content."""
        # If external content, return the URL directly
        if content.content_type == ContentType.EXTERNAL_LINK:
            return content.content_url
        
        # YouTube/Vimeo content
        if content.external_id:
            if content.content_type == ContentType.VIDEO:
                if "youtube" in (content.content_url or ""):
                    return f"https://www.youtube.com/embed/{content.external_id}"
                elif "vimeo" in (content.content_url or ""):
                    return f"https://player.vimeo.com/video/{content.external_id}"
        
        # Generate signed URL for protected content
        if content.content_url:
            if self.s3_client and content.content_url.startswith("s3://"):
                # Parse S3 URL
                parsed = urllib.parse.urlparse(content.content_url)
                bucket = parsed.netloc
                key = parsed.path.lstrip("/")
                
                # Generate presigned URL
                try:
                    url = self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': key},
                        ExpiresIn=expires_in
                    )
                    
                    # If CloudFront is configured, use it instead
                    if self.cloudfront_client and hasattr(settings, 'CLOUDFRONT_DOMAIN'):
                        url = self._generate_cloudfront_url(key, expires_in)
                    
                    return url
                    
                except ClientError:
                    raise Exception("Failed to generate content URL")
            
            elif content.content_url.startswith("local://"):
                # Generate temporary access token for local files
                token = self._generate_access_token(content.id, user_id, expires_in)
                return f"{settings.API_URL}/v1/content/stream/{content.id}?token={token}"
            
            else:
                # Direct URL (public content)
                return content.content_url
        
        raise Exception("No content URL available")
    
    def stream_content(
        self,
        content: CourseContent,
        range_header: Optional[str] = None
    ) -> Tuple[bytes, Dict[str, str]]:
        """Stream content with support for range requests."""
        headers = {}
        
        if content.content_url and content.content_url.startswith("local://"):
            # Parse local path
            local_path = content.content_url.replace("local://", "")
            file_path = Path(local_path)
            
            if not file_path.exists():
                raise FileNotFoundError("Content not found")
            
            file_size = file_path.stat().st_size
            
            # Handle range requests for video streaming
            if range_header:
                try:
                    # Parse range header
                    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
                    if range_match:
                        start = int(range_match.group(1))
                        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                        
                        # Read requested range
                        with open(file_path, 'rb') as f:
                            f.seek(start)
                            data = f.read(end - start + 1)
                        
                        # Set headers for partial content
                        headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                        headers['Accept-Ranges'] = 'bytes'
                        headers['Content-Length'] = str(len(data))
                        headers['Content-Type'] = content.mime_type or 'application/octet-stream'
                        
                        return data, headers
                except Exception:
                    pass
            
            # Full file request
            with open(file_path, 'rb') as f:
                data = f.read()
            
            headers['Content-Length'] = str(file_size)
            headers['Content-Type'] = content.mime_type or 'application/octet-stream'
            headers['Accept-Ranges'] = 'bytes'
            
            return data, headers
        
        raise Exception("Content streaming not available")
    
    def delete_content(self, content: CourseContent) -> bool:
        """Delete content from storage."""
        try:
            if content.content_url:
                if self.s3_client and content.content_url.startswith("s3://"):
                    # Parse S3 URL
                    parsed = urllib.parse.urlparse(content.content_url)
                    bucket = parsed.netloc
                    key = parsed.path.lstrip("/")
                    
                    # Delete from S3
                    self.s3_client.delete_object(Bucket=bucket, Key=key)
                    
                elif content.content_url.startswith("local://"):
                    # Delete local file
                    local_path = content.content_url.replace("local://", "")
                    file_path = Path(local_path)
                    if file_path.exists():
                        file_path.unlink()
            
            return True
            
        except Exception:
            return False
    
    def get_content_metadata(self, content: CourseContent) -> Dict[str, Any]:
        """Get detailed metadata about content."""
        metadata = {
            "id": content.id,
            "title": content.title,
            "type": content.content_type,
            "duration": content.duration_seconds,
            "size": content.file_size_bytes,
            "mime_type": content.mime_type
        }
        
        # Add type-specific metadata
        if content.content_type == ContentType.VIDEO:
            if content.metadata:
                metadata.update({
                    "resolution": content.metadata.get("resolution"),
                    "codec": content.metadata.get("codec"),
                    "bitrate": content.metadata.get("bitrate"),
                    "has_captions": content.metadata.get("has_captions", False)
                })
        
        elif content.content_type == ContentType.DOCUMENT:
            if content.metadata:
                metadata.update({
                    "page_count": content.metadata.get("page_count"),
                    "format": content.metadata.get("format"),
                    "searchable": content.metadata.get("searchable", True)
                })
        
        elif content.content_type == ContentType.SCORM:
            if content.metadata:
                metadata.update({
                    "scorm_version": content.metadata.get("scorm_version"),
                    "manifest_identifier": content.metadata.get("manifest_identifier"),
                    "launch_path": content.metadata.get("launch_path")
                })
        
        return metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _generate_access_token(
        self,
        content_id: int,
        user_id: int,
        expires_in: int
    ) -> str:
        """Generate temporary access token for content."""
        import jwt
        
        payload = {
            "content_id": content_id,
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        
        return token
    
    def _generate_cloudfront_url(self, key: str, expires_in: int) -> str:
        """Generate CloudFront signed URL."""
        # Implementation depends on CloudFront configuration
        # This is a placeholder
        domain = getattr(settings, 'CLOUDFRONT_DOMAIN', '')
        return f"https://{domain}/{key}"
    
    def validate_scorm_package(self, file_path: Path) -> Dict[str, Any]:
        """Validate and extract metadata from SCORM package."""
        import zipfile
        import xml.etree.ElementTree as ET
        
        if not zipfile.is_zipfile(file_path):
            raise ValueError("Not a valid SCORM package (not a zip file)")
        
        metadata = {}
        
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Check for imsmanifest.xml
            if 'imsmanifest.xml' not in zip_file.namelist():
                raise ValueError("Not a valid SCORM package (missing imsmanifest.xml)")
            
            # Parse manifest
            manifest_content = zip_file.read('imsmanifest.xml')
            root = ET.fromstring(manifest_content)
            
            # Extract metadata
            ns = {'imscp': 'http://www.imsproject.org/xsd/imscp_rootv1p1p2'}
            
            # Get identifier
            identifier = root.get('identifier')
            if identifier:
                metadata['manifest_identifier'] = identifier
            
            # Get launch path
            resources = root.find('.//imscp:resources', ns)
            if resources is not None:
                resource = resources.find('.//imscp:resource[@type="webcontent"]', ns)
                if resource is not None:
                    launch_path = resource.get('href')
                    if launch_path:
                        metadata['launch_path'] = launch_path
            
            # Detect SCORM version
            if 'adlcp:scormtype' in root.attrib:
                metadata['scorm_version'] = 'SCORM 2004'
            else:
                metadata['scorm_version'] = 'SCORM 1.2'
        
        return metadata


# Singleton instance
content_delivery = ContentDeliveryService()