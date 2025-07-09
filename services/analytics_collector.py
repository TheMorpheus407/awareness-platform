"""Analytics data collection service."""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.logging import logger
from models import (
    User, Company, Course, CourseEnrollment, Quiz, QuizAttempt,
    CourseAnalytics, UserEngagement, RevenueAnalytics,
    PhishingAnalytics, RealtimeMetric, AnalyticsEvent,
    Subscription, Payment, Invoice, PhishingCampaign, PhishingResult
)


class AnalyticsCollector:
    """Service for collecting and aggregating analytics data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_daily_analytics(self, target_date: Optional[date] = None):
        """Collect all analytics for a specific date."""
        if not target_date:
            target_date = date.today() - timedelta(days=1)  # Yesterday by default
        
        logger.info(f"Collecting analytics for {target_date}")
        
        try:
            # Collect different types of analytics
            await self.collect_course_analytics(target_date)
            await self.collect_user_engagement(target_date)
            await self.collect_revenue_analytics(target_date)
            await self.collect_phishing_analytics(target_date)
            
            # Update real-time metrics
            await self.update_realtime_metrics()
            
            logger.info(f"Analytics collection completed for {target_date}")
            
        except Exception as e:
            logger.error(f"Error collecting analytics: {str(e)}")
            raise
    
    async def collect_course_analytics(self, target_date: date):
        """Collect course analytics for the target date."""
        try:
            # Get all companies
            companies = self.db.query(Company).filter(Company.deleted_at.is_(None)).all()
            
            for company in companies:
                # Get all published courses
                courses = self.db.query(Course).filter(
                    Course.status == 'published'
                ).all()
                
                for course in courses:
                    # Get enrollments for this course and company
                    enrollments = self.db.query(CourseEnrollment).join(User).filter(
                        CourseEnrollment.course_id == course.id,
                        User.company_id == company.id,
                        CourseEnrollment.created_at <= target_date + timedelta(days=1)
                    ).all()
                    
                    if not enrollments:
                        continue
                    
                    # Calculate metrics
                    enrollments_count = len(enrollments)
                    completions_count = sum(1 for e in enrollments if e.completed_at and e.completed_at.date() <= target_date)
                    avg_progress = sum(e.progress or 0 for e in enrollments) / enrollments_count if enrollments_count > 0 else 0
                    
                    # Get quiz scores
                    quiz_scores = []
                    for enrollment in enrollments:
                        attempts = self.db.query(QuizAttempt).join(Quiz).filter(
                            Quiz.course_id == course.id,
                            QuizAttempt.user_id == enrollment.user_id,
                            QuizAttempt.completed_at.isnot(None)
                        ).all()
                        quiz_scores.extend([a.score for a in attempts if a.score is not None])
                    
                    avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
                    
                    # Calculate time spent (approximate based on progress updates)
                    total_time_spent = sum(e.time_spent or 0 for e in enrollments)
                    
                    # Count unique users
                    unique_users = len(set(e.user_id for e in enrollments))
                    
                    # Check if record exists
                    existing = self.db.query(CourseAnalytics).filter(
                        CourseAnalytics.course_id == course.id,
                        CourseAnalytics.company_id == company.id,
                        CourseAnalytics.date == target_date
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.enrollments_count = enrollments_count
                        existing.completions_count = completions_count
                        existing.avg_progress = Decimal(str(avg_progress))
                        existing.avg_score = Decimal(str(avg_score))
                        existing.total_time_spent = total_time_spent
                        existing.unique_users = unique_users
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new record
                        analytics = CourseAnalytics(
                            course_id=course.id,
                            company_id=company.id,
                            date=target_date,
                            enrollments_count=enrollments_count,
                            completions_count=completions_count,
                            avg_progress=Decimal(str(avg_progress)),
                            avg_score=Decimal(str(avg_score)),
                            total_time_spent=total_time_spent,
                            unique_users=unique_users
                        )
                        self.db.add(analytics)
            
            self.db.commit()
            logger.info("Course analytics collected successfully")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error collecting course analytics: {str(e)}")
            raise
    
    async def collect_user_engagement(self, target_date: date):
        """Collect user engagement metrics for the target date."""
        try:
            # Get all active users
            users = self.db.query(User).filter(
                User.is_active == True,
                User.deleted_at.is_(None)
            ).all()
            
            for user in users:
                # Count logins for the day
                login_count = self.db.query(AnalyticsEvent).filter(
                    AnalyticsEvent.user_id == user.id,
                    AnalyticsEvent.event_type == 'auth',
                    AnalyticsEvent.event_action == 'login',
                    func.date(AnalyticsEvent.created_at) == target_date
                ).count()
                
                # Count page views
                page_views = self.db.query(AnalyticsEvent).filter(
                    AnalyticsEvent.user_id == user.id,
                    AnalyticsEvent.event_type == 'navigation',
                    AnalyticsEvent.event_action == 'page_view',
                    func.date(AnalyticsEvent.created_at) == target_date
                ).count()
                
                # Calculate time spent (based on session duration events)
                time_events = self.db.query(AnalyticsEvent).filter(
                    AnalyticsEvent.user_id == user.id,
                    AnalyticsEvent.event_type == 'session',
                    AnalyticsEvent.event_action == 'duration',
                    func.date(AnalyticsEvent.created_at) == target_date
                ).all()
                time_spent = sum(int(e.event_value or 0) for e in time_events)
                
                # Count courses started on this day
                courses_started = self.db.query(CourseEnrollment).filter(
                    CourseEnrollment.user_id == user.id,
                    func.date(CourseEnrollment.created_at) == target_date
                ).count()
                
                # Count courses completed on this day
                courses_completed = self.db.query(CourseEnrollment).filter(
                    CourseEnrollment.user_id == user.id,
                    func.date(CourseEnrollment.completed_at) == target_date
                ).count()
                
                # Count quizzes taken
                quizzes_taken = self.db.query(QuizAttempt).filter(
                    QuizAttempt.user_id == user.id,
                    func.date(QuizAttempt.started_at) == target_date
                ).count()
                
                # Calculate average quiz score for the day
                quiz_scores = self.db.query(QuizAttempt.score).filter(
                    QuizAttempt.user_id == user.id,
                    func.date(QuizAttempt.completed_at) == target_date,
                    QuizAttempt.score.isnot(None)
                ).all()
                avg_quiz_score = sum(s[0] for s in quiz_scores) / len(quiz_scores) if quiz_scores else None
                
                # Count phishing attempts and reports
                phishing_attempts = self.db.query(PhishingResult).filter(
                    PhishingResult.user_id == user.id,
                    func.date(PhishingResult.sent_at) == target_date
                ).count()
                
                phishing_reported = self.db.query(PhishingResult).filter(
                    PhishingResult.user_id == user.id,
                    PhishingResult.reported == True,
                    func.date(PhishingResult.reported_at) == target_date
                ).count()
                
                # Check if record exists
                existing = self.db.query(UserEngagement).filter(
                    UserEngagement.user_id == user.id,
                    UserEngagement.date == target_date
                ).first()
                
                if existing:
                    # Update existing record
                    existing.login_count = login_count
                    existing.page_views = page_views
                    existing.time_spent = time_spent
                    existing.courses_started = courses_started
                    existing.courses_completed = courses_completed
                    existing.quizzes_taken = quizzes_taken
                    existing.avg_quiz_score = Decimal(str(avg_quiz_score)) if avg_quiz_score else None
                    existing.phishing_attempts = phishing_attempts
                    existing.phishing_reported = phishing_reported
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    engagement = UserEngagement(
                        user_id=user.id,
                        company_id=user.company_id,
                        date=target_date,
                        login_count=login_count,
                        page_views=page_views,
                        time_spent=time_spent,
                        courses_started=courses_started,
                        courses_completed=courses_completed,
                        quizzes_taken=quizzes_taken,
                        avg_quiz_score=Decimal(str(avg_quiz_score)) if avg_quiz_score else None,
                        phishing_attempts=phishing_attempts,
                        phishing_reported=phishing_reported
                    )
                    self.db.add(engagement)
            
            self.db.commit()
            logger.info("User engagement metrics collected successfully")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error collecting user engagement: {str(e)}")
            raise
    
    async def collect_revenue_analytics(self, target_date: date):
        """Collect revenue analytics for the target date."""
        try:
            # Get all companies
            companies = self.db.query(Company).filter(Company.deleted_at.is_(None)).all()
            
            for company in companies:
                # Get payments for the day
                payments = self.db.query(Payment).filter(
                    Payment.company_id == company.id,
                    func.date(Payment.created_at) == target_date,
                    Payment.status == 'completed'
                ).all()
                
                # Calculate revenue
                subscription_revenue = sum(
                    p.amount for p in payments 
                    if p.subscription_id is not None
                )
                one_time_revenue = sum(
                    p.amount for p in payments 
                    if p.subscription_id is None
                )
                total_revenue = subscription_revenue + one_time_revenue
                
                # Count new subscriptions
                new_subscriptions = self.db.query(Subscription).filter(
                    Subscription.company_id == company.id,
                    func.date(Subscription.created_at) == target_date
                ).count()
                
                # Count cancelled subscriptions
                cancelled_subscriptions = self.db.query(Subscription).filter(
                    Subscription.company_id == company.id,
                    func.date(Subscription.cancelled_at) == target_date
                ).count()
                
                # Count active subscriptions
                active_subscriptions = self.db.query(Subscription).filter(
                    Subscription.company_id == company.id,
                    Subscription.status == 'active',
                    Subscription.created_at <= target_date + timedelta(days=1)
                ).count()
                
                # Calculate MRR (Monthly Recurring Revenue)
                active_subs = self.db.query(Subscription).filter(
                    Subscription.company_id == company.id,
                    Subscription.status == 'active'
                ).all()
                
                mrr = sum(
                    s.amount if s.billing_interval == 'monthly' 
                    else s.amount / 12 if s.billing_interval == 'yearly'
                    else 0
                    for s in active_subs
                )
                
                # Calculate ARR (Annual Recurring Revenue)
                arr = mrr * 12
                
                # Check if record exists
                existing = self.db.query(RevenueAnalytics).filter(
                    RevenueAnalytics.company_id == company.id,
                    RevenueAnalytics.date == target_date
                ).first()
                
                if existing:
                    # Update existing record
                    existing.subscription_revenue = Decimal(str(subscription_revenue))
                    existing.one_time_revenue = Decimal(str(one_time_revenue))
                    existing.total_revenue = Decimal(str(total_revenue))
                    existing.new_subscriptions = new_subscriptions
                    existing.cancelled_subscriptions = cancelled_subscriptions
                    existing.active_subscriptions = active_subscriptions
                    existing.mrr = Decimal(str(mrr))
                    existing.arr = Decimal(str(arr))
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    analytics = RevenueAnalytics(
                        company_id=company.id,
                        date=target_date,
                        subscription_revenue=Decimal(str(subscription_revenue)),
                        one_time_revenue=Decimal(str(one_time_revenue)),
                        total_revenue=Decimal(str(total_revenue)),
                        new_subscriptions=new_subscriptions,
                        cancelled_subscriptions=cancelled_subscriptions,
                        active_subscriptions=active_subscriptions,
                        mrr=Decimal(str(mrr)),
                        arr=Decimal(str(arr)),
                        currency='EUR'
                    )
                    self.db.add(analytics)
            
            self.db.commit()
            logger.info("Revenue analytics collected successfully")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error collecting revenue analytics: {str(e)}")
            raise
    
    async def collect_phishing_analytics(self, target_date: date):
        """Collect phishing simulation analytics for the target date."""
        try:
            # Get all campaigns that were active on the target date
            campaigns = self.db.query(PhishingCampaign).filter(
                PhishingCampaign.started_at <= target_date + timedelta(days=1),
                or_(
                    PhishingCampaign.completed_at.is_(None),
                    PhishingCampaign.completed_at >= target_date
                )
            ).all()
            
            for campaign in campaigns:
                # Get results for this campaign and date
                results = self.db.query(PhishingResult).filter(
                    PhishingResult.campaign_id == campaign.id,
                    func.date(PhishingResult.sent_at) == target_date
                ).all()
                
                if not results:
                    continue
                
                # Calculate metrics
                emails_sent = len(results)
                emails_opened = sum(1 for r in results if r.opened_at is not None)
                links_clicked = sum(1 for r in results if r.clicked_at is not None)
                credentials_entered = sum(1 for r in results if r.submitted_data is not None)
                reported_suspicious = sum(1 for r in results if r.reported)
                
                # Calculate rates
                open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
                click_rate = (links_clicked / emails_sent * 100) if emails_sent > 0 else 0
                report_rate = (reported_suspicious / emails_sent * 100) if emails_sent > 0 else 0
                
                # Check if record exists
                existing = self.db.query(PhishingAnalytics).filter(
                    PhishingAnalytics.company_id == campaign.company_id,
                    PhishingAnalytics.campaign_id == campaign.id,
                    PhishingAnalytics.date == target_date
                ).first()
                
                if existing:
                    # Update existing record
                    existing.emails_sent = emails_sent
                    existing.emails_opened = emails_opened
                    existing.links_clicked = links_clicked
                    existing.credentials_entered = credentials_entered
                    existing.reported_suspicious = reported_suspicious
                    existing.open_rate = Decimal(str(open_rate))
                    existing.click_rate = Decimal(str(click_rate))
                    existing.report_rate = Decimal(str(report_rate))
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    analytics = PhishingAnalytics(
                        company_id=campaign.company_id,
                        campaign_id=campaign.id,
                        date=target_date,
                        emails_sent=emails_sent,
                        emails_opened=emails_opened,
                        links_clicked=links_clicked,
                        credentials_entered=credentials_entered,
                        reported_suspicious=reported_suspicious,
                        open_rate=Decimal(str(open_rate)),
                        click_rate=Decimal(str(click_rate)),
                        report_rate=Decimal(str(report_rate))
                    )
                    self.db.add(analytics)
            
            self.db.commit()
            logger.info("Phishing analytics collected successfully")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error collecting phishing analytics: {str(e)}")
            raise
    
    async def update_realtime_metrics(self):
        """Update real-time metrics for dashboards."""
        try:
            # Clear old metrics (beyond TTL)
            self.db.query(RealtimeMetric).filter(
                RealtimeMetric.timestamp < datetime.utcnow() - timedelta(hours=1)
            ).delete()
            
            # Update global metrics
            total_users = self.db.query(func.count(User.id)).filter(
                User.is_active == True,
                User.deleted_at.is_(None)
            ).scalar()
            
            self._update_metric("total_users", total_users, "gauge")
            
            # Active users (last 24 hours)
            active_users = self.db.query(func.count(distinct(User.id))).filter(
                User.last_login_at >= datetime.utcnow() - timedelta(days=1)
            ).scalar()
            
            self._update_metric("active_users_24h", active_users, "gauge")
            
            # Total courses
            total_courses = self.db.query(func.count(Course.id)).filter(
                Course.status == 'published'
            ).scalar()
            
            self._update_metric("total_courses", total_courses, "gauge")
            
            # Total enrollments
            total_enrollments = self.db.query(func.count(CourseEnrollment.id)).scalar()
            self._update_metric("total_enrollments", total_enrollments, "counter")
            
            # Completion rate
            completed_enrollments = self.db.query(func.count(CourseEnrollment.id)).filter(
                CourseEnrollment.completed_at.isnot(None)
            ).scalar()
            
            completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
            self._update_metric("completion_rate", completion_rate, "percentage")
            
            self.db.commit()
            logger.info("Real-time metrics updated successfully")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating real-time metrics: {str(e)}")
            raise
    
    def _update_metric(self, name: str, value: float, metric_type: str, 
                      company_id: Optional[UUID] = None, 
                      dimension: Optional[str] = None,
                      dimension_value: Optional[str] = None):
        """Update or create a real-time metric."""
        metric = RealtimeMetric(
            metric_name=name,
            metric_value=Decimal(str(value)),
            metric_type=metric_type,
            company_id=company_id,
            dimension=dimension,
            dimension_value=dimension_value,
            timestamp=datetime.utcnow(),
            ttl=3600  # 1 hour TTL
        )
        self.db.add(metric)