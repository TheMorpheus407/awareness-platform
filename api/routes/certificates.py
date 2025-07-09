"""Certificate API routes."""

from typing import Optional
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_

from api.dependencies.auth import get_current_active_user
from db.session import get_db
from models import (
    User, UserRole, Course, CourseEnrollment,
    ProgressStatus
)
from services.certificate_generator import certificate_generator

router = APIRouter()


@router.get("/enrollments/{enrollment_id}/certificate")
def get_certificate(
    enrollment_id: int,
    regenerate: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get or generate certificate for a completed course."""
    # Get enrollment
    enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.id == enrollment_id,
            CourseEnrollment.user_id == current_user.id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Check if course is completed
    if enrollment.status != ProgressStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must be completed to generate certificate"
        )
    
    # Check if certificate already exists and not regenerating
    if enrollment.certificate_url and not regenerate:
        # Return existing certificate
        try:
            return FileResponse(
                enrollment.certificate_url,
                media_type="application/pdf",
                filename=f"certificate_{enrollment.completion_certificate_id}.pdf"
            )
        except FileNotFoundError:
            # Certificate file missing, regenerate
            pass
    
    # Generate new certificate
    course = enrollment.course
    company = enrollment.company
    
    # Ensure certificate ID exists
    if not enrollment.completion_certificate_id:
        enrollment.completion_certificate_id = uuid.uuid4()
        enrollment.certificate_issued_at = datetime.utcnow()
        if course.validity_days:
            enrollment.certificate_expires_at = datetime.utcnow() + timedelta(days=course.validity_days)
    
    # Generate certificate
    try:
        certificate_path = certificate_generator.generate_certificate(
            enrollment=enrollment,
            user=current_user,
            course=course,
            company=company,
            template="compliance" if course.compliance_standards else "default"
        )
        
        # Update enrollment
        enrollment.certificate_url = certificate_path
        if not enrollment.certificate_issued_at:
            enrollment.certificate_issued_at = datetime.utcnow()
        
        db.commit()
        
        # Return certificate file
        return FileResponse(
            certificate_path,
            media_type="application/pdf",
            filename=f"certificate_{enrollment.completion_certificate_id}.pdf"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate certificate: {str(e)}"
        )


@router.get("/verify/{certificate_id}")
def verify_certificate(
    certificate_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Verify a certificate by its ID."""
    # Find enrollment by certificate ID
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.completion_certificate_id == certificate_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    # Check if certificate is valid
    is_valid = True
    validity_message = "Certificate is valid"
    
    if enrollment.certificate_expires_at and enrollment.certificate_expires_at < datetime.utcnow():
        is_valid = False
        validity_message = f"Certificate expired on {enrollment.certificate_expires_at.strftime('%B %d, %Y')}"
    
    # Get user and course info
    user = enrollment.user
    course = enrollment.course
    company = enrollment.company
    
    return {
        "certificate_id": certificate_id,
        "is_valid": is_valid,
        "validity_message": validity_message,
        "issued_to": {
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "company": company.name
        },
        "course": {
            "title": course.title,
            "category": course.category,
            "duration_minutes": course.duration_minutes
        },
        "issued_at": enrollment.certificate_issued_at,
        "completed_at": enrollment.completed_at,
        "expires_at": enrollment.certificate_expires_at,
        "compliance_standards": course.compliance_standards
    }


@router.get("/courses/{course_id}/certificate-preview")
def preview_certificate(
    course_id: int,
    template: str = "default",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Preview certificate template for a course (admin/instructor only)."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Generate preview
    try:
        preview_pdf = certificate_generator.generate_certificate_preview(
            course=course,
            template=template
        )
        
        return Response(
            content=preview_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=certificate_preview_{course_id}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get("/my-certificates")
def list_my_certificates(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all certificates earned by the current user."""
    # Get completed enrollments with certificates
    enrollments = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.status == ProgressStatus.COMPLETED,
            CourseEnrollment.certificate_issued_at.isnot(None)
        )
    ).order_by(CourseEnrollment.certificate_issued_at.desc()).offset(skip).limit(limit).all()
    
    certificates = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Check validity
        is_valid = True
        if enrollment.certificate_expires_at and enrollment.certificate_expires_at < datetime.utcnow():
            is_valid = False
        
        certificates.append({
            "enrollment_id": enrollment.id,
            "certificate_id": enrollment.completion_certificate_id,
            "course": {
                "id": course.id,
                "title": course.title,
                "category": course.category,
                "thumbnail_url": course.thumbnail_url
            },
            "issued_at": enrollment.certificate_issued_at,
            "expires_at": enrollment.certificate_expires_at,
            "is_valid": is_valid,
            "can_download": bool(enrollment.certificate_url)
        })
    
    return {
        "certificates": certificates,
        "total": db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.status == ProgressStatus.COMPLETED,
                CourseEnrollment.certificate_issued_at.isnot(None)
            )
        ).count()
    }


@router.post("/enrollments/{enrollment_id}/request-certificate")
def request_certificate(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Request certificate generation for a completed course."""
    # Get enrollment
    enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.id == enrollment_id,
            CourseEnrollment.user_id == current_user.id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Check if course is completed
    if enrollment.status != ProgressStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must be completed to request certificate"
        )
    
    # Check if certificate already requested
    if enrollment.certificate_issued_at:
        return {
            "message": "Certificate already issued",
            "certificate_id": enrollment.completion_certificate_id,
            "issued_at": enrollment.certificate_issued_at
        }
    
    # Mark certificate as requested (actual generation happens on download)
    enrollment.completion_certificate_id = uuid.uuid4()
    enrollment.certificate_issued_at = datetime.utcnow()
    
    course = enrollment.course
    if course.validity_days:
        from datetime import timedelta
        enrollment.certificate_expires_at = datetime.utcnow() + timedelta(days=course.validity_days)
    
    db.commit()
    
    return {
        "message": "Certificate generation requested",
        "certificate_id": enrollment.completion_certificate_id,
        "enrollment_id": enrollment.id
    }