# Testing Spezifikation - Cybersecurity Awareness Platform
**Version 1.0 | Umfassende Teststrategie**

## 1. Testing-Übersicht

### 1.1 Test-Pyramide
```
         /\
        /E2E\        5%  - End-to-End Tests
       /______\
      /        \
     /Integration\   25% - Integration Tests  
    /______________\
   /                \
  /   Unit Tests     \ 70% - Unit Tests
 /____________________\
```

### 1.2 Test-Coverage Ziele
- **Overall Coverage**: ≥ 80%
- **Critical Paths**: ≥ 95%
- **API Endpoints**: 100%
- **Security Functions**: 100%
- **UI Components**: ≥ 85%

### 1.3 Testing Tools Stack

#### Frontend Testing
- **Vitest**: Unit Tests
- **React Testing Library**: Component Tests
- **Playwright**: E2E Tests
- **MSW**: API Mocking
- **jest-axe**: Accessibility Tests

#### Backend Testing
- **pytest**: Unit & Integration Tests
- **pytest-asyncio**: Async Tests
- **pytest-cov**: Coverage Reports
- **factory_boy**: Test Data Generation
- **Faker**: Realistic Test Data

#### Performance Testing
- **Locust**: Load Testing
- **k6**: API Performance Testing
- **Lighthouse**: Frontend Performance

## 2. Unit Tests

### 2.1 Frontend Unit Tests

#### Component Test Example
```typescript
// Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('applies correct variant classes', () => {
    render(<Button variant="primary">Primary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-primary-500');
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables when loading', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('shows loading spinner', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

#### Hook Test Example
```typescript
// useAuth.test.ts
import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useAuth } from './useAuth';
import * as api from '@/api/auth';

vi.mock('@/api/auth');

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles successful login', async () => {
    const mockToken = 'mock-jwt-token';
    const mockUser = { id: '1', email: 'test@example.com' };
    
    vi.mocked(api.login).mockResolvedValue({
      access_token: mockToken,
      user: mockUser
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.error).toBeNull();
  });

  it('handles login failure', async () => {
    vi.mocked(api.login).mockRejectedValue(new Error('Invalid credentials'));

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login('test@example.com', 'wrong-password');
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.error).toBe('Invalid credentials');
  });
});
```

#### Store Test Example
```typescript
// courseStore.test.ts
import { act, renderHook } from '@testing-library/react';
import { useCourseStore } from './courseStore';

describe('Course Store', () => {
  beforeEach(() => {
    useCourseStore.setState({
      courses: [],
      loading: false,
      error: null
    });
  });

  it('loads courses successfully', async () => {
    const mockCourses = [
      { id: '1', title: 'Security Basics' },
      { id: '2', title: 'Phishing Awareness' }
    ];

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockCourses
    });

    const { result } = renderHook(() => useCourseStore());

    await act(async () => {
      await result.current.loadCourses();
    });

    expect(result.current.courses).toEqual(mockCourses);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('filters courses by difficulty', () => {
    const { result } = renderHook(() => useCourseStore());
    
    act(() => {
      useCourseStore.setState({
        courses: [
          { id: '1', title: 'Basic', difficulty: 'beginner' },
          { id: '2', title: 'Advanced', difficulty: 'advanced' }
        ]
      });
    });

    const filtered = result.current.getFilteredCourses('beginner');
    expect(filtered).toHaveLength(1);
    expect(filtered[0].title).toBe('Basic');
  });
});
```

### 2.2 Backend Unit Tests

#### Service Test Example
```python
# test_user_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from app.services.user_service import UserService
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

class TestUserService:
    @pytest.fixture
    def user_service(self, db_session):
        return UserService(db_session)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="test-user-id",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=UserRole.EMPLOYEE,
            company_id="test-company-id"
        )
    
    async def test_create_user_success(self, user_service, db_session):
        # Arrange
        user_data = UserCreate(
            email="newuser@example.com",
            first_name="New",
            last_name="User",
            role=UserRole.EMPLOYEE
        )
        
        # Act
        user = await user_service.create_user(user_data, "test-company-id")
        
        # Assert
        assert user.email == user_data.email
        assert user.company_id == "test-company-id"
        assert user.is_active is True
        assert user.hashed_password is not None
        
        # Verify user was saved to database
        saved_user = db_session.query(User).filter_by(email=user_data.email).first()
        assert saved_user is not None
    
    async def test_create_user_duplicate_email(self, user_service, db_session, mock_user):
        # Arrange
        db_session.add(mock_user)
        db_session.commit()
        
        user_data = UserCreate(
            email=mock_user.email,  # Duplicate email
            first_name="Another",
            last_name="User",
            role=UserRole.EMPLOYEE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            await user_service.create_user(user_data, "test-company-id")
    
    async def test_calculate_risk_score(self, user_service, mock_user):
        # Arrange
        with patch.object(user_service, '_get_phishing_performance') as mock_phishing:
            mock_phishing.return_value = 25.0  # 25% click rate
            
            with patch.object(user_service, '_get_training_performance') as mock_training:
                mock_training.return_value = 80.0  # 80% completion
                
                with patch.object(user_service, '_get_time_factor') as mock_time:
                    mock_time.return_value = 50.0  # Medium risk
                    
                    # Act
                    risk_score = await user_service.calculate_risk_score(mock_user.id)
                    
                    # Assert
                    # Risk = (25 * 0.4) + ((100-80) * 0.3) + (50 * 0.2) + (0 * 0.1)
                    # Risk = 10 + 6 + 10 + 0 = 26
                    assert risk_score == 26.0
    
    async def test_bulk_create_users(self, user_service, tmp_path):
        # Arrange
        csv_content = """email,first_name,last_name,department,role
user1@example.com,User,One,IT,employee
user2@example.com,User,Two,HR,manager
invalid-email,User,Three,Sales,employee"""
        
        csv_file = tmp_path / "users.csv"
        csv_file.write_text(csv_content)
        
        # Act
        result = await user_service.bulk_create_users(
            csv_file,
            "test-company-id",
            send_invites=False
        )
        
        # Assert
        assert result.created == 2
        assert result.failed == 1
        assert len(result.errors) == 1
        assert result.errors[0].email == "invalid-email"
        assert "Invalid email" in result.errors[0].error
```

#### API Endpoint Test Example
```python
# test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

class TestAuthEndpoints:
    def test_login_success(self, client: TestClient, test_user):
        # Act
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token is valid
        payload = jwt.decode(
            data["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(test_user.id)
    
    def test_login_invalid_credentials(self, client: TestClient):
        # Act
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "wrongpassword"
            }
        )
        
        # Assert
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_register_company_success(self, client: TestClient):
        # Arrange
        registration_data = {
            "company_name": "Test Company",
            "company_domain": "testcompany.com",
            "industry": "Technology",
            "size": "medium",
            "compliance_requirements": ["dsgvo", "iso27001"],
            "admin_email": "admin@testcompany.com",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Admin",
            "admin_last_name": "User"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["company"]["name"] == "Test Company"
        assert data["user"]["email"] == "admin@testcompany.com"
        assert data["user"]["role"] == "admin"
    
    def test_refresh_token_success(self, client: TestClient, test_user):
        # Arrange
        refresh_token = create_refresh_token(test_user.id)
        
        # Act
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != refresh_token
    
    @pytest.mark.parametrize("password,expected_error", [
        ("short", "Password must be at least 8 characters"),
        ("alllowercase", "Password must contain uppercase letter"),
        ("ALLUPPERCASE", "Password must contain lowercase letter"),
        ("NoNumbers!", "Password must contain number"),
        ("NoSpecial123", "Password must contain special character")
    ])
    def test_register_password_validation(self, client: TestClient, password, expected_error):
        # Arrange
        registration_data = {
            "company_name": "Test Company",
            "company_domain": "testcompany.com",
            "industry": "Technology", 
            "size": "medium",
            "admin_email": "admin@testcompany.com",
            "admin_password": password,
            "admin_first_name": "Admin",
            "admin_last_name": "User"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        # Assert
        assert response.status_code == 400
        assert expected_error in response.json()["detail"][0]["msg"]
```

#### Repository Test Example
```python
# test_course_repository.py
import pytest
from app.repositories.course_repository import CourseRepository
from app.models.course import Course

class TestCourseRepository:
    @pytest.fixture
    def course_repo(self, db_session):
        return CourseRepository(db_session)
    
    @pytest.fixture
    def sample_courses(self, db_session):
        courses = [
            Course(
                title="Security Basics",
                difficulty="beginner",
                tags=["security", "basics"],
                compliance_tags=["dsgvo"],
                duration_minutes=15
            ),
            Course(
                title="Advanced Phishing",
                difficulty="advanced",
                tags=["phishing", "advanced"],
                compliance_tags=["nis2"],
                duration_minutes=30
            ),
            Course(
                title="Password Management",
                difficulty="intermediate",
                tags=["passwords", "security"],
                compliance_tags=["dsgvo", "iso27001"],
                duration_minutes=20
            )
        ]
        db_session.add_all(courses)
        db_session.commit()
        return courses
    
    def test_get_by_difficulty(self, course_repo, sample_courses):
        # Act
        beginner_courses = course_repo.get_by_difficulty("beginner")
        
        # Assert
        assert len(beginner_courses) == 1
        assert beginner_courses[0].title == "Security Basics"
    
    def test_get_by_compliance_tag(self, course_repo, sample_courses):
        # Act
        dsgvo_courses = course_repo.get_by_compliance_tag("dsgvo")
        
        # Assert
        assert len(dsgvo_courses) == 2
        titles = [c.title for c in dsgvo_courses]
        assert "Security Basics" in titles
        assert "Password Management" in titles
    
    def test_search_courses(self, course_repo, sample_courses):
        # Act
        results = course_repo.search("phishing")
        
        # Assert
        assert len(results) == 1
        assert results[0].title == "Advanced Phishing"
```

## 3. Integration Tests

### 3.1 API Integration Tests

```python
# test_course_flow_integration.py
import pytest
from datetime import datetime, timedelta

class TestCourseFlowIntegration:
    @pytest.mark.integration
    async def test_complete_course_flow(self, client, auth_headers, test_user):
        # 1. Get available courses
        response = client.get("/api/v1/courses", headers=auth_headers)
        assert response.status_code == 200
        courses = response.json()
        assert len(courses) > 0
        
        course_id = courses[0]["id"]
        
        # 2. Start course
        response = client.post(
            f"/api/v1/courses/{course_id}/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        progress = response.json()
        assert progress["status"] == "in_progress"
        assert progress["video_progress_seconds"] == 0
        
        # 3. Update progress multiple times
        for seconds in [30, 60, 120, 180]:
            response = client.post(
                f"/api/v1/courses/{course_id}/progress",
                json={"video_progress_seconds": seconds},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # 4. Submit quiz
        quiz_answers = [
            {"question_id": "q1", "answer_id": "b"},
            {"question_id": "q2", "answer_id": "c"},
            {"question_id": "q3", "answer_id": "a"}
        ]
        
        response = client.post(
            f"/api/v1/courses/{course_id}/quiz",
            json={"answers": quiz_answers},
            headers=auth_headers
        )
        assert response.status_code == 200
        quiz_result = response.json()
        assert "score" in quiz_result
        assert "passed" in quiz_result
        
        # 5. Get certificate if passed
        if quiz_result["passed"]:
            response = client.get(
                f"/api/v1/courses/{course_id}/certificate",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
        
        # 6. Verify progress is recorded
        response = client.get("/api/v1/courses/assigned", headers=auth_headers)
        assigned = response.json()
        completed_course = next(c for c in assigned if c["id"] == course_id)
        assert completed_course["status"] == "completed"
        assert completed_course["quiz_score"] is not None
```

### 3.2 Database Integration Tests

```python
# test_database_integration.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import User, Course, UserCourseProgress

class TestDatabaseIntegration:
    @pytest.mark.integration
    def test_cascade_delete_user(self, db_session):
        # Create user with related data
        user = User(
            email="cascade@test.com",
            company_id="test-company"
        )
        db_session.add(user)
        db_session.commit()
        
        # Add course progress
        progress = UserCourseProgress(
            user_id=user.id,
            course_id="test-course",
            company_id="test-company"
        )
        db_session.add(progress)
        db_session.commit()
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Verify cascade
        assert db_session.query(UserCourseProgress).filter_by(
            user_id=user.id
        ).first() is None
    
    @pytest.mark.integration
    def test_transaction_rollback(self, db_session):
        # Start transaction
        initial_count = db_session.query(User).count()
        
        try:
            # Create user
            user = User(email="rollback@test.com", company_id="test")
            db_session.add(user)
            
            # Force error
            raise Exception("Simulated error")
            
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # Verify rollback
        assert db_session.query(User).count() == initial_count
```

### 3.3 External Service Integration Tests

```python
# test_youtube_integration.py
import pytest
from unittest.mock import patch, Mock
from app.utils.youtube_api import YouTubeService

class TestYouTubeIntegration:
    @pytest.mark.integration
    @pytest.mark.external
    async def test_real_youtube_api(self, youtube_api_key):
        # Skip if no API key
        if not youtube_api_key:
            pytest.skip("YouTube API key not available")
        
        service = YouTubeService(youtube_api_key)
        
        # Test with known video
        video_id = "dQw4w9WgXcQ"  # Well-known video ID
        details = await service.get_video_details(video_id)
        
        assert details is not None
        assert "contentDetails" in details
        assert "duration" in details["contentDetails"]
    
    @pytest.mark.integration
    async def test_youtube_api_mock(self):
        service = YouTubeService("mock-key")
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {
                    "items": [{
                        "contentDetails": {
                            "duration": "PT10M30S"
                        },
                        "snippet": {
                            "title": "Test Video"
                        }
                    }]
                }
            )
            
            details = await service.get_video_details("test-id")
            assert details["duration_seconds"] == 630
```

## 4. End-to-End Tests

### 4.1 E2E Test Setup

```typescript
// e2e/setup.ts
import { test as base, chromium } from '@playwright/test';

export const test = base.extend({
  // Authenticated page fixture
  authenticatedPage: async ({ page }, use) => {
    // Login
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    
    // Wait for redirect
    await page.waitForURL('/dashboard');
    
    // Use authenticated page
    await use(page);
  },
  
  // Admin page fixture
  adminPage: async ({ page }, use) => {
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'adminpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    await use(page);
  }
});
```

### 4.2 User Journey Tests

```typescript
// e2e/user-journey.spec.ts
import { test, expect } from './setup';

test.describe('Complete User Journey', () => {
  test('new user onboarding flow', async ({ page }) => {
    // 1. Register new company
    await page.goto('/auth/register');
    
    // Fill company info
    await page.fill('input[name="companyName"]', 'E2E Test Company');
    await page.fill('input[name="companyDomain"]', 'e2etest.com');
    await page.selectOption('select[name="industry"]', 'Technology');
    await page.selectOption('select[name="size"]', 'medium');
    
    // Select compliance requirements
    await page.check('input[value="dsgvo"]');
    await page.check('input[value="iso27001"]');
    
    // Fill admin info
    await page.fill('input[name="adminEmail"]', 'admin@e2etest.com');
    await page.fill('input[name="adminPassword"]', 'SecurePass123!');
    await page.fill('input[name="adminFirstName"]', 'Test');
    await page.fill('input[name="adminLastName"]', 'Admin');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // 2. Verify email (mock in test env)
    await page.waitForURL('/dashboard');
    
    // 3. Complete onboarding wizard
    await expect(page.locator('h1')).toContainText('Welcome to CyberSec Platform');
    
    // Skip tour
    await page.click('button:has-text("Skip Tour")');
    
    // 4. Verify dashboard loads
    await expect(page.locator('[data-testid="compliance-widget"]')).toBeVisible();
    await expect(page.locator('[data-testid="risk-score-chart"]')).toBeVisible();
  });
  
  test('complete course and get certificate', async ({ authenticatedPage: page }) => {
    // Navigate to courses
    await page.click('nav a:has-text("Courses")');
    
    // Select first course
    await page.click('[data-testid="course-card"]:first-child button:has-text("Start")');
    
    // Watch video (mock in test env - auto completes)
    await page.waitForSelector('[data-testid="video-player"]');
    
    // Wait for video to "complete"
    await page.waitForTimeout(2000); // Simulated video watch
    
    // Take quiz
    await page.click('button:has-text("Start Quiz")');
    
    // Answer questions
    const questions = await page.locator('[data-testid="quiz-question"]').all();
    for (const question of questions) {
      // Select first option (in test data, this is correct)
      await question.locator('input[type="radio"]').first().click();
    }
    
    // Submit quiz
    await page.click('button:has-text("Submit Quiz")');
    
    // Verify results
    await expect(page.locator('[data-testid="quiz-result"]')).toContainText('Passed');
    
    // Download certificate
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Download Certificate")');
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toMatch(/certificate.*\.pdf/);
  });
  
  test('phishing simulation campaign', async ({ adminPage: page }) => {
    // Navigate to phishing simulations
    await page.click('nav a:has-text("Phishing")');
    
    // Create new campaign
    await page.click('button:has-text("New Campaign")');
    
    // Fill campaign details
    await page.fill('input[name="campaignName"]', 'E2E Test Campaign');
    
    // Select template
    await page.click('[data-testid="template-card"]:has-text("Fake IT Support")');
    
    // Select targets
    await page.click('button:has-text("Select Recipients")');
    await page.check('input[value="all"]');
    await page.click('button:has-text("Confirm Selection")');
    
    // Schedule
    await page.click('input[name="scheduledDate"]');
    await page.click('button:has-text("Tomorrow")');
    
    // Launch campaign
    await page.click('button:has-text("Launch Campaign")');
    
    // Confirm
    await page.click('button:has-text("Yes, Launch")');
    
    // Verify campaign created
    await expect(page.locator('[data-testid="campaign-status"]')).toContainText('Scheduled');
  });
});
```

### 4.3 Accessibility Tests

```typescript
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility Tests', () => {
  test('login page accessibility', async ({ page }) => {
    await page.goto('/auth/login');
    await injectAxe(page);
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true
      }
    });
  });
  
  test('dashboard accessibility', async ({ page }) => {
    // Login first
    await page.goto('/auth/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    await injectAxe(page);
    await checkA11y(page, null, {
      rules: {
        'color-contrast': { enabled: true },
        'aria-roles': { enabled: true }
      }
    });
  });
  
  test('keyboard navigation', async ({ page }) => {
    await page.goto('/auth/login');
    
    // Tab through form
    await page.keyboard.press('Tab'); // Focus email
    await expect(page.locator('input[name="email"]')).toBeFocused();
    
    await page.keyboard.press('Tab'); // Focus password
    await expect(page.locator('input[name="password"]')).toBeFocused();
    
    await page.keyboard.press('Tab'); // Focus submit
    await expect(page.locator('button[type="submit"]')).toBeFocused();
    
    // Submit with Enter
    await page.keyboard.press('Enter');
  });
});
```

## 5. Performance Tests

### 5.1 API Load Testing (Locust)

```python
# locustfile.py
from locust import HttpUser, task, between
import random

class CybersecUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login once
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "loadtest@example.com",
                "password": "loadtestpass"
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/reports/dashboard/executive", headers=self.headers)
    
    @task(2)
    def list_courses(self):
        self.client.get("/api/v1/courses", headers=self.headers)
    
    @task(1)
    def view_course(self):
        # Assume we know some course IDs
        course_id = random.choice(["course1", "course2", "course3"])
        self.client.get(f"/api/v1/courses/{course_id}", headers=self.headers)
    
    @task(1)
    def update_progress(self):
        course_id = random.choice(["course1", "course2", "course3"])
        self.client.post(
            f"/api/v1/courses/{course_id}/progress",
            json={"video_progress_seconds": random.randint(0, 600)},
            headers=self.headers
        )

class AdminUser(HttpUser):
    wait_time = between(2, 5)
    weight = 1  # 1 admin for every 10 regular users
    
    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@example.com",
                "password": "adminpass"
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def generate_report(self):
        report_type = random.choice(["nis2", "dsgvo", "iso27001"])
        self.client.get(
            f"/api/v1/reports/compliance/{report_type}",
            headers=self.headers
        )
    
    @task
    def list_users(self):
        self.client.get("/api/v1/users?page=0&size=50", headers=self.headers)
```

### 5.2 Frontend Performance Tests

```typescript
// performance/lighthouse.test.ts
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

describe('Lighthouse Performance Tests', () => {
  let chrome;
  
  beforeAll(async () => {
    chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  });
  
  afterAll(async () => {
    await chrome.kill();
  });
  
  test('Homepage performance', async () => {
    const options = {
      logLevel: 'info',
      output: 'json',
      port: chrome.port
    };
    
    const runnerResult = await lighthouse('http://localhost:3000', options);
    const report = JSON.parse(runnerResult.report);
    
    // Performance assertions
    expect(report.categories.performance.score).toBeGreaterThan(0.8);
    expect(report.categories.accessibility.score).toBeGreaterThan(0.9);
    expect(report.categories['best-practices'].score).toBeGreaterThan(0.8);
    expect(report.categories.seo.score).toBeGreaterThan(0.9);
    
    // Specific metrics
    const metrics = report.audits.metrics.details.items[0];
    expect(metrics.firstContentfulPaint).toBeLessThan(2000); // 2s
    expect(metrics.largestContentfulPaint).toBeLessThan(3000); // 3s
    expect(metrics.totalBlockingTime).toBeLessThan(300); // 300ms
  });
});
```

### 5.3 Database Performance Tests

```python
# test_database_performance.py
import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import User, Course, UserCourseProgress

class TestDatabasePerformance:
    @pytest.mark.performance
    def test_bulk_insert_performance(self, db_session):
        start_time = time.time()
        
        # Insert 1000 users
        users = []
        for i in range(1000):
            users.append(User(
                email=f"perf_test_{i}@example.com",
                company_id="test-company",
                first_name=f"User{i}",
                last_name="Test"
            ))
        
        db_session.bulk_insert_mappings(User, [u.__dict__ for u in users])
        db_session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in under 5 seconds
        assert duration < 5.0
        print(f"Bulk insert 1000 users: {duration:.2f}s")
    
    @pytest.mark.performance
    def test_complex_query_performance(self, db_session, performance_data):
        # Setup: Create test data
        # performance_data fixture creates 10k users, 100 courses, 50k progress records
        
        start_time = time.time()
        
        # Complex query: Get users with high risk and incomplete mandatory courses
        query = db_session.query(User).join(
            UserCourseProgress
        ).filter(
            User.risk_score > 70,
            UserCourseProgress.is_mandatory == True,
            UserCourseProgress.status != 'completed'
        ).distinct()
        
        results = query.all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in under 1 second
        assert duration < 1.0
        print(f"Complex query execution: {duration:.2f}s")
```

## 6. Security Tests

### 6.1 Authentication Security Tests

```python
# test_security_auth.py
import pytest
from jose import jwt
from datetime import datetime, timedelta

class TestAuthenticationSecurity:
    def test_jwt_token_expiry(self, client, test_user):
        # Login
        response = client.post("/api/v1/auth/login", data={
            "username": test_user.email,
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        
        # Decode token
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Verify expiry is set correctly
        exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Should expire in 30 minutes
        assert (exp - now) < timedelta(minutes=31)
        assert (exp - now) > timedelta(minutes=29)
    
    def test_brute_force_protection(self, client):
        # Attempt multiple failed logins
        for i in range(6):
            response = client.post("/api/v1/auth/login", data={
                "username": "test@example.com",
                "password": "wrongpassword"
            })
        
        # Should be rate limited after 5 attempts
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_sql_injection_prevention(self, client):
        # Attempt SQL injection
        response = client.post("/api/v1/auth/login", data={
            "username": "admin' OR '1'='1",
            "password": "' OR '1'='1"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_xss_prevention(self, client, auth_headers):
        # Attempt to inject script
        response = client.post("/api/v1/users", 
            json={
                "email": "xss@test.com",
                "first_name": "<script>alert('XSS')</script>",
                "last_name": "Test",
                "role": "employee"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        
        # Verify script is escaped when returned
        user = response.json()
        assert "<script>" not in user["first_name"]
        assert "&lt;script&gt;" in user["first_name"] or user["first_name"] == ""
```

### 6.2 Authorization Tests

```python
# test_security_authorization.py
import pytest

class TestAuthorization:
    def test_employee_cannot_access_admin_endpoints(self, client, employee_auth_headers):
        # Try to access admin-only endpoints
        endpoints = [
            ("/api/v1/users", "POST"),
            ("/api/v1/users/123", "DELETE"),
            ("/api/v1/phishing/campaigns", "POST"),
            ("/api/v1/admin/settings", "PATCH")
        ]
        
        for endpoint, method in endpoints:
            response = client.request(
                method, 
                endpoint,
                headers=employee_auth_headers
            )
            assert response.status_code == 403
    
    def test_user_cannot_access_other_company_data(self, client, auth_headers):
        # Try to access user from different company
        response = client.get(
            "/api/v1/users/other-company-user-id",
            headers=auth_headers
        )
        assert response.status_code == 404  # Should not even reveal existence
    
    def test_csrf_protection(self, client):
        # Attempt request without CSRF token
        response = client.post(
            "/api/v1/users",
            json={"email": "test@example.com"},
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 401
```

## 7. Test Data Management

### 7.1 Test Fixtures

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Company, User
from app.core.security import get_password_hash

@pytest.fixture(scope="session")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_db):
    SessionLocal = sessionmaker(bind=test_db)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def test_company(db_session):
    company = Company(
        name="Test Company",
        domain="testcompany.com",
        industry="Technology",
        size="medium",
        compliance_requirements=["dsgvo", "iso27001"]
    )
    db_session.add(company)
    db_session.commit()
    return company

@pytest.fixture
def test_user(db_session, test_company):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        role="employee",
        company_id=test_company.id
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(client, test_user):
    response = client.post("/api/v1/auth/login", data={
        "username": test_user.email,
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### 7.2 Test Data Factories

```python
# factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from app.models import User, Course, Company

fake = Faker(['de_DE', 'en_US'])

class CompanyFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Company
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker("company")
    domain = factory.LazyAttribute(lambda obj: f"{obj.name.lower().replace(' ', '')}.com")
    industry = factory.Faker("random_element", elements=["Technology", "Finance", "Healthcare", "Manufacturing"])
    size = factory.Faker("random_element", elements=["small", "medium", "large", "enterprise"])
    compliance_requirements = factory.List([
        factory.Faker("random_element", elements=["dsgvo", "nis2", "iso27001", "tisax"])
        for _ in range(2)
    ])

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    department = factory.Faker("random_element", elements=["IT", "HR", "Sales", "Finance", "Operations"])
    role = factory.Faker("random_element", elements=["employee", "manager"])
    risk_score = factory.Faker("random_int", min=0, max=100)
    company = factory.SubFactory(CompanyFactory)

class CourseFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Course
        sqlalchemy_session_persistence = "commit"
    
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    duration_minutes = factory.Faker("random_element", elements=[10, 15, 20, 30])
    difficulty = factory.Faker("random_element", elements=["beginner", "intermediate", "advanced"])
    youtube_video_id = factory.Faker("lexify", text="???????????")
    tags = factory.List([fake.word() for _ in range(3)])
    compliance_tags = factory.List([
        factory.Faker("random_element", elements=["dsgvo", "nis2", "iso27001"])
    ])
```

## 8. Test Automation & CI/CD

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Run linting
      working-directory: ./frontend
      run: npm run lint
    
    - name: Run unit tests
      working-directory: ./frontend
      run: npm run test:unit -- --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./frontend/coverage/lcov.info
        flags: frontend

  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      working-directory: ./backend
      run: |
        pip install poetry
        poetry install
    
    - name: Run linting
      working-directory: ./backend
      run: |
        poetry run black --check .
        poetry run ruff .
        poetry run mypy .
    
    - name: Run unit tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost/test_db
        REDIS_URL: redis://localhost:6379
      run: |
        poetry run pytest tests/unit -v --cov=app --cov-report=xml
    
    - name: Run integration tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost/test_db
        REDIS_URL: redis://localhost:6379
      run: |
        poetry run pytest tests/integration -v -m integration
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./backend/coverage.xml
        flags: backend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [frontend-tests, backend-tests]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Playwright
      run: npx playwright install --with-deps
    
    - name: Start services
      run: docker-compose up -d
      env:
        COMPOSE_FILE: docker-compose.test.yml
    
    - name: Wait for services
      run: |
        timeout 60 bash -c 'until curl -f http://localhost:3000/health; do sleep 1; done'
    
    - name: Run E2E tests
      run: npx playwright test
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-report
        path: playwright-report/

  security-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Snyk security scan
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --all-projects --severity-threshold=high
    
    - name: Run OWASP ZAP scan
      uses: zaproxy/action-full-scan@v0.4.0
      with:
        target: 'http://localhost:3000'
        rules_file_name: '.zap/rules.tsv'
```

### 8.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  # Frontend
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.44.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@8.44.0
          - eslint-config-react-app

  # Backend
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.277
    hooks:
      - id: ruff

  # Security
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

## 9. Test Reporting

### 9.1 Coverage Configuration

```ini
# backend/.coveragerc
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__init__.py
    */config.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

### 9.2 Test Report Generation

```javascript
// frontend/vite.config.ts
export default defineConfig({
  test: {
    coverage: {
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/*'
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80
      }
    },
    reporters: ['verbose', 'json', 'html'],
    outputFile: {
      json: './test-results/results.json',
      html: './test-results/index.html'
    }
  }
});
```

## 10. Testing Best Practices

### 10.1 Test Naming Conventions
- **Unit Tests**: `test_<function_name>_<scenario>_<expected_result>`
- **Integration Tests**: `test_<feature>_integration_<scenario>`
- **E2E Tests**: `<user_role>_can_<action>_<feature>`

### 10.2 Test Organization
```
tests/
├── unit/
│   ├── services/
│   ├── models/
│   └── utils/
├── integration/
│   ├── api/
│   ├── database/
│   └── external/
├── e2e/
│   ├── user-flows/
│   ├── admin-flows/
│   └── accessibility/
├── performance/
├── security/
└── fixtures/
```

### 10.3 Testing Checklist
- [ ] All new code has tests
- [ ] Tests are isolated and independent
- [ ] Mock external dependencies
- [ ] Test edge cases and error conditions
- [ ] Performance tests for critical paths
- [ ] Security tests for authentication/authorization
- [ ] Accessibility tests for UI components
- [ ] Documentation updated with test examples

Diese umfassende Testing-Spezifikation stellt sicher, dass die Cybersecurity Awareness Platform robust, sicher und zuverlässig ist.