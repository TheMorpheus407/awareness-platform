"""Certificate generation and download routes."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.dependencies.auth import get_current_active_user
from api.dependencies.common import get_db
from core.exceptions import ValidationError
from models.user import User
from models.course import Course, UserCourseProgress
from services.certificate_generator import CertificateGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/course/{course_id}")
async def get_course_certificate(
    course_id: int,
    template: Optional[str] = "default",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Generate and download course completion certificate.
    
    Args:
        course_id: ID of the completed course
        template: Certificate template (default, professional, modern)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PDF certificate file
        
    Raises:
        HTTPException: If course not completed or certificate generation fails
    """
    try:
        # Check if user has completed the course
        stmt = select(UserCourseProgress).where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == course_id,
            UserCourseProgress.status == "completed"
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not completed or not found"
            )
        
        # Generate certificate
        cert_generator = CertificateGenerator(db)
        pdf_content = await cert_generator.generate_course_certificate(
            user_id=current_user.id,
            course_id=course_id,
            template=template
        )
        
        # Get course for filename
        course = await db.get(Course, course_id)
        filename = f"certificate_{course.title.replace(' ', '_')}_{current_user.last_name}.pdf"
        
        # Update certificate URL if not set
        if not progress.certificate_url:
            progress.certificate_issued = True
            progress.certificate_url = f"/api/v1/certificates/course/{course_id}"
            await db.commit()
        
        # Return PDF response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            }
        )
        
    except ValidationError as e:
        logger.warning(f"Certificate validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Certificate generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate certificate"
        )


@router.get("/verify/{certificate_id}")
async def verify_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify a certificate by its ID.
    
    Args:
        certificate_id: Certificate ID to verify
        db: Database session
        
    Returns:
        Certificate verification result
    """
    cert_generator = CertificateGenerator(db)
    result = await cert_generator.verify_certificate(certificate_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found or invalid"
        )
    
    return result


@router.get("/user/all")
async def get_user_certificates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict]:
    """
    Get all certificates for the current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of user's certificates
    """
    # Get all completed courses
    stmt = select(UserCourseProgress, Course).join(
        Course, UserCourseProgress.course_id == Course.id
    ).where(
        UserCourseProgress.user_id == current_user.id,
        UserCourseProgress.status == "completed",
        UserCourseProgress.certificate_issued == True
    )
    
    result = await db.execute(stmt)
    completed_courses = result.all()
    
    certificates = []
    for progress, course in completed_courses:
        # Generate certificate ID
        cert_id = f"CERT-{current_user.id:04d}-{course.id:04d}-{progress.completed_at.strftime('%Y%m%d%H%M%S')}"
        
        certificates.append({
            "certificate_id": cert_id,
            "course_id": course.id,
            "course_title": course.title,
            "completion_date": progress.completed_at,
            "score": progress.progress_percentage,
            "download_url": f"/api/v1/certificates/course/{course.id}",
            "verification_url": f"/api/v1/certificates/verify/{cert_id}",
        })
    
    return certificates


@router.get("/batch/download")
async def download_batch_certificates(
    course_ids: str,
    template: Optional[str] = "default",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Download multiple certificates as a ZIP file.
    
    Args:
        course_ids: Comma-separated list of course IDs
        template: Certificate template to use
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ZIP file containing certificates
    """
    import io
    import zipfile
    
    try:
        # Parse course IDs
        course_id_list = [int(id.strip()) for id in course_ids.split(",")]
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            cert_generator = CertificateGenerator(db)
            
            for course_id in course_id_list:
                try:
                    # Check if user completed the course
                    stmt = select(UserCourseProgress).where(
                        UserCourseProgress.user_id == current_user.id,
                        UserCourseProgress.course_id == course_id,
                        UserCourseProgress.status == "completed"
                    )
                    result = await db.execute(stmt)
                    progress = result.scalar_one_or_none()
                    
                    if progress:
                        # Generate certificate
                        pdf_content = await cert_generator.generate_course_certificate(
                            user_id=current_user.id,
                            course_id=course_id,
                            template=template
                        )
                        
                        # Get course for filename
                        course = await db.get(Course, course_id)
                        filename = f"certificate_{course.title.replace(' ', '_')}.pdf"
                        
                        # Add to ZIP
                        zip_file.writestr(filename, pdf_content)
                        
                except Exception as e:
                    logger.error(f"Failed to generate certificate for course {course_id}: {str(e)}")
                    continue
        
        # Prepare ZIP for download
        zip_buffer.seek(0)
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="certificates_{datetime.utcnow().strftime("%Y%m%d")}.zip"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            }
        )
        
    except Exception as e:
        logger.error(f"Batch certificate error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch certificates"
        )


@router.post("/regenerate/{course_id}")
async def regenerate_certificate(
    course_id: int,
    template: Optional[str] = "default",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Regenerate a certificate for a completed course.
    
    Args:
        course_id: Course ID
        template: Certificate template
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message with download URL
    """
    # Check if user has completed the course
    stmt = select(UserCourseProgress).where(
        UserCourseProgress.user_id == current_user.id,
        UserCourseProgress.course_id == course_id,
        UserCourseProgress.status == "completed"
    )
    result = await db.execute(stmt)
    progress = result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not completed or not found"
        )
    
    # Update certificate issued flag
    progress.certificate_issued = True
    progress.certificate_url = f"/api/v1/certificates/course/{course_id}"
    await db.commit()
    
    return {
        "message": "Certificate regenerated successfully",
        "download_url": f"/api/v1/certificates/course/{course_id}?template={template}"
    }


@router.get("/templates")
async def get_certificate_templates(
    current_user: User = Depends(get_current_active_user),
) -> list[dict]:
    """
    Get available certificate templates.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of available templates
    """
    return [
        {
            "id": "default",
            "name": "Default Certificate",
            "description": "Classic certificate design with decorative borders",
            "preview_url": "/api/v1/certificates/preview/default"
        },
        {
            "id": "professional",
            "name": "Professional Certificate",
            "description": "Clean, professional design suitable for corporate use",
            "preview_url": "/api/v1/certificates/preview/professional"
        },
        {
            "id": "modern",
            "name": "Modern Certificate",
            "description": "Contemporary design with geometric elements",
            "preview_url": "/api/v1/certificates/preview/modern"
        }
    ]


@router.get("/preview/{template}")
async def preview_certificate_template(
    template: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Preview a certificate template with sample data.
    
    Args:
        template: Template ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Sample certificate PDF
    """
    try:
        # Create sample data
        sample_data = {
            "user_name": f"{current_user.first_name} {current_user.last_name}",
            "course_title": "Sample Course: Introduction to Cybersecurity",
            "completion_date": datetime.utcnow(),
            "score": 95,
            "certificate_id": "CERT-SAMPLE-001",
            "company_name": "Your Company Name",
        }
        
        cert_generator = CertificateGenerator(db)
        
        # Generate certificate based on template
        if template == "professional":
            pdf_content = cert_generator._generate_professional_certificate(sample_data)
        elif template == "modern":
            pdf_content = cert_generator._generate_modern_certificate(sample_data)
        else:
            pdf_content = cert_generator._generate_default_certificate(sample_data)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="preview_{template}.pdf"',
                "Cache-Control": "public, max-age=3600",
            }
        )
        
    except Exception as e:
        logger.error(f"Certificate preview error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview"
        )