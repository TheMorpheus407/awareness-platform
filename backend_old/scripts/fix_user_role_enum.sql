-- Fix user_role enum type to use lowercase values
-- This script safely migrates from uppercase enum values to lowercase

-- Start transaction
BEGIN;

-- Create temporary table to backup users data
CREATE TEMP TABLE users_backup AS 
SELECT * FROM users;

-- Drop the foreign key constraints that reference the users table
-- We need to find all foreign keys first
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT conname, conrelid::regclass AS table_name
        FROM pg_constraint
        WHERE confrelid = 'users'::regclass
        AND contype = 'f'
    ) LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.table_name, r.conname);
    END LOOP;
END $$;

-- Store the current role values with case mapping
CREATE TEMP TABLE role_mapping (old_value text, new_value text);
INSERT INTO role_mapping VALUES 
    ('SYSTEM_ADMIN', 'system_admin'),
    ('COMPANY_ADMIN', 'company_admin'),
    ('MANAGER', 'manager'),
    ('EMPLOYEE', 'employee'),
    ('system_admin', 'system_admin'),   -- Handle case where values are already lowercase
    ('company_admin', 'company_admin'),
    ('manager', 'manager'),
    ('employee', 'employee');

-- Drop the column default first
ALTER TABLE users ALTER COLUMN role DROP DEFAULT;

-- Convert the column to text temporarily
ALTER TABLE users ALTER COLUMN role TYPE text USING role::text;

-- Update all role values to lowercase
UPDATE users u
SET role = rm.new_value
FROM role_mapping rm
WHERE u.role = rm.old_value;

-- Drop the old enum type
DROP TYPE IF EXISTS user_role CASCADE;

-- Create the new enum type with lowercase values
CREATE TYPE user_role AS ENUM ('system_admin', 'company_admin', 'manager', 'employee');

-- Convert the column back to the new enum type
ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::user_role;

-- Set the default value back
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'employee'::user_role;

-- Re-add NOT NULL constraint
ALTER TABLE users ALTER COLUMN role SET NOT NULL;

-- Recreate foreign key constraints
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Get foreign key information from backup
    FOR r IN (
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.constraint_name
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
              ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND ccu.table_name = 'users'
    ) LOOP
        -- Add back foreign keys
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I)',
            r.table_name, r.constraint_name, r.column_name, r.foreign_table_name, r.foreign_column_name);
    END LOOP;
END $$;

-- Verify the migration
DO $$
DECLARE
    invalid_count INTEGER;
BEGIN
    -- Check for any invalid values
    SELECT COUNT(*) INTO invalid_count
    FROM users
    WHERE role NOT IN ('system_admin', 'company_admin', 'manager', 'employee');
    
    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Migration failed: % users have invalid role values', invalid_count;
    END IF;
    
    -- Verify data integrity
    IF NOT EXISTS (
        SELECT 1 
        FROM users u
        JOIN users_backup b ON u.id = b.id
        WHERE LOWER(b.role::text) != u.role::text
    ) THEN
        RAISE NOTICE 'Migration successful: All role values converted to lowercase';
    ELSE
        RAISE EXCEPTION 'Migration failed: Some role values were not properly converted';
    END IF;
END $$;

-- If we reach here, everything worked
COMMIT;

-- Display summary
SELECT 
    role,
    COUNT(*) as user_count
FROM users
GROUP BY role
ORDER BY role;