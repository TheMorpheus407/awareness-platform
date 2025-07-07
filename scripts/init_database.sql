-- Cybersecurity Awareness Platform Database Initialization Script
-- This script is idempotent and can be run multiple times safely

-- Create database if not exists (run this separately with superuser privileges)
-- CREATE DATABASE IF NOT EXISTS cybersecurity_awareness;

-- Use the database
-- \c cybersecurity_awareness;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing types if they exist (for idempotency)
DROP TYPE IF EXISTS company_size CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS company_status CASCADE;
DROP TYPE IF EXISTS course_category CASCADE;
DROP TYPE IF EXISTS course_status CASCADE;
DROP TYPE IF EXISTS course_difficulty CASCADE;
DROP TYPE IF EXISTS campaign_status CASCADE;
DROP TYPE IF EXISTS template_category CASCADE;
DROP TYPE IF EXISTS assignment_status CASCADE;
DROP TYPE IF EXISTS quiz_question_type CASCADE;
DROP TYPE IF EXISTS certificate_status CASCADE;
DROP TYPE IF EXISTS notification_type CASCADE;
DROP TYPE IF EXISTS notification_status CASCADE;
DROP TYPE IF EXISTS audit_action CASCADE;
DROP TYPE IF EXISTS compliance_framework CASCADE;

-- Create enum types
CREATE TYPE company_size AS ENUM ('small', 'medium', 'large', 'enterprise');
CREATE TYPE user_role AS ENUM ('system_admin', 'company_admin', 'manager', 'employee');
CREATE TYPE company_status AS ENUM ('trial', 'active', 'suspended', 'cancelled');
CREATE TYPE course_category AS ENUM ('general_awareness', 'phishing', 'passwords', 'data_protection', 'compliance', 'incident_response', 'social_engineering', 'network_security', 'mobile_security', 'cloud_security');
CREATE TYPE course_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE course_difficulty AS ENUM ('beginner', 'intermediate', 'advanced');
CREATE TYPE campaign_status AS ENUM ('draft', 'scheduled', 'active', 'completed', 'cancelled');
CREATE TYPE template_category AS ENUM ('credential_harvesting', 'malware', 'business_email_compromise', 'social_media', 'invoice_fraud', 'tech_support', 'prize_scam', 'job_offer');
CREATE TYPE assignment_status AS ENUM ('assigned', 'in_progress', 'completed', 'overdue');
CREATE TYPE quiz_question_type AS ENUM ('single_choice', 'multiple_choice', 'true_false');
CREATE TYPE certificate_status AS ENUM ('pending', 'issued', 'revoked');
CREATE TYPE notification_type AS ENUM ('course_assigned', 'course_reminder', 'course_completed', 'phishing_campaign', 'certificate_issued', 'system_announcement');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'read', 'failed');
CREATE TYPE audit_action AS ENUM ('create', 'update', 'delete', 'login', 'logout', 'view', 'export', 'import');
CREATE TYPE compliance_framework AS ENUM ('nis2', 'gdpr', 'iso27001', 'tisax', 'sox', 'hipaa');

-- Drop existing tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS phishing_click_logs CASCADE;
DROP TABLE IF EXISTS phishing_campaign_users CASCADE;
DROP TABLE IF EXISTS phishing_campaigns CASCADE;
DROP TABLE IF EXISTS phishing_templates CASCADE;
DROP TABLE IF EXISTS certificates CASCADE;
DROP TABLE IF EXISTS quiz_attempts CASCADE;
DROP TABLE IF EXISTS quiz_answers CASCADE;
DROP TABLE IF EXISTS quiz_questions CASCADE;
DROP TABLE IF EXISTS course_progress CASCADE;
DROP TABLE IF EXISTS course_assignments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS password_reset_tokens CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS compliance_reports CASCADE;
DROP TABLE IF EXISTS company_settings CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

-- Create companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    size company_size NOT NULL DEFAULT 'small',
    status company_status NOT NULL DEFAULT 'trial',
    industry VARCHAR(100),
    country VARCHAR(2) NOT NULL DEFAULT 'DE',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Berlin',
    logo_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#1976d2',
    secondary_color VARCHAR(7) DEFAULT '#dc004e',
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    max_users INTEGER NOT NULL DEFAULT 50,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL DEFAULT 'employee',
    department VARCHAR(100),
    job_title VARCHAR(100),
    phone VARCHAR(50),
    avatar_url TEXT,
    language VARCHAR(5) NOT NULL DEFAULT 'de',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create courses table
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category course_category NOT NULL,
    difficulty course_difficulty NOT NULL DEFAULT 'beginner',
    status course_status NOT NULL DEFAULT 'draft',
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    passing_score INTEGER NOT NULL DEFAULT 70 CHECK (passing_score >= 0 AND passing_score <= 100),
    youtube_video_id VARCHAR(50),
    thumbnail_url TEXT,
    tags TEXT[],
    prerequisites UUID[],
    is_mandatory BOOLEAN NOT NULL DEFAULT false,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE
);

-- Create course assignments table
CREATE TABLE course_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id),
    status assignment_status NOT NULL DEFAULT 'assigned',
    due_date DATE NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(course_id, user_id)
);

-- Create course progress table
CREATE TABLE course_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES course_assignments(id) ON DELETE SET NULL,
    progress_percentage INTEGER NOT NULL DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    video_progress_seconds INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, course_id)
);

-- Create quiz questions table
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type quiz_question_type NOT NULL DEFAULT 'single_choice',
    options JSONB NOT NULL,
    correct_answers TEXT[] NOT NULL,
    explanation TEXT,
    points INTEGER NOT NULL DEFAULT 1,
    order_index INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create quiz attempts table
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES course_assignments(id) ON DELETE SET NULL,
    score INTEGER NOT NULL DEFAULT 0,
    total_points INTEGER NOT NULL DEFAULT 0,
    percentage INTEGER NOT NULL DEFAULT 0,
    passed BOOLEAN NOT NULL DEFAULT false,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create quiz answers table
CREATE TABLE quiz_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attempt_id UUID NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    selected_answers TEXT[],
    is_correct BOOLEAN NOT NULL DEFAULT false,
    points_earned INTEGER NOT NULL DEFAULT 0,
    answered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create certificates table
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    certificate_number VARCHAR(50) NOT NULL UNIQUE,
    status certificate_status NOT NULL DEFAULT 'pending',
    issued_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason TEXT,
    pdf_url TEXT,
    verification_url TEXT,
    metadata JSONB,
    UNIQUE(user_id, course_id)
);

-- Create phishing templates table
CREATE TABLE phishing_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category template_category NOT NULL,
    difficulty course_difficulty NOT NULL DEFAULT 'beginner',
    subject VARCHAR(255) NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    sender_email VARCHAR(255) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    landing_page_html TEXT,
    indicators TEXT[],
    education_content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create phishing campaigns table
CREATE TABLE phishing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    template_id UUID NOT NULL REFERENCES phishing_templates(id),
    status campaign_status NOT NULL DEFAULT 'draft',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    landing_page_url TEXT,
    tracking_pixel_url TEXT,
    redirect_url TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create phishing campaign users table
CREATE TABLE phishing_campaign_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES phishing_campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_sent BOOLEAN NOT NULL DEFAULT false,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_opened BOOLEAN NOT NULL DEFAULT false,
    email_opened_at TIMESTAMP WITH TIME ZONE,
    link_clicked BOOLEAN NOT NULL DEFAULT false,
    link_clicked_at TIMESTAMP WITH TIME ZONE,
    reported_phishing BOOLEAN NOT NULL DEFAULT false,
    reported_at TIMESTAMP WITH TIME ZONE,
    tracking_token VARCHAR(255) NOT NULL UNIQUE,
    UNIQUE(campaign_id, user_id)
);

-- Create phishing click logs table
CREATE TABLE phishing_click_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_user_id UUID NOT NULL REFERENCES phishing_campaign_users(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    clicked_url TEXT,
    referer TEXT,
    action VARCHAR(50) NOT NULL,
    clicked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    status notification_status NOT NULL DEFAULT 'pending',
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create company settings table
CREATE TABLE company_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, setting_key)
);

-- Create compliance reports table
CREATE TABLE compliance_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    framework compliance_framework NOT NULL,
    report_date DATE NOT NULL,
    compliance_score INTEGER NOT NULL CHECK (compliance_score >= 0 AND compliance_score <= 100),
    findings JSONB,
    recommendations JSONB,
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pdf_url TEXT
);

-- Create user sessions table for session management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create password reset tokens table
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

CREATE INDEX idx_courses_category ON courses(category);
CREATE INDEX idx_courses_status ON courses(status);
CREATE INDEX idx_courses_is_mandatory ON courses(is_mandatory);

CREATE INDEX idx_course_assignments_user_id ON course_assignments(user_id);
CREATE INDEX idx_course_assignments_course_id ON course_assignments(course_id);
CREATE INDEX idx_course_assignments_status ON course_assignments(status);
CREATE INDEX idx_course_assignments_due_date ON course_assignments(due_date);

CREATE INDEX idx_course_progress_user_id ON course_progress(user_id);
CREATE INDEX idx_course_progress_course_id ON course_progress(course_id);

CREATE INDEX idx_quiz_questions_course_id ON quiz_questions(course_id);
CREATE INDEX idx_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX idx_quiz_attempts_course_id ON quiz_attempts(course_id);

CREATE INDEX idx_certificates_user_id ON certificates(user_id);
CREATE INDEX idx_certificates_course_id ON certificates(course_id);
CREATE INDEX idx_certificates_certificate_number ON certificates(certificate_number);

CREATE INDEX idx_phishing_campaigns_company_id ON phishing_campaigns(company_id);
CREATE INDEX idx_phishing_campaigns_status ON phishing_campaigns(status);
CREATE INDEX idx_phishing_campaign_users_campaign_id ON phishing_campaign_users(campaign_id);
CREATE INDEX idx_phishing_campaign_users_user_id ON phishing_campaign_users(user_id);
CREATE INDEX idx_phishing_campaign_users_tracking_token ON phishing_campaign_users(tracking_token);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_scheduled_for ON notifications(scheduled_for);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update timestamp triggers
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quiz_questions_updated_at BEFORE UPDATE ON quiz_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_phishing_templates_updated_at BEFORE UPDATE ON phishing_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_phishing_campaigns_updated_at BEFORE UPDATE ON phishing_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_settings_updated_at BEFORE UPDATE ON company_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial seed data
-- Create default company
INSERT INTO companies (
    id,
    name,
    domain,
    size,
    status,
    industry,
    country,
    timezone,
    max_users,
    trial_ends_at,
    subscription_ends_at
) VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
    'Bootstrap Academy GmbH',
    'bootstrap-academy.com',
    'small',
    'active',
    'Education',
    'DE',
    'Europe/Berlin',
    100,
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    CURRENT_TIMESTAMP + INTERVAL '365 days'
) ON CONFLICT (domain) DO NOTHING;

-- Create system admin user (password: Admin123!@#)
INSERT INTO users (
    id,
    company_id,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    department,
    job_title,
    is_active,
    email_verified,
    email_verified_at
) VALUES (
    'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
    'admin@bootstrap-academy.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYTN4sUqfK',
    'System',
    'Administrator',
    'system_admin',
    'IT',
    'System Administrator',
    true,
    true,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- Insert default company settings
INSERT INTO company_settings (company_id, setting_key, setting_value) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'phishing_enabled', 'true'::jsonb),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'auto_assign_courses', 'true'::jsonb),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'reminder_days_before_due', '7'::jsonb),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'certificate_validity_days', '365'::jsonb),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'minimum_password_length', '12'::jsonb),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'session_timeout_minutes', '30'::jsonb)
ON CONFLICT (company_id, setting_key) DO NOTHING;

-- Create sample phishing templates
INSERT INTO phishing_templates (
    name,
    category,
    difficulty,
    subject,
    sender_name,
    sender_email,
    html_content,
    text_content,
    landing_page_html,
    indicators,
    education_content
) VALUES
(
    'Microsoft Password Reset',
    'credential_harvesting',
    'beginner',
    'Action Required: Reset Your Microsoft Password',
    'Microsoft Security',
    'security@microsoft-support.com',
    '<html><body><h2>Microsoft Security Alert</h2><p>We detected unusual activity on your account. Please reset your password immediately.</p><a href="{{PHISHING_URL}}">Reset Password Now</a></body></html>',
    'Microsoft Security Alert\n\nWe detected unusual activity on your account. Please reset your password immediately.\n\nClick here to reset: {{PHISHING_URL}}',
    '<html><body><h2>This was a phishing simulation!</h2><p>You clicked on a suspicious link. Here''s what you should have noticed...</p></body></html>',
    ARRAY['Suspicious sender domain', 'Generic greeting', 'Urgency tactics', 'Suspicious URL'],
    'Always verify the sender''s email address. Microsoft will never ask you to reset your password via email with urgent language.'
),
(
    'IT Support Update',
    'tech_support',
    'intermediate',
    'IT Support: System Update Required',
    'IT Department',
    'it-support@company-updates.net',
    '<html><body><h2>Important System Update</h2><p>Dear User,</p><p>A critical security update is available for your computer. Install it now to protect your data.</p><a href="{{PHISHING_URL}}">Download Update</a></body></html>',
    'Important System Update\n\nDear User,\n\nA critical security update is available for your computer. Install it now to protect your data.\n\nDownload here: {{PHISHING_URL}}',
    '<html><body><h2>Phishing Simulation Alert!</h2><p>This was a test. Real IT updates come through official channels, not email links.</p></body></html>',
    ARRAY['External sender', 'Generic greeting', 'Direct download link', 'Urgency without details'],
    'IT updates are typically pushed automatically or announced through official company channels, not via email links.'
)
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust based on your PostgreSQL setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;

-- Add helpful comments
COMMENT ON TABLE companies IS 'Organizations using the cybersecurity awareness platform';
COMMENT ON TABLE users IS 'Platform users including admins, managers, and employees';
COMMENT ON TABLE courses IS 'Training courses and educational content';
COMMENT ON TABLE phishing_campaigns IS 'Phishing simulation campaigns for security training';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for compliance and security';
COMMENT ON COLUMN users.role IS 'User role determining access permissions: system_admin > company_admin > manager > employee';
COMMENT ON COLUMN courses.passing_score IS 'Minimum score percentage required to pass the course (0-100)';
COMMENT ON COLUMN phishing_campaign_users.tracking_token IS 'Unique token for tracking email opens and clicks without exposing user identity';