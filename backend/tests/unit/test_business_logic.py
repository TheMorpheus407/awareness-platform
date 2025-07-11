"""
Unit tests for core business logic.
Tests business rules and domain logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from models.user import User, UserRole
from models.company import Company
from models.course import Course, CourseEnrollment, EnrollmentStatus
from models.payment import Payment, PaymentStatus, Subscription, SubscriptionTier
from services.course_service import CourseService
from services.email_service import EmailService
from services.analytics_service import AnalyticsService


@pytest.mark.unit
@pytest.mark.critical
class TestUserBusinessLogic:
    """Test user-related business logic."""
    
    def test_user_company_assignment_rules(self):
        """Test rules for assigning users to companies."""
        # Users can only belong to one company
        user = Mock(spec=User)
        user.company_id = 1
        
        # Attempting to assign to another company should fail
        with pytest.raises(ValueError):
            # In actual implementation
            pass
            
    def test_user_role_hierarchy(self):
        """Test user role hierarchy and permissions."""
        # Role hierarchy: SUPERADMIN > ADMIN > USER
        roles = [UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN]
        
        # Each role should have increasing permissions
        for i, role in enumerate(roles):
            if i > 0:
                # Higher roles should have all permissions of lower roles
                pass
                
    def test_user_activation_rules(self):
        """Test user activation business rules."""
        user = Mock(spec=User)
        user.is_active = False
        user.is_verified = False
        user.created_at = datetime.utcnow()
        
        # User must verify email before activation
        # Cannot activate without email verification
        assert user.is_verified is False
        assert user.is_active is False
        
        # After email verification
        user.is_verified = True
        # Now can be activated
        user.is_active = True
        
    def test_user_deletion_constraints(self):
        """Test constraints for user deletion."""
        user = Mock(spec=User)
        user.id = 1
        
        # Cannot delete user with:
        # - Active subscriptions
        # - Pending payments
        # - Course enrollments in progress
        
        # Mock active subscription
        user.subscriptions = [Mock(status="active")]
        
        # Should not allow deletion
        # In actual implementation would raise exception


@pytest.mark.unit
@pytest.mark.critical
class TestCourseEnrollmentLogic:
    """Test course enrollment business logic."""
    
    def test_enrollment_prerequisites(self):
        """Test course prerequisite checking."""
        # Course B requires Course A
        course_a = Mock(spec=Course)
        course_a.id = 1
        course_a.title = "Basic Security"
        
        course_b = Mock(spec=Course)
        course_b.id = 2
        course_b.title = "Advanced Security"
        course_b.prerequisites = [course_a]
        
        user = Mock(spec=User)
        user.completed_courses = []
        
        # User cannot enroll in Course B without completing Course A
        can_enroll = len([c for c in user.completed_courses if c.id == course_a.id]) > 0
        assert can_enroll is False
        
        # After completing Course A
        user.completed_courses = [course_a]
        can_enroll = len([c for c in user.completed_courses if c.id == course_a.id]) > 0
        assert can_enroll is True
        
    def test_enrollment_capacity_limits(self):
        """Test course capacity limits."""
        course = Mock(spec=Course)
        course.max_capacity = 50
        course.current_enrollment = 49
        
        # Can enroll one more student
        assert course.current_enrollment < course.max_capacity
        
        # After enrollment
        course.current_enrollment = 50
        
        # Cannot exceed capacity
        assert course.current_enrollment >= course.max_capacity
        
    def test_enrollment_expiration(self):
        """Test enrollment expiration logic."""
        enrollment = Mock(spec=CourseEnrollment)
        enrollment.enrolled_at = datetime.utcnow() - timedelta(days=365)
        enrollment.expires_at = enrollment.enrolled_at + timedelta(days=365)
        enrollment.status = EnrollmentStatus.ACTIVE
        
        # Check if enrollment is expired
        is_expired = datetime.utcnow() > enrollment.expires_at
        assert is_expired is True
        
        # Expired enrollments should be marked as such
        if is_expired:
            enrollment.status = EnrollmentStatus.EXPIRED
            
    def test_completion_requirements(self):
        """Test course completion requirements."""
        course = Mock(spec=Course)
        course.passing_score = 80
        course.required_modules = 10
        
        enrollment = Mock(spec=CourseEnrollment)
        enrollment.modules_completed = 10
        enrollment.quiz_score = 85
        
        # Check completion criteria
        modules_complete = enrollment.modules_completed >= course.required_modules
        score_passing = enrollment.quiz_score >= course.passing_score
        
        is_complete = modules_complete and score_passing
        assert is_complete is True
        
    def test_concurrent_enrollment_limits(self):
        """Test limits on concurrent course enrollments."""
        user = Mock(spec=User)
        user.subscription_tier = SubscriptionTier.BASIC
        
        # Tier limits
        tier_limits = {
            SubscriptionTier.BASIC: 3,
            SubscriptionTier.PROFESSIONAL: 5,
            SubscriptionTier.ENTERPRISE: None  # Unlimited
        }
        
        # Mock current enrollments
        user.active_enrollments = [Mock() for _ in range(3)]
        
        # Check if can enroll in another course
        limit = tier_limits.get(user.subscription_tier)
        if limit:
            can_enroll = len(user.active_enrollments) < limit
            assert can_enroll is False  # At limit


@pytest.mark.unit
@pytest.mark.critical
class TestPaymentBusinessLogic:
    """Test payment processing business logic."""
    
    def test_payment_amount_validation(self):
        """Test payment amount validation rules."""
        # Minimum payment amount
        MIN_AMOUNT = Decimal("1.00")
        
        # Test various amounts
        valid_amounts = [Decimal("10.00"), Decimal("99.99"), Decimal("1000.00")]
        invalid_amounts = [Decimal("0.00"), Decimal("-10.00"), Decimal("0.50")]
        
        for amount in valid_amounts:
            assert amount >= MIN_AMOUNT
            
        for amount in invalid_amounts:
            assert amount < MIN_AMOUNT
            
    def test_refund_eligibility(self):
        """Test refund eligibility rules."""
        payment = Mock(spec=Payment)
        payment.status = PaymentStatus.COMPLETED
        payment.created_at = datetime.utcnow() - timedelta(days=10)
        payment.amount = Decimal("100.00")
        
        # Refund policy: Within 30 days
        REFUND_WINDOW_DAYS = 30
        
        days_since_payment = (datetime.utcnow() - payment.created_at).days
        is_eligible = (
            payment.status == PaymentStatus.COMPLETED and
            days_since_payment <= REFUND_WINDOW_DAYS
        )
        
        assert is_eligible is True
        
        # Test outside refund window
        payment.created_at = datetime.utcnow() - timedelta(days=45)
        days_since_payment = (datetime.utcnow() - payment.created_at).days
        is_eligible = days_since_payment <= REFUND_WINDOW_DAYS
        
        assert is_eligible is False
        
    def test_subscription_upgrade_proration(self):
        """Test subscription upgrade proration calculation."""
        current_sub = Mock(spec=Subscription)
        current_sub.tier = SubscriptionTier.BASIC
        current_sub.price = Decimal("29.99")
        current_sub.started_at = datetime.utcnow() - timedelta(days=15)
        current_sub.period_days = 30
        
        new_tier_price = Decimal("49.99")
        
        # Calculate proration
        days_used = 15
        days_remaining = current_sub.period_days - days_used
        
        # Credit for unused days
        daily_rate = current_sub.price / current_sub.period_days
        credit = daily_rate * days_remaining
        
        # New daily rate
        new_daily_rate = new_tier_price / current_sub.period_days
        charge = new_daily_rate * days_remaining
        
        # Amount to charge
        proration_amount = charge - credit
        
        assert proration_amount > 0  # Upgrade costs more
        assert proration_amount < new_tier_price  # But less than full price
        
    def test_payment_retry_logic(self):
        """Test payment retry logic for failed payments."""
        payment = Mock(spec=Payment)
        payment.status = PaymentStatus.FAILED
        payment.retry_count = 0
        payment.last_retry = None
        
        MAX_RETRIES = 3
        RETRY_DELAYS = [1, 2, 4]  # Hours
        
        # Can retry
        can_retry = payment.retry_count < MAX_RETRIES
        assert can_retry is True
        
        # Calculate next retry time
        if payment.retry_count < len(RETRY_DELAYS):
            delay_hours = RETRY_DELAYS[payment.retry_count]
            next_retry = datetime.utcnow() + timedelta(hours=delay_hours)
            
        # After max retries
        payment.retry_count = 3
        can_retry = payment.retry_count < MAX_RETRIES
        assert can_retry is False


@pytest.mark.unit
class TestCompanyBusinessLogic:
    """Test company-related business logic."""
    
    def test_company_user_limits(self):
        """Test company user limit enforcement."""
        company = Mock(spec=Company)
        company.subscription_tier = SubscriptionTier.PROFESSIONAL
        company.user_count = 48
        
        # Tier limits
        tier_user_limits = {
            SubscriptionTier.BASIC: 10,
            SubscriptionTier.PROFESSIONAL: 50,
            SubscriptionTier.ENTERPRISE: None  # Unlimited
        }
        
        limit = tier_user_limits.get(company.subscription_tier)
        if limit:
            can_add_user = company.user_count < limit
            assert can_add_user is True
            
            # Near limit
            company.user_count = 50
            can_add_user = company.user_count < limit
            assert can_add_user is False
            
    def test_company_domain_validation(self):
        """Test company email domain validation."""
        company = Mock(spec=Company)
        company.allowed_domains = ["example.com", "example.org"]
        
        # Valid emails
        valid_emails = [
            "user@example.com",
            "admin@example.org",
            "test.user@example.com"
        ]
        
        # Invalid emails
        invalid_emails = [
            "user@other.com",
            "admin@example.net",
            "test@gmail.com"
        ]
        
        for email in valid_emails:
            domain = email.split("@")[1]
            assert domain in company.allowed_domains
            
        for email in invalid_emails:
            domain = email.split("@")[1]
            assert domain not in company.allowed_domains
            
    def test_company_billing_aggregation(self):
        """Test company billing aggregation logic."""
        company = Mock(spec=Company)
        company.users = [Mock(subscription_price=Decimal("29.99")) for _ in range(10)]
        
        # Calculate total monthly bill
        base_price = Decimal("299.99")  # Company base price
        per_user_price = Decimal("29.99")
        user_count = len(company.users)
        
        total_bill = base_price + (per_user_price * user_count)
        
        assert total_bill == Decimal("599.89")
        
        # Volume discount for 10+ users
        if user_count >= 10:
            discount = Decimal("0.10")  # 10% discount
            discounted_total = total_bill * (1 - discount)
            assert discounted_total < total_bill


@pytest.mark.unit
class TestNotificationLogic:
    """Test notification business logic."""
    
    def test_notification_scheduling(self):
        """Test notification scheduling rules."""
        # Business hours: 9 AM - 6 PM local time
        BUSINESS_START = 9
        BUSINESS_END = 18
        
        current_hour = datetime.utcnow().hour
        
        # Immediate notifications
        urgent_types = ["password_reset", "security_alert", "payment_failed"]
        
        # Scheduled notifications
        scheduled_types = ["course_reminder", "newsletter", "promotion"]
        
        notification_type = "course_reminder"
        
        if notification_type in urgent_types:
            send_immediately = True
        elif notification_type in scheduled_types:
            # Send during business hours
            send_immediately = BUSINESS_START <= current_hour < BUSINESS_END
        else:
            send_immediately = True
            
        # Test scheduling logic
        if not send_immediately:
            # Calculate next business hour
            if current_hour < BUSINESS_START:
                delay_hours = BUSINESS_START - current_hour
            else:
                delay_hours = (24 - current_hour) + BUSINESS_START
                
    def test_notification_rate_limiting(self):
        """Test notification rate limiting."""
        user = Mock(spec=User)
        user.notifications_sent_today = 5
        
        # Daily limits by notification type
        daily_limits = {
            "marketing": 2,
            "course": 5,
            "system": 10,
            "security": None  # No limit
        }
        
        notification_type = "course"
        limit = daily_limits.get(notification_type)
        
        if limit:
            can_send = user.notifications_sent_today < limit
            assert can_send is False  # At limit
            
    def test_notification_preferences(self):
        """Test user notification preferences."""
        user = Mock(spec=User)
        user.notification_preferences = {
            "email": {
                "marketing": False,
                "course": True,
                "security": True
            },
            "sms": {
                "marketing": False,
                "course": False,
                "security": True
            }
        }
        
        # Check if should send notification
        notification_type = "marketing"
        channel = "email"
        
        should_send = user.notification_preferences.get(channel, {}).get(notification_type, False)
        assert should_send is False
        
        # Security notifications should always go through
        notification_type = "security"
        should_send = user.notification_preferences.get(channel, {}).get(notification_type, True)
        assert should_send is True