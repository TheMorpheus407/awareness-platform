"""Certificate generation and management routes."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies.auth import get_current_active_user
from core.logging import logger
from db.session import get_db
from models.course import UserCourseProgress
from models.user import User
from schemas.course import Certificate, CertificateGenerate
from services.certificate_generator import CertificateGenerator

router = APIRouter()


@router.get("/{course_id}/download", response_class=FileResponse)
async def download_certificate(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """
    Download certificate for a completed course.
    
    Returns PDF file if user has completed the course.
    """
    # Get course progress with course details
    progress = await db.execute(
        select(UserCourseProgress)
        .options(selectinload(UserCourseProgress.course))
        .where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == course_id,
        )
    )
    progress = progress.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(status_code=404, detail="Course progress not found")
    
    if progress.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Certificate is only available for completed courses"
        )
    
    # Generate certificate if not already generated
    if not progress.certificate_url:
        try:
            generator = CertificateGenerator()
            certificate_path = await generator.generate_certificate(
                user_name=f"{current_user.first_name} {current_user.last_name}",
                course_title=progress.course.title,
                completion_date=progress.completed_at or datetime.utcnow(),
                certificate_id=f"CERT-{progress.id}",
                template_name="default",
            )
            
            # Update progress with certificate URL
            progress.certificate_url = certificate_path
            progress.certificate_issued = True
            await db.commit()
            
            logger.info(
                f"Generated certificate for user {current_user.id} "
                f"for course {course_id}"
            )
        except Exception as e:
            logger.error(f"Certificate generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate certificate"
            )
    
    # Return the certificate file
    return FileResponse(
        path=progress.certificate_url,
        media_type="application/pdf",
        filename=f"certificate_{course_id}_{current_user.id}.pdf",
    )


@router.post("/{course_id}/regenerate", response_model=Certificate)
async def regenerate_certificate(
    course_id: int,
    template: Optional[str] = "default",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Certificate:
    """
    Regenerate certificate with a different template.
    
    Useful for updating certificates with new designs.
    """
    # Get course progress
    progress = await db.execute(
        select(UserCourseProgress)
        .options(selectinload(UserCourseProgress.course))
        .where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == course_id,
        )
    )
    progress = progress.scalar_one_or_none()
    
    if not progress or progress.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Certificate is only available for completed courses"
        )
    
    try:
        generator = CertificateGenerator()
        certificate_path = await generator.generate_certificate(
            user_name=f"{current_user.first_name} {current_user.last_name}",
            course_title=progress.course.title,
            completion_date=progress.completed_at or datetime.utcnow(),
            certificate_id=f"CERT-{progress.id}",
            template_name=template,
        )
        
        # Update progress
        progress.certificate_url = certificate_path
        progress.certificate_issued = True
        await db.commit()
        
        return Certificate(
            id=f"CERT-{progress.id}",
            user_id=current_user.id,
            course_id=course_id,
            issued_date=progress.completed_at or datetime.utcnow(),
            certificate_url=certificate_path,
            verification_code=f"VERIFY-{progress.id}",
        )
    except Exception as e:
        logger.error(f"Certificate regeneration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to regenerate certificate"
        )


@router.get("/verify/{verification_code}", response_model=Certificate)
async def verify_certificate(
    verification_code: str,
    db: AsyncSession = Depends(get_db),
) -> Certificate:
    """
    Verify certificate authenticity by verification code.
    
    Public endpoint for certificate verification.
    """
    # Extract progress ID from verification code
    if not verification_code.startswith("VERIFY-"):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    try:
        progress_id = int(verification_code.replace("VERIFY-", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Get course progress
    progress = await db.execute(
        select(UserCourseProgress)
        .options(
            selectinload(UserCourseProgress.course),
            selectinload(UserCourseProgress.user)
        )
        .where(UserCourseProgress.id == progress_id)
    )
    progress = progress.scalar_one_or_none()
    
    if not progress or not progress.certificate_issued:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return Certificate(
        id=f"CERT-{progress.id}",
        user_id=progress.user_id,
        user_name=f"{progress.user.first_name} {progress.user.last_name}",
        course_id=progress.course_id,
        course_title=progress.course.title,
        issued_date=progress.completed_at or progress.created_at,
        certificate_url=progress.certificate_url,
        verification_code=verification_code,
        is_valid=True,
    )


@router.get("/user/all", response_model=list[Certificate])
async def get_user_certificates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Certificate]:
    """Get all certificates earned by the current user."""
    # Get all completed courses with certificates
    result = await db.execute(
        select(UserCourseProgress)
        .options(selectinload(UserCourseProgress.course))
        .where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.status == "completed",
            UserCourseProgress.certificate_issued == True,
        )
    )
    progress_list = result.scalars().all()
    
    certificates = []
    for progress in progress_list:
        certificates.append(
            Certificate(
                id=f"CERT-{progress.id}",
                user_id=current_user.id,
                course_id=progress.course_id,
                course_title=progress.course.title,
                issued_date=progress.completed_at or progress.created_at,
                certificate_url=progress.certificate_url,
                verification_code=f"VERIFY-{progress.id}",
                is_valid=True,
            )
        )
    
    return certificates