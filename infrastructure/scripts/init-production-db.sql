-- Production Database Initialization Script
-- This script sets up the database with proper security configurations

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS awareness_platform
    WITH 
    OWNER = awareness_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 200;

-- Connect to the database
\c awareness_platform;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Revoke all privileges from public
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE awareness_platform FROM PUBLIC;

-- Create application role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_role') THEN
        CREATE ROLE app_role;
    END IF;
END $$;

-- Grant necessary privileges to app_role
GRANT CONNECT ON DATABASE awareness_platform TO app_role;
GRANT USAGE ON SCHEMA public TO app_role;
GRANT CREATE ON SCHEMA public TO app_role;

-- Grant privileges to awareness_user
GRANT app_role TO awareness_user;

-- Create audit schema
CREATE SCHEMA IF NOT EXISTS audit;
GRANT USAGE ON SCHEMA audit TO app_role;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    user_id UUID,
    username TEXT,
    row_data JSONB,
    changed_fields JSONB,
    query TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for audit log
CREATE INDEX idx_audit_log_created_at ON audit.activity_log(created_at DESC);
CREATE INDEX idx_audit_log_user_id ON audit.activity_log(user_id);
CREATE INDEX idx_audit_log_table_name ON audit.activity_log(table_name);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit.log_activity() RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields JSONB;
BEGIN
    -- Get the current user info
    IF TG_OP = 'DELETE' THEN
        old_data = to_jsonb(OLD);
        INSERT INTO audit.activity_log (
            table_name,
            operation,
            user_id,
            username,
            row_data,
            query
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            current_setting('app.current_user_id', true)::UUID,
            current_setting('app.current_username', true),
            old_data,
            current_query()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data = to_jsonb(OLD);
        new_data = to_jsonb(NEW);
        
        -- Calculate changed fields
        SELECT jsonb_object_agg(key, value) INTO changed_fields
        FROM jsonb_each(new_data)
        WHERE value IS DISTINCT FROM old_data->key;
        
        INSERT INTO audit.activity_log (
            table_name,
            operation,
            user_id,
            username,
            row_data,
            changed_fields,
            query
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            current_setting('app.current_user_id', true)::UUID,
            current_setting('app.current_username', true),
            new_data,
            changed_fields,
            current_query()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        new_data = to_jsonb(NEW);
        INSERT INTO audit.activity_log (
            table_name,
            operation,
            user_id,
            username,
            row_data,
            query
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            current_setting('app.current_user_id', true)::UUID,
            current_setting('app.current_username', true),
            new_data,
            current_query()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to enable audit logging on a table
CREATE OR REPLACE FUNCTION audit.enable_audit_on_table(target_table regclass) RETURNS void AS $$
DECLARE
    table_name TEXT;
BEGIN
    table_name := target_table::TEXT;
    
    -- Drop existing trigger if exists
    EXECUTE format('DROP TRIGGER IF EXISTS audit_trigger ON %s', target_table);
    
    -- Create new trigger
    EXECUTE format('
        CREATE TRIGGER audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON %s
        FOR EACH ROW EXECUTE FUNCTION audit.log_activity()
    ', target_table);
    
    RAISE NOTICE 'Audit logging enabled for table %', table_name;
END;
$$ LANGUAGE plpgsql;

-- Security functions
CREATE OR REPLACE FUNCTION public.set_user_context(p_user_id UUID, p_username TEXT) RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', p_user_id::TEXT, true);
    PERFORM set_config('app.current_username', p_username, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create performance monitoring views
CREATE OR REPLACE VIEW public.database_stats AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

CREATE OR REPLACE VIEW public.slow_queries AS
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Create backup user with limited privileges
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'backup_user') THEN
        CREATE USER backup_user WITH PASSWORD 'secure_backup_password';
        GRANT CONNECT ON DATABASE awareness_platform TO backup_user;
        GRANT USAGE ON SCHEMA public TO backup_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;
    END IF;
END $$;

-- Set up connection limits
ALTER ROLE awareness_user CONNECTION LIMIT 150;
ALTER ROLE backup_user CONNECTION LIMIT 5;

-- Configure statement timeout for application user
ALTER ROLE awareness_user SET statement_timeout = '30s';
ALTER ROLE awareness_user SET idle_in_transaction_session_timeout = '5min';

-- Create function to clean old audit logs
CREATE OR REPLACE FUNCTION audit.clean_old_logs(days_to_keep INTEGER DEFAULT 90) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit.activity_log 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic cleanup (needs pg_cron extension or external scheduling)
-- SELECT cron.schedule('clean-audit-logs', '0 2 * * *', 'SELECT audit.clean_old_logs(90);');

-- Performance indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower ON public.users(LOWER(email));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_company_active ON public.users(company_id) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_courses_published ON public.courses(created_at DESC) WHERE is_published = true;

-- Create materialized view for dashboard statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS public.dashboard_stats AS
SELECT 
    COUNT(DISTINCT u.id) FILTER (WHERE u.is_active) as active_users,
    COUNT(DISTINCT c.id) FILTER (WHERE c.is_published) as published_courses,
    COUNT(DISTINCT e.id) FILTER (WHERE e.completed_at IS NOT NULL) as completed_enrollments,
    COUNT(DISTINCT co.id) as total_companies,
    AVG(EXTRACT(EPOCH FROM (e.completed_at - e.enrolled_at))/3600)::INTEGER as avg_completion_hours
FROM users u
LEFT JOIN courses c ON true
LEFT JOIN enrollments e ON true
LEFT JOIN companies co ON true;

-- Create index on materialized view
CREATE UNIQUE INDEX idx_dashboard_stats_refresh ON public.dashboard_stats(active_users);

-- Refresh materialized view function
CREATE OR REPLACE FUNCTION public.refresh_dashboard_stats() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.dashboard_stats;
END;
$$ LANGUAGE plpgsql;

-- Grant minimal required permissions
GRANT SELECT ON public.dashboard_stats TO app_role;
GRANT EXECUTE ON FUNCTION public.refresh_dashboard_stats() TO app_role;
GRANT EXECUTE ON FUNCTION public.set_user_context(UUID, TEXT) TO app_role;

-- Final security check
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;