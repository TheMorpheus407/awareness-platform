# Database Performance Optimization Guide

## Overview

This document describes the database performance optimizations implemented to address N+1 query issues and improve overall application performance.

## Issue #210 - Database Index Optimization

### Implemented Indexes

The following database indexes have been added to optimize query performance:

1. **User Table Indexes**
   - `idx_users_company_id` - Already exists (defined in model)
   - `idx_users_company_is_active` - Composite index for filtering company users by active status
   - `idx_users_company_active_verified` - Composite index for common join queries

2. **Course Table Indexes**
   - `idx_courses_category_is_active` - Composite index on (category, is_active)
   - `idx_courses_is_active_category` - Partial index for filtering active courses by category

3. **Phishing Results Table Indexes**
   - `idx_phishing_results_user_id` - Already exists (defined in model)
   - `idx_phishing_results_user_created` - Composite index for user queries with date filtering

4. **User Course Progress Table Indexes** (replaces enrollments)
   - `idx_user_course_progress_user_course` - Composite index on (user_id, course_id)
   - `idx_user_course_progress_status_user` - Composite index for status-based queries

### Migration File

The indexes are created via Alembic migration:
- File: `alembic/versions/20250711_0700-c84f92a3b7d2_add_performance_indexes_issue_210.py`
- Revision ID: `c84f92a3b7d2`

To apply the migration:
```bash
cd backend
alembic upgrade head
```

## N+1 Query Fixes

### Problem
N+1 queries occur when fetching a list of entities and then accessing their related entities, causing one query for the main list plus N additional queries for each related entity.

### Solution: SQLAlchemy `selectinload`

We've implemented eager loading using SQLAlchemy's `selectinload` to fetch related data in a single query.

### Fixed Locations

1. **User Routes** (`api/routes/users.py`)
   - Line 59: Loading company data with users
   ```python
   query = select(User).options(selectinload(User.company))
   ```
   - Line 199-202: Loading company when getting user by ID
   ```python
   select(User)
       .options(selectinload(User.company))
       .where(User.id == user_id)
   ```

2. **Course Service** (`services/course_service.py`)
   - Line 31-34: Loading modules and quizzes with course search
   ```python
   query = select(Course).options(
       selectinload(Course.modules),
       selectinload(Course.quizzes)
   )
   ```
   - Line 100-107: Loading related data when getting single course
   ```python
   select(Course)
       .where(Course.id == course_id)
       .options(
           selectinload(Course.modules).selectinload("lessons"),
           selectinload(Course.quizzes).selectinload("questions"),
           selectinload(Course.user_progress)
       )
   ```

3. **Progress Service** (`services/progress_service.py`)
   - Line 75: Loading course with user progress
   - Line 87: Loading course with enrolled courses list
   - Line 107: Loading module and course with lesson

4. **Course Routes** (`api/routes/courses.py`)
   - Line 826-831: Loading user and course with certificate
   ```python
   select(Certificate)
       .where(Certificate.id == certificate_id)
       .options(
           selectinload(Certificate.user),
           selectinload(Certificate.course)
       )
   ```

5. **Phishing Service** (`services/phishing_service.py`)
   - Line 107: Loading template with campaign
   - Line 130: Loading template when executing campaign

## Performance Benefits

### Query Reduction
- **Before**: 1 + N queries (where N = number of related entities)
- **After**: 2 queries (one for main entities, one for all related data)

### Example Improvements
1. **User List with Companies**
   - Before: 1 query for users + 50 queries for companies (if listing 50 users)
   - After: 1 query for users + 1 query for all companies = 2 total queries
   - **96% reduction in queries**

2. **Course Details**
   - Before: 1 query for course + N queries for modules + M queries for lessons
   - After: 3 queries total (course, modules, lessons)
   - **Significant reduction** for courses with many modules

### Index Benefits
- Faster filtering by company, category, and status
- Improved join performance
- Reduced table scan operations
- Better query plan optimization

## Best Practices

### When to Use `selectinload`
- Use when you know you'll need the related data
- Ideal for one-to-many relationships
- Good for displaying lists with related data

### When NOT to Use `selectinload`
- Don't use if you don't need the related data
- Avoid for very large related datasets
- Consider pagination for large result sets

### Index Guidelines
1. Add indexes for:
   - Foreign keys used in joins
   - Columns used in WHERE clauses
   - Columns used in ORDER BY
   - Composite indexes for common filter combinations

2. Monitor index usage:
   ```sql
   -- PostgreSQL query to check index usage
   SELECT 
       schemaname,
       tablename,
       indexname,
       idx_scan as index_scans,
       idx_tup_read as tuples_read
   FROM pg_stat_user_indexes
   ORDER BY idx_scan DESC;
   ```

## Monitoring Performance

### Query Analysis
Use PostgreSQL's `EXPLAIN ANALYZE` to verify improvements:

```sql
-- Example: Check user query performance
EXPLAIN ANALYZE
SELECT users.*, companies.*
FROM users
LEFT JOIN companies ON users.company_id = companies.id
WHERE users.is_active = true
  AND users.company_id = 1;
```

### Application Monitoring
- Monitor response times for affected endpoints
- Track database connection pool usage
- Watch for slow query logs

## Future Optimizations

1. **Pagination Optimization**
   - Implement cursor-based pagination for large datasets
   - Add result caching for frequently accessed data

2. **Query Caching**
   - Cache frequently accessed course lists
   - Cache user permission checks

3. **Database Connection Pooling**
   - Optimize pool size based on usage patterns
   - Implement connection retry logic

4. **Additional Indexes**
   - Monitor slow queries and add indexes as needed
   - Consider partial indexes for specific query patterns

## Testing

### Performance Tests
Run performance tests to verify improvements:

```bash
# Run performance benchmarks
cd backend
pytest tests/performance/test_query_optimization.py -v

# Profile specific endpoints
python -m cProfile -o profile.stats scripts/profile_endpoints.py
```

### Load Testing
Use tools like locust or k6 to verify performance under load:

```bash
# Example locust test
locust -f tests/load/test_user_endpoints.py --host=http://localhost:8000
```

## Rollback Plan

If issues arise, rollback the migration:

```bash
cd backend
alembic downgrade -1
```

This will remove the newly added indexes. The selectinload changes are backward compatible and don't require rollback.