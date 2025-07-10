"""Add comprehensive course management system

Revision ID: 005
Revises: 004
Create Date: 2024-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004_add_payment_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contenttype') THEN
                CREATE TYPE contenttype AS ENUM ('video', 'document', 'presentation', 'interactive', 'scorm', 'external_link', 'text', 'quiz');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'difficultylevel') THEN
                CREATE TYPE difficultylevel AS ENUM ('beginner', 'intermediate', 'advanced', 'expert');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coursestatus') THEN
                CREATE TYPE coursestatus AS ENUM ('draft', 'published', 'archived');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'progressstatus') THEN
                CREATE TYPE progressstatus AS ENUM ('not_started', 'in_progress', 'completed', 'failed');
            END IF;
        END $$;
    """)
    
    # Drop old tables if they exist (from previous simple models)
    op.execute("DROP TABLE IF EXISTS user_course_progress CASCADE")
    op.execute("DROP TABLE IF EXISTS quiz_questions CASCADE")
    op.execute("DROP TABLE IF EXISTS quizzes CASCADE")
    op.execute("DROP TABLE IF EXISTS courses CASCADE")
    
    # Create courses table with enhanced fields
    op.create_table('courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('difficulty_level', postgresql.ENUM('beginner', 'intermediate', 'advanced', 'expert', name='difficultylevel'), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'published', 'archived', name='coursestatus'), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('preview_video_url', sa.String(length=500), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('available_languages', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('prerequisites', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('learning_objectives', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('is_free', sa.Boolean(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('meta_title', sa.String(length=255), nullable=True),
        sa.Column('meta_description', sa.String(length=500), nullable=True),
        sa.Column('enrolled_count', sa.Integer(), nullable=False),
        sa.Column('completion_count', sa.Integer(), nullable=False),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False),
        sa.Column('compliance_standards', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('certificate_template_id', sa.Integer(), nullable=True),
        sa.Column('validity_days', sa.Integer(), nullable=True),
        sa.Column('scorm_package_url', sa.String(length=500), nullable=True),
        sa.Column('scorm_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_category'), 'courses', ['category'], unique=False)
    op.create_index(op.f('ix_courses_slug'), 'courses', ['slug'], unique=True)
    op.create_index(op.f('ix_courses_status'), 'courses', ['status'], unique=False)
    
    # Create modules table
    op.create_table('modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'slug', name='uq_course_module_slug')
    )
    op.create_index(op.f('ix_modules_course_id'), 'modules', ['course_id'], unique=False)
    
    # Create lessons table
    op.create_table('lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('content_type', postgresql.ENUM('video', 'document', 'presentation', 'interactive', 'scorm', 'external_link', 'text', 'quiz', name='contenttype'), nullable=False),
        sa.Column('is_preview', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id', 'slug', name='uq_module_lesson_slug')
    )
    op.create_index(op.f('ix_lessons_module_id'), 'lessons', ['module_id'], unique=False)
    
    # Create course_content table
    op.create_table('course_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_type', postgresql.ENUM('video', 'document', 'presentation', 'interactive', 'scorm', 'external_link', 'text', 'quiz', name='contenttype'), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('content_url', sa.String(length=500), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_content_lesson_id'), 'course_content', ['lesson_id'], unique=False)
    
    # Create quizzes table
    op.create_table('quizzes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('passing_score', sa.Integer(), nullable=False),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('randomize_questions', sa.Boolean(), nullable=False),
        sa.Column('randomize_answers', sa.Boolean(), nullable=False),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quizzes_lesson_id'), 'quizzes', ['lesson_id'], unique=True)
    
    # Create quiz_questions table
    op.create_table('quiz_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.JSON(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('hint', sa.Text(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('negative_points', sa.Integer(), nullable=False),
        sa.Column('partial_credit', sa.Boolean(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('is_bonus', sa.Boolean(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('video_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_questions_quiz_id'), 'quiz_questions', ['quiz_id'], unique=False)
    
    # Create course_enrollments table
    op.create_table('course_enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', postgresql.ENUM('not_started', 'in_progress', 'completed', 'failed', name='progressstatus'), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completion_certificate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('certificate_issued_at', sa.DateTime(), nullable=True),
        sa.Column('certificate_expires_at', sa.DateTime(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
        sa.Column('lessons_completed', sa.Integer(), nullable=False),
        sa.Column('lessons_total', sa.Integer(), nullable=False),
        sa.Column('certificate_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_enrollment')
    )
    op.create_index(op.f('ix_course_enrollments_company_id'), 'course_enrollments', ['company_id'], unique=False)
    op.create_index(op.f('ix_course_enrollments_course_id'), 'course_enrollments', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_enrollments_status'), 'course_enrollments', ['status'], unique=False)
    op.create_index(op.f('ix_course_enrollments_user_id'), 'course_enrollments', ['user_id'], unique=False)
    
    # Create module_progress table
    op.create_table('module_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('not_started', 'in_progress', 'completed', 'failed', name='progressstatus'), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
        sa.Column('lessons_completed', sa.Integer(), nullable=False),
        sa.Column('lessons_total', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['enrollment_id'], ['course_enrollments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enrollment_id', 'module_id', name='uq_enrollment_module')
    )
    op.create_index(op.f('ix_module_progress_enrollment_id'), 'module_progress', ['enrollment_id'], unique=False)
    op.create_index(op.f('ix_module_progress_module_id'), 'module_progress', ['module_id'], unique=False)
    
    # Create lesson_progress table
    op.create_table('lesson_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('not_started', 'in_progress', 'completed', 'failed', name='progressstatus'), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_position_seconds', sa.Integer(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['enrollment_id'], ['course_enrollments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_enrollment_lesson')
    )
    op.create_index(op.f('ix_lesson_progress_enrollment_id'), 'lesson_progress', ['enrollment_id'], unique=False)
    op.create_index(op.f('ix_lesson_progress_lesson_id'), 'lesson_progress', ['lesson_id'], unique=False)
    
    # Create quiz_attempts table
    op.create_table('quiz_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('questions_answered', sa.Integer(), nullable=False),
        sa.Column('questions_correct', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['enrollment_id'], ['course_enrollments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_attempts_quiz_id'), 'quiz_attempts', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_quiz_attempts_user_id'), 'quiz_attempts', ['user_id'], unique=False)
    
    # Create quiz_answers table
    op.create_table('quiz_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer', sa.JSON(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_attempt_question')
    )
    op.create_index(op.f('ix_quiz_answers_attempt_id'), 'quiz_answers', ['attempt_id'], unique=False)
    
    # Create course_reviews table
    op.create_table('course_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('helpful_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['course_enrollments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_review')
    )
    op.create_index(op.f('ix_course_reviews_course_id'), 'course_reviews', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_reviews_user_id'), 'course_reviews', ['user_id'], unique=False)
    
    # Create course_announcements table
    op.create_table('course_announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_announcements_course_id'), 'course_announcements', ['course_id'], unique=False)
    
    # Create alias view for backward compatibility
    op.execute("""
        CREATE VIEW user_course_progress AS
        SELECT * FROM course_enrollments
    """)


def downgrade() -> None:
    # Drop view
    op.execute("DROP VIEW IF EXISTS user_course_progress")
    
    # Drop tables in reverse order
    op.drop_table('course_announcements')
    op.drop_table('course_reviews')
    op.drop_table('quiz_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('lesson_progress')
    op.drop_table('module_progress')
    op.drop_table('course_enrollments')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
    op.drop_table('course_content')
    op.drop_table('lessons')
    op.drop_table('modules')
    op.drop_table('courses')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS progressstatus")
    op.execute("DROP TYPE IF EXISTS coursestatus")
    op.execute("DROP TYPE IF EXISTS difficultylevel")
    op.execute("DROP TYPE IF EXISTS contenttype")