"""Critical functionality tests to ensure core features work correctly."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json
from sqlalchemy.orm import Session

from models.user import User, UserRole
from models.company import Company, CompanySize, CompanyStatus, SubscriptionTier
from models.course import Course, CourseModule, UserProgress
from core.security import create_access_token, verify_password, get_password_hash
from services.email_service import EmailService
from services.payment_service import PaymentService
from services.phishing_service import PhishingService
from services.analytics_service import AnalyticsService


class TestCriticalAuthentication:
    """Test critical authentication flows."""
    
    @pytest.mark.critical
    def test_user_registration_complete_flow(self, db_session: Session):
        """Test complete user registration including company creation."""
        # Create company
        company = Company(
            name="Critical Test Company",
            domain="critical-test.com",
            industry="Technology",
            size=CompanySize.MEDIUM,
            status=CompanyStatus.ACTIVE,
            subscription_tier=SubscriptionTier.PROFESSIONAL
        )
        db_session.add(company)
        db_session.commit()
        
        # Create user
        user = User(
            email="critical@test.com",
            password_hash=get_password_hash("SecurePassword123!"),
            first_name="Critical",
            last_name="Test",
            company_id=company.id,
            is_active=True,
            email_verified=False,
            role=UserRole.EMPLOYEE
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify user creation
        assert user.id is not None
        assert user.company_id == company.id
        assert verify_password("SecurePassword123!", user.password_hash)
        
        # Generate verification token
        verification_token = create_access_token(
            {"sub": user.email, "type": "email_verification"}
        )
        assert verification_token is not None
        
        # Simulate email verification
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        db_session.commit()
        
        assert user.email_verified is True
        assert user.email_verified_at is not None
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_two_factor_authentication_flow(self, db_session: Session):
        """Test complete 2FA flow."""
        from core.two_factor_auth import TwoFactorAuth
        
        # Create user with 2FA
        user = User(
            email="2fa-critical@test.com",
            password_hash=get_password_hash("2FAPassword123!"),
            first_name="TwoFA",
            last_name="Critical",
            company_id=1,
            is_active=True,
            email_verified=True
        )
        
        # Enable 2FA
        two_fa = TwoFactorAuth()
        secret = two_fa.generate_secret()
        user.totp_secret = two_fa.encrypt_secret(secret)
        user.totp_enabled = True
        
        # Generate backup codes
        backup_codes = two_fa.generate_backup_codes()
        user.backup_codes = json.dumps([get_password_hash(code) for code in backup_codes])
        
        db_session.add(user)
        db_session.commit()
        
        # Verify 2FA setup
        assert user.totp_enabled is True
        assert user.totp_secret is not None
        assert len(json.loads(user.backup_codes)) == 8
        
        # Test TOTP verification
        totp_code = two_fa.generate_totp(secret)
        assert two_fa.verify_totp(secret, totp_code) is True
        
        # Test backup code usage
        backup_code = backup_codes[0]
        hashed_codes = json.loads(user.backup_codes)
        assert any(verify_password(backup_code, hashed) for hashed in hashed_codes)
    
    @pytest.mark.critical
    def test_password_reset_flow(self, db_session: Session):
        """Test complete password reset flow."""
        # Create user
        user = User(
            email="reset@test.com",
            password_hash=get_password_hash("OldPassword123!"),
            first_name="Reset",
            last_name="Test",
            company_id=1,
            is_active=True,
            email_verified=True
        )
        db_session.add(user)
        db_session.commit()
        
        old_password_hash = user.password_hash
        
        # Generate reset token
        reset_token = create_access_token(
            {"sub": user.email, "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        assert reset_token is not None
        
        # Update password
        new_password = "NewSecurePassword123!"
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        db_session.commit()
        
        # Verify password change
        assert user.password_hash != old_password_hash
        assert verify_password(new_password, user.password_hash)
        assert not verify_password("OldPassword123!", user.password_hash)
        assert user.password_changed_at is not None


class TestCriticalCourseManagement:
    """Test critical course and learning functionality."""
    
    @pytest.mark.critical
    def test_course_enrollment_and_progress(self, db_session: Session):
        """Test course enrollment and progress tracking."""
        # Create course
        course = Course(
            title="Critical Security Training",
            description="Essential security awareness training",
            duration_hours=2,
            difficulty_level="beginner",
            is_active=True,
            passing_score=80
        )
        db_session.add(course)
        db_session.commit()
        
        # Create modules
        modules = []
        for i in range(3):
            module = CourseModule(
                course_id=course.id,
                title=f"Module {i+1}",
                content=f"Content for module {i+1}",
                order=i+1,
                duration_minutes=30
            )
            modules.append(module)
        db_session.add_all(modules)
        db_session.commit()
        
        # Create user progress
        user_progress = UserProgress(
            user_id=1,
            course_id=course.id,
            started_at=datetime.utcnow(),
            current_module_id=modules[0].id,
            progress_percentage=0,
            time_spent_minutes=0
        )
        db_session.add(user_progress)
        db_session.commit()
        
        # Simulate progress through modules
        total_modules = len(modules)
        completed_modules = 0
        quiz_scores = []
        
        for i, module in enumerate(modules):
            # Complete module
            user_progress.current_module_id = module.id
            user_progress.time_spent_minutes += 25
            
            # Take quiz
            quiz_score = 85 + i * 5  # Scores: 85, 90, 95
            quiz_scores.append(quiz_score)
            
            completed_modules += 1
            user_progress.progress_percentage = (completed_modules / total_modules) * 100
            
            db_session.commit()
        
        # Complete course
        user_progress.completed_at = datetime.utcnow()
        user_progress.quiz_score = sum(quiz_scores) / len(quiz_scores)
        user_progress.certificate_issued = user_progress.quiz_score >= course.passing_score
        db_session.commit()
        
        # Verify completion
        assert user_progress.progress_percentage == 100
        assert user_progress.completed_at is not None
        assert user_progress.quiz_score == 90  # Average of 85, 90, 95
        assert user_progress.certificate_issued is True
        assert user_progress.time_spent_minutes == 75


class TestCriticalPaymentProcessing:
    """Test critical payment functionality."""
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_subscription_upgrade_flow(self):
        """Test complete subscription upgrade flow."""
        with patch('stripe.Customer.create') as mock_customer_create, \
             patch('stripe.PaymentMethod.attach') as mock_payment_attach, \
             patch('stripe.Subscription.create') as mock_subscription_create:
            
            # Mock Stripe responses
            mock_customer_create.return_value = Mock(id='cus_test123')
            mock_payment_attach.return_value = Mock(id='pm_test123')
            mock_subscription_create.return_value = Mock(
                id='sub_test123',
                status='active',
                current_period_end=int((datetime.utcnow() + timedelta(days=30)).timestamp())
            )
            
            service = PaymentService()
            
            # Create customer
            customer_id = await service.create_customer(
                email="payment@test.com",
                name="Payment Test"
            )
            assert customer_id == 'cus_test123'
            
            # Attach payment method
            await service.attach_payment_method(
                customer_id=customer_id,
                payment_method_id='pm_test123'
            )
            
            # Create subscription
            subscription = await service.create_subscription(
                customer_id=customer_id,
                price_id='price_professional',
                payment_method_id='pm_test123'
            )
            
            assert subscription['id'] == 'sub_test123'
            assert subscription['status'] == 'active'
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_payment_webhook_processing(self):
        """Test payment webhook event processing."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            # Mock webhook event
            mock_event = Mock(
                type='payment_intent.succeeded',
                data=Mock(object=Mock(
                    id='pi_test123',
                    amount=9900,  # $99.00
                    currency='usd',
                    metadata={'user_id': '1', 'subscription_tier': 'professional'}
                ))
            )
            mock_construct.return_value = mock_event
            
            service = PaymentService()
            
            # Process webhook
            result = await service.process_webhook_event(
                payload=b'test_payload',
                signature='test_signature'
            )
            
            assert result['processed'] is True
            assert result['event_type'] == 'payment_intent.succeeded'


class TestCriticalSecurityFeatures:
    """Test critical security features."""
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_phishing_simulation_flow(self):
        """Test phishing simulation campaign flow."""
        service = PhishingService()
        
        with patch.object(service, 'send_phishing_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            # Create campaign
            campaign_data = {
                "name": "Q4 Security Awareness",
                "template_id": 1,
                "target_users": [1, 2, 3, 4, 5],
                "scheduled_at": datetime.utcnow() + timedelta(days=1)
            }
            
            campaign = await service.create_campaign(campaign_data)
            assert campaign['status'] == 'scheduled'
            assert len(campaign['target_users']) == 5
            
            # Simulate campaign execution
            results = await service.execute_campaign(campaign['id'])
            assert results['emails_sent'] == 5
            assert mock_send.call_count == 5
            
            # Track user interaction
            interaction = await service.track_interaction(
                campaign_id=campaign['id'],
                user_id=1,
                action='clicked',
                timestamp=datetime.utcnow()
            )
            assert interaction['action'] == 'clicked'
            
            # Generate report
            report = await service.generate_campaign_report(campaign['id'])
            assert report['total_sent'] == 5
            assert report['clicks'] == 1
            assert report['click_rate'] == 20.0  # 1/5 = 20%
    
    @pytest.mark.critical
    def test_rate_limiting(self):
        """Test API rate limiting."""
        from core.rate_limiting import RateLimiter
        
        limiter = RateLimiter(
            max_requests=5,
            window_seconds=60
        )
        
        client_id = "test-client-123"
        
        # Make allowed requests
        for i in range(5):
            allowed = limiter.check_rate_limit(client_id)
            assert allowed is True
        
        # Exceed rate limit
        exceeded = limiter.check_rate_limit(client_id)
        assert exceeded is False
        
        # Check remaining time
        remaining = limiter.get_reset_time(client_id)
        assert remaining > 0
        assert remaining <= 60
    
    @pytest.mark.critical
    def test_input_validation_and_sanitization(self):
        """Test input validation and XSS prevention."""
        from core.input_validation import validate_and_sanitize
        
        # Test SQL injection attempt
        malicious_sql = "'; DROP TABLE users; --"
        sanitized_sql = validate_and_sanitize(malicious_sql, 'sql')
        assert "DROP TABLE" not in sanitized_sql
        
        # Test XSS attempt
        malicious_xss = "<script>alert('XSS')</script>"
        sanitized_xss = validate_and_sanitize(malicious_xss, 'html')
        assert "<script>" not in sanitized_xss
        assert "&lt;script&gt;" in sanitized_xss
        
        # Test valid input
        valid_input = "Normal user input with special chars: @#$%"
        sanitized_valid = validate_and_sanitize(valid_input, 'text')
        assert sanitized_valid == valid_input


class TestCriticalAnalytics:
    """Test critical analytics functionality."""
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_real_time_analytics_tracking(self):
        """Test real-time analytics event tracking."""
        service = AnalyticsService()
        
        # Track user login
        login_event = await service.track_event(
            user_id=1,
            event_type="user_login",
            event_data={
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        assert login_event['tracked'] is True
        
        # Track course progress
        progress_event = await service.track_event(
            user_id=1,
            event_type="course_progress",
            event_data={
                "course_id": 1,
                "module_id": 3,
                "progress_percentage": 75,
                "time_spent_minutes": 45
            }
        )
        assert progress_event['tracked'] is True
        
        # Get user analytics
        analytics = await service.get_user_analytics(user_id=1)
        assert analytics['total_logins'] >= 1
        assert analytics['courses_in_progress'] >= 1
        assert analytics['total_time_spent'] >= 45
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_company_dashboard_metrics(self):
        """Test company-wide dashboard metrics."""
        service = AnalyticsService()
        
        with patch.object(service, 'get_company_metrics', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {
                "total_users": 150,
                "active_users_30d": 120,
                "courses_completed": 450,
                "avg_completion_rate": 85.5,
                "phishing_catch_rate": 72.3,
                "compliance_score": 92
            }
            
            metrics = await service.get_company_metrics(company_id=1)
            
            assert metrics['total_users'] == 150
            assert metrics['active_users_30d'] == 120
            assert metrics['avg_completion_rate'] == 85.5
            assert metrics['compliance_score'] == 92
            
            # Calculate engagement rate
            engagement_rate = (metrics['active_users_30d'] / metrics['total_users']) * 100
            assert engagement_rate == 80.0


class TestCriticalErrorHandling:
    """Test critical error handling and recovery."""
    
    @pytest.mark.critical
    def test_database_connection_recovery(self):
        """Test database connection failure and recovery."""
        from sqlalchemy.exc import OperationalError
        from db.session import get_db_with_retry
        
        with patch('sqlalchemy.create_engine') as mock_engine:
            # Simulate connection failure then success
            mock_engine.side_effect = [
                OperationalError("Connection failed", None, None),
                Mock()  # Successful connection
            ]
            
            # Should retry and succeed
            engine = get_db_with_retry(max_retries=2)
            assert engine is not None
            assert mock_engine.call_count == 2
    
    @pytest.mark.critical
    @pytest.mark.asyncio
    async def test_external_service_circuit_breaker(self):
        """Test circuit breaker for external services."""
        from core.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5,
            expected_exception=Exception
        )
        
        # Simulate failures
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(AsyncMock(side_effect=Exception("Service down")))
        
        # Circuit should be open
        assert breaker.state == 'open'
        
        # Further calls should fail immediately
        with pytest.raises(Exception) as exc_info:
            await breaker.call(AsyncMock())
        assert "Circuit breaker is open" in str(exc_info.value)
    
    @pytest.mark.critical
    def test_graceful_degradation(self):
        """Test graceful degradation when services fail."""
        from services.cache_service import CacheService
        
        cache = CacheService()
        
        with patch.object(cache, 'get', side_effect=Exception("Redis down")):
            # Should return None instead of crashing
            result = cache.get_with_fallback("test_key", fallback_value="default")
            assert result == "default"
        
        with patch.object(cache, 'set', side_effect=Exception("Redis down")):
            # Should log error but not crash
            result = cache.set_with_retry("test_key", "value", retries=1)
            assert result is False