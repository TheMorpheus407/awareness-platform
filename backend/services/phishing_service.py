"""Phishing simulation service."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from backend.models import (
    PhishingCampaign, PhishingTemplate, PhishingResult,
    User, Company, PhishingAnalytics
)
from backend.schemas.phishing import (
    CampaignStatus, PhishingTrackingEvent,
    CampaignAnalytics, ComplianceReport
)
from backend.core.exceptions import NotFoundError, ValidationError, PermissionError
from backend.services.email_service import EmailService
from backend.services.analytics_collector import AnalyticsCollector


class PhishingService:
    """Service for managing phishing simulations."""
    
    def __init__(self, db: Session):
        """Initialize phishing service."""
        self.db = db
        self.email_service = EmailService()
        self.analytics = AnalyticsCollector(db)
    
    # Template Management
    def create_template(
        self,
        template_data: dict,
        company_id: Optional[int] = None
    ) -> PhishingTemplate:
        """Create a new phishing template."""
        template = PhishingTemplate(
            **template_data,
            company_id=company_id
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        # Track event
        self.analytics.track_event(
            event_type="phishing_template_created",
            event_category="phishing",
            event_action="create_template",
            event_label=template.name,
            company_id=company_id
        )
        
        return template
    
    def get_template(self, template_id: int, company_id: Optional[int] = None) -> PhishingTemplate:
        """Get a phishing template by ID."""
        query = self.db.query(PhishingTemplate).filter(PhishingTemplate.id == template_id)
        
        if company_id:
            query = query.filter(
                or_(
                    PhishingTemplate.is_public == True,
                    PhishingTemplate.company_id == company_id
                )
            )
        
        template = query.first()
        if not template:
            raise NotFoundError(f"Template {template_id} not found")
        
        return template
    
    def list_templates(
        self,
        company_id: Optional[int] = None,
        filters: Optional[dict] = None
    ) -> List[PhishingTemplate]:
        """List phishing templates with filters."""
        query = self.db.query(PhishingTemplate)
        
        if company_id:
            query = query.filter(
                or_(
                    PhishingTemplate.is_public == True,
                    PhishingTemplate.company_id == company_id
                )
            )
        
        if filters:
            if filters.get("categories"):
                query = query.filter(PhishingTemplate.category.in_(filters["categories"]))
            if filters.get("difficulties"):
                query = query.filter(PhishingTemplate.difficulty.in_(filters["difficulties"]))
            if filters.get("languages"):
                query = query.filter(PhishingTemplate.language.in_(filters["languages"]))
            if filters.get("search_query"):
                search = f"%{filters['search_query']}%"
                query = query.filter(
                    or_(
                        PhishingTemplate.name.ilike(search),
                        PhishingTemplate.subject.ilike(search),
                        PhishingTemplate.sender_name.ilike(search)
                    )
                )
        
        return query.all()
    
    def update_template(
        self,
        template_id: int,
        template_data: dict,
        company_id: Optional[int] = None
    ) -> PhishingTemplate:
        """Update a phishing template."""
        template = self.get_template(template_id, company_id)
        
        # Only allow updating custom templates
        if template.is_public and template.company_id != company_id:
            raise PermissionError("Cannot modify public templates")
        
        for key, value in template_data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def delete_template(self, template_id: int, company_id: int) -> None:
        """Delete a phishing template."""
        template = self.get_template(template_id, company_id)
        
        # Only allow deleting custom templates
        if template.company_id != company_id:
            raise PermissionError("Cannot delete public templates")
        
        self.db.delete(template)
        self.db.commit()
    
    # Campaign Management
    def create_campaign(
        self,
        campaign_data: dict,
        company_id: int,
        created_by_id: int
    ) -> PhishingCampaign:
        """Create a new phishing campaign."""
        # Validate template exists and is accessible
        template = self.get_template(campaign_data["template_id"], company_id)
        
        # Create campaign
        campaign = PhishingCampaign(
            company_id=company_id,
            created_by_id=created_by_id,
            name=campaign_data["name"],
            description=campaign_data.get("description"),
            template_id=template.id,
            target_groups=campaign_data["target_groups"],
            scheduled_at=campaign_data.get("scheduled_at"),
            settings=campaign_data["settings"],
            status=CampaignStatus.DRAFT
        )
        
        self.db.add(campaign)
        self.db.commit()
        
        # Create recipient records
        recipients = self._get_campaign_recipients(campaign)
        for user in recipients:
            result = PhishingResult(
                campaign_id=campaign.id,
                user_id=user.id
            )
            self.db.add(result)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        # Track event
        self.analytics.track_event(
            event_type="phishing_campaign_created",
            event_category="phishing",
            event_action="create_campaign",
            event_label=campaign.name,
            event_value=len(recipients),
            company_id=company_id,
            user_id=created_by_id
        )
        
        return campaign
    
    def get_campaign(self, campaign_id: int, company_id: int) -> PhishingCampaign:
        """Get a phishing campaign by ID."""
        campaign = self.db.query(PhishingCampaign).filter(
            PhishingCampaign.id == campaign_id,
            PhishingCampaign.company_id == company_id
        ).options(
            joinedload(PhishingCampaign.template),
            joinedload(PhishingCampaign.results)
        ).first()
        
        if not campaign:
            raise NotFoundError(f"Campaign {campaign_id} not found")
        
        return campaign
    
    def list_campaigns(
        self,
        company_id: int,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PhishingCampaign]:
        """List phishing campaigns for a company."""
        query = self.db.query(PhishingCampaign).filter(
            PhishingCampaign.company_id == company_id
        ).options(
            joinedload(PhishingCampaign.template),
            joinedload(PhishingCampaign.results)
        )
        
        if status:
            query = query.filter(PhishingCampaign.status == status)
        
        return query.order_by(PhishingCampaign.created_at.desc()).offset(offset).limit(limit).all()
    
    def update_campaign(
        self,
        campaign_id: int,
        campaign_data: dict,
        company_id: int
    ) -> PhishingCampaign:
        """Update a phishing campaign."""
        campaign = self.get_campaign(campaign_id, company_id)
        
        # Only allow updates to draft or scheduled campaigns
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValidationError("Cannot update active or completed campaigns")
        
        for key, value in campaign_data.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        
        # If target groups changed, update recipients
        if "target_groups" in campaign_data:
            # Remove old recipients
            self.db.query(PhishingResult).filter(
                PhishingResult.campaign_id == campaign_id,
                PhishingResult.email_sent_at.is_(None)
            ).delete()
            
            # Add new recipients
            recipients = self._get_campaign_recipients(campaign)
            for user in recipients:
                result = PhishingResult(
                    campaign_id=campaign.id,
                    user_id=user.id
                )
                self.db.add(result)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def start_campaign(self, campaign_id: int, company_id: int) -> PhishingCampaign:
        """Start a phishing campaign."""
        campaign = self.get_campaign(campaign_id, company_id)
        
        if campaign.status != CampaignStatus.SCHEDULED:
            raise ValidationError("Campaign must be scheduled before starting")
        
        campaign.status = CampaignStatus.RUNNING
        campaign.started_at = datetime.utcnow()
        
        self.db.commit()
        
        # Start sending emails
        self._send_campaign_emails(campaign)
        
        # Track event
        self.analytics.track_event(
            event_type="phishing_campaign_started",
            event_category="phishing",
            event_action="start_campaign",
            event_label=campaign.name,
            event_value=campaign.total_recipients,
            company_id=company_id
        )
        
        return campaign
    
    def cancel_campaign(self, campaign_id: int, company_id: int) -> PhishingCampaign:
        """Cancel a phishing campaign."""
        campaign = self.get_campaign(campaign_id, company_id)
        
        if campaign.status in [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED]:
            raise ValidationError("Campaign is already completed or cancelled")
        
        campaign.status = CampaignStatus.CANCELLED
        campaign.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        return campaign
    
    def schedule_campaign(
        self,
        campaign_id: int,
        scheduled_at: datetime,
        company_id: int
    ) -> PhishingCampaign:
        """Schedule a phishing campaign."""
        campaign = self.get_campaign(campaign_id, company_id)
        
        if campaign.status != CampaignStatus.DRAFT:
            raise ValidationError("Only draft campaigns can be scheduled")
        
        if scheduled_at <= datetime.utcnow():
            raise ValidationError("Scheduled time must be in the future")
        
        campaign.scheduled_at = scheduled_at
        campaign.status = CampaignStatus.SCHEDULED
        
        self.db.commit()
        
        return campaign
    
    # Email Tracking
    def track_email_open(self, tracking_data: PhishingTrackingEvent) -> None:
        """Track email open event."""
        result = self._get_result_by_tracking_id(tracking_data.tracking_id)
        
        if result and not result.email_opened_at:
            result.email_opened_at = tracking_data.timestamp
            result.ip_address = tracking_data.ip_address
            result.user_agent = tracking_data.user_agent
            
            self.db.commit()
            
            # Track analytics event
            self.analytics.track_event(
                event_type="phishing_email_opened",
                event_category="phishing",
                event_action="email_open",
                event_label=f"campaign_{result.campaign_id}",
                user_id=result.user_id,
                company_id=result.campaign.company_id
            )
    
    def track_link_click(self, tracking_data: PhishingTrackingEvent) -> str:
        """Track link click event and return redirect URL."""
        result = self._get_result_by_tracking_id(tracking_data.tracking_id)
        
        if result:
            if not result.link_clicked_at:
                result.link_clicked_at = tracking_data.timestamp
                result.ip_address = tracking_data.ip_address
                result.user_agent = tracking_data.user_agent
                result.location_data = tracking_data.additional_data
                
                self.db.commit()
                
                # Track analytics event
                self.analytics.track_event(
                    event_type="phishing_link_clicked",
                    event_category="phishing",
                    event_action="link_click",
                    event_label=f"campaign_{result.campaign_id}",
                    user_id=result.user_id,
                    company_id=result.campaign.company_id
                )
                
                # Trigger immediate training if configured
                if result.campaign.settings.get("training_url"):
                    return result.campaign.settings["training_url"]
            
            # Return landing page or redirect URL
            if result.campaign.settings.get("landing_page_url"):
                return result.campaign.settings["landing_page_url"]
            elif result.campaign.settings.get("redirect_url"):
                return result.campaign.settings["redirect_url"]
        
        # Default redirect
        return "/phishing-awareness"
    
    def track_data_submission(self, tracking_data: PhishingTrackingEvent) -> None:
        """Track credential submission event."""
        result = self._get_result_by_tracking_id(tracking_data.tracking_id)
        
        if result and not result.data_submitted_at:
            result.data_submitted_at = tracking_data.timestamp
            
            self.db.commit()
            
            # Track analytics event
            self.analytics.track_event(
                event_type="phishing_credentials_entered",
                event_category="phishing",
                event_action="data_submit",
                event_label=f"campaign_{result.campaign_id}",
                user_id=result.user_id,
                company_id=result.campaign.company_id
            )
    
    def report_phishing(
        self,
        campaign_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> None:
        """Report a phishing email."""
        result = self.db.query(PhishingResult).filter(
            PhishingResult.campaign_id == campaign_id,
            PhishingResult.user_id == user_id
        ).first()
        
        if result and not result.reported_at:
            result.reported_at = datetime.utcnow()
            
            self.db.commit()
            
            # Track analytics event
            self.analytics.track_event(
                event_type="phishing_reported",
                event_category="phishing",
                event_action="report",
                event_label=f"campaign_{campaign_id}",
                event_value=1 if not result.link_clicked_at else 0,  # 1 if reported before clicking
                user_id=user_id,
                company_id=result.campaign.company_id,
                metadata={"reason": reason}
            )
    
    # Analytics and Reporting
    def get_campaign_analytics(self, campaign_id: int, company_id: int) -> CampaignAnalytics:
        """Get detailed analytics for a campaign."""
        campaign = self.get_campaign(campaign_id, company_id)
        results = campaign.results
        
        # Calculate metrics
        emails_sent = len([r for r in results if r.email_sent_at])
        unique_opens = len([r for r in results if r.email_opened_at])
        unique_clicks = len([r for r in results if r.link_clicked_at])
        credentials_entered = len([r for r in results if r.data_submitted_at])
        reported = len([r for r in results if r.reported_at])
        
        # Time-based metrics
        open_times = []
        click_times = []
        for result in results:
            if result.email_sent_at and result.email_opened_at:
                open_times.append((result.email_opened_at - result.email_sent_at).total_seconds() / 60)
            if result.email_sent_at and result.link_clicked_at:
                click_times.append((result.link_clicked_at - result.email_sent_at).total_seconds() / 60)
        
        # Department/role breakdown
        department_stats = self._calculate_department_stats(campaign)
        role_stats = self._calculate_role_stats(campaign)
        
        # Risk score (0-100)
        risk_score = (unique_clicks / emails_sent * 100) if emails_sent > 0 else 0
        
        analytics = CampaignAnalytics(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            status=campaign.status,
            scheduled_at=campaign.scheduled_at,
            started_at=campaign.started_at,
            completed_at=campaign.completed_at,
            duration_hours=(
                (campaign.completed_at - campaign.started_at).total_seconds() / 3600
                if campaign.started_at and campaign.completed_at else None
            ),
            total_recipients=len(results),
            emails_sent=emails_sent,
            emails_pending=len(results) - emails_sent,
            emails_failed=0,  # TODO: Track failed emails
            unique_opens=unique_opens,
            total_opens=unique_opens,  # TODO: Track multiple opens
            unique_clicks=unique_clicks,
            total_clicks=unique_clicks,  # TODO: Track multiple clicks
            credentials_entered=credentials_entered,
            reported_suspicious=reported,
            delivery_rate=100.0,  # TODO: Track actual delivery
            open_rate=(unique_opens / emails_sent * 100) if emails_sent > 0 else 0,
            click_rate=(unique_clicks / emails_sent * 100) if emails_sent > 0 else 0,
            report_rate=(reported / emails_sent * 100) if emails_sent > 0 else 0,
            failure_rate=0.0,  # TODO: Track failures
            avg_time_to_open_minutes=sum(open_times) / len(open_times) if open_times else None,
            avg_time_to_click_minutes=sum(click_times) / len(click_times) if click_times else None,
            fastest_click_minutes=min(click_times) if click_times else None,
            risk_score=risk_score,
            department_stats=department_stats,
            role_stats=role_stats
        )
        
        return analytics
    
    def get_compliance_report(
        self,
        company_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """Generate compliance report for a company."""
        # Get campaigns in date range
        campaigns = self.db.query(PhishingCampaign).filter(
            PhishingCampaign.company_id == company_id,
            PhishingCampaign.started_at.between(start_date, end_date)
        ).all()
        
        # Calculate metrics
        total_campaigns = len(campaigns)
        all_results = []
        for campaign in campaigns:
            all_results.extend(campaign.results)
        
        unique_users_tested = len(set(r.user_id for r in all_results))
        total_emails_sent = len([r for r in all_results if r.email_sent_at])
        total_clicks = len([r for r in all_results if r.link_clicked_at])
        total_reports = len([r for r in all_results if r.reported_at])
        
        # Risk assessment
        high_risk_users = self._identify_high_risk_users(company_id, all_results)
        departmental_risk_scores = self._calculate_departmental_risk(company_id, all_results)
        
        # Training metrics
        users_requiring_training = len([u for u in high_risk_users if u["click_rate"] > 50])
        users_completed_training = 0  # TODO: Integrate with training system
        
        # Compliance scoring
        total_users = self.db.query(User).filter(User.company_id == company_id).count()
        coverage_rate = (unique_users_tested / total_users * 100) if total_users > 0 else 0
        
        report = ComplianceReport(
            company_id=company_id,
            report_period_start=start_date,
            report_period_end=end_date,
            total_campaigns=total_campaigns,
            total_users_tested=len(all_results),
            unique_users_tested=unique_users_tested,
            total_emails_sent=total_emails_sent,
            total_clicks=total_clicks,
            overall_click_rate=(total_clicks / total_emails_sent * 100) if total_emails_sent > 0 else 0,
            overall_report_rate=(total_reports / total_emails_sent * 100) if total_emails_sent > 0 else 0,
            click_rate_trend=self._calculate_trend("click_rate", company_id, start_date, end_date),
            report_rate_trend=self._calculate_trend("report_rate", company_id, start_date, end_date),
            users_requiring_training=users_requiring_training,
            users_completed_training=users_completed_training,
            training_completion_rate=(
                users_completed_training / users_requiring_training * 100
                if users_requiring_training > 0 else 0
            ),
            high_risk_users=high_risk_users[:10],  # Top 10 high risk users
            departmental_risk_scores=departmental_risk_scores,
            testing_frequency_compliant=total_campaigns >= 4,  # At least quarterly
            coverage_compliant=coverage_rate >= 80,  # 80% coverage
            training_compliant=users_completed_training >= users_requiring_training * 0.9,  # 90% training completion
            overall_compliance_score=self._calculate_compliance_score(
                total_campaigns, coverage_rate, users_completed_training, users_requiring_training
            )
        )
        
        return report
    
    # Private helper methods
    def _get_campaign_recipients(self, campaign: PhishingCampaign) -> List[User]:
        """Get list of users targeted by campaign."""
        recipients = []
        
        for target_group in campaign.target_groups:
            if target_group["type"] == "department":
                users = self.db.query(User).filter(
                    User.company_id == campaign.company_id,
                    User.department.in_(target_group["value"]),
                    User.is_active == True
                ).all()
                recipients.extend(users)
            elif target_group["type"] == "role":
                users = self.db.query(User).filter(
                    User.company_id == campaign.company_id,
                    User.role.in_(target_group["value"]),
                    User.is_active == True
                ).all()
                recipients.extend(users)
            elif target_group["type"] == "users":
                user_ids = [int(uid) for uid in target_group["value"]]
                users = self.db.query(User).filter(
                    User.id.in_(user_ids),
                    User.company_id == campaign.company_id,
                    User.is_active == True
                ).all()
                recipients.extend(users)
        
        # Remove duplicates
        return list({user.id: user for user in recipients}.values())
    
    def _generate_tracking_id(self, campaign_id: int, user_id: int) -> str:
        """Generate unique tracking ID for email."""
        data = f"{campaign_id}:{user_id}:{secrets.token_urlsafe(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def _get_result_by_tracking_id(self, tracking_id: str) -> Optional[PhishingResult]:
        """Get phishing result by tracking ID."""
        # TODO: Implement tracking ID lookup
        # For now, this is a placeholder
        return None
    
    def _send_campaign_emails(self, campaign: PhishingCampaign) -> None:
        """Send phishing emails for campaign."""
        template = campaign.template
        settings = campaign.settings
        
        # Get unsent results
        results = self.db.query(PhishingResult).filter(
            PhishingResult.campaign_id == campaign.id,
            PhishingResult.email_sent_at.is_(None)
        ).all()
        
        send_rate = settings.get("send_rate_per_hour", 100)
        batch_size = min(send_rate, len(results))
        
        for i, result in enumerate(results[:batch_size]):
            user = result.user
            tracking_id = self._generate_tracking_id(campaign.id, user.id)
            
            # Prepare email content with tracking
            html_content = self._prepare_email_content(
                template.html_content,
                user,
                tracking_id,
                settings
            )
            
            # Send email
            try:
                self.email_service.send_email(
                    to_email=user.email,
                    subject=template.subject,
                    html_content=html_content,
                    text_content=template.text_content,
                    from_name=template.sender_name,
                    from_email=template.sender_email,
                    headers={
                        "X-Phishing-Campaign": str(campaign.id),
                        "X-Tracking-ID": tracking_id
                    }
                )
                
                result.email_sent_at = datetime.utcnow()
                
                # Add random delay if configured
                if settings.get("randomize_send_times") and i < batch_size - 1:
                    import time
                    time.sleep(secrets.randbelow(10) + 1)  # 1-10 seconds
                    
            except Exception as e:
                # Log error but continue with other emails
                print(f"Failed to send email to {user.email}: {e}")
        
        self.db.commit()
        
        # Check if all emails sent
        remaining = self.db.query(PhishingResult).filter(
            PhishingResult.campaign_id == campaign.id,
            PhishingResult.email_sent_at.is_(None)
        ).count()
        
        if remaining == 0:
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = datetime.utcnow()
            self.db.commit()
    
    def _prepare_email_content(
        self,
        template_content: str,
        user: User,
        tracking_id: str,
        settings: dict
    ) -> str:
        """Prepare email content with personalization and tracking."""
        # Replace variables
        content = template_content
        content = content.replace("{{first_name}}", user.first_name or "")
        content = content.replace("{{last_name}}", user.last_name or "")
        content = content.replace("{{email}}", user.email)
        content = content.replace("{{company}}", user.company.name if user.company else "")
        
        # Add tracking pixel if enabled
        if settings.get("track_opens", True):
            tracking_pixel = f'<img src="/api/phishing/track/open/{tracking_id}" width="1" height="1" style="display:none">'
            content = content.replace("</body>", f"{tracking_pixel}</body>")
        
        # Replace links with tracking links if enabled
        if settings.get("track_clicks", True):
            import re
            link_pattern = r'href="([^"]+)"'
            
            def replace_link(match):
                original_url = match.group(1)
                if original_url.startswith(("http://", "https://")):
                    tracking_url = f"/api/phishing/track/click/{tracking_id}?url={original_url}"
                    return f'href="{tracking_url}"'
                return match.group(0)
            
            content = re.sub(link_pattern, replace_link, content)
        
        return content
    
    def _calculate_department_stats(self, campaign: PhishingCampaign) -> List[Dict[str, Any]]:
        """Calculate statistics by department."""
        stats = {}
        
        for result in campaign.results:
            dept = result.user.department or "Unknown"
            if dept not in stats:
                stats[dept] = {
                    "department": dept,
                    "total": 0,
                    "clicked": 0,
                    "reported": 0,
                    "click_rate": 0.0,
                    "report_rate": 0.0
                }
            
            stats[dept]["total"] += 1
            if result.link_clicked_at:
                stats[dept]["clicked"] += 1
            if result.reported_at:
                stats[dept]["reported"] += 1
        
        # Calculate rates
        for dept_stats in stats.values():
            if dept_stats["total"] > 0:
                dept_stats["click_rate"] = dept_stats["clicked"] / dept_stats["total"] * 100
                dept_stats["report_rate"] = dept_stats["reported"] / dept_stats["total"] * 100
        
        return list(stats.values())
    
    def _calculate_role_stats(self, campaign: PhishingCampaign) -> List[Dict[str, Any]]:
        """Calculate statistics by role."""
        # Similar to department stats but by role
        return []
    
    def _identify_high_risk_users(
        self,
        company_id: int,
        results: List[PhishingResult]
    ) -> List[Dict[str, Any]]:
        """Identify users with high phishing risk."""
        user_stats = {}
        
        for result in results:
            user_id = result.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "user_id": user_id,
                    "email": result.user.email,
                    "name": f"{result.user.first_name} {result.user.last_name}",
                    "campaigns": 0,
                    "clicks": 0,
                    "reports": 0
                }
            
            user_stats[user_id]["campaigns"] += 1
            if result.link_clicked_at:
                user_stats[user_id]["clicks"] += 1
            if result.reported_at:
                user_stats[user_id]["reports"] += 1
        
        # Calculate click rate and sort by risk
        high_risk_users = []
        for stats in user_stats.values():
            if stats["campaigns"] > 0:
                stats["click_rate"] = stats["clicks"] / stats["campaigns"] * 100
                stats["report_rate"] = stats["reports"] / stats["campaigns"] * 100
                high_risk_users.append(stats)
        
        # Sort by click rate (descending)
        high_risk_users.sort(key=lambda x: x["click_rate"], reverse=True)
        
        return high_risk_users
    
    def _calculate_departmental_risk(
        self,
        company_id: int,
        results: List[PhishingResult]
    ) -> List[Dict[str, Any]]:
        """Calculate risk scores by department."""
        # Similar to department stats but focused on risk
        return []
    
    def _calculate_trend(
        self,
        metric: str,
        company_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Calculate trend for a metric."""
        # TODO: Implement trend calculation
        return "stable"
    
    def _calculate_compliance_score(
        self,
        campaigns: int,
        coverage_rate: float,
        users_trained: int,
        users_requiring_training: int
    ) -> float:
        """Calculate overall compliance score."""
        # Weighted scoring
        frequency_score = min(campaigns / 4 * 100, 100)  # Quarterly target
        coverage_score = coverage_rate
        training_score = (
            (users_trained / users_requiring_training * 100)
            if users_requiring_training > 0 else 100
        )
        
        # Weighted average
        return (frequency_score * 0.3 + coverage_score * 0.4 + training_score * 0.3)