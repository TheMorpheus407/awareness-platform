"""Seed data for development and testing."""

import asyncio
from datetime import datetime, timedelta
import random
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session_maker
from models import (
    User, Company, Course, Quiz, QuizQuestion, 
    PhishingTemplate, UserCourseProgress
)
from core.security import get_password_hash


async def create_companies(session: AsyncSession) -> List[Company]:
    """Create sample companies."""
    companies = []
    
    company_data = [
        {
            "name": "acme-corp",
            "display_name": "ACME Corporation",
            "domain": "acme.com",
            "contact_email": "admin@acme.com",
            "industry": "Technology",
            "size": "201-500",
            "subscription_plan": "professional",
            "settings": {"theme": "blue", "features": ["phishing", "courses", "analytics"]},
        },
        {
            "name": "globex-industries",
            "display_name": "Globex Industries",
            "domain": "globex.com",
            "contact_email": "security@globex.com",
            "industry": "Manufacturing",
            "size": "501-1000",
            "subscription_plan": "enterprise",
            "settings": {"theme": "green", "features": ["phishing", "courses", "analytics", "compliance"]},
        },
        {
            "name": "bootstrap-demo",
            "display_name": "Bootstrap Demo Company",
            "domain": "demo.bootstrap-awareness.de",
            "contact_email": "demo@bootstrap-awareness.de",
            "industry": "Education",
            "size": "11-50",
            "subscription_plan": "starter",
            "settings": {"theme": "purple", "features": ["courses", "analytics"]},
        },
    ]
    
    for data in company_data:
        company = Company(**data)
        session.add(company)
        companies.append(company)
    
    await session.flush()
    return companies


async def create_users(session: AsyncSession, companies: List[Company]) -> List[User]:
    """Create sample users."""
    users = []
    
    # Platform admin
    admin = User(
        email="admin@bootstrap-awareness.de",
        password_hash=get_password_hash("admin123"),
        first_name="Platform",
        last_name="Admin",
        role="admin",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        verified_at=datetime.utcnow(),
    )
    session.add(admin)
    users.append(admin)
    
    # Company admins and employees
    for company in companies:
        # Company admin
        company_admin = User(
            email=f"admin@{company.domain}",
            password_hash=get_password_hash("password123"),
            first_name="Company",
            last_name="Admin",
            company_id=company.id,
            role="company_admin",
            is_active=True,
            is_verified=True,
            verified_at=datetime.utcnow(),
        )
        session.add(company_admin)
        users.append(company_admin)
        
        # Regular employees
        for i in range(5):
            employee = User(
                email=f"user{i+1}@{company.domain}",
                password_hash=get_password_hash("password123"),
                first_name=f"User{i+1}",
                last_name=company.display_name.split()[0],
                company_id=company.id,
                role="user",
                is_active=True,
                is_verified=True,
                verified_at=datetime.utcnow(),
            )
            session.add(employee)
            users.append(employee)
    
    await session.flush()
    return users


async def create_courses(session: AsyncSession) -> List[Course]:
    """Create sample courses."""
    courses = []
    
    course_data = [
        {
            "title": "Password Security Basics",
            "description": "Learn how to create and manage strong passwords to protect your accounts.",
            "category": "Security Basics",
            "difficulty_level": "beginner",
            "duration_minutes": 15,
            "youtube_video_id": "3NjQ9b3pgIg",
            "tags": ["passwords", "security", "basics"],
            "language": "de",
        },
        {
            "title": "Recognizing Phishing Emails",
            "description": "Master the art of identifying and avoiding phishing attacks.",
            "category": "Email Security",
            "difficulty_level": "intermediate",
            "duration_minutes": 20,
            "youtube_video_id": "Y7zNlEMDmI4",
            "tags": ["phishing", "email", "security"],
            "language": "de",
        },
        {
            "title": "GDPR for Employees",
            "description": "Understand your responsibilities under GDPR regulations.",
            "category": "Compliance",
            "difficulty_level": "beginner",
            "duration_minutes": 30,
            "youtube_video_id": "ZyYW6Wc7Zno",
            "tags": ["gdpr", "compliance", "privacy"],
            "language": "de",
        },
        {
            "title": "Social Engineering Defense",
            "description": "Protect yourself against manipulation and social engineering attacks.",
            "category": "Advanced Security",
            "difficulty_level": "advanced",
            "duration_minutes": 25,
            "youtube_video_id": "lc7scxvKQOo",
            "tags": ["social-engineering", "security", "advanced"],
            "language": "de",
        },
        {
            "title": "Secure Remote Work",
            "description": "Best practices for maintaining security while working from home.",
            "category": "Remote Work",
            "difficulty_level": "intermediate",
            "duration_minutes": 20,
            "youtube_video_id": "We1rnNpV_rA",
            "tags": ["remote-work", "vpn", "security"],
            "language": "de",
        },
    ]
    
    for data in course_data:
        course = Course(**data)
        session.add(course)
        courses.append(course)
    
    await session.flush()
    
    # Create quizzes for each course
    for course in courses:
        quiz = Quiz(
            course_id=course.id,
            title=f"{course.title} - Assessment",
            passing_score=70,
            time_limit_minutes=10,
            max_attempts=3,
        )
        session.add(quiz)
        await session.flush()
        
        # Add sample questions
        questions = [
            {
                "question_text": f"What is the main topic of the '{course.title}' course?",
                "question_type": "multiple_choice",
                "options": {
                    "a": "Network security",
                    "b": course.category,
                    "c": "Database management",
                    "d": "Cloud computing"
                },
                "correct_answer": "b",
                "explanation": f"This course focuses on {course.category}.",
                "points": 10,
                "order_index": 1,
            },
            {
                "question_text": f"True or False: This course is suitable for {course.difficulty_level} level learners.",
                "question_type": "true_false",
                "correct_answer": "true",
                "explanation": f"Yes, this course is designed for {course.difficulty_level} level.",
                "points": 5,
                "order_index": 2,
            },
        ]
        
        for q_data in questions:
            question = QuizQuestion(quiz_id=quiz.id, **q_data)
            session.add(question)
    
    await session.flush()
    return courses


async def create_phishing_templates(session: AsyncSession) -> List[PhishingTemplate]:
    """Create sample phishing templates."""
    templates = []
    
    template_data = [
        {
            "name": "IT Support Password Reset",
            "category": "IT Support",
            "difficulty": "easy",
            "subject": "Urgent: Password Reset Required",
            "sender_name": "IT Support Team",
            "sender_email": "it-support@company-internal.com",
            "html_content": """
                <p>Dear Employee,</p>
                <p>We have detected unusual activity on your account. Please reset your password immediately.</p>
                <p><a href="{tracking_link}">Click here to reset your password</a></p>
                <p>Best regards,<br>IT Support Team</p>
            """,
            "landing_page_html": "<h1>This was a phishing simulation!</h1><p>Learn more about phishing attacks.</p>",
        },
        {
            "name": "CEO Urgent Request",
            "category": "CEO Fraud",
            "difficulty": "medium",
            "subject": "Urgent - Need your help",
            "sender_name": "John Smith (CEO)",
            "sender_email": "ceo@companyy.com",  # Note the typo
            "html_content": """
                <p>Hi,</p>
                <p>I need you to handle an urgent matter for me. I'm in a meeting and can't talk.</p>
                <p>Please purchase gift cards worth €500 for a client meeting. Reply with the codes ASAP.</p>
                <p>Thanks,<br>John</p>
            """,
            "landing_page_html": "<h1>CEO Fraud Attempt!</h1><p>Always verify unusual requests through official channels.</p>",
        },
        {
            "name": "Package Delivery Notification",
            "category": "Delivery",
            "difficulty": "easy",
            "subject": "Your package could not be delivered",
            "sender_name": "DHL Delivery",
            "sender_email": "noreply@dhl-delivery.net",
            "html_content": """
                <p>Your package could not be delivered due to an incorrect address.</p>
                <p>Tracking number: DH4839583958</p>
                <p><a href="{tracking_link}">Click here to update your delivery address</a></p>
                <p>DHL Express</p>
            """,
            "landing_page_html": "<h1>Phishing Alert!</h1><p>Always check the sender's email address carefully.</p>",
        },
    ]
    
    for data in template_data:
        template = PhishingTemplate(**data)
        session.add(template)
        templates.append(template)
    
    await session.flush()
    return templates


async def create_user_progress(session: AsyncSession, users: List[User], courses: List[Course]):
    """Create sample user course progress."""
    # Skip admin users
    regular_users = [u for u in users if u.role == "user"]
    
    for user in regular_users[:10]:  # First 10 regular users
        for course in courses[:3]:  # First 3 courses
            progress = random.randint(0, 100)
            status = "not_started" if progress == 0 else ("completed" if progress == 100 else "in_progress")
            
            user_progress = UserCourseProgress(
                user_id=user.id,
                course_id=course.id,
                company_id=user.company_id,
                status=status,
                progress_percentage=progress,
                started_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)) if progress > 0 else None,
                completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)) if progress == 100 else None,
                certificate_issued=progress == 100,
            )
            session.add(user_progress)
    
    await session.flush()


async def seed_database():
    """Main function to seed the database."""
    async with async_session_maker() as session:
        try:
            # Check if data already exists
            result = await session.execute(select(Company).limit(1))
            if result.scalar_one_or_none():
                print("Database already contains data. Skipping seed.")
                return
            
            print("Seeding database...")
            
            # Create data
            companies = await create_companies(session)
            print(f"Created {len(companies)} companies")
            
            users = await create_users(session, companies)
            print(f"Created {len(users)} users")
            
            courses = await create_courses(session)
            print(f"Created {len(courses)} courses with quizzes")
            
            templates = await create_phishing_templates(session)
            print(f"Created {len(templates)} phishing templates")
            
            await create_user_progress(session, users, courses)
            print("Created user progress records")
            
            # Commit all changes
            await session.commit()
            print("Database seeding completed successfully!")
            
            # Print login credentials
            print("\n=== Login Credentials ===")
            print("Platform Admin: admin@bootstrap-awareness.de / admin123")
            print("Company Admin: admin@acme.com / password123")
            print("Regular User: user1@acme.com / password123")
            
        except Exception as e:
            await session.rollback()
            print(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())