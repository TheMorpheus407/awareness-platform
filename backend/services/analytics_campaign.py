"""Campaign performance analytics service."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import select, func, and_, or_, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.email_campaign import EmailCampaign, EmailLog
from models.phishing import PhishingCampaign, PhishingResult
from models.user import User
from models.company import Company
from core.cache import cache, cache_key, cached
from core.logging import logger


class CampaignAnalyticsService:
    """Service for analyzing campaign performance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    @cached(expire=300, key_prefix="campaign_analytics")
    async def get_campaign_overview(
        self,
        company_id: int,
        campaign_type: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive campaign overview.
        
        Args:
            company_id: Company ID
            campaign_type: Optional filter by campaign type ('email', 'phishing')
            date_range: Optional date range filter
            
        Returns:
            Campaign overview metrics
        """
        if not date_range:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
            
        metrics = {
            "summary": await self._get_campaign_summary(company_id, campaign_type, date_range),
            "performance": await self._get_campaign_performance(company_id, campaign_type, date_range),
            "engagement": await self._get_engagement_metrics(company_id, campaign_type, date_range),
            "conversion": await self._get_conversion_metrics(company_id, campaign_type, date_range),
            "trends": await self._get_campaign_trends(company_id, campaign_type, date_range),
            "top_campaigns": await self._get_top_performing_campaigns(company_id, campaign_type, date_range),
        }
        
        return metrics
        
    async def _get_campaign_summary(
        self,
        company_id: int,
        campaign_type: Optional[str],
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get campaign summary statistics."""
        start_date, end_date = date_range
        summary = {}
        
        # Email campaigns
        if not campaign_type or campaign_type == "email":
            email_query = select(
                func.count(EmailCampaign.id).label('total_campaigns'),
                func.sum(case((EmailCampaign.status == 'sent', 1), else_=0)).label('sent'),
                func.sum(case((EmailCampaign.status == 'draft', 1), else_=0)).label('draft'),
                func.sum(case((EmailCampaign.status == 'scheduled', 1), else_=0)).label('scheduled')
            ).where(
                EmailCampaign.company_id == company_id,
                EmailCampaign.created_at.between(start_date, end_date)
            )
            
            email_result = await self.db.execute(email_query)
            email_data = email_result.one()
            
            summary["email_campaigns"] = {
                "total": email_data.total_campaigns or 0,
                "sent": email_data.sent or 0,
                "draft": email_data.draft or 0,
                "scheduled": email_data.scheduled or 0,
            }
            
        # Phishing campaigns
        if not campaign_type or campaign_type == "phishing":
            phishing_query = select(
                func.count(PhishingCampaign.id).label('total_campaigns'),
                func.sum(case((PhishingCampaign.status == 'completed', 1), else_=0)).label('completed'),
                func.sum(case((PhishingCampaign.status == 'active', 1), else_=0)).label('active'),
                func.sum(case((PhishingCampaign.status == 'scheduled', 1), else_=0)).label('scheduled')
            ).where(
                PhishingCampaign.company_id == company_id,
                PhishingCampaign.created_at.between(start_date, end_date)
            )
            
            phishing_result = await self.db.execute(phishing_query)
            phishing_data = phishing_result.one()
            
            summary["phishing_campaigns"] = {
                "total": phishing_data.total_campaigns or 0,
                "completed": phishing_data.completed or 0,
                "active": phishing_data.active or 0,
                "scheduled": phishing_data.scheduled or 0,
            }
            
        return summary
        
    async def _get_campaign_performance(
        self,
        company_id: int,
        campaign_type: Optional[str],
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get campaign performance metrics."""
        start_date, end_date = date_range
        performance = {}
        
        # Email campaign performance
        if not campaign_type or campaign_type == "email":
            email_perf_query = select(
                func.count(EmailLog.id).label('total_sent'),
                func.sum(case((EmailLog.opened_at.isnot(None), 1), else_=0)).label('opened'),
                func.sum(case((EmailLog.clicked_at.isnot(None), 1), else_=0)).label('clicked'),
                func.sum(case((EmailLog.unsubscribed_at.isnot(None), 1), else_=0)).label('unsubscribed'),
                func.sum(case((EmailLog.bounced == True, 1), else_=0)).label('bounced')
            ).join(
                EmailCampaign, EmailLog.campaign_id == EmailCampaign.id
            ).where(
                EmailCampaign.company_id == company_id,
                EmailLog.sent_at.between(start_date, end_date)
            )
            
            email_perf_result = await self.db.execute(email_perf_query)
            email_perf = email_perf_result.one()
            
            total_sent = email_perf.total_sent or 1  # Avoid division by zero
            
            performance["email"] = {
                "total_sent": email_perf.total_sent or 0,
                "opened": email_perf.opened or 0,
                "clicked": email_perf.clicked or 0,
                "unsubscribed": email_perf.unsubscribed or 0,
                "bounced": email_perf.bounced or 0,
                "open_rate": round((email_perf.opened or 0) / total_sent * 100, 2),
                "click_rate": round((email_perf.clicked or 0) / total_sent * 100, 2),
                "unsubscribe_rate": round((email_perf.unsubscribed or 0) / total_sent * 100, 2),
                "bounce_rate": round((email_perf.bounced or 0) / total_sent * 100, 2),
            }
            
        # Phishing campaign performance
        if not campaign_type or campaign_type == "phishing":
            phishing_perf_query = select(
                func.count(PhishingResult.id).label('total_sent'),
                func.sum(case((PhishingResult.email_opened_at.isnot(None), 1), else_=0)).label('opened'),
                func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked'),
                func.sum(case((PhishingResult.data_submitted_at.isnot(None), 1), else_=0)).label('submitted'),
                func.sum(case((PhishingResult.reported_at.isnot(None), 1), else_=0)).label('reported')
            ).join(
                PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
            ).where(
                PhishingCampaign.company_id == company_id,
                PhishingResult.email_sent_at.between(start_date, end_date)
            )
            
            phishing_perf_result = await self.db.execute(phishing_perf_query)
            phishing_perf = phishing_perf_result.one()
            
            total_phishing = phishing_perf.total_sent or 1
            
            performance["phishing"] = {
                "total_sent": phishing_perf.total_sent or 0,
                "opened": phishing_perf.opened or 0,
                "clicked": phishing_perf.clicked or 0,
                "submitted": phishing_perf.submitted or 0,
                "reported": phishing_perf.reported or 0,
                "open_rate": round((phishing_perf.opened or 0) / total_phishing * 100, 2),
                "click_rate": round((phishing_perf.clicked or 0) / total_phishing * 100, 2),
                "submit_rate": round((phishing_perf.submitted or 0) / total_phishing * 100, 2),
                "report_rate": round((phishing_perf.reported or 0) / total_phishing * 100, 2),
            }
            
        return performance
        
    async def _get_engagement_metrics(
        self,
        company_id: int,
        campaign_type: Optional[str],
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get user engagement metrics."""
        start_date, end_date = date_range
        engagement = {}
        
        # Time-based engagement analysis
        if not campaign_type or campaign_type == "email":
            # Best time to send emails
            email_hour_query = select(
                func.extract('hour', EmailLog.opened_at).label('hour'),
                func.count(EmailLog.id).label('opens')
            ).join(
                EmailCampaign, EmailLog.campaign_id == EmailCampaign.id
            ).where(
                EmailCampaign.company_id == company_id,
                EmailLog.opened_at.isnot(None),
                EmailLog.opened_at.between(start_date, end_date)
            ).group_by('hour').order_by('opens', desc()).limit(5)
            
            email_hour_result = await self.db.execute(email_hour_query)
            best_hours = [
                {"hour": int(row.hour), "opens": row.opens}
                for row in email_hour_result
            ]
            
            engagement["email_best_hours"] = best_hours
            
        # Device and client analysis
        device_query = select(
            func.coalesce(EmailLog.device_type, 'unknown').label('device'),
            func.count(EmailLog.id).label('count')
        ).join(
            EmailCampaign, EmailLog.campaign_id == EmailCampaign.id
        ).where(
            EmailCampaign.company_id == company_id,
            EmailLog.opened_at.isnot(None),
            EmailLog.opened_at.between(start_date, end_date)
        ).group_by('device')
        
        device_result = await self.db.execute(device_query)
        engagement["devices"] = [
            {"device": row.device, "count": row.count}
            for row in device_result
        ]
        
        return engagement
        
    async def _get_conversion_metrics(
        self,
        company_id: int,
        campaign_type: Optional[str],
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get conversion funnel metrics."""
        start_date, end_date = date_range
        conversion = {}
        
        if not campaign_type or campaign_type == "email":
            # Email conversion funnel
            email_funnel_query = select(
                func.count(EmailLog.id).label('sent'),
                func.sum(case((EmailLog.opened_at.isnot(None), 1), else_=0)).label('opened'),
                func.sum(case((EmailLog.clicked_at.isnot(None), 1), else_=0)).label('clicked'),
                func.sum(case((EmailLog.converted_at.isnot(None), 1), else_=0)).label('converted')
            ).join(
                EmailCampaign, EmailLog.campaign_id == EmailCampaign.id
            ).where(
                EmailCampaign.company_id == company_id,
                EmailLog.sent_at.between(start_date, end_date)
            )
            
            funnel_result = await self.db.execute(email_funnel_query)
            funnel_data = funnel_result.one()
            
            conversion["email_funnel"] = {
                "sent": funnel_data.sent or 0,
                "opened": funnel_data.opened or 0,
                "clicked": funnel_data.clicked or 0,
                "converted": funnel_data.converted or 0,
                "open_to_click": round((funnel_data.clicked or 0) / (funnel_data.opened or 1) * 100, 2),
                "click_to_convert": round((funnel_data.converted or 0) / (funnel_data.clicked or 1) * 100, 2),
            }
            
        if not campaign_type or campaign_type == "phishing":
            # Phishing awareness funnel
            phishing_funnel_query = select(
                func.count(PhishingResult.id).label('sent'),
                func.sum(case((PhishingResult.email_opened_at.isnot(None), 1), else_=0)).label('opened'),
                func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked'),
                func.sum(case((PhishingResult.data_submitted_at.isnot(None), 1), else_=0)).label('submitted'),
                func.sum(case((PhishingResult.reported_at.isnot(None), 1), else_=0)).label('reported')
            ).join(
                PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
            ).where(
                PhishingCampaign.company_id == company_id,
                PhishingResult.email_sent_at.between(start_date, end_date)
            )
            
            phishing_funnel_result = await self.db.execute(phishing_funnel_query)
            phishing_funnel = phishing_funnel_result.one()
            
            conversion["phishing_funnel"] = {
                "sent": phishing_funnel.sent or 0,
                "opened": phishing_funnel.opened or 0,
                "clicked": phishing_funnel.clicked or 0,
                "submitted": phishing_funnel.submitted or 0,
                "reported": phishing_funnel.reported or 0,
                "awareness_score": round(
                    (1 - (phishing_funnel.clicked or 0) / (phishing_funnel.sent or 1)) * 100, 2
                ),
            }
            
        return conversion
        
    async def _get_campaign_trends(
        self,
        company_id: int,
        campaign_type: Optional[str],
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get campaign performance trends over time."""
        start_date, end_date = date_range
        trends = {}
        
        # Daily email performance
        if not campaign_type or campaign_type == "email":
            daily_email_query = select(
                func.date(EmailLog.sent_at).label('date'),
                func.count(EmailLog.id).label('sent'),
                func.sum(case((EmailLog.opened_at.isnot(None), 1), else_=0)).label('opened'),
                func.sum(case((EmailLog.clicked_at.isnot(None), 1), else_=0)).label('clicked')
            ).join(
                EmailCampaign, EmailLog.campaign_id == EmailCampaign.id
            ).where(
                EmailCampaign.company_id == company_id,
                EmailLog.sent_at.between(start_date, end_date)
            ).group_by('date').order_by('date')
            
            daily_email_result = await self.db.execute(daily_email_query)
            
            trends["email_daily"] = [
                {
                    "date": row.date.isoformat(),
                    "sent": row.sent,
                    "opened": row.opened,
                    "clicked": row.clicked,
                    "open_rate": round(row.opened / row.sent * 100, 2) if row.sent > 0 else 0,
                    "click_rate": round(row.clicked / row.sent * 100, 2) if row.sent > 0 else 0,
                }
                for row in daily_email_result
            ]
            
        # Weekly phishing trends
        if not campaign_type or campaign_type == "phishing":
            weekly_phishing_query = select(
                func.date_trunc('week', PhishingResult.email_sent_at).label('week'),
                func.count(PhishingResult.id).label('sent'),
                func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked')
            ).join(
                PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
            ).where(
                PhishingCampaign.company_id == company_id,
                PhishingResult.email_sent_at.between(start_date, end_date)
            ).group_by('week').order_by('week')
            
            weekly_phishing_result = await self.db.execute(weekly_phishing_query)
            
            trends["phishing_weekly"] = [
                {
                    "week": row.week.isoformat(),
                    "sent": row.sent,
                    "clicked": row.clicked,
                    "click_rate": round(row.clicked / row.sent * 100, 2) if row.sent > 0 else 0,
                }
                for row in weekly_phishing_result
            ]
            
        return trends
        
    async def _get_top_performing_campaigns(
        self,
        company_id: int,
        campaign_type: Optional[str],
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get top performing campaigns."""
        start_date, end_date = date_range
        top_campaigns = {}
        
        # Top email campaigns by engagement
        if not campaign_type or campaign_type == "email":
            top_email_query = select(
                EmailCampaign.id,
                EmailCampaign.name,
                EmailCampaign.subject,
                func.count(EmailLog.id).label('sent'),
                func.sum(case((EmailLog.opened_at.isnot(None), 1), else_=0)).label('opened'),
                func.sum(case((EmailLog.clicked_at.isnot(None), 1), else_=0)).label('clicked')
            ).join(
                EmailLog, EmailCampaign.id == EmailLog.campaign_id
            ).where(
                EmailCampaign.company_id == company_id,
                EmailCampaign.created_at.between(start_date, end_date)
            ).group_by(EmailCampaign.id).order_by(
                func.sum(case((EmailLog.clicked_at.isnot(None), 1), else_=0)).desc()
            ).limit(10)
            
            top_email_result = await self.db.execute(top_email_query)
            
            top_campaigns["email"] = [
                {
                    "id": row.id,
                    "name": row.name,
                    "subject": row.subject,
                    "sent": row.sent,
                    "opened": row.opened,
                    "clicked": row.clicked,
                    "engagement_score": round(
                        (row.opened * 0.3 + row.clicked * 0.7) / row.sent * 100, 2
                    ) if row.sent > 0 else 0,
                }
                for row in top_email_result
            ]
            
        # Top phishing campaigns by effectiveness
        if not campaign_type or campaign_type == "phishing":
            top_phishing_query = select(
                PhishingCampaign.id,
                PhishingCampaign.name,
                func.count(PhishingResult.id).label('sent'),
                func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked'),
                func.sum(case((PhishingResult.reported_at.isnot(None), 1), else_=0)).label('reported')
            ).join(
                PhishingResult, PhishingCampaign.id == PhishingResult.campaign_id
            ).where(
                PhishingCampaign.company_id == company_id,
                PhishingCampaign.created_at.between(start_date, end_date)
            ).group_by(PhishingCampaign.id).order_by(
                func.sum(case((PhishingResult.reported_at.isnot(None), 1), else_=0)).desc()
            ).limit(10)
            
            top_phishing_result = await self.db.execute(top_phishing_query)
            
            top_campaigns["phishing"] = [
                {
                    "id": row.id,
                    "name": row.name,
                    "sent": row.sent,
                    "clicked": row.clicked,
                    "reported": row.reported,
                    "effectiveness_score": round(
                        (row.reported * 2 - row.clicked) / row.sent * 100, 2
                    ) if row.sent > 0 else 0,
                }
                for row in top_phishing_result
            ]
            
        return top_campaigns
        
    async def get_campaign_details(
        self,
        company_id: int,
        campaign_id: int,
        campaign_type: str
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific campaign."""
        if campaign_type == "email":
            return await self._get_email_campaign_details(company_id, campaign_id)
        elif campaign_type == "phishing":
            return await self._get_phishing_campaign_details(company_id, campaign_id)
        else:
            raise ValueError(f"Invalid campaign type: {campaign_type}")
            
    async def _get_email_campaign_details(
        self,
        company_id: int,
        campaign_id: int
    ) -> Dict[str, Any]:
        """Get detailed email campaign analytics."""
        # Get campaign info
        campaign_query = select(EmailCampaign).where(
            EmailCampaign.id == campaign_id,
            EmailCampaign.company_id == company_id
        )
        campaign_result = await self.db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()
        
        if not campaign:
            raise ValueError("Campaign not found")
            
        # Get detailed metrics
        metrics_query = select(
            func.count(EmailLog.id).label('total_sent'),
            func.sum(case((EmailLog.opened_at.isnot(None), 1), else_=0)).label('opened'),
            func.sum(case((EmailLog.clicked_at.isnot(None), 1), else_=0)).label('clicked'),
            func.sum(case((EmailLog.unsubscribed_at.isnot(None), 1), else_=0)).label('unsubscribed'),
            func.sum(case((EmailLog.bounced == True, 1), else_=0)).label('bounced'),
            func.avg(
                func.extract('epoch', EmailLog.opened_at - EmailLog.sent_at) / 3600
            ).label('avg_open_time_hours')
        ).where(EmailLog.campaign_id == campaign_id)
        
        metrics_result = await self.db.execute(metrics_query)
        metrics = metrics_result.one()
        
        # Get click map
        click_map_query = select(
            EmailLog.click_data['link'].label('link'),
            func.count(EmailLog.id).label('clicks')
        ).where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.click_data.isnot(None)
        ).group_by('link')
        
        click_map_result = await self.db.execute(click_map_query)
        click_map = [
            {"link": row.link, "clicks": row.clicks}
            for row in click_map_result
        ]
        
        return {
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "subject": campaign.subject,
                "created_at": campaign.created_at.isoformat(),
                "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
                "status": campaign.status,
            },
            "metrics": {
                "total_sent": metrics.total_sent or 0,
                "opened": metrics.opened or 0,
                "clicked": metrics.clicked or 0,
                "unsubscribed": metrics.unsubscribed or 0,
                "bounced": metrics.bounced or 0,
                "open_rate": round((metrics.opened or 0) / (metrics.total_sent or 1) * 100, 2),
                "click_rate": round((metrics.clicked or 0) / (metrics.total_sent or 1) * 100, 2),
                "avg_open_time_hours": round(metrics.avg_open_time_hours or 0, 2),
            },
            "click_map": click_map,
        }
        
    async def _get_phishing_campaign_details(
        self,
        company_id: int,
        campaign_id: int
    ) -> Dict[str, Any]:
        """Get detailed phishing campaign analytics."""
        # Get campaign info
        campaign_query = select(PhishingCampaign).where(
            PhishingCampaign.id == campaign_id,
            PhishingCampaign.company_id == company_id
        ).options(selectinload(PhishingCampaign.template))
        
        campaign_result = await self.db.execute(campaign_query)
        campaign = campaign_result.scalar_one_or_none()
        
        if not campaign:
            raise ValueError("Campaign not found")
            
        # Get user performance
        user_perf_query = select(
            User.id,
            User.first_name,
            User.last_name,
            PhishingResult.email_opened_at,
            PhishingResult.link_clicked_at,
            PhishingResult.data_submitted_at,
            PhishingResult.reported_at
        ).join(
            PhishingResult, User.id == PhishingResult.user_id
        ).where(PhishingResult.campaign_id == campaign_id)
        
        user_perf_result = await self.db.execute(user_perf_query)
        
        user_performance = []
        for row in user_perf_result:
            status = "safe"
            if row.data_submitted_at:
                status = "compromised"
            elif row.link_clicked_at:
                status = "clicked"
            elif row.reported_at:
                status = "reported"
            elif row.email_opened_at:
                status = "opened"
                
            user_performance.append({
                "user_id": row.id,
                "name": f"{row.first_name} {row.last_name}",
                "status": status,
                "opened_at": row.email_opened_at.isoformat() if row.email_opened_at else None,
                "clicked_at": row.link_clicked_at.isoformat() if row.link_clicked_at else None,
                "submitted_at": row.data_submitted_at.isoformat() if row.data_submitted_at else None,
                "reported_at": row.reported_at.isoformat() if row.reported_at else None,
            })
            
        return {
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "template": campaign.template.name if campaign.template else None,
                "created_at": campaign.created_at.isoformat(),
                "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                "status": campaign.status,
            },
            "user_performance": user_performance,
            "summary": {
                "total_users": len(user_performance),
                "safe": len([u for u in user_performance if u["status"] == "safe"]),
                "opened": len([u for u in user_performance if u["status"] in ["opened", "clicked", "compromised"]]),
                "clicked": len([u for u in user_performance if u["status"] in ["clicked", "compromised"]]),
                "compromised": len([u for u in user_performance if u["status"] == "compromised"]),
                "reported": len([u for u in user_performance if u["status"] == "reported"]),
            }
        }