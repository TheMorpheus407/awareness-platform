# Datenbank Spezifikation - Cybersecurity Awareness Platform
**Version 1.0 | PostgreSQL 15+**

## 1. Übersicht

### 1.1 Datenbank-Konfiguration
```sql
-- Datenbank erstellen
CREATE DATABASE cybersec_awareness
    WITH 
    OWNER = cybersec_admin
    ENCODING = 'UTF8'
    LC_COLLATE = 'de_DE.UTF-8'
    LC_CTYPE = 'de_DE.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Extensions aktivieren
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Für Fuzzy Text Search
```

### 1.2 Schemas
```sql
-- Haupt-Schema für Anwendungsdaten
CREATE SCHEMA IF NOT EXISTS app;

-- Schema für Audit/Logging
CREATE SCHEMA IF NOT EXISTS audit;

-- Schema für Reporting Views
CREATE SCHEMA IF NOT EXISTS reporting;
```

## 2. Tabellen-Definitionen

### 2.1 Companies (Unternehmen)
```sql
CREATE TABLE app.companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    industry VARCHAR(100),
    size VARCHAR(50) CHECK (size IN ('small', 'medium', 'large', 'enterprise')),
    
    -- Compliance Profile
    compliance_requirements JSONB DEFAULT '[]'::jsonb,
    -- Beispiel: ["nis2", "dsgvo", "iso27001", "tisax"]
    
    -- Settings
    settings JSONB DEFAULT '{
        "phishing_frequency": "monthly",
        "reminder_days": [3, 7, 14],
        "auto_assign_courses": true,
        "language": "de"
    }'::jsonb,
    
    -- Subscription
    subscription_tier VARCHAR(50) DEFAULT 'trial',
    subscription_valid_until TIMESTAMP WITH TIME ZONE,
    max_users INTEGER,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT company_domain_format CHECK (domain ~ '^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
);

CREATE INDEX idx_companies_domain ON app.companies(domain);
CREATE INDEX idx_companies_subscription ON app.companies(subscription_valid_until);
CREATE INDEX idx_companies_compliance ON app.companies USING GIN(compliance_requirements);
```

### 2.2 Users (Benutzer)
```sql
CREATE TABLE app.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES app.companies(id) ON DELETE CASCADE,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL DEFAULT 'employee' CHECK (role IN ('admin', 'manager', 'employee')),
    department VARCHAR(100),
    employee_id VARCHAR(100),
    
    -- Security Metrics
    risk_score DECIMAL(5,2) DEFAULT 0.0 CHECK (risk_score >= 0 AND risk_score <= 100),
    last_training_date TIMESTAMP WITH TIME ZONE,
    phishing_click_rate DECIMAL(5,2) DEFAULT 0.0,
    training_completion_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- 2FA
    totp_secret VARCHAR(255),
    totp_enabled BOOLEAN DEFAULT false,
    
    -- Session Management
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    
    -- Constraints
    CONSTRAINT user_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_company ON app.users(company_id);
CREATE INDEX idx_users_email ON app.users(email);
CREATE INDEX idx_users_department ON app.users(company_id, department);
CREATE INDEX idx_users_risk_score ON app.users(company_id, risk_score DESC);
CREATE INDEX idx_users_active ON app.users(company_id, is_active) WHERE is_active = true;
```

### 2.3 Courses (Kurse)
```sql
CREATE TABLE app.courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic Info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INTEGER DEFAULT 10 CHECK (duration_minutes > 0),
    difficulty VARCHAR(50) CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    
    -- Content
    youtube_video_id VARCHAR(50),
    content_markdown TEXT,
    thumbnail_url VARCHAR(500),
    
    -- Quiz
    quiz_questions JSONB DEFAULT '[]'::jsonb,
    /* Struktur:
    [{
        "id": "q1",
        "question": "Was ist Phishing?",
        "options": [
            {"id": "a", "text": "Eine Angelmethode"},
            {"id": "b", "text": "Ein Cyberangriff"},
            {"id": "c", "text": "Ein Computervirus"},
            {"id": "d", "text": "Eine Software"}
        ],
        "correct_answer": "b",
        "explanation": "Phishing ist eine Betrugsmethode..."
    }]
    */
    passing_score INTEGER DEFAULT 80 CHECK (passing_score >= 0 AND passing_score <= 100),
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    compliance_tags TEXT[] DEFAULT '{}',
    target_roles TEXT[] DEFAULT '{}',
    target_departments TEXT[] DEFAULT '{}',
    
    -- Localization
    available_languages TEXT[] DEFAULT '{de}',
    translations JSONB DEFAULT '{}'::jsonb,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_mandatory BOOLEAN DEFAULT false,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES app.courses(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES app.users(id),
    
    -- Constraints
    CONSTRAINT course_valid_dates CHECK (valid_until IS NULL OR valid_until > valid_from)
);

CREATE INDEX idx_courses_active ON app.courses(is_active);
CREATE INDEX idx_courses_tags ON app.courses USING GIN(tags);
CREATE INDEX idx_courses_compliance ON app.courses USING GIN(compliance_tags);
CREATE INDEX idx_courses_youtube ON app.courses(youtube_video_id);
```

### 2.4 User Course Progress (Kursfortschritt)
```sql
CREATE TABLE app.user_course_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES app.courses(id),
    company_id UUID NOT NULL REFERENCES app.companies(id),
    
    -- Assignment
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES app.users(id),
    due_date TIMESTAMP WITH TIME ZONE,
    is_mandatory BOOLEAN DEFAULT false,
    
    -- Progress
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Video Progress
    video_progress_seconds INTEGER DEFAULT 0,
    video_total_seconds INTEGER,
    video_completion_percentage DECIMAL(5,2) DEFAULT 0.0,
    
    -- Quiz Results
    quiz_attempts INTEGER DEFAULT 0,
    quiz_score DECIMAL(5,2),
    quiz_passed BOOLEAN DEFAULT false,
    quiz_answers JSONB,
    
    -- Certificate
    certificate_id UUID,
    certificate_issued_at TIMESTAMP WITH TIME ZONE,
    certificate_url VARCHAR(500),
    
    -- Metadata
    time_spent_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_user_course UNIQUE (user_id, course_id),
    CONSTRAINT valid_video_progress CHECK (video_progress_seconds <= video_total_seconds)
);

CREATE INDEX idx_progress_user ON app.user_course_progress(user_id);
CREATE INDEX idx_progress_status ON app.user_course_progress(company_id, status);
CREATE INDEX idx_progress_due ON app.user_course_progress(company_id, due_date) WHERE status != 'completed';
CREATE INDEX idx_progress_mandatory ON app.user_course_progress(company_id, is_mandatory) WHERE is_mandatory = true;
```

### 2.5 Phishing Templates (Phishing-Vorlagen)
```sql
CREATE TABLE app.phishing_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) CHECK (category IN ('credential', 'attachment', 'link', 'mixed')),
    difficulty VARCHAR(50) CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    
    -- Email Content
    subject VARCHAR(500) NOT NULL,
    sender_name VARCHAR(255),
    sender_email VARCHAR(255),
    reply_to VARCHAR(255),
    html_content TEXT NOT NULL,
    text_content TEXT,
    
    -- Attachments (if any)
    attachment_name VARCHAR(255),
    attachment_type VARCHAR(50),
    
    -- Red Flags (für Training)
    red_flags JSONB DEFAULT '[]'::jsonb,
    /* Beispiel:
    [
        {"type": "sender", "description": "Absender-Domain stimmt nicht mit Anzeigename überein"},
        {"type": "urgency", "description": "Dringender Handlungsbedarf wird suggeriert"},
        {"type": "grammar", "description": "Rechtschreibfehler im Text"}
    ]
    */
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'de',
    tags TEXT[] DEFAULT '{}',
    industry_specific TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES app.users(id)
);

CREATE INDEX idx_templates_active ON app.phishing_templates(is_active);
CREATE INDEX idx_templates_category ON app.phishing_templates(category);
CREATE INDEX idx_templates_difficulty ON app.phishing_templates(difficulty);
```

### 2.6 Phishing Campaigns (Phishing-Kampagnen)
```sql
CREATE TABLE app.phishing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES app.companies(id) ON DELETE CASCADE,
    
    -- Campaign Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id UUID NOT NULL REFERENCES app.phishing_templates(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'running', 'completed', 'cancelled')),
    
    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Target Configuration
    target_groups JSONB DEFAULT '[]'::jsonb,
    -- Beispiel: ["all", "department:IT", "role:manager", "users:[uuid1,uuid2]"]
    excluded_users UUID[] DEFAULT '{}',
    total_recipients INTEGER DEFAULT 0,
    
    -- Settings
    landing_page_type VARCHAR(50) DEFAULT 'training' CHECK (landing_page_type IN ('training', 'warning', 'custom')),
    landing_page_content TEXT,
    track_duration_days INTEGER DEFAULT 7,
    send_training_immediately BOOLEAN DEFAULT true,
    
    -- Results Summary
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    links_clicked INTEGER DEFAULT 0,
    data_submitted INTEGER DEFAULT 0,
    reported_suspicious INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES app.users(id)
);

CREATE INDEX idx_campaigns_company ON app.phishing_campaigns(company_id);
CREATE INDEX idx_campaigns_status ON app.phishing_campaigns(status);
CREATE INDEX idx_campaigns_scheduled ON app.phishing_campaigns(scheduled_at) WHERE status = 'scheduled';
```

### 2.7 Phishing Results (Phishing-Ergebnisse)
```sql
CREATE TABLE app.phishing_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES app.phishing_campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    
    -- Tracking ID für anonyme Links
    tracking_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    
    -- Email Status
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_delivered_at TIMESTAMP WITH TIME ZONE,
    email_bounced BOOLEAN DEFAULT false,
    
    -- User Actions
    email_opened_at TIMESTAMP WITH TIME ZONE,
    email_open_count INTEGER DEFAULT 0,
    
    link_clicked_at TIMESTAMP WITH TIME ZONE,
    link_click_count INTEGER DEFAULT 0,
    
    data_submitted_at TIMESTAMP WITH TIME ZONE,
    submitted_data JSONB, -- Verschlüsselt speichern!
    
    reported_at TIMESTAMP WITH TIME ZONE,
    report_method VARCHAR(50), -- 'button', 'forward', 'manual'
    
    -- Technical Details
    ip_addresses INET[] DEFAULT '{}',
    user_agents TEXT[] DEFAULT '{}',
    
    -- Training
    training_required BOOLEAN DEFAULT false,
    training_completed BOOLEAN DEFAULT false,
    training_completed_at TIMESTAMP WITH TIME ZONE,
    training_score DECIMAL(5,2),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_campaign_user UNIQUE (campaign_id, user_id)
);

CREATE INDEX idx_results_campaign ON app.phishing_results(campaign_id);
CREATE INDEX idx_results_user ON app.phishing_results(user_id);
CREATE INDEX idx_results_tracking ON app.phishing_results(tracking_id);
CREATE INDEX idx_results_clicked ON app.phishing_results(campaign_id) WHERE link_clicked_at IS NOT NULL;
```

### 2.8 Audit Logs (Audit-Protokoll)
```sql
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Actor
    user_id UUID REFERENCES app.users(id),
    company_id UUID REFERENCES app.companies(id),
    
    -- Action
    action VARCHAR(100) NOT NULL,
    -- Beispiele: 'user.login', 'user.logout', 'course.completed', 'phishing.clicked', 'report.generated'
    
    -- Resource
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- Details
    ip_address INET,
    user_agent TEXT,
    
    -- Request/Response
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    response_status INTEGER,
    
    -- Additional Data
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Compliance Fields
    data_classification VARCHAR(50) DEFAULT 'internal',
    retention_until TIMESTAMP WITH TIME ZONE,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Partitioning by month
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Monatliche Partitionen erstellen
CREATE TABLE audit.audit_logs_2025_01 PARTITION OF audit.audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit.audit_logs_2025_02 PARTITION OF audit.audit_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Index für Partitionen
CREATE INDEX idx_audit_logs_user ON audit.audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_company ON audit.audit_logs(company_id, created_at);
CREATE INDEX idx_audit_logs_action ON audit.audit_logs(action, created_at);
CREATE INDEX idx_audit_logs_resource ON audit.audit_logs(resource_type, resource_id, created_at);
```

### 2.9 Notifications (Benachrichtigungen)
```sql
CREATE TABLE app.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Recipient
    user_id UUID REFERENCES app.users(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES app.companies(id),
    
    -- Type & Content
    type VARCHAR(50) NOT NULL,
    -- 'course_assigned', 'course_reminder', 'course_overdue', 'phishing_result', 'certificate_ready'
    
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Actions
    action_type VARCHAR(50),
    action_url VARCHAR(500),
    action_data JSONB,
    
    -- Delivery
    email_sent BOOLEAN DEFAULT false,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Auto-cleanup old notifications
    CONSTRAINT notification_expiry CHECK (expires_at IS NULL OR expires_at > created_at)
);

CREATE INDEX idx_notifications_user ON app.notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_expires ON app.notifications(expires_at) WHERE expires_at IS NOT NULL;
```

### 2.10 Reports Cache (Report-Cache)
```sql
CREATE TABLE app.reports_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES app.companies(id) ON DELETE CASCADE,
    
    -- Report Identification
    report_type VARCHAR(50) NOT NULL,
    -- 'compliance_nis2', 'compliance_dsgvo', 'executive_dashboard', 'risk_analysis'
    
    parameters JSONB DEFAULT '{}'::jsonb,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    
    -- Content
    report_data JSONB NOT NULL,
    format VARCHAR(20) DEFAULT 'json',
    
    -- Validity
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Usage
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    generation_time_ms INTEGER,
    data_points_count INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_cache_key ON app.reports_cache(cache_key);
CREATE INDEX idx_reports_validity ON app.reports_cache(company_id, valid_until);
CREATE INDEX idx_reports_type ON app.reports_cache(company_id, report_type);
```

## 3. Views für Reporting

### 3.1 Company Risk Overview
```sql
CREATE OR REPLACE VIEW reporting.company_risk_overview AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    COUNT(DISTINCT u.id) as total_users,
    AVG(u.risk_score) as avg_risk_score,
    COUNT(DISTINCT u.id) FILTER (WHERE u.risk_score > 70) as high_risk_users,
    AVG(u.training_completion_rate) as avg_training_completion,
    AVG(u.phishing_click_rate) as avg_phishing_click_rate,
    MAX(u.last_training_date) as last_training_activity
FROM app.companies c
LEFT JOIN app.users u ON c.id = u.company_id AND u.is_active = true
GROUP BY c.id, c.name;
```

### 3.2 User Training Status
```sql
CREATE OR REPLACE VIEW reporting.user_training_status AS
SELECT 
    u.id as user_id,
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    u.department,
    u.role,
    COUNT(DISTINCT ucp.course_id) FILTER (WHERE ucp.status = 'completed') as courses_completed,
    COUNT(DISTINCT ucp.course_id) FILTER (WHERE ucp.is_mandatory AND ucp.status = 'completed') as mandatory_completed,
    COUNT(DISTINCT ucp.course_id) FILTER (WHERE ucp.is_mandatory) as mandatory_total,
    MIN(ucp.due_date) FILTER (WHERE ucp.status != 'completed') as next_due_date,
    u.risk_score,
    u.last_training_date
FROM app.users u
LEFT JOIN app.user_course_progress ucp ON u.id = ucp.user_id
WHERE u.is_active = true
GROUP BY u.id, u.email, u.first_name, u.last_name, u.department, u.role, u.risk_score, u.last_training_date;
```

### 3.3 Phishing Campaign Performance
```sql
CREATE OR REPLACE VIEW reporting.phishing_campaign_performance AS
SELECT 
    pc.id as campaign_id,
    pc.name as campaign_name,
    pc.company_id,
    pt.difficulty,
    pt.category,
    pc.total_recipients,
    pc.emails_sent,
    pc.emails_opened,
    pc.links_clicked,
    pc.data_submitted,
    pc.reported_suspicious,
    CASE 
        WHEN pc.emails_sent > 0 THEN 
            ROUND((pc.links_clicked::DECIMAL / pc.emails_sent) * 100, 2)
        ELSE 0 
    END as click_rate,
    CASE 
        WHEN pc.emails_sent > 0 THEN 
            ROUND((pc.reported_suspicious::DECIMAL / pc.emails_sent) * 100, 2)
        ELSE 0 
    END as report_rate,
    pc.status,
    pc.completed_at
FROM app.phishing_campaigns pc
JOIN app.phishing_templates pt ON pc.template_id = pt.id;
```

### 3.4 Compliance Status View
```sql
CREATE OR REPLACE VIEW reporting.compliance_status AS
WITH user_compliance AS (
    SELECT 
        u.company_id,
        u.id as user_id,
        u.role,
        MAX(ucp.completed_at) as last_training_completed,
        COUNT(DISTINCT ucp.course_id) FILTER (
            WHERE ucp.status = 'completed' 
            AND ucp.completed_at > CURRENT_TIMESTAMP - INTERVAL '1 year'
        ) as annual_trainings_completed
    FROM app.users u
    LEFT JOIN app.user_course_progress ucp ON u.id = ucp.user_id
    WHERE u.is_active = true
    GROUP BY u.company_id, u.id, u.role
),
phishing_stats AS (
    SELECT 
        pc.company_id,
        COUNT(DISTINCT pc.id) FILTER (
            WHERE pc.status = 'completed' 
            AND pc.completed_at > CURRENT_TIMESTAMP - INTERVAL '3 months'
        ) as quarterly_phishing_tests
    FROM app.phishing_campaigns pc
    GROUP BY pc.company_id
)
SELECT 
    c.id as company_id,
    c.name as company_name,
    c.compliance_requirements,
    
    -- NIS-2 Compliance
    CASE 
        WHEN 'nis2' = ANY(c.compliance_requirements) THEN
            CASE
                WHEN COUNT(uc.user_id) FILTER (WHERE uc.role = 'admin' AND uc.annual_trainings_completed > 0) > 0
                AND AVG(uc.annual_trainings_completed) >= 1
                AND COALESCE(ps.quarterly_phishing_tests, 0) >= 1
                THEN 'compliant'
                ELSE 'non-compliant'
            END
        ELSE 'not-applicable'
    END as nis2_status,
    
    -- DSGVO Compliance
    CASE 
        WHEN 'dsgvo' = ANY(c.compliance_requirements) THEN
            CASE
                WHEN AVG(uc.annual_trainings_completed) >= 1
                THEN 'compliant'
                ELSE 'non-compliant'
            END
        ELSE 'not-applicable'
    END as dsgvo_status,
    
    -- Metrics
    COUNT(DISTINCT uc.user_id) as total_active_users,
    AVG(uc.annual_trainings_completed) as avg_annual_trainings,
    COALESCE(ps.quarterly_phishing_tests, 0) as quarterly_phishing_tests
    
FROM app.companies c
LEFT JOIN user_compliance uc ON c.id = uc.company_id
LEFT JOIN phishing_stats ps ON c.id = ps.company_id
GROUP BY c.id, c.name, c.compliance_requirements, ps.quarterly_phishing_tests;
```

## 4. Funktionen und Prozeduren

### 4.1 Update User Risk Score
```sql
CREATE OR REPLACE FUNCTION app.update_user_risk_score(p_user_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    v_risk_score DECIMAL;
    v_phishing_performance DECIMAL;
    v_training_performance DECIMAL;
    v_time_factor DECIMAL;
    v_role_factor DECIMAL;
BEGIN
    -- Phishing Performance (40% weight)
    SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN 50
            ELSE (COUNT(*) FILTER (WHERE link_clicked_at IS NOT NULL)::DECIMAL / COUNT(*)) * 100
        END INTO v_phishing_performance
    FROM app.phishing_results
    WHERE user_id = p_user_id
    AND campaign_id IN (
        SELECT id FROM app.phishing_campaigns 
        WHERE completed_at > CURRENT_TIMESTAMP - INTERVAL '6 months'
    );
    
    -- Training Performance (30% weight)
    SELECT 
        CASE 
            WHEN COUNT(*) FILTER (WHERE is_mandatory) = 0 THEN 100
            ELSE (COUNT(*) FILTER (WHERE status = 'completed' AND is_mandatory)::DECIMAL / 
                  COUNT(*) FILTER (WHERE is_mandatory)) * 100
        END INTO v_training_performance
    FROM app.user_course_progress
    WHERE user_id = p_user_id;
    
    -- Time Since Last Training (20% weight)
    SELECT 
        CASE 
            WHEN MAX(completed_at) IS NULL THEN 100
            WHEN MAX(completed_at) > CURRENT_TIMESTAMP - INTERVAL '3 months' THEN 0
            WHEN MAX(completed_at) > CURRENT_TIMESTAMP - INTERVAL '6 months' THEN 25
            WHEN MAX(completed_at) > CURRENT_TIMESTAMP - INTERVAL '12 months' THEN 50
            ELSE 100
        END INTO v_time_factor
    FROM app.user_course_progress
    WHERE user_id = p_user_id AND status = 'completed';
    
    -- Role Factor (10% weight)
    SELECT 
        CASE role
            WHEN 'admin' THEN 20
            WHEN 'manager' THEN 10
            ELSE 0
        END INTO v_role_factor
    FROM app.users
    WHERE id = p_user_id;
    
    -- Calculate final risk score
    v_risk_score := (v_phishing_performance * 0.4) + 
                    ((100 - v_training_performance) * 0.3) +
                    (v_time_factor * 0.2) +
                    (v_role_factor * 0.1);
    
    -- Update user record
    UPDATE app.users 
    SET 
        risk_score = v_risk_score,
        phishing_click_rate = v_phishing_performance,
        training_completion_rate = v_training_performance,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_user_id;
    
    RETURN v_risk_score;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Assign Mandatory Courses
```sql
CREATE OR REPLACE FUNCTION app.assign_mandatory_courses(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_company_id UUID;
    v_user_role VARCHAR(50);
    v_user_department VARCHAR(100);
    v_compliance_requirements JSONB;
    v_assigned_count INTEGER := 0;
BEGIN
    -- Get user details
    SELECT company_id, role, department 
    INTO v_company_id, v_user_role, v_user_department
    FROM app.users 
    WHERE id = p_user_id;
    
    -- Get company compliance requirements
    SELECT compliance_requirements 
    INTO v_compliance_requirements
    FROM app.companies 
    WHERE id = v_company_id;
    
    -- Assign mandatory courses based on compliance and role
    INSERT INTO app.user_course_progress (
        user_id, course_id, company_id, is_mandatory, due_date
    )
    SELECT 
        p_user_id,
        c.id,
        v_company_id,
        true,
        CURRENT_TIMESTAMP + INTERVAL '30 days'
    FROM app.courses c
    WHERE c.is_active = true
    AND c.is_mandatory = true
    AND (
        -- General mandatory courses
        cardinality(c.target_roles) = 0 
        OR v_user_role = ANY(c.target_roles)
    )
    AND (
        -- Department specific
        cardinality(c.target_departments) = 0 
        OR v_user_department = ANY(c.target_departments)
    )
    AND (
        -- Compliance specific
        EXISTS (
            SELECT 1 
            FROM jsonb_array_elements_text(v_compliance_requirements) AS req
            WHERE req = ANY(c.compliance_tags)
        )
        OR cardinality(c.compliance_tags) = 0
    )
    ON CONFLICT (user_id, course_id) DO NOTHING;
    
    GET DIAGNOSTICS v_assigned_count = ROW_COUNT;
    
    RETURN v_assigned_count;
END;
$$ LANGUAGE plpgsql;
```

### 4.3 Generate Compliance Report Data
```sql
CREATE OR REPLACE FUNCTION app.generate_compliance_report(
    p_company_id UUID,
    p_report_type VARCHAR(50),
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
)
RETURNS JSONB AS $$
DECLARE
    v_report_data JSONB;
BEGIN
    CASE p_report_type
        WHEN 'nis2' THEN
            SELECT jsonb_build_object(
                'company_id', p_company_id,
                'report_type', 'nis2',
                'period', jsonb_build_object(
                    'start', p_start_date,
                    'end', p_end_date
                ),
                'management_training', (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'user_id', u.id,
                            'name', u.first_name || ' ' || u.last_name,
                            'role', u.role,
                            'trainings_completed', COUNT(ucp.id),
                            'last_training', MAX(ucp.completed_at)
                        )
                    )
                    FROM app.users u
                    LEFT JOIN app.user_course_progress ucp ON u.id = ucp.user_id
                        AND ucp.status = 'completed'
                        AND ucp.completed_at BETWEEN p_start_date AND p_end_date
                    WHERE u.company_id = p_company_id
                    AND u.role IN ('admin', 'manager')
                    GROUP BY u.id, u.first_name, u.last_name, u.role
                ),
                'phishing_tests', (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'campaign_name', pc.name,
                            'date', pc.completed_at,
                            'recipients', pc.total_recipients,
                            'click_rate', 
                                CASE WHEN pc.emails_sent > 0 
                                THEN ROUND((pc.links_clicked::DECIMAL / pc.emails_sent) * 100, 2)
                                ELSE 0 END
                        )
                    )
                    FROM app.phishing_campaigns pc
                    WHERE pc.company_id = p_company_id
                    AND pc.status = 'completed'
                    AND pc.completed_at BETWEEN p_start_date AND p_end_date
                ),
                'compliance_status', (
                    SELECT 
                        CASE
                            WHEN COUNT(*) FILTER (WHERE role IN ('admin', 'manager') AND trainings > 0) > 0
                            AND COUNT(*) FILTER (WHERE trainings = 0) = 0
                            THEN 'compliant'
                            ELSE 'non-compliant'
                        END
                    FROM (
                        SELECT u.role, COUNT(ucp.id) as trainings
                        FROM app.users u
                        LEFT JOIN app.user_course_progress ucp ON u.id = ucp.user_id
                            AND ucp.status = 'completed'
                            AND ucp.completed_at BETWEEN p_start_date AND p_end_date
                        WHERE u.company_id = p_company_id
                        AND u.is_active = true
                        GROUP BY u.id, u.role
                    ) user_training_stats
                ),
                'generated_at', CURRENT_TIMESTAMP
            ) INTO v_report_data;
            
        WHEN 'dsgvo' THEN
            -- DSGVO specific report logic
            v_report_data := jsonb_build_object(
                'report_type', 'dsgvo',
                'status', 'not_implemented'
            );
            
        ELSE
            v_report_data := jsonb_build_object(
                'error', 'Unknown report type'
            );
    END CASE;
    
    RETURN v_report_data;
END;
$$ LANGUAGE plpgsql;
```

## 5. Trigger

### 5.1 Updated Timestamp Trigger
```sql
CREATE OR REPLACE FUNCTION app.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON app.companies
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON app.users
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at_column();

-- ... weitere Trigger für andere Tabellen
```

### 5.2 Audit Log Trigger
```sql
CREATE OR REPLACE FUNCTION audit.log_user_action()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.audit_logs (
        user_id,
        company_id,
        action,
        resource_type,
        resource_id,
        metadata,
        created_at
    ) VALUES (
        current_setting('app.current_user_id', true)::UUID,
        current_setting('app.current_company_id', true)::UUID,
        TG_OP || '.' || TG_TABLE_NAME,
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        jsonb_build_object(
            'old', to_jsonb(OLD),
            'new', to_jsonb(NEW)
        ),
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to sensitive tables
CREATE TRIGGER audit_user_changes AFTER INSERT OR UPDATE OR DELETE ON app.users
    FOR EACH ROW EXECUTE FUNCTION audit.log_user_action();
```

### 5.3 Auto-assign Courses Trigger
```sql
CREATE OR REPLACE FUNCTION app.auto_assign_courses_on_user_create()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if company has auto-assign enabled
    IF EXISTS (
        SELECT 1 FROM app.companies 
        WHERE id = NEW.company_id 
        AND (settings->>'auto_assign_courses')::boolean = true
    ) THEN
        PERFORM app.assign_mandatory_courses(NEW.id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER assign_courses_new_user AFTER INSERT ON app.users
    FOR EACH ROW EXECUTE FUNCTION app.auto_assign_courses_on_user_create();
```

## 6. Indizes und Performance-Optimierung

### 6.1 Zusätzliche Performance-Indizes
```sql
-- Text Search für Kurse
CREATE INDEX idx_courses_title_search ON app.courses USING GIN(to_tsvector('german', title));
CREATE INDEX idx_courses_description_search ON app.courses USING GIN(to_tsvector('german', description));

-- JSON Indizes
CREATE INDEX idx_companies_settings_language ON app.companies ((settings->>'language'));
CREATE INDEX idx_phishing_results_submitted_data ON app.phishing_results USING GIN(submitted_data);

-- Partial Indizes für häufige Queries
CREATE INDEX idx_users_active_high_risk ON app.users(company_id, risk_score DESC) 
WHERE is_active = true AND risk_score > 70;

CREATE INDEX idx_progress_overdue ON app.user_course_progress(company_id, due_date) 
WHERE status != 'completed' AND due_date < CURRENT_TIMESTAMP;
```

### 6.2 Materialized Views für Performance
```sql
CREATE MATERIALIZED VIEW reporting.daily_company_metrics AS
SELECT 
    company_id,
    DATE(CURRENT_TIMESTAMP) as metric_date,
    COUNT(DISTINCT user_id) as active_users,
    AVG(risk_score) as avg_risk_score,
    SUM(CASE WHEN risk_score > 70 THEN 1 ELSE 0 END) as high_risk_count,
    COUNT(DISTINCT course_id) as courses_in_progress,
    COUNT(DISTINCT CASE WHEN status = 'completed' THEN course_id END) as courses_completed_today
FROM app.users u
JOIN app.user_course_progress ucp ON u.id = ucp.user_id
WHERE u.is_active = true
GROUP BY company_id;

-- Refresh täglich
CREATE INDEX idx_daily_metrics ON reporting.daily_company_metrics(company_id, metric_date);
```

## 7. Backup und Maintenance

### 7.1 Backup Strategie
```sql
-- Backup Konfiguration
-- Continuous Archiving mit WAL
-- Point-in-Time Recovery (PITR) enabled
-- Tägliche Base Backups um 02:00 Uhr
-- WAL Archive alle 5 Minuten

-- Backup Retention:
-- - Daily backups: 7 days
-- - Weekly backups: 4 weeks  
-- - Monthly backups: 12 months
```

### 7.2 Maintenance Tasks
```sql
-- Vacuum und Analyze Schedule
-- Daily: VACUUM ANALYZE on high-traffic tables
-- Weekly: VACUUM FREEZE on all tables
-- Monthly: REINDEX on frequently updated indexes

-- Partition Maintenance
CREATE OR REPLACE FUNCTION audit.create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE + interval '1 month');
    end_date := start_date + interval '1 month';
    partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS audit.%I PARTITION OF audit.audit_logs FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly via cron/pg_cron
```

## 8. Security Policies

### 8.1 Row Level Security
```sql
-- Enable RLS
ALTER TABLE app.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.user_course_progress ENABLE ROW LEVEL SECURITY;

-- Policies für Users
CREATE POLICY users_company_isolation ON app.users
    FOR ALL
    USING (company_id = current_setting('app.current_company_id')::UUID);

CREATE POLICY users_self_read ON app.users
    FOR SELECT
    USING (id = current_setting('app.current_user_id')::UUID);

-- Policies für Course Progress
CREATE POLICY progress_company_isolation ON app.user_course_progress
    FOR ALL
    USING (company_id = current_setting('app.current_company_id')::UUID);

CREATE POLICY progress_self_access ON app.user_course_progress
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

### 8.2 Encryption
```sql
-- Sensitive data encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt submitted phishing data
CREATE OR REPLACE FUNCTION app.encrypt_sensitive_data(p_data TEXT, p_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(
        pgp_sym_encrypt(p_data, p_key),
        'base64'
    );
END;
$$ LANGUAGE plpgsql;

-- Decrypt function (nur für autorisierte Zugriffe)
CREATE OR REPLACE FUNCTION app.decrypt_sensitive_data(p_data TEXT, p_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(
        decode(p_data, 'base64'),
        p_key
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 9. Monitoring Queries

### 9.1 Performance Monitoring
```sql
-- Slow Query Detection
CREATE OR REPLACE VIEW monitoring.slow_queries AS
SELECT 
    query,
    mean_exec_time,
    calls,
    total_exec_time,
    min_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000 -- queries slower than 1 second
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Table Bloat Check
CREATE OR REPLACE VIEW monitoring.table_bloat AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as external_size
FROM pg_tables
WHERE schemaname IN ('app', 'audit')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 9.2 Business Monitoring
```sql
-- Active Users per Company
CREATE OR REPLACE VIEW monitoring.active_users_per_company AS
SELECT 
    c.name as company_name,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT u.id) FILTER (WHERE u.last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days') as active_30d,
    COUNT(DISTINCT u.id) FILTER (WHERE u.last_login_at > CURRENT_TIMESTAMP - INTERVAL '7 days') as active_7d,
    COUNT(DISTINCT u.id) FILTER (WHERE u.last_login_at > CURRENT_TIMESTAMP - INTERVAL '1 day') as active_1d
FROM app.companies c
LEFT JOIN app.users u ON c.id = u.company_id AND u.is_active = true
GROUP BY c.id, c.name
ORDER BY active_7d DESC;
```

## 10. Datenbank-Rollen und Berechtigungen

### 10.1 Rollen-Setup
```sql
-- Application Role (für Backend)
CREATE ROLE cybersec_app WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE cybersec_awareness TO cybersec_app;
GRANT USAGE ON SCHEMA app, audit, reporting TO cybersec_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO cybersec_app;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO cybersec_app;
GRANT SELECT ON ALL TABLES IN SCHEMA reporting TO cybersec_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA app TO cybersec_app;

-- Read-Only Role (für Reporting)
CREATE ROLE cybersec_readonly WITH LOGIN PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE cybersec_awareness TO cybersec_readonly;
GRANT USAGE ON SCHEMA app, reporting TO cybersec_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA app, reporting TO cybersec_readonly;

-- Admin Role
CREATE ROLE cybersec_admin WITH LOGIN PASSWORD 'admin_password' SUPERUSER;
```

### 10.2 Connection Pooling
```sql
-- pgBouncer configuration recommendations
-- pool_mode = transaction
-- max_client_conn = 1000
-- default_pool_size = 25
-- min_pool_size = 10
-- reserve_pool_size = 5
-- server_lifetime = 3600
```