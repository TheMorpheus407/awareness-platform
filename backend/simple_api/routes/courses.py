"""Simplified course routes for MVP."""
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.simple_schemas.course import CourseCreate, CourseResponse, ModuleResponse, QuizSubmit

router = APIRouter(prefix="/courses", tags=["courses"])

# Temporary in-memory storage for MVP
COURSES = {}
MODULES = {}
USER_PROGRESS = {}


@router.get("/", response_model=List[CourseResponse])
def get_courses():
    """Get all available courses."""
    return list(COURSES.values())


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: UUID):
    """Get specific course details."""
    if course_id not in COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    return COURSES[course_id]


@router.post("/", response_model=CourseResponse)
def create_course(course: CourseCreate):
    """Create a new course (admin only)."""
    course_id = uuid4()
    new_course = CourseResponse(
        id=course_id,
        **course.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    COURSES[course_id] = new_course
    return new_course


@router.get("/{course_id}/modules", response_model=List[ModuleResponse])
def get_course_modules(course_id: UUID):
    """Get all modules for a course."""
    if course_id not in COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return [m for m in MODULES.values() if m.course_id == course_id]


@router.post("/{course_id}/start")
def start_course(course_id: UUID, user_id: str = "demo-user"):
    """Start a course for the current user."""
    if course_id not in COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    
    progress_key = f"{user_id}:{course_id}"
    if progress_key not in USER_PROGRESS:
        USER_PROGRESS[progress_key] = {
            "user_id": user_id,
            "course_id": course_id,
            "started_at": datetime.utcnow(),
            "progress_percent": 0,
            "completed_modules": []
        }
    
    return {"message": "Course started successfully"}


@router.post("/{course_id}/modules/{module_id}/complete")
def complete_module(course_id: UUID, module_id: UUID, user_id: str = "demo-user"):
    """Mark a module as completed."""
    progress_key = f"{user_id}:{course_id}"
    if progress_key not in USER_PROGRESS:
        raise HTTPException(status_code=400, detail="Course not started")
    
    progress = USER_PROGRESS[progress_key]
    if module_id not in progress["completed_modules"]:
        progress["completed_modules"].append(module_id)
    
    # Calculate progress
    total_modules = len([m for m in MODULES.values() if m.course_id == course_id])
    if total_modules > 0:
        progress["progress_percent"] = int(
            (len(progress["completed_modules"]) / total_modules) * 100
        )
    
    return {"progress_percent": progress["progress_percent"]}


@router.post("/quiz/submit")
def submit_quiz(submission: QuizSubmit, user_id: str = "demo-user"):
    """Submit quiz answers and get results."""
    # Simple quiz logic
    score = 80  # Mock score
    passed = score >= 70
    
    return {
        "score": score,
        "passed": passed,
        "feedback": "Good job! You passed the quiz."
    }


# Initialize some demo data
def init_demo_data():
    """Initialize demo courses and modules."""
    # Create a demo course
    course_id = uuid4()
    COURSES[course_id] = CourseResponse(
        id=course_id,
        title="Cybersecurity Basics",
        description="Learn the fundamentals of cybersecurity",
        duration_minutes=30,
        is_mandatory=True,
        status="published",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create demo modules
    for i in range(3):
        module_id = uuid4()
        MODULES[module_id] = ModuleResponse(
            id=module_id,
            course_id=course_id,
            title=f"Module {i+1}: Security Topic {i+1}",
            description=f"Learn about security topic {i+1}",
            video_url=f"https://youtube.com/watch?v=demo{i+1}",
            order_index=i,
            duration_minutes=10
        )


# Initialize demo data on module load
init_demo_data()