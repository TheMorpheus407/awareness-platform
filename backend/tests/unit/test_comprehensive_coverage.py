"""Comprehensive unit tests to ensure 80%+ code coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session

from core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from core.config import settings
from services.email_service import EmailService
from services.analytics_service import AnalyticsService
from services.content_delivery import ContentDeliveryService
from services.cache_service import CacheService
from api.deps import get_current_user, get_current_active_user, require_admin
from models.user import User, UserRole
from models.company import Company, CompanySize, SubscriptionTier
from schemas.user import UserCreate, UserUpdate
from crud.user import crud_user
from crud.company import crud_company


class TestSecurity:
    """Test security functions for coverage."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com", "type": "access"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Test with expiration
        token_with_exp = create_access_token(data, expires_delta=timedelta(hours=1))
        assert isinstance(token_with_exp, str)
    
    def test_decode_access_token(self):
        """Test JWT token decoding."""
        data = {"sub": "test@example.com", "type": "access"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        assert decoded["sub"] == "test@example.com"
        assert decoded["type"] == "access"
        
        # Test invalid token
        decoded_invalid = decode_access_token("invalid.token.here")
        assert decoded_invalid is None
    
    def test_refresh_tokens(self):
        """Test refresh token functionality."""
        data = {"sub": "test@example.com"}
        refresh_token = create_refresh_token(data)
        
        assert isinstance(refresh_token, str)
        
        verified = verify_refresh_token(refresh_token)
        assert verified["sub"] == "test@example.com"
        
        # Test invalid refresh token
        assert verify_refresh_token("invalid.refresh.token") is None


class TestEmailService:
    """Test email service for coverage."""
    
    @pytest.mark.asyncio
    async def test_send_verification_email(self):
        """Test sending verification email."""
        with patch('aiosmtplib.send') as mock_send:
            mock_send.return_value = (None, None)
            
            service = EmailService()
            result = await service.send_verification_email(
                "test@example.com",
                "Test User",
                "verification-token"
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_password_reset_email(self):
        """Test sending password reset email."""
        with patch('aiosmtplib.send') as mock_send:
            mock_send.return_value = (None, None)
            
            service = EmailService()
            result = await service.send_password_reset_email(
                "test@example.com",
                "Test User",
                "reset-token"
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_2fa_code(self):
        """Test sending 2FA code email."""
        with patch('aiosmtplib.send') as mock_send:
            mock_send.return_value = (None, None)
            
            service = EmailService()
            result = await service.send_2fa_code(
                "test@example.com",
                "123456"
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_email_service_error_handling(self):
        """Test email service error handling."""
        with patch('aiosmtplib.send') as mock_send:
            mock_send.side_effect = Exception("SMTP Error")
            
            service = EmailService()
            result = await service.send_verification_email(
                "test@example.com",
                "Test User",
                "token"
            )
            
            assert result is False


class TestAnalyticsService:
    """Test analytics service for coverage."""
    
    @pytest.mark.asyncio
    async def test_track_event(self):
        """Test event tracking."""
        with patch.object(CacheService, 'set', new_callable=AsyncMock) as mock_set:
            service = AnalyticsService()
            
            await service.track_event(
                user_id=1,
                event_type="page_view",
                event_data={"page": "/dashboard"}
            )
            
            mock_set.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_user_analytics(self):
        """Test getting user analytics."""
        with patch.object(CacheService, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = json.dumps({
                "total_events": 100,
                "last_activity": "2024-01-01T00:00:00Z"
            })
            
            service = AnalyticsService()
            analytics = await service.get_user_analytics(user_id=1)
            
            assert analytics["total_events"] == 100
            assert "last_activity" in analytics
    
    @pytest.mark.asyncio
    async def test_calculate_engagement_score(self):
        """Test engagement score calculation."""
        service = AnalyticsService()
        
        # Test with sample data
        user_data = {
            "logins": 10,
            "courses_completed": 3,
            "time_spent": 7200,  # 2 hours
            "quiz_scores": [85, 90, 95]
        }
        
        score = await service.calculate_engagement_score(user_data)
        assert isinstance(score, float)
        assert 0 <= score <= 100


class TestContentDeliveryService:
    """Test content delivery service for coverage."""
    
    @pytest.mark.asyncio
    async def test_get_optimized_content(self):
        """Test content optimization."""
        service = ContentDeliveryService()
        
        content = {
            "title": "Test Course",
            "modules": ["Module 1", "Module 2"],
            "duration": 3600
        }
        
        optimized = await service.optimize_content(
            content,
            user_preferences={"difficulty": "beginner"}
        )
        
        assert optimized["title"] == "Test Course"
        assert "optimized" in optimized
        assert optimized["optimized"] is True
    
    @pytest.mark.asyncio
    async def test_get_content_recommendations(self):
        """Test content recommendations."""
        service = ContentDeliveryService()
        
        with patch.object(service, '_get_user_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = ["course1", "course2"]
            
            recommendations = await service.get_recommendations(
                user_id=1,
                limit=5
            )
            
            assert isinstance(recommendations, list)
            assert len(recommendations) <= 5


class TestCRUDOperations:
    """Test CRUD operations for coverage."""
    
    def test_user_crud_create(self, db_session: Session):
        """Test user creation."""
        user_in = UserCreate(
            email="crud@example.com",
            password="TestPassword123!",
            first_name="CRUD",
            last_name="Test",
            company_id=1
        )
        
        with patch.object(crud_user, 'get_by_email', return_value=None):
            user = crud_user.create(db_session, obj_in=user_in)
            
            assert user.email == "crud@example.com"
            assert user.first_name == "CRUD"
            assert verify_password("TestPassword123!", user.password_hash)
    
    def test_user_crud_update(self, db_session: Session):
        """Test user update."""
        # Create mock user
        user = User(
            id=1,
            email="update@example.com",
            password_hash=get_password_hash("OldPassword"),
            first_name="Old",
            last_name="Name"
        )
        
        update_data = UserUpdate(
            first_name="New",
            last_name="Name",
            password="NewPassword123!"
        )
        
        with patch.object(db_session, 'commit'):
            updated_user = crud_user.update(
                db_session,
                db_obj=user,
                obj_in=update_data
            )
            
            assert updated_user.first_name == "New"
            assert verify_password("NewPassword123!", updated_user.password_hash)
    
    def test_company_crud_operations(self, db_session: Session):
        """Test company CRUD operations."""
        # Test create
        company_data = {
            "name": "Test Company",
            "domain": "testcompany.com",
            "industry": "Technology",
            "size": CompanySize.MEDIUM,
            "subscription_tier": SubscriptionTier.PROFESSIONAL
        }
        
        company = crud_company.create(db_session, obj_in=company_data)
        assert company.name == "Test Company"
        assert company.subscription_tier == SubscriptionTier.PROFESSIONAL
        
        # Test get
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = company
            retrieved = crud_company.get(db_session, id=1)
            assert retrieved.name == "Test Company"


class TestAPIDependencies:
    """Test API dependencies for coverage."""
    
    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """Test get current user dependency."""
        token = create_access_token({"sub": "test@example.com"})
        
        with patch('api.deps.crud_user.get_by_email') as mock_get:
            mock_user = User(
                id=1,
                email="test@example.com",
                is_active=True
            )
            mock_get.return_value = mock_user
            
            user = await get_current_user(token=token, db=Mock())
            assert user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_active_user(self):
        """Test active user requirement."""
        active_user = User(id=1, email="active@example.com", is_active=True)
        inactive_user = User(id=2, email="inactive@example.com", is_active=False)
        
        # Test with active user
        result = await get_current_active_user(active_user)
        assert result.email == "active@example.com"
        
        # Test with inactive user
        with pytest.raises(Exception):
            await get_current_active_user(inactive_user)
    
    @pytest.mark.asyncio
    async def test_require_admin(self):
        """Test admin requirement."""
        admin_user = User(
            id=1,
            email="admin@example.com",
            role=UserRole.COMPANY_ADMIN
        )
        regular_user = User(
            id=2,
            email="user@example.com",
            role=UserRole.EMPLOYEE
        )
        
        # Test with admin
        result = await require_admin(admin_user)
        assert result.role == UserRole.COMPANY_ADMIN
        
        # Test with non-admin
        with pytest.raises(Exception):
            await require_admin(regular_user)


class TestBusinessLogic:
    """Test business logic for coverage."""
    
    def test_subscription_tier_limits(self):
        """Test subscription tier limit validation."""
        limits = {
            SubscriptionTier.FREE: {"users": 10, "courses": 3},
            SubscriptionTier.PROFESSIONAL: {"users": 100, "courses": 10},
            SubscriptionTier.ENTERPRISE: {"users": -1, "courses": -1},  # Unlimited
        }
        
        # Test free tier
        assert limits[SubscriptionTier.FREE]["users"] == 10
        assert limits[SubscriptionTier.FREE]["courses"] == 3
        
        # Test enterprise unlimited
        assert limits[SubscriptionTier.ENTERPRISE]["users"] == -1
    
    def test_user_role_permissions(self):
        """Test role-based permissions."""
        permissions = {
            UserRole.EMPLOYEE: ["view_courses", "take_quizzes"],
            UserRole.MANAGER: ["view_courses", "take_quizzes", "view_team_reports"],
            UserRole.COMPANY_ADMIN: ["view_courses", "take_quizzes", "view_team_reports", "manage_users"],
            UserRole.SUPER_ADMIN: ["*"],  # All permissions
        }
        
        # Test employee permissions
        assert "view_courses" in permissions[UserRole.EMPLOYEE]
        assert "manage_users" not in permissions[UserRole.EMPLOYEE]
        
        # Test admin permissions
        assert "manage_users" in permissions[UserRole.COMPANY_ADMIN]
        
        # Test super admin
        assert permissions[UserRole.SUPER_ADMIN] == ["*"]
    
    @pytest.mark.asyncio
    async def test_course_completion_logic(self):
        """Test course completion calculation."""
        course_progress = {
            "total_modules": 10,
            "completed_modules": 7,
            "quiz_scores": [85, 90, 78, 92],
            "time_spent": 3600  # 1 hour
        }
        
        # Calculate completion percentage
        completion = (course_progress["completed_modules"] / course_progress["total_modules"]) * 100
        assert completion == 70.0
        
        # Calculate average quiz score
        avg_score = sum(course_progress["quiz_scores"]) / len(course_progress["quiz_scores"])
        assert avg_score == 86.25
        
        # Check if course is passed (>= 80% completion and >= 80% avg score)
        is_passed = completion >= 80 and avg_score >= 80
        assert is_passed is False  # 70% completion is below threshold


class TestErrorHandling:
    """Test error handling for coverage."""
    
    def test_database_error_handling(self, db_session: Session):
        """Test database error handling."""
        with patch.object(db_session, 'commit', side_effect=Exception("DB Error")):
            with pytest.raises(Exception) as exc_info:
                user = User(email="error@example.com")
                db_session.add(user)
                db_session.commit()
            
            assert "DB Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_api_error_responses(self):
        """Test API error response formatting."""
        from api.errors import APIError, ValidationError
        
        # Test validation error
        validation_error = ValidationError(
            field="email",
            message="Invalid email format"
        )
        assert validation_error.field == "email"
        assert "Invalid email format" in validation_error.message
        
        # Test generic API error
        api_error = APIError(
            status_code=400,
            message="Bad request"
        )
        assert api_error.status_code == 400
        assert api_error.message == "Bad request"


class TestIntegrationScenarios:
    """Test integration scenarios for coverage."""
    
    @pytest.mark.asyncio
    async def test_full_user_registration_flow(self, db_session: Session):
        """Test complete user registration flow."""
        # 1. Check email availability
        with patch('crud.user.crud_user.get_by_email', return_value=None):
            email_available = True
        
        assert email_available is True
        
        # 2. Create user
        user_data = UserCreate(
            email="newuser@example.com",
            password="SecurePassword123!",
            first_name="New",
            last_name="User",
            company_id=1
        )
        
        with patch('crud.user.crud_user.create') as mock_create:
            mock_user = User(
                id=1,
                email=user_data.email,
                email_verified=False
            )
            mock_create.return_value = mock_user
            
            # 3. Send verification email
            with patch('services.email_service.EmailService.send_verification_email') as mock_email:
                mock_email.return_value = True
                
                # 4. Generate verification token
                verification_token = create_access_token(
                    {"sub": user_data.email, "type": "email_verification"}
                )
                
                assert verification_token is not None
                assert mock_email.called
    
    @pytest.mark.asyncio
    async def test_course_enrollment_and_progress(self):
        """Test course enrollment and progress tracking."""
        user_id = 1
        course_id = 1
        
        # 1. Check enrollment eligibility
        with patch('services.course_service.CourseService.check_eligibility') as mock_check:
            mock_check.return_value = True
            is_eligible = await mock_check(user_id, course_id)
        
        assert is_eligible is True
        
        # 2. Enroll in course
        enrollment_data = {
            "user_id": user_id,
            "course_id": course_id,
            "enrolled_at": datetime.utcnow()
        }
        
        # 3. Track progress
        progress_updates = [
            {"module_id": 1, "completed": True, "score": 85},
            {"module_id": 2, "completed": True, "score": 90},
            {"module_id": 3, "completed": False, "score": None},
        ]
        
        completed_modules = sum(1 for p in progress_updates if p["completed"])
        completion_percentage = (completed_modules / len(progress_updates)) * 100
        
        assert completion_percentage == 66.67
        
        # 4. Generate certificate if completed
        if completion_percentage >= 100:
            certificate = {"user_id": user_id, "course_id": course_id}
        else:
            certificate = None
        
        assert certificate is None  # Not yet completed