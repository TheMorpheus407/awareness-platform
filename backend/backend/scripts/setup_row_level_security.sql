-- Row Level Security (RLS) Setup for Multi-Tenant Isolation
-- This script implements company-based isolation for all relevant tables

-- Start transaction
BEGIN;

-- Enable RLS on all relevant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_course_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE phishing_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE phishing_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE phishing_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Create a function to get current user's company_id
CREATE OR REPLACE FUNCTION auth.current_user_company_id()
RETURNS UUID AS $$
DECLARE
    company_id UUID;
BEGIN
    -- Get company_id from current_setting
    -- This will be set by the application when a user authenticates
    company_id := current_setting('app.current_company_id', true)::UUID;
    RETURN company_id;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to check if current user is a system admin
CREATE OR REPLACE FUNCTION auth.is_system_admin()
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if the current user role is system_admin
    RETURN current_setting('app.current_user_role', true) = 'system_admin';
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS users_company_isolation ON users;
DROP POLICY IF EXISTS users_system_admin ON users;
DROP POLICY IF EXISTS companies_isolation ON companies;
DROP POLICY IF EXISTS companies_system_admin ON companies;
DROP POLICY IF EXISTS user_course_progress_isolation ON user_course_progress;
DROP POLICY IF EXISTS user_course_progress_system_admin ON user_course_progress;
DROP POLICY IF EXISTS phishing_campaigns_isolation ON phishing_campaigns;
DROP POLICY IF EXISTS phishing_campaigns_system_admin ON phishing_campaigns;
DROP POLICY IF EXISTS phishing_results_isolation ON phishing_results;
DROP POLICY IF EXISTS phishing_results_system_admin ON phishing_results;
DROP POLICY IF EXISTS phishing_templates_public ON phishing_templates;
DROP POLICY IF EXISTS phishing_templates_private ON phishing_templates;
DROP POLICY IF EXISTS phishing_templates_system_admin ON phishing_templates;
DROP POLICY IF EXISTS audit_logs_isolation ON audit_logs;
DROP POLICY IF EXISTS audit_logs_system_admin ON audit_logs;
DROP POLICY IF EXISTS analytics_events_isolation ON analytics_events;
DROP POLICY IF EXISTS analytics_events_system_admin ON analytics_events;

-- Users table policies
-- Regular users can only see users from their company
CREATE POLICY users_company_isolation ON users
    FOR ALL
    USING (company_id = auth.current_user_company_id());

-- System admins can see all users
CREATE POLICY users_system_admin ON users
    FOR ALL
    USING (auth.is_system_admin());

-- Companies table policies
-- Users can only see their own company
CREATE POLICY companies_isolation ON companies
    FOR SELECT
    USING (id = auth.current_user_company_id());

-- System admins can see and modify all companies
CREATE POLICY companies_system_admin ON companies
    FOR ALL
    USING (auth.is_system_admin());

-- User course progress policies
-- Users can only see progress from their company
CREATE POLICY user_course_progress_isolation ON user_course_progress
    FOR ALL
    USING (company_id = auth.current_user_company_id());

-- System admins can see all progress
CREATE POLICY user_course_progress_system_admin ON user_course_progress
    FOR ALL
    USING (auth.is_system_admin());

-- Phishing campaigns policies
-- Users can only see campaigns from their company
CREATE POLICY phishing_campaigns_isolation ON phishing_campaigns
    FOR ALL
    USING (company_id = auth.current_user_company_id());

-- System admins can see all campaigns
CREATE POLICY phishing_campaigns_system_admin ON phishing_campaigns
    FOR ALL
    USING (auth.is_system_admin());

-- Phishing results policies
-- Users can only see results from their company's campaigns
CREATE POLICY phishing_results_isolation ON phishing_results
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM phishing_campaigns pc
            WHERE pc.id = phishing_results.campaign_id
            AND pc.company_id = auth.current_user_company_id()
        )
    );

-- System admins can see all results
CREATE POLICY phishing_results_system_admin ON phishing_results
    FOR ALL
    USING (auth.is_system_admin());

-- Phishing templates policies
-- Public templates are visible to all
CREATE POLICY phishing_templates_public ON phishing_templates
    FOR SELECT
    USING (is_public = true);

-- Private templates are only visible to the owning company
CREATE POLICY phishing_templates_private ON phishing_templates
    FOR ALL
    USING (
        is_public = false 
        AND company_id = auth.current_user_company_id()
    );

-- System admins can see all templates
CREATE POLICY phishing_templates_system_admin ON phishing_templates
    FOR ALL
    USING (auth.is_system_admin());

-- Audit logs policies
-- Users can only see audit logs from their company
CREATE POLICY audit_logs_isolation ON audit_logs
    FOR SELECT
    USING (company_id = auth.current_user_company_id());

-- System admins can see all audit logs
CREATE POLICY audit_logs_system_admin ON audit_logs
    FOR ALL
    USING (auth.is_system_admin());

-- Analytics events policies
-- Users can only see analytics from their company
CREATE POLICY analytics_events_isolation ON analytics_events
    FOR SELECT
    USING (company_id = auth.current_user_company_id());

-- System admins can see all analytics
CREATE POLICY analytics_events_system_admin ON analytics_events
    FOR ALL
    USING (auth.is_system_admin());

-- Grant necessary permissions
GRANT USAGE ON SCHEMA auth TO PUBLIC;
GRANT EXECUTE ON FUNCTION auth.current_user_company_id() TO PUBLIC;
GRANT EXECUTE ON FUNCTION auth.is_system_admin() TO PUBLIC;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_user_course_progress_company_id ON user_course_progress(company_id);
CREATE INDEX IF NOT EXISTS idx_phishing_campaigns_company_id ON phishing_campaigns(company_id);
CREATE INDEX IF NOT EXISTS idx_phishing_templates_company_id ON phishing_templates(company_id) WHERE is_public = false;
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_company_id ON analytics_events(company_id);

-- Commit the transaction
COMMIT;

-- Verify RLS is enabled
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'users', 'companies', 'user_course_progress', 
    'phishing_campaigns', 'phishing_results', 'phishing_templates',
    'audit_logs', 'analytics_events'
)
ORDER BY tablename;