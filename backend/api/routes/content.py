"""Content delivery routes for secure file access."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_active_user, get_optional_current_user
from core.config import settings
from core.logging import logger
from core.security import SecurityUtils
from db.session import get_db
from models.course import Course, UserCourseProgress
from models.user import User
from schemas.content import (
    ContentAccessToken,
    ContentMetadata,
    ContentUploadResponse,
    SecureContentURL,
)
# Conditional import due to boto3 dependency issues
try:
    from services.content_delivery import ContentDeliveryService
    HAS_CONTENT_DELIVERY = True
except ImportError as e:
    logger.warning(f"ContentDeliveryService not available: {str(e)}")
    ContentDeliveryService = None
    HAS_CONTENT_DELIVERY = False

router = APIRouter()


@router.get("/course/{course_id}/video", response_model=SecureContentURL)
async def get_course_video_url(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SecureContentURL:
    """
    Get secure URL for course video content.
    
    Returns a time-limited signed URL for video streaming.
    """
    # Check if user is enrolled
    progress = await db.execute(
        select(UserCourseProgress).where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == course_id,
        )
    )
    if not progress.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in the course to access content"
        )
    
    # Get course
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if not course.youtube_video_id:
        raise HTTPException(
            status_code=404,
            detail="This course does not have video content"
        )
    
    # Generate secure access token
    if not HAS_CONTENT_DELIVERY:
        raise HTTPException(
            status_code=503,
            detail="Content delivery service is not available"
        )
    content_service = ContentDeliveryService()
    
    # For YouTube videos, return the video ID with access token
    access_token = SecurityUtils.create_content_access_token(
        user_id=current_user.id,
        course_id=course_id,
        content_type="video",
        duration_minutes=120,  # 2 hour access
    )
    
    return SecureContentURL(
        url=f"https://www.youtube.com/embed/{course.youtube_video_id}",
        access_token=access_token,
        expires_at=datetime.utcnow() + timedelta(minutes=120),
        content_type="video/youtube",
    )


@router.get("/course/{course_id}/materials", response_model=list[ContentMetadata])
async def get_course_materials(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ContentMetadata]:
    """Get list of downloadable course materials."""
    # Check enrollment
    progress = await db.execute(
        select(UserCourseProgress).where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == course_id,
        )
    )
    if not progress.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in the course to access materials"
        )
    
    # Get course materials from content service
    if not HAS_CONTENT_DELIVERY:
        raise HTTPException(
            status_code=503,
            detail="Content delivery service is not available"
        )
    content_service = ContentDeliveryService()
    materials = await content_service.list_course_materials(course_id)
    
    # Generate metadata with secure URLs
    material_list = []
    for material in materials:
        access_token = SecurityUtils.create_content_access_token(
            user_id=current_user.id,
            course_id=course_id,
            content_type="document",
            content_id=material["id"],
            duration_minutes=60,
        )
        
        material_list.append(
            ContentMetadata(
                id=material["id"],
                name=material["name"],
                content_type=material["content_type"],
                size_bytes=material["size"],
                upload_date=material["upload_date"],
                download_url=f"/api/v1/content/download/{material['id']}?token={access_token}",
            )
        )
    
    return material_list


@router.get("/download/{content_id}")
async def download_content(
    content_id: str,
    token: str = Query(..., description="Access token"),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Download protected content with access token.
    
    Token must be valid and user must have access rights.
    """
    # Verify access token
    try:
        payload = SecurityUtils.verify_content_access_token(token)
    except Exception as e:
        logger.warning(f"Invalid content access token: {str(e)}")
        raise HTTPException(status_code=403, detail="Invalid or expired access token")
    
    # Verify content_id matches token
    if payload.get("content_id") != content_id:
        raise HTTPException(status_code=403, detail="Access token mismatch")
    
    # Get content from service
    if not HAS_CONTENT_DELIVERY:
        raise HTTPException(
            status_code=503,
            detail="Content delivery service is not available"
        )
    content_service = ContentDeliveryService()
    try:
        file_path = await content_service.get_content_path(content_id)
        
        # Log content access
        logger.info(
            f"User {payload['user_id']} downloading content {content_id}"
        )
        
        return FileResponse(
            path=file_path,
            filename=f"material_{content_id}.pdf",  # TODO: Get actual filename
            media_type="application/octet-stream",
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        logger.error(f"Content delivery error: {str(e)}")
        raise HTTPException(status_code=500, detail="Content delivery failed")


@router.get("/stream/{content_id}")
async def stream_content(
    content_id: str,
    token: str = Query(..., description="Access token"),
    range: Optional[str] = None,
) -> Response:
    """
    Stream video content with range support.
    
    Supports partial content requests for video streaming.
    """
    # Verify access token
    try:
        payload = SecurityUtils.verify_content_access_token(token)
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid or expired access token")
    
    # Get content service
    if not HAS_CONTENT_DELIVERY:
        raise HTTPException(
            status_code=503,
            detail="Content delivery service is not available"
        )
    content_service = ContentDeliveryService()
    
    try:
        # Handle range requests for video streaming
        if range:
            # Parse range header
            range_start = 0
            range_end = None
            
            if range.startswith("bytes="):
                range_spec = range[6:]
                parts = range_spec.split("-")
                if parts[0]:
                    range_start = int(parts[0])
                if len(parts) > 1 and parts[1]:
                    range_end = int(parts[1])
            
            # Stream partial content
            content, content_length, content_range = await content_service.stream_content(
                content_id, range_start, range_end
            )
            
            return Response(
                content=content,
                status_code=206,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(content_length),
                    "Content-Range": content_range,
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "no-cache",
                },
            )
        else:
            # Stream full content
            content = await content_service.get_content(content_id)
            return Response(
                content=content,
                media_type="video/mp4",
                headers={
                    "Cache-Control": "no-cache",
                    "Accept-Ranges": "bytes",
                },
            )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        logger.error(f"Content streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail="Content streaming failed")


@router.post("/upload/course/{course_id}", response_model=ContentUploadResponse)
async def upload_course_material(
    course_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContentUploadResponse:
    """
    Upload course material (admin only).
    
    Supports PDF, PPT, and other document formats.
    """
    # Check admin permissions
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can upload course materials"
        )
    
    # Validate file
    if file.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Check file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_UPLOAD_EXTENSIONS}"
        )
    
    # Upload file
    if not HAS_CONTENT_DELIVERY:
        raise HTTPException(
            status_code=503,
            detail="Content delivery service is not available"
        )
    content_service = ContentDeliveryService()
    try:
        content_id = await content_service.upload_content(
            file=file.file,
            filename=file.filename,
            content_type=file.content_type,
            course_id=course_id,
            uploaded_by=current_user.id,
        )
        
        logger.info(
            f"User {current_user.id} uploaded material {content_id} "
            f"for course {course_id}"
        )
        
        return ContentUploadResponse(
            content_id=content_id,
            filename=file.filename,
            size_bytes=file.size,
            content_type=file.content_type,
            upload_date=datetime.utcnow(),
            message="File uploaded successfully",
        )
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.delete("/material/{content_id}", status_code=204)
async def delete_course_material(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete course material (admin only)."""
    # Check admin permissions
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete course materials"
        )
    
    # Delete content
    if not HAS_CONTENT_DELIVERY:
        raise HTTPException(
            status_code=503,
            detail="Content delivery service is not available"
        )
    content_service = ContentDeliveryService()
    try:
        await content_service.delete_content(content_id)
        logger.info(
            f"User {current_user.id} deleted content {content_id}"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        logger.error(f"Content deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Content deletion failed")