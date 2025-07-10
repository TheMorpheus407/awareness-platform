# Training Module API Documentation

This document describes the training module features and API endpoints for the AwarenessSchulungen backend.

## Overview

The training module system provides:
- **Interactive Training Modules** with multimedia content (video, text, interactive)
- **Quiz System** with multiple question types and automatic scoring
- **Progress Tracking** at course, module, and lesson levels
- **Certificate Generation** upon course completion
- **Gamification Features** including badges, points, levels, and leaderboards
- **Role-Based Access Control** for content management

## Database Models

### Core Training Models

#### Course
- Stores course information with categories, difficulty levels, and metadata
- Supports prerequisites and tags
- Links to modules, quizzes, and user progress

#### Module
- Organizes course content into logical sections
- Contains multiple lessons with ordering
- Tracks duration and requirements

#### Lesson
- Individual learning units within modules
- Supports multiple content types: video, text, interactive, mixed
- Includes interactive elements and resources

#### Quiz & QuizQuestion
- Assessment system with configurable passing scores
- Multiple question types: multiple choice, true/false, text
- Time limits and attempt restrictions

### Progress Tracking Models

#### UserCourseProgress
- Tracks overall course enrollment and completion
- Manages certificate issuance
- Records timestamps and progress percentage

#### UserLessonProgress
- Granular progress tracking per lesson
- Video progress tracking (current/total seconds)
- Interactive element completion tracking

### Gamification Models

#### Badge
- Defines achievement badges with requirements
- Types: completion, streak, score, special
- Configurable point values

#### UserBadge
- Tracks earned badges per user
- Records context of achievement

#### UserPoints
- Manages user points and levels
- Tracks streaks and statistics
- Automatic level progression

#### Certificate
- Course completion certificates
- Unique certificate numbers and verification codes
- Expiration support

## API Endpoints

### Course Management

#### GET /api/v1/courses/
List available courses with filtering and search.

**Query Parameters:**
- `search`: Search in title or description
- `category`: Filter by category
- `difficulty`: Filter by difficulty (beginner, intermediate, advanced)
- `is_published`: Filter by published status (default: true)
- `limit`: Results per page (default: 10)
- `offset`: Skip results (default: 0)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Security Awareness Basics",
    "description": "Learn the fundamentals of cybersecurity",
    "category": "security",
    "difficulty": "beginner",
    "duration_hours": 2,
    "is_published": true,
    "created_at": "2024-01-01T00:00:00Z",
    "tags": ["security", "basics"]
  }
]
```

#### POST /api/v1/courses/
Create a new course (admin only).

**Request Body:**
```json
{
  "title": "Advanced Security Techniques",
  "description": "Deep dive into security practices",
  "category": "security",
  "difficulty": "advanced",
  "duration_hours": 5,
  "is_published": false,
  "tags": ["security", "advanced"],
  "prerequisites": [1, 2]
}
```

#### GET /api/v1/courses/{course_id}
Get detailed course information with modules.

**Response:**
```json
{
  "id": 1,
  "title": "Security Awareness Basics",
  "description": "Learn the fundamentals",
  "modules": [
    {
      "id": 1,
      "title": "Introduction",
      "description": "Course overview",
      "order_index": 0,
      "duration_minutes": 30,
      "lessons": [
        {
          "id": 1,
          "title": "Welcome",
          "content_type": "video",
          "duration_minutes": 10
        }
      ]
    }
  ],
  "has_quiz": true,
  "enrolled": true,
  "progress": {
    "status": "in_progress",
    "percentage": 50,
    "completed_at": null
  }
}
```

### Module & Lesson Management

#### POST /api/v1/courses/{course_id}/modules
Create a new module (admin only).

**Request Body:**
```json
{
  "title": "Module Title",
  "description": "Module description",
  "order_index": 1,
  "duration_minutes": 60,
  "is_required": true
}
```

#### POST /api/v1/courses/{course_id}/modules/{module_id}/lessons
Create a new lesson (admin only).

**Request Body:**
```json
{
  "title": "Lesson Title",
  "description": "Lesson description",
  "content_type": "interactive",
  "content_url": "https://example.com/video.mp4",
  "content_markdown": "# Lesson Content\n\nText content here...",
  "order_index": 1,
  "duration_minutes": 15,
  "interactive_elements": {
    "interaction_ids": ["click1", "drag2"]
  },
  "resources": [
    {"title": "PDF Guide", "url": "/resources/guide.pdf"}
  ]
}
```

### Progress Tracking

#### POST /api/v1/courses/{course_id}/enroll
Enroll in a course.

**Response:**
```json
{
  "enrollment_id": 123,
  "course_id": 1,
  "user_id": 456,
  "status": "not_started",
  "enrolled_at": "2024-01-01T00:00:00Z",
  "message": "Successfully enrolled in course"
}
```

#### GET /api/v1/courses/{course_id}/progress
Get detailed progress for a course.

**Response:**
```json
{
  "enrollment_id": 123,
  "course_id": 1,
  "user_id": 456,
  "status": "in_progress",
  "total_lessons": 10,
  "completed_lessons": 5,
  "progress_percentage": 50,
  "time_spent_hours": 2.5,
  "current_streak_days": 3,
  "certificate_issued": false
}
```

#### POST /api/v1/courses/{course_id}/lessons/{lesson_id}/progress
Update lesson progress.

**Request Body:**
```json
{
  "video_progress_seconds": 120,
  "video_total_seconds": 300,
  "time_spent_seconds": 150,
  "interactions_completed": {
    "click1": true,
    "drag2": false
  }
}
```

### Quiz System

#### GET /api/v1/courses/{course_id}/quiz
Get quiz questions (without answers).

**Response:**
```json
{
  "quiz_id": 1,
  "title": "Final Assessment",
  "passing_score": 70,
  "time_limit_minutes": 30,
  "max_attempts": 3,
  "total_points": 100,
  "questions": [
    {
      "id": 1,
      "question_text": "What is phishing?",
      "question_type": "multiple_choice",
      "points": 10,
      "options": [
        {"id": "a", "text": "A type of fish"},
        {"id": "b", "text": "A cyber attack"},
        {"id": "c", "text": "A software bug"}
      ]
    }
  ]
}
```

#### POST /api/v1/courses/{course_id}/quiz/submit
Submit quiz answers.

**Request Body:**
```json
{
  "1": "b",
  "2": "true",
  "3": "SQL injection"
}
```

**Response:**
```json
{
  "score": 85.5,
  "passed": true,
  "passing_score": 70,
  "correct_answers": 17,
  "total_questions": 20,
  "feedback": [
    {
      "question_id": "1",
      "correct": true,
      "points_earned": 10
    }
  ],
  "certificate_id": "550e8400-e29b-41d4-a716",
  "gamification": {
    "points_awarded": 75,
    "total_points": 1250,
    "current_level": 5,
    "leveled_up": true,
    "new_badges": [
      {
        "name": "Quiz Master",
        "description": "Score 85% or higher"
      }
    ]
  }
}
```

### Gamification

#### GET /api/v1/courses/gamification/my-stats
Get user's gamification statistics.

**Response:**
```json
{
  "user_id": 123,
  "total_points": 1250,
  "current_level": 5,
  "points_to_next_level": 1500,
  "progress_to_next_level": 83.3,
  "global_rank": 42,
  "badges_earned": 8,
  "total_badges_available": 15,
  "courses_completed": 12,
  "perfect_quizzes": 3,
  "current_streak_days": 7,
  "longest_streak_days": 15,
  "badges": [
    {
      "badge_id": 1,
      "name": "First Steps",
      "description": "Complete your first course",
      "earned_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET /api/v1/courses/gamification/leaderboard
Get leaderboard rankings.

**Query Parameters:**
- `scope`: "company" or "global" (default: "company")
- `limit`: Number of results (default: 10, max: 100)

**Response:**
```json
[
  {
    "rank": 1,
    "user_id": 123,
    "user_name": "John Doe",
    "total_points": 2500,
    "current_level": 8,
    "courses_completed": 25,
    "perfect_quizzes": 10,
    "current_streak": 30
  }
]
```

### User Courses

#### GET /api/v1/courses/my-courses
Get all enrolled courses.

**Query Parameters:**
- `status`: Filter by status (not_started, in_progress, completed)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Security Basics",
    "category": "security",
    "difficulty": "beginner",
    "enrollment": {
      "status": "completed",
      "progress_percentage": 100,
      "enrolled_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-15T00:00:00Z",
      "certificate_issued": true
    }
  }
]
```

### Certificates

#### GET /api/v1/courses/certificates/{certificate_id}
Get certificate details.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716",
  "certificate_number": "CERT-202401-123456",
  "verification_code": "AbCdEfGhIjKlMnOpQrStUvWxYz",
  "user": {
    "id": 123,
    "name": "John Doe"
  },
  "course": {
    "id": 1,
    "title": "Security Awareness Basics"
  },
  "issued_at": "2024-01-15T00:00:00Z",
  "expires_at": null,
  "completion_date": "2024-01-15T00:00:00Z",
  "final_score": 92,
  "time_spent_hours": 3,
  "is_valid": true,
  "pdf_url": "/api/v1/certificates/550e8400-e29b-41d4-a716/download"
}
```

## Gamification System

### Point System
- **Course Completion**: 50 points
- **Perfect Quiz (100%)**: 50 bonus points
- **High Score (90%+)**: 25 bonus points
- **Daily Activity**: 10 points
- **Weekly Streak**: 50 points
- **Monthly Streak**: 200 points
- **First Course**: 100 points
- **Level Up**: 25 points per level

### Badge Types
1. **Completion Badges**: Based on number of courses completed
2. **Streak Badges**: For maintaining learning streaks
3. **Score Badges**: For quiz performance
4. **Special Badges**: Custom achievements

### Level System
- Levels increase based on total points
- Each level requires progressively more points
- Visual progress indicator to next level

## Role-Based Access Control

### User Roles
- **Employee**: Can enroll, view courses, track progress
- **Manager**: Employee permissions + view team analytics
- **Company Admin**: All permissions + create/edit courses
- **System Admin**: Full system access

### Permission Matrix
| Action | Employee | Manager | Company Admin | System Admin |
|--------|----------|---------|---------------|--------------|
| View Courses | ✓ | ✓ | ✓ | ✓ |
| Enroll in Courses | ✓ | ✓ | ✓ | ✓ |
| Track Progress | ✓ | ✓ | ✓ | ✓ |
| View Team Analytics | ✗ | ✓ | ✓ | ✓ |
| Create Courses | ✗ | ✗ | ✓ | ✓ |
| Edit Courses | ✗ | ✗ | ✓ | ✓ |
| Delete Courses | ✗ | ✗ | ✓ | ✓ |
| Manage Users | ✗ | ✗ | ✓ | ✓ |

## Security Considerations

1. **Authentication**: All endpoints require JWT authentication
2. **Authorization**: Role-based access control enforced
3. **Data Privacy**: Users can only access their own progress data
4. **Certificate Verification**: Unique verification codes for authenticity
5. **Content Protection**: Secure URLs with time-limited access tokens

## Integration Points

1. **Content Delivery**: Integration with `/api/v1/content/` for secure file access
2. **Email Notifications**: Course enrollment and completion notifications
3. **Analytics**: Integration with analytics service for reporting
4. **Payment**: Premium courses can integrate with payment system

## Best Practices

1. **Progress Saving**: Save progress frequently (every 30 seconds for videos)
2. **Offline Support**: Cache course content for offline viewing
3. **Responsive Design**: Support multiple device types
4. **Accessibility**: WCAG 2.1 compliance for all content
5. **Performance**: Lazy load modules and lessons