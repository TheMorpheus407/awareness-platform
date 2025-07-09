# Row Level Security (RLS) Implementation

## Overview

This document describes the Row Level Security (RLS) implementation for the Cybersecurity Awareness Platform. RLS ensures that users can only access data belonging to their own company, providing robust multi-tenant isolation at the database level.

## Architecture

### Database-Level Security

PostgreSQL's Row Level Security feature is used to enforce data isolation. This provides defense-in-depth by ensuring that even if application-level security is bypassed, the database will still enforce access controls.

### Key Components

1. **RLS Policies** (`scripts/setup_row_level_security.sql`)
   - Defines access rules for each table
   - Implements company-based isolation
   - Provides system admin bypass

2. **RLS Context Functions** (`core/rls.py`)
   - `set_rls_context()`: Sets the current user's company and role
   - `clear_rls_context()`: Clears the RLS context
   - `RLSMiddleware`: Manages RLS context lifecycle

3. **Session Management** (`db/session.py`)
   - `get_db_with_rls()`: Provides RLS-enabled database sessions
   - Automatically sets context based on authenticated user

## How It Works

### 1. User Authentication
When a user authenticates, their company_id and role are stored in the session.

### 2. Request Processing
For each API request:
- The authenticated user's context is retrieved
- RLS context is set using PostgreSQL session variables
- Database queries automatically filter results

### 3. Data Access Rules

#### Users Table
- Regular users: Can only see users from their company
- System admins: Can see all users

#### Companies Table
- Regular users: Can only see their own company
- System admins: Can see all companies

#### Course Progress
- Users can only see progress records from their company
- System admins can see all progress

#### Phishing Campaigns & Results
- Users can only see campaigns and results from their company
- System admins can see all data

#### Phishing Templates
- Public templates: Visible to all users
- Private templates: Only visible to the owning company
- System admins can see all templates

#### Audit Logs & Analytics
- Users can only see logs from their company
- System admins can see all logs

## Implementation Guide

### 1. Initial Setup

```bash
# Run migrations and apply RLS policies
cd backend
python scripts/init_database_with_rls.py
```

### 2. Using RLS in Code

#### With Dependency Injection (Recommended)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db_with_rls
from api.dependencies.auth import get_current_user

@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db_with_rls),
    current_user: User = Depends(get_current_user)
):
    # RLS context is automatically set
    # This query will only return users from current_user's company
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

#### Manual Context Setting

```python
from core.rls import set_rls_context, clear_rls_context

async def process_with_rls(session: AsyncSession, user: User):
    try:
        # Set RLS context
        await set_rls_context(session, user.company_id, user.role.value)
        
        # Perform queries - automatically filtered
        result = await session.execute(select(User))
        users = result.scalars().all()
        
    finally:
        # Clear context
        await clear_rls_context(session)
```

### 3. Testing RLS

```bash
# Run RLS tests
python scripts/test_rls.py
```

## Security Considerations

### 1. Context Injection
- Always use parameterized queries when setting RLS context
- Never concatenate user input into SQL statements

### 2. Session Lifecycle
- Always clear RLS context when session ends
- Use try/finally blocks to ensure cleanup

### 3. Bypass Scenarios
- System admins bypass RLS for administrative tasks
- Background jobs may need special handling

### 4. Performance
- RLS policies add minimal overhead
- Indexes on company_id columns ensure fast filtering

## Troubleshooting

### Issue: No data returned
**Cause**: RLS context not set
**Solution**: Ensure `get_db_with_rls` is used or context is manually set

### Issue: Users see data from other companies
**Cause**: RLS not enabled on table or policy misconfigured
**Solution**: Run `setup_row_level_security.sql` and verify with `test_rls.py`

### Issue: System admin can't see all data
**Cause**: Role not properly set in context
**Solution**: Verify user.role is 'system_admin' when setting context

## Maintenance

### Adding New Tables

1. Add RLS policy in `setup_row_level_security.sql`:
```sql
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY new_table_isolation ON new_table
    FOR ALL
    USING (company_id = auth.current_user_company_id());

CREATE POLICY new_table_system_admin ON new_table
    FOR ALL
    USING (auth.is_system_admin());
```

2. Add index for performance:
```sql
CREATE INDEX idx_new_table_company_id ON new_table(company_id);
```

3. Update test cases in `test_rls.py`

### Monitoring

- Check active RLS policies: 
```sql
SELECT * FROM pg_policies WHERE tablename = 'your_table';
```

- Verify RLS is enabled:
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

## Best Practices

1. **Always use RLS-enabled sessions** for user-facing endpoints
2. **Document bypass scenarios** when RLS is intentionally disabled
3. **Test thoroughly** when adding new tables or modifying policies
4. **Monitor performance** and add indexes as needed
5. **Regular audits** to ensure policies match business requirements