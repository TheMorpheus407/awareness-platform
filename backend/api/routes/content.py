"""Content delivery API routes."""

from typing import Optional
from datetime import datetime
import jwt

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_

from api.dependencies.auth import get_current_active_user
from db.session import get_db
from core.config import get_settings
from models import (
    User, CourseContent, CourseEnrollment, Lesson,
    ProgressStatus
)
from services.content_delivery import content_delivery

router = APIRouter()
settings = get_settings()


def verify_content_access(
    content: CourseContent,
    user: User,
    db: Session
) -> bool:
    """Verify user has access to content."""
    # Get lesson and course
    lesson = content.lesson
    module = lesson.module
    course = module.course
    
    # Check if lesson is preview
    if lesson.is_preview:
        return True
    
    # Check enrollment
    enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course.id
        )
    ).first()
    
    return enrollment is not None


@router.get("/content/{content_id}/url")
def get_content_url(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get secure URL for accessing content."""
    # Get content
    content = db.query(CourseContent).filter(
        CourseContent.id == content_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify access
    if not verify_content_access(content, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get secure URL
    try:
        url = content_delivery.get_content_url(
            content=content,
            user_id=current_user.id,
            expires_in=7200  # 2 hours
        )
        
        return {
            "url": url,
            "expires_in": 7200,
            "content_type": content.content_type,
            "mime_type": content.mime_type
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content URL: {str(e)}"
        )


@router.get("/stream/{content_id}")
def stream_content(
    content_id: int,
    token: str = Query(...),
    range: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Stream content with token authentication."""
    # Verify token
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        if payload.get("content_id") != content_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token"
            )
        
        user_id = payload.get("user_id")
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )
    
    # Get content
    content = db.query(CourseContent).filter(
        CourseContent.id == content_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Stream content
    try:
        data, headers = content_delivery.stream_content(
            content=content,
            range_header=range
        )
        
        # Return streaming response
        if range:
            return Response(
                content=data,
                status_code=206,  # Partial Content
                headers=headers
            )
        else:
            return Response(
                content=data,
                headers=headers
            )
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content file not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream content: {str(e)}"
        )


@router.get("/content/{content_id}/metadata")
def get_content_metadata(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed metadata about content."""
    # Get content
    content = db.query(CourseContent).filter(
        CourseContent.id == content_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify access
    if not verify_content_access(content, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get metadata
    metadata = content_delivery.get_content_metadata(content)
    
    # Add lesson context
    lesson = content.lesson
    metadata["lesson"] = {
        "id": lesson.id,
        "title": lesson.title,
        "module": {
            "id": lesson.module.id,
            "title": lesson.module.title
        }
    }
    
    return metadata


@router.post("/content/{content_id}/track-progress")
def track_content_progress(
    content_id: int,
    progress: float = Query(..., ge=0, le=100),
    position_seconds: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Track user's progress on content (e.g., video position)."""
    # Get content
    content = db.query(CourseContent).filter(
        CourseContent.id == content_id
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify access
    if not verify_content_access(content, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get enrollment
    lesson = content.lesson
    course = lesson.module.course
    
    enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enrolled in course"
        )
    
    # Store progress in content metadata (or separate tracking table)
    if not content.metadata:
        content.metadata = {}
    
    if "user_progress" not in content.metadata:
        content.metadata["user_progress"] = {}
    
    content.metadata["user_progress"][str(current_user.id)] = {
        "progress": progress,
        "position_seconds": position_seconds,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Mark metadata as modified for SQLAlchemy to detect the change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(content, "metadata")
    
    db.commit()
    
    # If content is 95% complete, consider it viewed
    if progress >= 95:
        # Update lesson progress
        from api.routes.enrollments import update_lesson_progress
        from schemas.course import LessonProgressUpdate
        
        progress_update = LessonProgressUpdate(
            progress_percentage=progress,
            last_position_seconds=position_seconds
        )
        
        update_lesson_progress(
            lesson_id=lesson.id,
            progress_in=progress_update,
            db=db,
            current_user=current_user
        )
    
    return {
        "message": "Progress tracked",
        "content_id": content_id,
        "progress": progress,
        "position_seconds": position_seconds
    }


@router.get("/lessons/{lesson_id}/download-materials")
def download_lesson_materials(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get download links for all downloadable materials in a lesson."""
    # Get lesson
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Check enrollment (unless preview)
    if not lesson.is_preview:
        course = lesson.module.course
        enrollment = db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.course_id == course.id
            )
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enrollment required"
            )
    
    # Get downloadable content
    downloadable_types = [
        ContentType.DOCUMENT,
        ContentType.PRESENTATION
    ]
    
    contents = db.query(CourseContent).filter(
        and_(
            CourseContent.lesson_id == lesson_id,
            CourseContent.content_type.in_(downloadable_types)
        )
    ).order_by(CourseContent.order_index).all()
    
    # Generate download URLs
    materials = []
    for content in contents:
        try:
            url = content_delivery.get_content_url(
                content=content,
                user_id=current_user.id,
                expires_in=3600  # 1 hour
            )
            
            materials.append({
                "id": content.id,
                "title": content.title,
                "type": content.content_type,
                "mime_type": content.mime_type,
                "size_bytes": content.file_size_bytes,
                "download_url": url
            })
            
        except Exception:
            continue
    
    return {
        "lesson_id": lesson_id,
        "lesson_title": lesson.title,
        "materials": materials,
        "total": len(materials)
    }