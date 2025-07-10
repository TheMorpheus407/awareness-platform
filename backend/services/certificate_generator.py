"""
Certificate generator service for creating PDF certificates using ReportLab.
"""

import io
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
import logging
from pathlib import Path
import qrcode
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Course, UserCourseProgress, Company
from core.config import settings
from core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CertificateGenerator:
    """Service for generating PDF certificates."""

    def __init__(self, db: AsyncSession):
        """Initialize certificate generator."""
        self.db = db
        self.template_dir = Path(__file__).parent.parent / "templates" / "certificates"
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Default certificate settings
        self.page_size = A4
        self.margin = 2 * cm
        self.primary_color = HexColor("#2E7D32")  # Green
        self.secondary_color = HexColor("#1976D2")  # Blue
        self.text_color = HexColor("#333333")
        
        # Load fonts if available
        self._register_fonts()

    def _register_fonts(self):
        """Register custom fonts if available."""
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Try to register custom fonts
            font_dir = self.template_dir / "fonts"
            if font_dir.exists():
                for font_file in font_dir.glob("*.ttf"):
                    font_name = font_file.stem
                    pdfmetrics.registerFont(TTFont(font_name, str(font_file)))
                    logger.info(f"Registered font: {font_name}")
        except Exception as e:
            logger.warning(f"Could not register custom fonts: {str(e)}")

    async def generate_course_certificate(
        self,
        user_id: int,
        course_id: int,
        template: str = "default"
    ) -> bytes:
        """
        Generate a course completion certificate.

        Args:
            user_id: User ID
            course_id: Course ID
            template: Certificate template to use

        Returns:
            PDF content as bytes
        """
        # Get user, course, and progress data
        user = await self.db.get(User, user_id)
        if not user:
            raise ValidationError("User not found")

        course = await self.db.get(Course, course_id)
        if not course:
            raise ValidationError("Course not found")

        # Get course progress
        progress = await self._get_course_progress(user_id, course_id)
        if not progress or progress.completion_percentage < 100:
            raise ValidationError("Course not completed")

        company = await self.db.get(Company, user.company_id)

        # Generate certificate
        certificate_data = {
            "user_name": f"{user.first_name} {user.last_name}",
            "course_title": course.title,
            "completion_date": progress.completed_at or datetime.utcnow(),
            "score": progress.quiz_score,
            "certificate_id": self._generate_certificate_id(user_id, course_id),
            "company_name": company.name if company else settings.APP_NAME,
        }

        # Select template method
        if template == "professional":
            return self._generate_professional_certificate(certificate_data)
        elif template == "modern":
            return self._generate_modern_certificate(certificate_data)
        else:
            return self._generate_default_certificate(certificate_data)

    async def _get_course_progress(
        self,
        user_id: int,
        course_id: int
    ) -> Optional[UserCourseProgress]:
        """Get user's course progress."""
        from sqlalchemy import select
        
        stmt = select(UserCourseProgress).where(
            UserCourseProgress.user_id == user_id,
            UserCourseProgress.course_id == course_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _generate_certificate_id(self, user_id: int, course_id: int) -> str:
        """Generate unique certificate ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"CERT-{user_id:04d}-{course_id:04d}-{timestamp}"

    def _generate_default_certificate(self, data: Dict[str, Any]) -> bytes:
        """Generate default certificate template."""
        buffer = io.BytesIO()
        
        # Create canvas
        c = canvas.Canvas(buffer, pagesize=self.page_size)
        width, height = self.page_size
        
        # Add border
        c.setStrokeColor(self.primary_color)
        c.setLineWidth(3)
        c.rect(self.margin, self.margin, width - 2*self.margin, height - 2*self.margin)
        
        # Add decorative corners
        self._add_decorative_corners(c, width, height)
        
        # Add header
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(width/2, height - 3*self.margin, "CERTIFICATE")
        
        c.setFont("Helvetica", 24)
        c.drawCentredString(width/2, height - 4*self.margin, "OF COMPLETION")
        
        # Add content
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 18)
        c.drawCentredString(width/2, height - 6*self.margin, "This is to certify that")
        
        # User name
        c.setFillColor(self.secondary_color)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width/2, height - 7.5*self.margin, data["user_name"])
        
        # Course completion text
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 18)
        c.drawCentredString(width/2, height - 9*self.margin, "has successfully completed the course")
        
        # Course title
        c.setFillColor(self.secondary_color)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 10.5*self.margin, data["course_title"])
        
        # Score and date
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 16)
        if data.get("score") is not None:
            c.drawCentredString(
                width/2,
                height - 12*self.margin,
                f"with a score of {data['score']}%"
            )
        
        c.drawCentredString(
            width/2,
            height - 13*self.margin,
            f"on {data['completion_date'].strftime('%B %d, %Y')}"
        )
        
        # Add signature line
        y_pos = height - 16*self.margin
        c.setLineWidth(1)
        c.line(width/4, y_pos, width/4 + width/4, y_pos)
        c.line(width/2 + width/8, y_pos, width - width/4, y_pos)
        
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/4 + width/8, y_pos - 20, "Instructor")
        c.drawCentredString(width - width/4 - width/8, y_pos - 20, "Date")
        
        # Add certificate ID and QR code
        self._add_footer(c, width, height, data)
        
        # Save PDF
        c.save()
        
        buffer.seek(0)
        return buffer.read()

    def _generate_professional_certificate(self, data: Dict[str, Any]) -> bytes:
        """Generate professional certificate template."""
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=36,
            textColor=self.primary_color,
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=24,
            textColor=self.secondary_color,
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=16,
            textColor=self.text_color,
            spaceAfter=15,
            alignment=TA_CENTER,
        )
        
        # Add content
        elements.append(Paragraph("CERTIFICATE OF ACHIEVEMENT", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph("This is to certify that", body_style))
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph(f"<b>{data['user_name']}</b>", subtitle_style))
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph("has successfully completed", body_style))
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph(f"<b>{data['course_title']}</b>", subtitle_style))
        elements.append(Spacer(1, 0.5*inch))
        
        if data.get("score") is not None:
            elements.append(
                Paragraph(f"Achieved Score: <b>{data['score']}%</b>", body_style)
            )
        
        elements.append(
            Paragraph(
                f"Date: <b>{data['completion_date'].strftime('%B %d, %Y')}</b>",
                body_style
            )
        )
        
        elements.append(Spacer(1, 1*inch))
        
        # Add signatures
        sig_style = ParagraphStyle(
            'Signature',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
        )
        
        elements.append(
            Paragraph(
                "_____________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "_____________________",
                sig_style
            )
        )
        elements.append(
            Paragraph(
                "Program Director&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Date",
                sig_style
            )
        )
        
        # Build PDF
        doc.build(elements, onFirstPage=lambda c, d: self._add_professional_header_footer(c, d, data))
        
        buffer.seek(0)
        return buffer.read()

    def _generate_modern_certificate(self, data: Dict[str, Any]) -> bytes:
        """Generate modern certificate template with graphics."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=self.page_size)
        width, height = self.page_size
        
        # Background gradient effect
        self._add_gradient_background(c, width, height)
        
        # Modern geometric design
        self._add_modern_design_elements(c, width, height)
        
        # Content with modern typography
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(width/2, height - 3*self.margin, "CERTIFICATE")
        
        c.setFont("Helvetica", 20)
        c.drawCentredString(width/2, height - 4*self.margin, "OF EXCELLENCE")
        
        # White box for main content
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.roundRect(
            self.margin * 1.5,
            height/2 - 3*self.margin,
            width - 3*self.margin,
            6*self.margin,
            20,
            fill=1
        )
        
        # Add content in white box
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height/2 + 1.5*self.margin, "Awarded to")
        
        c.setFillColor(self.primary_color)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(width/2, height/2, data["user_name"])
        
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height/2 - 1.5*self.margin, "for completing")
        
        c.setFillColor(self.secondary_color)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height/2 - 2.5*self.margin, data["course_title"])
        
        # Add badge or icon
        self._add_achievement_badge(c, width/2, height - 8*self.margin, data)
        
        # Footer with QR code
        self._add_modern_footer(c, width, height, data)
        
        c.save()
        buffer.seek(0)
        return buffer.read()

    def _add_decorative_corners(self, c: canvas.Canvas, width: float, height: float):
        """Add decorative corners to certificate."""
        corner_size = 50
        c.setStrokeColor(self.primary_color)
        c.setLineWidth(2)
        
        # Top-left
        c.lines([
            (self.margin, height - self.margin - corner_size,
             self.margin, height - self.margin,
             self.margin + corner_size, height - self.margin)
        ])
        
        # Top-right
        c.lines([
            (width - self.margin - corner_size, height - self.margin,
             width - self.margin, height - self.margin,
             width - self.margin, height - self.margin - corner_size)
        ])
        
        # Bottom-left
        c.lines([
            (self.margin, self.margin + corner_size,
             self.margin, self.margin,
             self.margin + corner_size, self.margin)
        ])
        
        # Bottom-right
        c.lines([
            (width - self.margin - corner_size, self.margin,
             width - self.margin, self.margin,
             width - self.margin, self.margin + corner_size)
        ])

    def _add_footer(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        data: Dict[str, Any]
    ):
        """Add footer with certificate ID and QR code."""
        # Certificate ID
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 10)
        c.drawString(
            self.margin,
            self.margin/2,
            f"Certificate ID: {data['certificate_id']}"
        )
        
        # Company name
        c.drawRightString(
            width - self.margin,
            self.margin/2,
            data.get("company_name", settings.APP_NAME)
        )
        
        # Generate QR code
        verification_url = f"{settings.FRONTEND_URL}/verify/{data['certificate_id']}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        # Convert QR to image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Add QR code to PDF
        c.drawImage(
            ImageReader(qr_buffer),
            width - self.margin - 60,
            self.margin,
            60,
            60,
            preserveAspectRatio=True
        )

    def _add_professional_header_footer(
        self,
        c: canvas.Canvas,
        doc: SimpleDocTemplate,
        data: Dict[str, Any]
    ):
        """Add header and footer for professional template."""
        width, height = doc.pagesize
        
        # Header line
        c.setStrokeColor(self.primary_color)
        c.setLineWidth(2)
        c.line(doc.leftMargin, height - doc.topMargin/2, width - doc.rightMargin, height - doc.topMargin/2)
        
        # Footer
        c.setLineWidth(1)
        c.line(doc.leftMargin, doc.bottomMargin, width - doc.rightMargin, doc.bottomMargin)
        
        # Certificate details
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 9)
        c.drawString(doc.leftMargin, doc.bottomMargin - 15, f"Certificate ID: {data['certificate_id']}")
        c.drawRightString(
            width - doc.rightMargin,
            doc.bottomMargin - 15,
            f"Issued by {data.get('company_name', settings.APP_NAME)}"
        )

    def _add_gradient_background(
        self,
        c: canvas.Canvas,
        width: float,
        height: float
    ):
        """Add gradient background effect."""
        # Simple gradient simulation with rectangles
        steps = 20
        for i in range(steps):
            alpha = 1 - (i / steps)
            color = HexColor("#E3F2FD")  # Light blue
            c.setFillColorRGB(
                color.red * alpha + (1-alpha),
                color.green * alpha + (1-alpha),
                color.blue * alpha + (1-alpha)
            )
            c.rect(0, i * height/steps, width, height/steps, fill=1, stroke=0)

    def _add_modern_design_elements(
        self,
        c: canvas.Canvas,
        width: float,
        height: float
    ):
        """Add modern geometric design elements."""
        # Abstract shapes
        c.setFillColor(self.primary_color)
        c.setAlpha(0.3)
        
        # Top right triangle
        c.beginPath()
        c.moveTo(width - width/4, height)
        c.lineTo(width, height)
        c.lineTo(width, height - height/4)
        c.closePath()
        c.fill()
        
        # Bottom left triangle
        c.beginPath()
        c.moveTo(0, height/4)
        c.lineTo(0, 0)
        c.lineTo(width/4, 0)
        c.closePath()
        c.fill()
        
        c.setAlpha(1)

    def _add_achievement_badge(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        data: Dict[str, Any]
    ):
        """Add achievement badge or icon."""
        # Draw a simple badge
        radius = 40
        c.setFillColor(self.primary_color)
        c.circle(x, y, radius, fill=1)
        
        # Add stars or checkmark
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(x, y - 8, "✓")
        
        # Score badge if applicable
        if data.get("score") is not None and data["score"] >= 90:
            c.setFillColor(HexColor("#FFD700"))  # Gold
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(x, y - radius - 15, "EXCELLENCE")

    def _add_modern_footer(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        data: Dict[str, Any]
    ):
        """Add modern footer design."""
        # Colored footer band
        c.setFillColor(self.primary_color)
        c.rect(0, 0, width, self.margin, fill=1, stroke=0)
        
        # Footer text
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(
            self.margin,
            self.margin/2 - 5,
            f"Certificate ID: {data['certificate_id']}"
        )
        c.drawRightString(
            width - self.margin,
            self.margin/2 - 5,
            f"© {datetime.utcnow().year} {data.get('company_name', settings.APP_NAME)}"
        )

    async def generate_batch_certificates(
        self,
        user_course_pairs: List[Tuple[int, int]],
        template: str = "default"
    ) -> Dict[int, bytes]:
        """
        Generate multiple certificates.

        Args:
            user_course_pairs: List of (user_id, course_id) tuples
            template: Certificate template to use

        Returns:
            Dict mapping user_id to certificate PDF bytes
        """
        certificates = {}
        
        for user_id, course_id in user_course_pairs:
            try:
                pdf_content = await self.generate_course_certificate(
                    user_id,
                    course_id,
                    template
                )
                certificates[user_id] = pdf_content
            except Exception as e:
                logger.error(
                    f"Failed to generate certificate for user {user_id}, "
                    f"course {course_id}: {str(e)}"
                )

        return certificates

    async def verify_certificate(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Verify a certificate by its ID."""
        # Parse certificate ID
        try:
            parts = certificate_id.split("-")
            if len(parts) < 4 or parts[0] != "CERT":
                return None
                
            user_id = int(parts[1])
            course_id = int(parts[2])
            
            # Verify the certificate exists
            progress = await self._get_course_progress(user_id, course_id)
            if not progress or progress.completion_percentage < 100:
                return None
                
            # Get user and course info
            user = await self.db.get(User, user_id)
            course = await self.db.get(Course, course_id)
            
            if not user or not course:
                return None
                
            return {
                "valid": True,
                "certificate_id": certificate_id,
                "user_name": f"{user.first_name} {user.last_name}",
                "course_title": course.title,
                "completion_date": progress.completed_at,
                "score": progress.quiz_score,
            }
            
        except Exception as e:
            logger.error(f"Error verifying certificate {certificate_id}: {str(e)}")
            return None