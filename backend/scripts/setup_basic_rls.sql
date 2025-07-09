-- Basic RLS setup for existing tables
BEGIN;

-- Enable RLS on existing tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE phishing_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE phishing_templates ENABLE ROW LEVEL SECURITY;

-- Create schema for auth functions if it doesn't exist
CREATE SCHEMA IF NOT EXISTS auth;

-- Create function to get current user's company_id
CREATE OR REPLACE FUNCTION auth.current_user_company_id()
RETURNS UUID AS $$
DECLARE
    company_id UUID;
BEGIN
    company_id := current_setting('app.current_company_id', true)::UUID;
    RETURN company_id;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check if current user is a system admin
CREATE OR REPLACE FUNCTION auth.is_system_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN current_setting('app.current_user_role', true) = 'system_admin';
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Users policies
DROP POLICY IF EXISTS users_company_isolation ON users;
DROP POLICY IF EXISTS users_system_admin ON users;

CREATE POLICY users_company_isolation ON users
    FOR ALL
    USING (company_id = auth.current_user_company_id() OR auth.is_system_admin());

CREATE POLICY users_system_admin ON users
    FOR ALL
    USING (auth.is_system_admin());

-- Companies policies
DROP POLICY IF EXISTS companies_isolation ON companies;
DROP POLICY IF EXISTS companies_system_admin ON companies;

CREATE POLICY companies_isolation ON companies
    FOR SELECT
    USING (id = auth.current_user_company_id() OR auth.is_system_admin());

CREATE POLICY companies_system_admin ON companies
    FOR ALL
    USING (auth.is_system_admin());

-- Audit logs policies
DROP POLICY IF EXISTS audit_logs_company_isolation ON audit_logs;
DROP POLICY IF EXISTS audit_logs_system_admin ON audit_logs;

CREATE POLICY audit_logs_company_isolation ON audit_logs
    FOR ALL
    USING (company_id = auth.current_user_company_id() OR auth.is_system_admin());

CREATE POLICY audit_logs_system_admin ON audit_logs
    FOR ALL
    USING (auth.is_system_admin());

-- Grant necessary permissions
GRANT USAGE ON SCHEMA auth TO awareness;
GRANT EXECUTE ON FUNCTION auth.current_user_company_id() TO awareness;
GRANT EXECUTE ON FUNCTION auth.is_system_admin() TO awareness;

COMMIT;

-- Show RLS status
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'companies', 'audit_logs', 'phishing_campaigns', 'phishing_templates')
ORDER BY tablename;