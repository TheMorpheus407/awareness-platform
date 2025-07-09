# ADR-002: Implement Row-Level Security with PostgreSQL

## Status
Accepted

## Context
Our multi-tenant cybersecurity awareness platform requires strict data isolation between different companies. Each company's data must be completely isolated from other companies' data. We need a robust security mechanism that:
- Prevents data leaks between tenants
- Works transparently with our application code
- Scales well with multiple tenants
- Provides defense in depth
- Can be audited and tested

## Decision
We will implement PostgreSQL Row-Level Security (RLS) policies to enforce data isolation at the database level, in addition to application-level security checks.

## Consequences

### Positive
- **Defense in depth**: Database-level security as an additional layer
- **Transparent to application**: Once configured, works automatically
- **Performance**: PostgreSQL optimizes RLS policies with query planning
- **Auditability**: Policies are defined in database and can be reviewed
- **Prevents mistakes**: Even if application code has bugs, data remains isolated
- **SQL injection protection**: Even successful SQL injection cannot bypass RLS
- **Compliance**: Helps meet data isolation requirements for certifications

### Negative
- **Complexity**: Requires understanding of RLS policies and PostgreSQL security
- **Testing overhead**: Need to test both application and database security
- **Migration complexity**: Need careful migration scripts to enable RLS
- **Debugging difficulty**: Can make debugging queries more complex
- **Performance overhead**: Small performance impact from policy evaluation
- **PostgreSQL lock-in**: RLS is PostgreSQL-specific feature

### Neutral
- Requires setting company context for each database session
- All tables need RLS policies defined
- Requires superuser privileges for initial setup

## Implementation Details
```sql
-- Example RLS policy for users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY company_isolation ON users
    FOR ALL
    TO application_role
    USING (company_id = current_setting('app.current_company_id')::uuid);
```

## Alternatives Considered

1. **Application-level filtering only**
   - Pros: Simpler, database-agnostic
   - Cons: Single point of failure, vulnerable to bugs
   - Not chosen: Insufficient security for multi-tenant data

2. **Separate databases per tenant**
   - Pros: Complete isolation, simple security model
   - Cons: Difficult to scale, complex deployment, expensive
   - Not chosen: Not practical for SaaS with many tenants

3. **Separate schemas per tenant**
   - Pros: Good isolation, easier than separate databases
   - Cons: Still complex to manage, migration challenges
   - Not chosen: RLS provides similar security with less complexity

4. **View-based security**
   - Pros: Database-level security, works with multiple databases
   - Cons: Complex to maintain, performance issues
   - Not chosen: RLS is more elegant and performant

## References
- [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Multi-tenant Security Best Practices](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/security)
- Backend RLS Implementation: `/backend/docs/ROW_LEVEL_SECURITY.md`

## Date
2025-01-07

## Authors
- Claude (AI Assistant)