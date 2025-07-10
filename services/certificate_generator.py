"""Certificate generation service for course completions."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import io
import uuid
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from PIL import Image as PILImage

from models import User, Course, CourseEnrollment, Company
from core.config import get_settings

settings = get_settings()


class CertificateGenerator:
    """Generate PDF certificates for course completions."""
    
    def __init__(self):
        """Initialize certificate generator."""
        self.template_dir = Path(__file__).parent.parent / "templates" / "certificates"
        self.output_dir = Path(settings.UPLOAD_DIR) / "certificates"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Register custom fonts if available
        try:
            font_dir = self.template_dir / "fonts"
            if (font_dir / "Montserrat-Bold.ttf").exists():
                pdfmetrics.registerFont(TTFont('Montserrat-Bold', str(font_dir / "Montserrat-Bold.ttf")))
            if (font_dir / "Montserrat-Regular.ttf").exists():
                pdfmetrics.registerFont(TTFont('Montserrat-Regular', str(font_dir / "Montserrat-Regular.ttf")))
        except Exception:
            pass  # Use default fonts if custom fonts not available
    
    def generate_certificate(
        self,
        enrollment: CourseEnrollment,
        user: User,
        course: Course,
        company: Company,
        template: str = "default"
    ) -> str:
        """Generate a certificate PDF and return the file path."""
        # Generate unique certificate ID
        cert_id = enrollment.completion_certificate_id or uuid.uuid4()
        filename = f"cert_{cert_id}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Get template method
        template_method = getattr(self, f"_create_{template}_certificate", self._create_default_certificate)
        
        # Build certificate content
        story = template_method(enrollment, user, course, company, cert_id)
        
        # Generate PDF
        doc.build(story, onFirstPage=lambda c, d: self._add_background(c, d, template))
        
        # Save to file
        pdf_buffer.seek(0)
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.read())
        
        return str(filepath)
    
    def _create_default_certificate(
        self,
        enrollment: CourseEnrollment,
        user: User,
        course: Course,
        company: Company,
        cert_id: uuid.UUID
    ) -> list:
        """Create default certificate content."""
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=36,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Heading2'],
            fontSize=28,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#444444'),
            spaceAfter=12,
            alignment=TA_CENTER,
            leading=20,
            fontName='Helvetica'
        )
        
        # Add company logo if available
        logo_path = self.template_dir / "logo.png"
        if logo_path.exists():
            logo = Image(str(logo_path), width=2*inch, height=1*inch)
            story.append(logo)
            story.append(Spacer(1, 0.5*inch))
        else:
            story.append(Spacer(1, 1*inch))
        
        # Certificate title
        story.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
        story.append(Paragraph("This is to certify that", subtitle_style))
        
        # Recipient name
        full_name = f"{user.first_name} {user.last_name}"
        story.append(Paragraph(full_name, name_style))
        
        # Course completion text
        completion_text = f"has successfully completed the course"
        story.append(Paragraph(completion_text, body_style))
        
        # Course title
        story.append(Spacer(1, 0.2*inch))
        course_style = ParagraphStyle(
            'CourseStyle',
            parent=name_style,
            fontSize=24,
            textColor=colors.HexColor('#27ae60')
        )
        story.append(Paragraph(f'"{course.title}"', course_style))
        
        # Course details
        story.append(Spacer(1, 0.3*inch))
        details = []
        
        if course.duration_minutes:
            hours = course.duration_minutes / 60
            duration_text = f"{hours:.1f} hours" if hours >= 1 else f"{course.duration_minutes} minutes"
            details.append(f"Duration: {duration_text}")
        
        if course.category:
            details.append(f"Category: {course.category}")
        
        if details:
            detail_text = " • ".join(details)
            story.append(Paragraph(detail_text, subtitle_style))
        
        # Completion date
        story.append(Spacer(1, 0.3*inch))
        completion_date = enrollment.completed_at.strftime("%B %d, %Y")
        story.append(Paragraph(f"Completed on {completion_date}", body_style))
        
        # Validity period if applicable
        if enrollment.certificate_expires_at:
            expiry_date = enrollment.certificate_expires_at.strftime("%B %d, %Y")
            story.append(Paragraph(f"Valid until {expiry_date}", subtitle_style))
        
        # Add signatures section
        story.append(Spacer(1, 0.5*inch))
        
        # Create signature table
        signature_data = []
        signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER
        )
        
        # Add QR code for verification
        qr_code = self._generate_qr_code(cert_id, course.id, user.id)
        
        signature_data = [[
            [Paragraph("_______________________", signature_style),
             Paragraph("Instructor", subtitle_style)],
            qr_code,
            [Paragraph("_______________________", signature_style),
             Paragraph("Date", subtitle_style)]
        ]]
        
        sig_table = Table(signature_data, colWidths=[3*inch, 2*inch, 3*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(sig_table)
        
        # Certificate ID
        story.append(Spacer(1, 0.3*inch))
        id_style = ParagraphStyle(
            'IDStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Certificate ID: {cert_id}", id_style))
        
        return story
    
    def _create_compliance_certificate(
        self,
        enrollment: CourseEnrollment,
        user: User,
        course: Course,
        company: Company,
        cert_id: uuid.UUID
    ) -> list:
        """Create compliance-focused certificate with additional details."""
        # Start with default certificate
        story = self._create_default_certificate(enrollment, user, course, company, cert_id)
        
        # Add compliance-specific information
        styles = getSampleStyleSheet()
        compliance_style = ParagraphStyle(
            'ComplianceStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_LEFT,
            spaceAfter=6
        )
        
        # Insert compliance section before signatures
        insert_index = -4  # Before signature table
        
        story.insert(insert_index, Spacer(1, 0.3*inch))
        
        # Compliance standards
        if course.compliance_standards:
            standards_text = f"Compliance Standards: {', '.join(course.compliance_standards)}"
            story.insert(insert_index + 1, Paragraph(standards_text, compliance_style))
        
        # Company information
        company_text = f"Organization: {company.name}"
        story.insert(insert_index + 2, Paragraph(company_text, compliance_style))
        
        # Learning objectives if available
        if course.learning_objectives:
            objectives_text = "Learning Objectives Achieved:"
            story.insert(insert_index + 3, Paragraph(objectives_text, compliance_style))
            for obj in course.learning_objectives[:3]:  # Limit to 3 objectives
                story.insert(insert_index + 4, Paragraph(f"• {obj}", compliance_style))
        
        return story
    
    def _add_background(self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate, template: str):
        """Add background design to certificate."""
        canvas_obj.saveState()
        
        # Add border
        canvas_obj.setStrokeColor(colors.HexColor('#e0e0e0'))
        canvas_obj.setLineWidth(2)
        canvas_obj.rect(0.5*inch, 0.5*inch, doc.width + inch, doc.height + inch)
        
        # Add inner border
        canvas_obj.setStrokeColor(colors.HexColor('#cccccc'))
        canvas_obj.setLineWidth(1)
        canvas_obj.rect(0.7*inch, 0.7*inch, doc.width + 0.6*inch, doc.height + 0.6*inch)
        
        # Add watermark pattern (optional)
        if template == "compliance":
            canvas_obj.setFillColor(colors.HexColor('#f8f8f8'))
            # Add subtle pattern or watermark here
        
        canvas_obj.restoreState()
    
    def _generate_qr_code(self, cert_id: uuid.UUID, course_id: int, user_id: int) -> Image:
        """Generate QR code for certificate verification."""
        # Create verification URL
        verify_url = f"{settings.FRONTEND_URL}/certificates/verify/{cert_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=2,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        
        # Create image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to reportlab Image
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return Image(img_buffer, width=1.5*inch, height=1.5*inch)
    
    def generate_certificate_preview(
        self,
        course: Course,
        template: str = "default"
    ) -> bytes:
        """Generate a preview certificate for a course."""
        # Create mock data
        mock_user = type('MockUser', (), {
            'first_name': 'John',
            'last_name': 'Doe',
            'id': 0
        })()
        
        mock_company = type('MockCompany', (), {
            'name': 'Example Company Ltd.',
            'id': 0
        })()
        
        mock_enrollment = type('MockEnrollment', (), {
            'completion_certificate_id': uuid.uuid4(),
            'completed_at': datetime.utcnow(),
            'certificate_expires_at': datetime.utcnow() + timedelta(days=365) if course.validity_days else None
        })()
        
        # Generate certificate
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Get template method
        template_method = getattr(self, f"_create_{template}_certificate", self._create_default_certificate)
        
        # Build certificate content
        story = template_method(
            mock_enrollment,
            mock_user,
            course,
            mock_company,
            mock_enrollment.completion_certificate_id
        )
        
        # Add "PREVIEW" watermark
        story.insert(0, Paragraph(
            "PREVIEW",
            ParagraphStyle(
                'Preview',
                fontSize=72,
                textColor=colors.HexColor('#cccccc'),
                alignment=TA_CENTER
            )
        ))
        
        # Generate PDF
        doc.build(story, onFirstPage=lambda c, d: self._add_background(c, d, template))
        
        pdf_buffer.seek(0)
        return pdf_buffer.read()


# Singleton instance
certificate_generator = CertificateGenerator()