# Content Management Spezifikation
**Version 1.0 | Kurse & Phishing-Template Verwaltung**

## 1. Content Architecture

### 1.1 Content-Typen
```yaml
Content Types:
  Courses:
    - Video-basierte Kurse
    - Interaktive Module
    - Quiz-Assessments
    - Downloadbare Ressourcen
    - Zertifikate
    
  Phishing Templates:
    - E-Mail Templates
    - Landing Pages
    - Attachments
    - Variationen/Personalisierung
    
  Learning Paths:
    - Kurs-Sequenzen
    - Rollenbasierte Pfade
    - Compliance-Pfade
    
  Resources:
    - PDFs/Dokumente
    - Infografiken
    - Checklisten
    - Best Practices
```

### 1.2 Content Lifecycle
```
Create → Review → Approve → Publish → Monitor → Update → Archive
```

## 2. Kurs-Management System

### 2.1 Kurs-Struktur

```python
# backend/app/models/course_content.py
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

class CourseModule(Base):
    __tablename__ = "course_modules"
    
    id = Column(UUID, primary_key=True)
    course_id = Column(UUID, ForeignKey("courses.id"))
    
    # Module Info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)
    
    # Content Types
    content_type = Column(String(50))  # 'video', 'text', 'interactive', 'quiz'
    
    # Video Content
    youtube_video_id = Column(String(50))
    video_duration_seconds = Column(Integer)
    video_transcript = Column(Text)
    
    # Text Content
    markdown_content = Column(Text)
    
    # Interactive Content
    interactive_content = Column(JSON)
    # {
    #   "type": "scenario",
    #   "questions": [...],
    #   "feedback": {...}
    # }
    
    # Settings
    is_mandatory = Column(Boolean, default=True)
    min_time_seconds = Column(Integer)  # Minimum time to spend
    can_skip = Column(Boolean, default=False)
    
    # Relationships
    course = relationship("Course", back_populates="modules")
    resources = relationship("ModuleResource", back_populates="module")

class ModuleResource(Base):
    __tablename__ = "module_resources"
    
    id = Column(UUID, primary_key=True)
    module_id = Column(UUID, ForeignKey("course_modules.id"))
    
    title = Column(String(255))
    description = Column(Text)
    file_url = Column(String(500))
    file_type = Column(String(50))  # 'pdf', 'docx', 'pptx'
    file_size = Column(Integer)
    
    # Access Control
    requires_completion = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    module = relationship("CourseModule", back_populates="resources")

class CourseVersion(Base):
    __tablename__ = "course_versions"
    
    id = Column(UUID, primary_key=True)
    course_id = Column(UUID, ForeignKey("courses.id"))
    version_number = Column(String(20))  # "1.0.0"
    
    # Changes
    change_summary = Column(Text)
    changed_by = Column(UUID, ForeignKey("users.id"))
    approved_by = Column(UUID, ForeignKey("users.id"))
    
    # Status
    status = Column(String(50))  # 'draft', 'review', 'approved', 'published'
    published_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Content Snapshot
    content_snapshot = Column(JSON)  # Full course content at this version
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.2 Content Authoring Service

```python
# backend/app/services/content_authoring_service.py
from typing import Dict, Any, List, Optional
import markdown
from youtube_transcript_api import YouTubeTranscriptApi

class ContentAuthoringService:
    def __init__(self, db: Session, storage_service: StorageService):
        self.db = db
        self.storage = storage_service
    
    async def create_course(
        self,
        course_data: CourseCreate,
        author_id: str
    ) -> Course:
        """Create new course with modules"""
        
        # Create course
        course = Course(
            title=course_data.title,
            description=course_data.description,
            difficulty=course_data.difficulty,
            tags=course_data.tags,
            compliance_tags=course_data.compliance_tags,
            created_by=author_id,
            status="draft"
        )
        self.db.add(course)
        
        # Create modules
        for idx, module_data in enumerate(course_data.modules):
            module = await self._create_module(
                course.id,
                module_data,
                order_index=idx
            )
            course.modules.append(module)
        
        # Calculate total duration
        course.duration_minutes = sum(
            m.video_duration_seconds // 60 
            for m in course.modules 
            if m.video_duration_seconds
        )
        
        self.db.commit()
        return course
    
    async def _create_module(
        self,
        course_id: str,
        module_data: ModuleCreate,
        order_index: int
    ) -> CourseModule:
        """Create course module"""
        
        module = CourseModule(
            course_id=course_id,
            title=module_data.title,
            description=module_data.description,
            order_index=order_index,
            content_type=module_data.content_type
        )
        
        # Handle different content types
        if module_data.content_type == "video":
            await self._process_video_content(module, module_data)
        elif module_data.content_type == "text":
            module.markdown_content = module_data.markdown_content
        elif module_data.content_type == "interactive":
            module.interactive_content = module_data.interactive_content
        
        # Add resources
        for resource_data in module_data.resources:
            resource = await self._upload_resource(resource_data)
            module.resources.append(resource)
        
        self.db.add(module)
        return module
    
    async def _process_video_content(
        self,
        module: CourseModule,
        module_data: ModuleCreate
    ):
        """Process video content"""
        
        module.youtube_video_id = module_data.youtube_video_id
        
        # Get video info from YouTube
        video_info = await self.youtube_service.get_video_details(
            module_data.youtube_video_id
        )
        
        # Parse duration
        duration = self._parse_youtube_duration(
            video_info["contentDetails"]["duration"]
        )
        module.video_duration_seconds = duration
        
        # Get transcript if available
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                module_data.youtube_video_id,
                languages=['de', 'en']
            )
            module.video_transcript = self._format_transcript(transcript)
        except Exception:
            # Transcript not available
            pass
    
    async def update_course_content(
        self,
        course_id: str,
        updates: CourseUpdate,
        editor_id: str
    ) -> CourseVersion:
        """Update course and create new version"""
        
        course = self.db.query(Course).filter(
            Course.id == course_id
        ).first()
        
        if not course:
            raise ValueError("Course not found")
        
        # Create version snapshot
        version = CourseVersion(
            course_id=course_id,
            version_number=self._increment_version(course.current_version),
            change_summary=updates.change_summary,
            changed_by=editor_id,
            status="draft",
            content_snapshot=self._create_content_snapshot(course)
        )
        
        # Apply updates
        if updates.title:
            course.title = updates.title
        if updates.description:
            course.description = updates.description
        
        # Update modules
        for module_update in updates.module_updates:
            module = self.db.query(CourseModule).filter(
                CourseModule.id == module_update.id
            ).first()
            
            if module:
                await self._update_module(module, module_update)
        
        self.db.add(version)
        self.db.commit()
        
        return version
    
    async def generate_quiz_questions(
        self,
        module_id: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions from module content"""
        
        module = self.db.query(CourseModule).filter(
            CourseModule.id == module_id
        ).first()
        
        if not module:
            raise ValueError("Module not found")
        
        # Extract content
        content = ""
        if module.markdown_content:
            content = module.markdown_content
        elif module.video_transcript:
            content = module.video_transcript
        
        # Use AI to generate questions
        questions = await self.ai_service.generate_quiz_questions(
            content=content,
            count=count,
            difficulty=module.course.difficulty
        )
        
        return questions
    
    async def validate_course_compliance(
        self,
        course_id: str,
        compliance_standard: str
    ) -> Dict[str, Any]:
        """Validate course meets compliance requirements"""
        
        course = self.db.query(Course).filter(
            Course.id == course_id
        ).first()
        
        compliance_rules = self._get_compliance_rules(compliance_standard)
        validation_results = {
            "compliant": True,
            "issues": []
        }
        
        # Check duration
        if course.duration_minutes < compliance_rules.get("min_duration", 0):
            validation_results["compliant"] = False
            validation_results["issues"].append({
                "type": "duration",
                "message": f"Course duration must be at least {compliance_rules['min_duration']} minutes"
            })
        
        # Check required topics
        required_topics = compliance_rules.get("required_topics", [])
        course_topics = set(course.tags + course.compliance_tags)
        
        missing_topics = set(required_topics) - course_topics
        if missing_topics:
            validation_results["compliant"] = False
            validation_results["issues"].append({
                "type": "topics",
                "message": f"Missing required topics: {', '.join(missing_topics)}"
            })
        
        # Check assessment
        if compliance_rules.get("requires_assessment", False):
            has_quiz = any(
                m.content_type == "quiz" 
                for m in course.modules
            )
            if not has_quiz:
                validation_results["compliant"] = False
                validation_results["issues"].append({
                    "type": "assessment",
                    "message": "Course must include an assessment"
                })
        
        return validation_results
```

### 2.3 Content Delivery API

```python
# backend/app/api/content_delivery.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

router = APIRouter()

@router.get("/courses/{course_id}/content")
async def get_course_content(
    course_id: str,
    version: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get complete course content"""
    
    # Check access
    if not await has_course_access(current_user, course_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get course with modules
    course = db.query(Course).options(
        joinedload(Course.modules).joinedload(CourseModule.resources)
    ).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get specific version if requested
    if version:
        course_version = db.query(CourseVersion).filter(
            CourseVersion.course_id == course_id,
            CourseVersion.version_number == version
        ).first()
        
        if course_version:
            return course_version.content_snapshot
    
    # Transform to response
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "modules": [
            {
                "id": module.id,
                "title": module.title,
                "order": module.order_index,
                "content_type": module.content_type,
                "content": await get_module_content(module, current_user),
                "resources": [
                    {
                        "id": resource.id,
                        "title": resource.title,
                        "url": generate_signed_url(resource.file_url),
                        "type": resource.file_type
                    }
                    for resource in module.resources
                ]
            }
            for module in sorted(course.modules, key=lambda m: m.order_index)
        ]
    }

async def get_module_content(module: CourseModule, user: User) -> Dict[str, Any]:
    """Get module content based on type"""
    
    if module.content_type == "video":
        return {
            "youtube_video_id": module.youtube_video_id,
            "duration": module.video_duration_seconds,
            "transcript": module.video_transcript if user.settings.get("show_transcript") else None
        }
    
    elif module.content_type == "text":
        return {
            "html": markdown.markdown(
                module.markdown_content,
                extensions=['extra', 'codehilite', 'toc']
            ),
            "markdown": module.markdown_content
        }
    
    elif module.content_type == "interactive":
        return module.interactive_content
    
    elif module.content_type == "quiz":
        # Don't send correct answers
        quiz_data = module.interactive_content.copy()
        for question in quiz_data.get("questions", []):
            question.pop("correct_answer", None)
            question.pop("explanation", None)
        return quiz_data
```

## 3. Phishing Template Management

### 3.1 Template Structure

```python
# backend/app/models/phishing_content.py
class PhishingTemplateCategory(Base):
    __tablename__ = "phishing_template_categories"
    
    id = Column(UUID, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    icon = Column(String(50))
    
    templates = relationship("PhishingTemplate", back_populates="category")

class PhishingTemplateVariation(Base):
    __tablename__ = "phishing_template_variations"
    
    id = Column(UUID, primary_key=True)
    template_id = Column(UUID, ForeignKey("phishing_templates.id"))
    
    # Variation Info
    name = Column(String(255))
    description = Column(Text)
    
    # Content Variations
    subject_variations = Column(JSON)
    # ["Your account needs verification", "Urgent: Verify your account"]
    
    sender_variations = Column(JSON)
    # [
    #   {"name": "IT Support", "email": "support@{company-domain}"},
    #   {"name": "Security Team", "email": "security@{company-domain}"}
    # ]
    
    content_variables = Column(JSON)
    # {
    #   "urgency_level": ["immediately", "within 24 hours", "by end of week"],
    #   "threat_type": ["suspicious activity", "unauthorized access", "policy violation"]
    # }
    
    # A/B Testing
    selection_weight = Column(Float, default=1.0)
    performance_score = Column(Float)
    
    template = relationship("PhishingTemplate", back_populates="variations")

class PhishingLandingPage(Base):
    __tablename__ = "phishing_landing_pages"
    
    id = Column(UUID, primary_key=True)
    template_id = Column(UUID, ForeignKey("phishing_templates.id"))
    
    # Page Info
    title = Column(String(255))
    page_type = Column(String(50))  # 'training', 'warning', 'capture'
    
    # Content
    html_content = Column(Text)
    css_content = Column(Text)
    js_content = Column(Text)
    
    # Training Content
    training_points = Column(JSON)
    # [
    #   {"title": "Red Flag #1", "description": "Unknown sender", "icon": "alert"},
    #   {"title": "Red Flag #2", "description": "Urgency tactics", "icon": "clock"}
    # ]
    
    # Capture Fields (for testing)
    capture_fields = Column(JSON)
    # ["username", "password", "otp"]
    
    template = relationship("PhishingTemplate")

class PhishingAttachment(Base):
    __tablename__ = "phishing_attachments"
    
    id = Column(UUID, primary_key=True)
    template_id = Column(UUID, ForeignKey("phishing_templates.id"))
    
    # File Info
    filename = Column(String(255))
    file_type = Column(String(50))  # 'pdf', 'docx', 'xlsx'
    file_size = Column(Integer)
    
    # Content
    is_malicious = Column(Boolean, default=False)  # For testing only
    contains_macro = Column(Boolean, default=False)
    
    # Storage
    storage_path = Column(String(500))
    checksum = Column(String(64))
    
    template = relationship("PhishingTemplate")
```

### 3.2 Template Builder Service

```python
# backend/app/services/phishing_template_service.py
from jinja2 import Template, Environment, FileSystemLoader
import premailer
from bs4 import BeautifulSoup

class PhishingTemplateService:
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/phishing'),
            autoescape=True
        )
    
    async def create_template(
        self,
        template_data: PhishingTemplateCreate,
        author_id: str
    ) -> PhishingTemplate:
        """Create new phishing template"""
        
        # Create base template
        template = PhishingTemplate(
            name=template_data.name,
            description=template_data.description,
            category_id=template_data.category_id,
            difficulty=template_data.difficulty,
            created_by=author_id
        )
        
        # Process HTML content
        template.html_content = await self._process_html_content(
            template_data.html_content
        )
        
        # Extract and validate red flags
        template.red_flags = await self._extract_red_flags(
            template.html_content,
            template_data.subject
        )
        
        # Create variations
        for variation_data in template_data.variations:
            variation = PhishingTemplateVariation(
                name=variation_data.name,
                subject_variations=variation_data.subjects,
                sender_variations=variation_data.senders,
                content_variables=variation_data.variables
            )
            template.variations.append(variation)
        
        # Create landing page
        if template_data.landing_page:
            landing_page = await self._create_landing_page(
                template_data.landing_page
            )
            template.landing_pages.append(landing_page)
        
        self.db.add(template)
        self.db.commit()
        
        return template
    
    async def _process_html_content(self, html: str) -> str:
        """Process and optimize HTML content"""
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Add tracking pixel
        tracking_pixel = soup.new_tag(
            'img',
            src='{{tracking_url}}',
            width='1',
            height='1',
            style='display:none'
        )
        soup.body.append(tracking_pixel)
        
        # Process links
        for link in soup.find_all('a'):
            original_href = link.get('href', '')
            link['href'] = '{{redirect_url}}?url=' + original_href
            link['data-original-href'] = original_href
        
        # Inline CSS for better email client support
        html_with_inline_css = premailer.transform(str(soup))
        
        return html_with_inline_css
    
    async def _extract_red_flags(
        self,
        html_content: str,
        subject: str
    ) -> List[Dict[str, str]]:
        """Extract red flags from template"""
        
        red_flags = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check sender domain
        sender_analysis = self._analyze_sender_domain(html_content)
        if sender_analysis:
            red_flags.append(sender_analysis)
        
        # Check urgency indicators
        urgency_words = [
            'urgent', 'immediately', 'expire', 'suspend',
            'dringend', 'sofort', 'ablaufen', 'sperren'
        ]
        
        text_content = soup.get_text().lower()
        for word in urgency_words:
            if word in text_content or word in subject.lower():
                red_flags.append({
                    "type": "urgency",
                    "description": f"Uses urgency tactics: '{word}'",
                    "severity": "high"
                })
                break
        
        # Check for suspicious links
        for link in soup.find_all('a'):
            href = link.get('data-original-href', '')
            if self._is_suspicious_url(href):
                red_flags.append({
                    "type": "suspicious_link",
                    "description": "Contains suspicious URL",
                    "severity": "high"
                })
        
        # Check grammar/spelling (using language tool)
        grammar_issues = await self._check_grammar(text_content)
        if grammar_issues:
            red_flags.append({
                "type": "grammar",
                "description": "Contains grammar/spelling errors",
                "severity": "medium"
            })
        
        return red_flags
    
    async def generate_campaign_email(
        self,
        template_id: str,
        campaign_id: str,
        recipient: User,
        company: Company
    ) -> Dict[str, Any]:
        """Generate personalized email from template"""
        
        template = self.db.query(PhishingTemplate).filter(
            PhishingTemplate.id == template_id
        ).first()
        
        # Select variation
        variation = self._select_variation(template.variations)
        
        # Prepare context
        context = {
            "recipient_name": recipient.first_name,
            "recipient_email": recipient.email,
            "company_name": company.name,
            "company_domain": company.domain,
            "tracking_url": f"{settings.BASE_URL}/api/v1/phishing/track/{campaign_id}/{recipient.id}",
            "redirect_url": f"{settings.BASE_URL}/api/v1/phishing/click/{campaign_id}/{recipient.id}",
            "current_year": datetime.now().year,
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
        
        # Add variation variables
        if variation.content_variables:
            for key, values in variation.content_variables.items():
                context[key] = random.choice(values)
        
        # Render template
        jinja_template = Template(template.html_content)
        html_content = jinja_template.render(**context)
        
        # Select subject and sender
        subject = random.choice(variation.subject_variations)
        sender = random.choice(variation.sender_variations)
        
        # Process sender email
        sender_email = sender["email"].replace("{company-domain}", company.domain)
        
        return {
            "to": recipient.email,
            "subject": subject,
            "sender_name": sender["name"],
            "sender_email": sender_email,
            "html_content": html_content,
            "text_content": self._html_to_text(html_content),
            "headers": {
                "X-Phishing-Campaign": campaign_id,
                "X-Phishing-Template": template_id
            }
        }
    
    async def analyze_campaign_performance(
        self,
        template_id: str
    ) -> Dict[str, Any]:
        """Analyze template performance across campaigns"""
        
        # Get all campaigns using this template
        campaigns = self.db.query(PhishingCampaign).filter(
            PhishingCampaign.template_id == template_id,
            PhishingCampaign.status == 'completed'
        ).all()
        
        if not campaigns:
            return {"message": "No completed campaigns found"}
        
        # Aggregate metrics
        total_sent = sum(c.emails_sent for c in campaigns)
        total_opened = sum(c.emails_opened for c in campaigns)
        total_clicked = sum(c.links_clicked for c in campaigns)
        total_reported = sum(c.reported_suspicious for c in campaigns)
        
        # Calculate rates
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        report_rate = (total_reported / total_sent * 100) if total_sent > 0 else 0
        
        # Variation performance
        variation_stats = await self._calculate_variation_performance(template_id)
        
        # Time-based analysis
        time_analysis = await self._analyze_click_timing(template_id)
        
        return {
            "summary": {
                "campaigns_run": len(campaigns),
                "total_recipients": total_sent,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "report_rate": round(report_rate, 2)
            },
            "variation_performance": variation_stats,
            "timing_analysis": time_analysis,
            "effectiveness_score": self._calculate_effectiveness_score(
                click_rate, report_rate
            )
        }
```

### 3.3 Landing Page Builder

```python
# backend/app/services/landing_page_builder.py
class LandingPageBuilder:
    def __init__(self):
        self.components = self._load_components()
    
    def _load_components(self) -> Dict[str, str]:
        """Load reusable page components"""
        return {
            "header": """
                <header class="warning-header">
                    <div class="alert-icon">⚠️</div>
                    <h1>Security Alert</h1>
                </header>
            """,
            "training_intro": """
                <div class="training-intro">
                    <h2>This was a simulated phishing attack</h2>
                    <p>You've just experienced a training simulation designed to help you recognize and avoid real phishing attempts.</p>
                </div>
            """,
            "red_flags": """
                <div class="red-flags">
                    <h3>Red flags you might have missed:</h3>
                    <ul>
                        {{#red_flags}}
                        <li class="red-flag-item">
                            <span class="icon">{{icon}}</span>
                            <div>
                                <strong>{{title}}</strong>
                                <p>{{description}}</p>
                            </div>
                        </li>
                        {{/red_flags}}
                    </ul>
                </div>
            """,
            "tips": """
                <div class="security-tips">
                    <h3>How to protect yourself:</h3>
                    <div class="tips-grid">
                        {{#tips}}
                        <div class="tip-card">
                            <div class="tip-icon">{{icon}}</div>
                            <h4>{{title}}</h4>
                            <p>{{description}}</p>
                        </div>
                        {{/tips}}
                    </div>
                </div>
            """
        }
    
    async def create_landing_page(
        self,
        page_data: LandingPageCreate
    ) -> PhishingLandingPage:
        """Create landing page from components"""
        
        # Build HTML
        html_parts = ['<!DOCTYPE html><html><head>']
        
        # Add meta tags
        html_parts.append(self._generate_meta_tags(page_data.title))
        
        # Add CSS
        html_parts.append('<style>')
        html_parts.append(self._get_default_css())
        if page_data.custom_css:
            html_parts.append(page_data.custom_css)
        html_parts.append('</style>')
        
        html_parts.append('</head><body>')
        
        # Add components
        for component in page_data.components:
            if component.type in self.components:
                component_html = self._render_component(
                    self.components[component.type],
                    component.data
                )
                html_parts.append(component_html)
        
        # Add tracking
        html_parts.append(self._generate_tracking_script())
        
        html_parts.append('</body></html>')
        
        # Create landing page
        landing_page = PhishingLandingPage(
            title=page_data.title,
            page_type=page_data.page_type,
            html_content=''.join(html_parts),
            training_points=page_data.training_points
        )
        
        return landing_page
    
    def _get_default_css(self) -> str:
        """Get default landing page CSS"""
        return """
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .warning-header {
                background: #ff4444;
                color: white;
                padding: 30px;
                text-align: center;
            }
            .alert-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            .training-intro {
                background: white;
                padding: 30px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .red-flags {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .red-flag-item {
                display: flex;
                align-items: start;
                margin: 15px 0;
            }
            .red-flag-item .icon {
                font-size: 24px;
                margin-right: 15px;
                color: #ff6b6b;
            }
            .security-tips {
                background: white;
                padding: 30px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .tips-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .tip-card {
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                text-align: center;
            }
            .tip-icon {
                font-size: 36px;
                margin-bottom: 10px;
            }
            @media (max-width: 600px) {
                .tips-grid { grid-template-columns: 1fr; }
            }
        """
```

## 4. Learning Path Management

### 4.1 Learning Path Models

```python
# backend/app/models/learning_paths.py
class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(UUID, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    
    # Target Audience
    target_roles = Column(JSON)  # ["employee", "manager", "admin"]
    target_departments = Column(JSON)  # ["IT", "Finance", "HR"]
    compliance_standards = Column(JSON)  # ["nis2", "dsgvo", "iso27001"]
    
    # Path Configuration
    is_sequential = Column(Boolean, default=True)
    estimated_duration_hours = Column(Float)
    
    # Completion Requirements
    min_score = Column(Integer, default=80)
    completion_deadline_days = Column(Integer)  # Days from assignment
    
    # Status
    is_active = Column(Boolean, default=True)
    is_mandatory = Column(Boolean, default=False)
    
    # Relationships
    path_courses = relationship("LearningPathCourse", back_populates="path")
    assignments = relationship("LearningPathAssignment", back_populates="path")

class LearningPathCourse(Base):
    __tablename__ = "learning_path_courses"
    
    id = Column(UUID, primary_key=True)
    path_id = Column(UUID, ForeignKey("learning_paths.id"))
    course_id = Column(UUID, ForeignKey("courses.id"))
    
    # Sequencing
    order_index = Column(Integer)
    is_optional = Column(Boolean, default=False)
    
    # Prerequisites
    prerequisite_courses = Column(JSON)  # List of course IDs
    min_score_required = Column(Integer)  # Min score in prerequisites
    
    # Time Constraints
    unlock_after_days = Column(Integer, default=0)  # Days after path start
    complete_within_days = Column(Integer)  # Days to complete after unlock
    
    # Relationships
    path = relationship("LearningPath", back_populates="path_courses")
    course = relationship("Course")

class LearningPathAssignment(Base):
    __tablename__ = "learning_path_assignments"
    
    id = Column(UUID, primary_key=True)
    path_id = Column(UUID, ForeignKey("learning_paths.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    company_id = Column(UUID, ForeignKey("companies.id"))
    
    # Assignment Info
    assigned_by = Column(UUID, ForeignKey("users.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    
    # Progress
    status = Column(String(50))  # 'not_started', 'in_progress', 'completed'
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    current_course_index = Column(Integer, default=0)
    
    # Scoring
    overall_score = Column(Float)
    course_scores = Column(JSON)  # {course_id: score}
    
    # Relationships
    path = relationship("LearningPath", back_populates="assignments")
    user = relationship("User")
```

### 4.2 Learning Path Service

```python
# backend/app/services/learning_path_service.py
class LearningPathService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_learning_path(
        self,
        path_data: LearningPathCreate
    ) -> LearningPath:
        """Create new learning path"""
        
        path = LearningPath(
            name=path_data.name,
            description=path_data.description,
            target_roles=path_data.target_roles,
            target_departments=path_data.target_departments,
            compliance_standards=path_data.compliance_standards,
            is_sequential=path_data.is_sequential
        )
        
        # Add courses
        total_duration = 0
        for idx, course_config in enumerate(path_data.courses):
            course = self.db.query(Course).filter(
                Course.id == course_config.course_id
            ).first()
            
            if not course:
                raise ValueError(f"Course {course_config.course_id} not found")
            
            path_course = LearningPathCourse(
                course_id=course.id,
                order_index=idx,
                is_optional=course_config.is_optional,
                prerequisite_courses=course_config.prerequisites,
                unlock_after_days=course_config.unlock_after_days
            )
            
            path.path_courses.append(path_course)
            
            if not course_config.is_optional:
                total_duration += course.duration_minutes
        
        path.estimated_duration_hours = total_duration / 60
        
        self.db.add(path)
        self.db.commit()
        
        return path
    
    async def assign_learning_path(
        self,
        path_id: str,
        user_ids: List[str],
        assigned_by: str,
        deadline_override: Optional[datetime] = None
    ) -> List[LearningPathAssignment]:
        """Assign learning path to users"""
        
        path = self.db.query(LearningPath).filter(
            LearningPath.id == path_id
        ).first()
        
        if not path:
            raise ValueError("Learning path not found")
        
        assignments = []
        
        for user_id in user_ids:
            # Check if already assigned
            existing = self.db.query(LearningPathAssignment).filter(
                LearningPathAssignment.path_id == path_id,
                LearningPathAssignment.user_id == user_id,
                LearningPathAssignment.status != 'completed'
            ).first()
            
            if existing:
                continue
            
            # Create assignment
            assignment = LearningPathAssignment(
                path_id=path_id,
                user_id=user_id,
                assigned_by=assigned_by,
                status='not_started'
            )
            
            # Set due date
            if deadline_override:
                assignment.due_date = deadline_override
            elif path.completion_deadline_days:
                assignment.due_date = datetime.utcnow() + timedelta(
                    days=path.completion_deadline_days
                )
            
            assignments.append(assignment)
            self.db.add(assignment)
            
            # Create course assignments
            await self._create_course_assignments(assignment, path)
            
            # Send notification
            await self.notification_service.send_path_assignment(
                user_id, path, assignment.due_date
            )
        
        self.db.commit()
        return assignments
    
    async def get_user_learning_paths(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's assigned learning paths"""
        
        query = self.db.query(LearningPathAssignment).filter(
            LearningPathAssignment.user_id == user_id
        )
        
        if status:
            query = query.filter(LearningPathAssignment.status == status)
        
        assignments = query.all()
        
        result = []
        for assignment in assignments:
            path_data = {
                "assignment_id": assignment.id,
                "path": {
                    "id": assignment.path.id,
                    "name": assignment.path.name,
                    "description": assignment.path.description,
                    "estimated_hours": assignment.path.estimated_duration_hours
                },
                "status": assignment.status,
                "assigned_at": assignment.assigned_at,
                "due_date": assignment.due_date,
                "progress": await self._calculate_path_progress(assignment),
                "next_course": await self._get_next_course(assignment)
            }
            result.append(path_data)
        
        return result
    
    async def _calculate_path_progress(
        self,
        assignment: LearningPathAssignment
    ) -> Dict[str, Any]:
        """Calculate learning path progress"""
        
        total_courses = len([
            pc for pc in assignment.path.path_courses 
            if not pc.is_optional
        ])
        
        completed_courses = len(assignment.course_scores or {})
        
        # Get detailed progress
        course_progress = []
        for path_course in sorted(
            assignment.path.path_courses,
            key=lambda pc: pc.order_index
        ):
            course_status = await self._get_course_status(
                assignment.user_id,
                path_course.course_id
            )
            
            course_progress.append({
                "course_id": path_course.course_id,
                "course_name": path_course.course.title,
                "order": path_course.order_index,
                "is_optional": path_course.is_optional,
                "status": course_status["status"],
                "score": course_status.get("score"),
                "can_start": await self._can_start_course(
                    assignment, path_course
                )
            })
        
        return {
            "completed_courses": completed_courses,
            "total_courses": total_courses,
            "percentage": round((completed_courses / total_courses * 100), 2) if total_courses > 0 else 0,
            "courses": course_progress
        }
    
    async def update_path_progress(
        self,
        assignment_id: str,
        course_id: str,
        score: float
    ):
        """Update progress when course is completed"""
        
        assignment = self.db.query(LearningPathAssignment).filter(
            LearningPathAssignment.id == assignment_id
        ).first()
        
        if not assignment:
            return
        
        # Update course scores
        if not assignment.course_scores:
            assignment.course_scores = {}
        
        assignment.course_scores[course_id] = score
        
        # Update status
        if assignment.status == 'not_started':
            assignment.status = 'in_progress'
            assignment.started_at = datetime.utcnow()
        
        # Check if path is completed
        required_courses = [
            pc.course_id for pc in assignment.path.path_courses
            if not pc.is_optional
        ]
        
        if all(cid in assignment.course_scores for cid in required_courses):
            assignment.status = 'completed'
            assignment.completed_at = datetime.utcnow()
            
            # Calculate overall score
            scores = [
                assignment.course_scores[cid] 
                for cid in required_courses
            ]
            assignment.overall_score = sum(scores) / len(scores)
            
            # Send completion notification
            await self.notification_service.send_path_completion(
                assignment.user_id,
                assignment.path,
                assignment.overall_score
            )
        
        self.db.commit()
```

## 5. Content Analytics

### 5.1 Analytics Models

```python
# backend/app/models/content_analytics.py
class ContentEngagement(Base):
    __tablename__ = "content_engagement"
    
    id = Column(UUID, primary_key=True)
    content_type = Column(String(50))  # 'course', 'module', 'resource'
    content_id = Column(UUID)
    user_id = Column(UUID, ForeignKey("users.id"))
    company_id = Column(UUID, ForeignKey("companies.id"))
    
    # Engagement Metrics
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    time_spent_seconds = Column(Integer)
    
    # Interaction Metrics
    play_count = Column(Integer, default=0)
    pause_count = Column(Integer, default=0)
    rewind_count = Column(Integer, default=0)
    speed_changes = Column(JSON)  # [{"time": timestamp, "speed": 1.5}]
    
    # Quality Metrics
    quiz_attempts = Column(Integer, default=0)
    quiz_score = Column(Float)
    feedback_rating = Column(Integer)  # 1-5 stars
    feedback_comment = Column(Text)
    
    # Device/Context
    device_type = Column(String(50))  # 'desktop', 'mobile', 'tablet'
    browser = Column(String(50))
    location = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ContentEffectiveness(Base):
    __tablename__ = "content_effectiveness"
    
    id = Column(UUID, primary_key=True)
    content_id = Column(UUID)
    content_type = Column(String(50))
    
    # Calculated Metrics
    avg_completion_rate = Column(Float)
    avg_time_to_complete = Column(Integer)
    avg_quiz_score = Column(Float)
    avg_rating = Column(Float)
    
    # Behavioral Impact
    pre_phishing_click_rate = Column(Float)
    post_phishing_click_rate = Column(Float)
    behavior_change_score = Column(Float)
    
    # Engagement Patterns
    dropout_points = Column(JSON)  # {"5:30": 15%, "10:45": 8%}
    replay_sections = Column(JSON)  # {"2:15-3:30": 45 replays}
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
```

### 5.2 Content Analytics Service

```python
# backend/app/services/content_analytics_service.py
class ContentAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def track_content_engagement(
        self,
        user_id: str,
        content_id: str,
        content_type: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Track user engagement with content"""
        
        # Get or create engagement record
        engagement = self.db.query(ContentEngagement).filter(
            ContentEngagement.user_id == user_id,
            ContentEngagement.content_id == content_id,
            ContentEngagement.completed_at.is_(None)
        ).first()
        
        if not engagement:
            user = self.db.query(User).filter(User.id == user_id).first()
            engagement = ContentEngagement(
                content_type=content_type,
                content_id=content_id,
                user_id=user_id,
                company_id=user.company_id,
                started_at=datetime.utcnow(),
                device_type=event_data.get("device_type"),
                browser=event_data.get("browser")
            )
            self.db.add(engagement)
        
        # Update based on event
        if event_type == "play":
            engagement.play_count += 1
        elif event_type == "pause":
            engagement.pause_count += 1
        elif event_type == "rewind":
            engagement.rewind_count += 1
        elif event_type == "speed_change":
            if not engagement.speed_changes:
                engagement.speed_changes = []
            engagement.speed_changes.append({
                "time": datetime.utcnow().isoformat(),
                "speed": event_data.get("speed")
            })
        elif event_type == "progress":
            engagement.time_spent_seconds = event_data.get("time_spent")
        elif event_type == "complete":
            engagement.completed_at = datetime.utcnow()
            engagement.time_spent_seconds = event_data.get("total_time")
        
        self.db.commit()
    
    async def calculate_content_effectiveness(
        self,
        content_id: str,
        content_type: str
    ) -> ContentEffectiveness:
        """Calculate content effectiveness metrics"""
        
        # Get all engagements
        engagements = self.db.query(ContentEngagement).filter(
            ContentEngagement.content_id == content_id
        ).all()
        
        if not engagements:
            return None
        
        # Calculate metrics
        total_started = len(engagements)
        total_completed = len([e for e in engagements if e.completed_at])
        
        completion_rate = (total_completed / total_started * 100) if total_started > 0 else 0
        
        # Average time to complete
        completion_times = [
            e.time_spent_seconds for e in engagements 
            if e.completed_at and e.time_spent_seconds
        ]
        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Quiz scores
        quiz_scores = [
            e.quiz_score for e in engagements 
            if e.quiz_score is not None
        ]
        avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        # Ratings
        ratings = [
            e.feedback_rating for e in engagements 
            if e.feedback_rating
        ]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Behavioral impact (for security training)
        if content_type == "course":
            behavior_impact = await self._calculate_behavior_impact(
                content_id, engagements
            )
        else:
            behavior_impact = {}
        
        # Analyze dropout points
        dropout_analysis = await self._analyze_dropout_points(engagements)
        
        # Create or update effectiveness record
        effectiveness = self.db.query(ContentEffectiveness).filter(
            ContentEffectiveness.content_id == content_id
        ).first()
        
        if not effectiveness:
            effectiveness = ContentEffectiveness(
                content_id=content_id,
                content_type=content_type
            )
            self.db.add(effectiveness)
        
        effectiveness.avg_completion_rate = completion_rate
        effectiveness.avg_time_to_complete = avg_time
        effectiveness.avg_quiz_score = avg_quiz_score
        effectiveness.avg_rating = avg_rating
        effectiveness.pre_phishing_click_rate = behavior_impact.get("pre_click_rate")
        effectiveness.post_phishing_click_rate = behavior_impact.get("post_click_rate")
        effectiveness.behavior_change_score = behavior_impact.get("change_score")
        effectiveness.dropout_points = dropout_analysis
        effectiveness.calculated_at = datetime.utcnow()
        
        self.db.commit()
        
        return effectiveness
    
    async def get_content_insights(
        self,
        content_id: str
    ) -> Dict[str, Any]:
        """Get actionable insights for content improvement"""
        
        effectiveness = await self.calculate_content_effectiveness(
            content_id, "course"
        )
        
        insights = {
            "performance_summary": {
                "completion_rate": effectiveness.avg_completion_rate,
                "avg_time_minutes": effectiveness.avg_time_to_complete / 60,
                "satisfaction_score": effectiveness.avg_rating,
                "knowledge_retention": effectiveness.avg_quiz_score
            },
            "recommendations": []
        }
        
        # Generate recommendations
        if effectiveness.avg_completion_rate < 70:
            insights["recommendations"].append({
                "type": "completion",
                "priority": "high",
                "message": "Low completion rate detected",
                "suggestion": "Consider breaking content into smaller modules"
            })
        
        if effectiveness.dropout_points:
            high_dropout_points = [
                point for point, rate in effectiveness.dropout_points.items()
                if rate > 10
            ]
            if high_dropout_points:
                insights["recommendations"].append({
                    "type": "engagement",
                    "priority": "medium",
                    "message": f"High dropout at {high_dropout_points[0]}",
                    "suggestion": "Review content at this timestamp for clarity"
                })
        
        if effectiveness.avg_quiz_score < 70:
            insights["recommendations"].append({
                "type": "comprehension",
                "priority": "high",
                "message": "Low quiz scores indicate comprehension issues",
                "suggestion": "Add more examples or simplify explanations"
            })
        
        if effectiveness.behavior_change_score and effectiveness.behavior_change_score < 20:
            insights["recommendations"].append({
                "type": "effectiveness",
                "priority": "critical",
                "message": "Training not effectively changing behavior",
                "suggestion": "Add more practical exercises and real-world scenarios"
            })
        
        return insights
```

## 6. Content Localization

### 6.1 Localization Models

```python
# backend/app/models/content_localization.py
class ContentTranslation(Base):
    __tablename__ = "content_translations"
    
    id = Column(UUID, primary_key=True)
    content_type = Column(String(50))  # 'course', 'module', 'template'
    content_id = Column(UUID)
    language_code = Column(String(5))  # 'de', 'en', 'fr', 'it'
    
    # Translated Fields
    title = Column(String(255))
    description = Column(Text)
    content = Column(Text)  # JSON or Markdown depending on type
    
    # Metadata
    translated_by = Column(UUID, ForeignKey("users.id"))
    reviewed_by = Column(UUID, ForeignKey("users.id"))
    
    # Status
    status = Column(String(50))  # 'draft', 'review', 'approved', 'published'
    quality_score = Column(Float)  # Auto-assessed quality
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    published_at = Column(DateTime)

class LocalizationGlossary(Base):
    __tablename__ = "localization_glossary"
    
    id = Column(UUID, primary_key=True)
    term = Column(String(255))
    context = Column(String(255))  # 'security', 'compliance', 'general'
    
    # Translations
    translations = Column(JSON)
    # {
    #   "de": "Phishing-Angriff",
    #   "en": "Phishing Attack",
    #   "fr": "Attaque par hameçonnage",
    #   "it": "Attacco di phishing"
    # }
    
    # Usage
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
```

### 6.2 Localization Service

```python
# backend/app/services/localization_service.py
from googletrans import Translator
import deepl

class LocalizationService:
    def __init__(self):
        self.translator = Translator()
        self.deepl = deepl.Translator(settings.DEEPL_API_KEY)
        self.glossary = self._load_glossary()
    
    async def translate_content(
        self,
        content_id: str,
        content_type: str,
        target_language: str,
        use_machine_translation: bool = True
    ) -> ContentTranslation:
        """Translate content to target language"""
        
        # Get source content
        source_content = await self._get_source_content(
            content_id, content_type
        )
        
        # Check if translation exists
        existing = self.db.query(ContentTranslation).filter(
            ContentTranslation.content_id == content_id,
            ContentTranslation.language_code == target_language
        ).first()
        
        if existing and existing.status == 'published':
            return existing
        
        # Create new translation
        translation = ContentTranslation(
            content_type=content_type,
            content_id=content_id,
            language_code=target_language,
            status='draft'
        )
        
        if use_machine_translation:
            # Translate using DeepL (better quality than Google)
            translated_title = await self._translate_text(
                source_content['title'],
                target_language,
                context='title'
            )
            
            translated_description = await self._translate_text(
                source_content['description'],
                target_language,
                context='description'
            )
            
            # Translate content based on type
            if content_type == 'course':
                translated_content = await self._translate_course_content(
                    source_content['content'],
                    target_language
                )
            else:
                translated_content = await self._translate_text(
                    source_content['content'],
                    target_language
                )
            
            translation.title = translated_title
            translation.description = translated_description
            translation.content = translated_content
            
            # Auto-assess quality
            translation.quality_score = await self._assess_translation_quality(
                source_content, translation
            )
        
        self.db.add(translation)
        self.db.commit()
        
        return translation
    
    async def _translate_text(
        self,
        text: str,
        target_lang: str,
        context: str = 'general'
    ) -> str:
        """Translate text using glossary and MT"""
        
        if not text:
            return ""
        
        # Apply glossary terms
        text_with_placeholders, replacements = self._apply_glossary(
            text, target_lang
        )
        
        # Translate
        if target_lang in ['de', 'fr', 'it']:
            # Use DeepL for better quality
            result = self.deepl.translate_text(
                text_with_placeholders,
                target_lang=target_lang.upper()
            )
            translated = result.text
        else:
            # Fallback to Google Translate
            result = self.translator.translate(
                text_with_placeholders,
                dest=target_lang
            )
            translated = result.text
        
        # Replace placeholders with glossary terms
        for placeholder, term in replacements.items():
            translated = translated.replace(placeholder, term)
        
        return translated
    
    async def _translate_course_content(
        self,
        content: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Translate structured course content"""
        
        translated = content.copy()
        
        # Translate modules
        if 'modules' in content:
            translated['modules'] = []
            for module in content['modules']:
                translated_module = module.copy()
                
                translated_module['title'] = await self._translate_text(
                    module['title'], target_lang
                )
                
                if module['content_type'] == 'text':
                    translated_module['content'] = await self._translate_text(
                        module['content'], target_lang
                    )
                elif module['content_type'] == 'quiz':
                    translated_module['questions'] = await self._translate_quiz(
                        module['questions'], target_lang
                    )
                
                translated['modules'].append(translated_module)
        
        return translated
    
    async def _translate_quiz(
        self,
        questions: List[Dict],
        target_lang: str
    ) -> List[Dict]:
        """Translate quiz questions"""
        
        translated_questions = []
        
        for question in questions:
            translated_q = question.copy()
            
            translated_q['question'] = await self._translate_text(
                question['question'], target_lang
            )
            
            translated_q['options'] = []
            for option in question['options']:
                translated_option = option.copy()
                translated_option['text'] = await self._translate_text(
                    option['text'], target_lang
                )
                translated_q['options'].append(translated_option)
            
            if 'explanation' in question:
                translated_q['explanation'] = await self._translate_text(
                    question['explanation'], target_lang
                )
            
            translated_questions.append(translated_q)
        
        return translated_questions
    
    async def review_translation(
        self,
        translation_id: str,
        reviewer_id: str,
        approved: bool,
        feedback: Optional[str] = None
    ):
        """Review and approve translation"""
        
        translation = self.db.query(ContentTranslation).filter(
            ContentTranslation.id == translation_id
        ).first()
        
        if not translation:
            raise ValueError("Translation not found")
        
        translation.reviewed_by = reviewer_id
        translation.reviewed_at = datetime.utcnow()
        
        if approved:
            translation.status = 'approved'
            # Optionally publish immediately
            if settings.AUTO_PUBLISH_TRANSLATIONS:
                translation.status = 'published'
                translation.published_at = datetime.utcnow()
        else:
            translation.status = 'review'
            # Store feedback for translator
            if feedback:
                self._store_translation_feedback(
                    translation_id, reviewer_id, feedback
                )
        
        self.db.commit()
```

Diese umfassende Content Management Spezifikation deckt alle Aspekte der Verwaltung von Kursinhalten und Phishing-Templates ab, einschließlich Versionierung, Lokalisierung und Analytics.