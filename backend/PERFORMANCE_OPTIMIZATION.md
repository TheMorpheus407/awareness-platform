# Performance Optimization Guide

## Overview
This guide provides comprehensive strategies and techniques for optimizing the performance of the Cybersecurity Awareness Platform backend, covering database optimization, caching, async operations, and monitoring.

## Table of Contents
1. [Performance Principles](#performance-principles)
2. [Database Optimization](#database-optimization)
3. [Caching Strategies](#caching-strategies)
4. [Async Optimization](#async-optimization)
5. [API Performance](#api-performance)
6. [Resource Management](#resource-management)
7. [Monitoring & Profiling](#monitoring--profiling)
8. [Load Testing](#load-testing)
9. [Common Bottlenecks](#common-bottlenecks)
10. [Performance Checklist](#performance-checklist)

## Performance Principles

### Key Metrics
- **Response Time**: < 200ms for simple queries
- **Throughput**: > 1000 requests/second
- **Database Queries**: < 5 queries per request
- **Memory Usage**: < 500MB per worker
- **CPU Usage**: < 70% under normal load

### Optimization Philosophy
1. **Measure First**: Profile before optimizing
2. **Optimize Hotspots**: Focus on bottlenecks
3. **Cache Aggressively**: But invalidate correctly
4. **Async Everything**: Don't block the event loop
5. **Database Efficiency**: Minimize queries

## Database Optimization

### 1. Query Optimization
```python
# BAD: N+1 query problem
users = await db.execute(select(User))
for user in users:
    courses = await db.execute(
        select(Course).where(Course.user_id == user.id)
    )

# GOOD: Eager loading with join
users = await db.execute(
    select(User).options(
        selectinload(User.courses),
        joinedload(User.company)
    )
)

# BETTER: Only load needed fields
users = await db.execute(
    select(
        User.id,
        User.email,
        User.full_name,
        func.count(Course.id).label('course_count')
    )
    .select_from(User)
    .outerjoin(Course)
    .group_by(User.id)
)
```

### 2. Index Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT u.*, c.name as company_name
FROM users u
JOIN companies c ON u.company_id = c.id
WHERE u.email = 'user@example.com';

-- Add appropriate indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company_id ON users(company_id);

-- Composite indexes for common queries
CREATE INDEX idx_users_company_active ON users(company_id, is_active)
WHERE is_active = true;

-- Full-text search index
CREATE INDEX idx_courses_search ON courses
USING gin(to_tsvector('english', title || ' ' || description));
```

### 3. Connection Pooling
```python
# core/database.py
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.ext.asyncio import create_async_engine

# Production configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,          # Number of connections
    max_overflow=10,       # Maximum overflow connections
    pool_timeout=30,       # Timeout for getting connection
    pool_pre_ping=True,    # Verify connections before use
    echo=False,            # Disable SQL logging in production
    pool_recycle=3600,     # Recycle connections after 1 hour
)

# For serverless/Lambda
serverless_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,    # No connection pooling
)
```

### 4. Batch Operations
```python
# services/user_service.py
class UserService:
    async def bulk_create_users(self, user_data: List[dict]):
        """Efficiently create multiple users."""
        # BAD: Individual inserts
        # for data in user_data:
        #     user = User(**data)
        #     db.add(user)
        #     await db.commit()
        
        # GOOD: Bulk insert
        await db.execute(
            insert(User),
            user_data
        )
        await db.commit()
    
    async def bulk_update_last_login(self, user_ids: List[int]):
        """Update last login for multiple users."""
        await db.execute(
            update(User)
            .where(User.id.in_(user_ids))
            .values(last_login=datetime.utcnow())
        )
        await db.commit()
```

## Caching Strategies

### 1. Redis Caching Layer
```python
# core/cache.py
from typing import Optional, Any, Callable
import json
import hashlib
from redis import asyncio as aioredis

class CacheManager:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_or_set(
        self,
        key: str,
        func: Callable,
        ttl: int = 300,
        namespace: str = "default"
    ) -> Any:
        """Get from cache or execute function and cache result."""
        full_key = f"{namespace}:{key}"
        
        # Try to get from cache
        cached = await self.redis.get(full_key)
        if cached:
            return json.loads(cached)
        
        # Execute function and cache result
        result = await func()
        await self.redis.setex(
            full_key,
            ttl,
            json.dumps(result, default=str)
        )
        return result
    
    async def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor,
                match=pattern,
                count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

# Usage in routes
@router.get("/courses")
async def get_courses(
    cache: CacheManager = Depends(get_cache),
    db: AsyncSession = Depends(get_db)
):
    return await cache.get_or_set(
        key="all_courses",
        func=lambda: CourseService(db).get_all_courses(),
        ttl=600,  # 10 minutes
        namespace="courses"
    )
```

### 2. Response Caching
```python
# middleware/cache_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CacheMiddleware(BaseHTTPMiddleware):
    """Cache GET responses based on URL and user."""
    
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        cached_response = await cache.get(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type="application/json"
            )
        
        # Execute request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            await cache.setex(
                cache_key,
                300,  # 5 minutes
                {
                    "content": response_body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            )
            
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )
        
        return response
```

### 3. Database Query Caching
```python
# decorators/cache.py
from functools import wraps

def cached_query(ttl: int = 300, key_prefix: str = None):
    """Decorator for caching database queries."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:{args}:{kwargs}"
            
            # Try cache first
            result = await self.cache.get(cache_key)
            if result:
                return json.loads(result)
            
            # Execute query
            result = await func(self, *args, **kwargs)
            
            # Cache result
            await self.cache.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

# Usage
class UserService:
    @cached_query(ttl=600, key_prefix="user")
    async def get_user_by_email(self, email: str):
        return await self.db.execute(
            select(User).where(User.email == email)
        )
```

## Async Optimization

### 1. Concurrent Operations
```python
# services/analytics_service.py
import asyncio
from typing import List, Dict

class AnalyticsService:
    async def get_dashboard_data(self, company_id: int) -> Dict:
        """Fetch dashboard data concurrently."""
        # BAD: Sequential execution
        # users = await self.get_active_users(company_id)
        # courses = await self.get_popular_courses(company_id)
        # compliance = await self.get_compliance_rate(company_id)
        
        # GOOD: Concurrent execution
        users_task = self.get_active_users(company_id)
        courses_task = self.get_popular_courses(company_id)
        compliance_task = self.get_compliance_rate(company_id)
        risk_task = self.calculate_risk_score(company_id)
        
        # Wait for all tasks
        results = await asyncio.gather(
            users_task,
            courses_task,
            compliance_task,
            risk_task,
            return_exceptions=True
        )
        
        # Handle results
        users, courses, compliance, risk = results
        
        return {
            "active_users": users if not isinstance(users, Exception) else 0,
            "popular_courses": courses if not isinstance(courses, Exception) else [],
            "compliance_rate": compliance if not isinstance(compliance, Exception) else 0,
            "risk_score": risk if not isinstance(risk, Exception) else 0
        }
```

### 2. Background Tasks
```python
# api/routes/reports.py
from fastapi import BackgroundTasks

@router.post("/reports/generate")
async def generate_report(
    report_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate report in background."""
    # Quick response to user
    report_id = str(uuid.uuid4())
    
    # Schedule background task
    background_tasks.add_task(
        generate_report_task,
        report_id,
        report_type,
        current_user.id
    )
    
    return {
        "report_id": report_id,
        "status": "processing",
        "check_url": f"/reports/{report_id}/status"
    }

async def generate_report_task(
    report_id: str,
    report_type: str,
    user_id: int
):
    """Heavy report generation task."""
    try:
        # Update status
        await cache.set(f"report:{report_id}:status", "processing")
        
        # Generate report
        report_data = await ReportService().generate(report_type, user_id)
        
        # Store result
        await cache.set(
            f"report:{report_id}:data",
            json.dumps(report_data),
            ex=3600  # 1 hour
        )
        await cache.set(f"report:{report_id}:status", "completed")
        
    except Exception as e:
        await cache.set(f"report:{report_id}:status", "failed")
        await cache.set(f"report:{report_id}:error", str(e))
```

### 3. Streaming Responses
```python
# api/routes/export.py
from fastapi.responses import StreamingResponse
import csv
import io

@router.get("/users/export")
async def export_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Stream large CSV export."""
    async def generate_csv():
        # Headers
        yield "id,email,full_name,created_at\n"
        
        # Stream data in chunks
        offset = 0
        chunk_size = 1000
        
        while True:
            users = await db.execute(
                select(User)
                .offset(offset)
                .limit(chunk_size)
            )
            users = users.scalars().all()
            
            if not users:
                break
            
            # Generate CSV rows
            for user in users:
                row = f"{user.id},{user.email},{user.full_name},{user.created_at}\n"
                yield row
            
            offset += chunk_size
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users_export.csv"
        }
    )
```

## API Performance

### 1. Request Optimization
```python
# dependencies/pagination.py
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Optimized pagination parameters."""
    page: int = Field(1, ge=1, le=1000)
    size: int = Field(20, ge=1, le=100)
    sort: Optional[str] = None
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with metadata."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1

# Usage
@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Count query (cached)
    count_query = select(func.count(User.id))
    total = await db.scalar(count_query)
    
    # Data query
    query = (
        select(User)
        .offset(pagination.offset)
        .limit(pagination.size)
    )
    
    if pagination.sort:
        # Safe sorting
        if pagination.sort.startswith('-'):
            query = query.order_by(
                getattr(User, pagination.sort[1:]).desc()
            )
        else:
            query = query.order_by(
                getattr(User, pagination.sort)
            )
    
    users = await db.execute(query)
    
    return PaginatedResponse(
        items=users.scalars().all(),
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size
    )
```

### 2. Response Compression
```python
# middleware/compression.py
from gzip import compress
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CompressionMiddleware(BaseHTTPMiddleware):
    """Compress large responses."""
    
    MIN_SIZE = 1024  # 1KB minimum for compression
    
    async def dispatch(self, request: Request, call_next):
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return await call_next(request)
        
        response = await call_next(request)
        
        # Only compress successful JSON responses
        if (response.status_code == 200 and
            response.headers.get("content-type", "").startswith("application/json")):
            
            # Collect response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Compress if large enough
            if len(body) > self.MIN_SIZE:
                compressed = compress(body)
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers={
                        **response.headers,
                        "content-encoding": "gzip",
                        "content-length": str(len(compressed))
                    }
                )
        
        return response
```

### 3. Field Selection
```python
# dependencies/field_selection.py
from typing import Set, Optional
from pydantic import BaseModel

class FieldSelection:
    """Allow clients to request specific fields."""
    
    def __init__(self, fields: Optional[str] = None):
        self.fields = set(fields.split(',')) if fields else None
    
    def filter_dict(self, data: dict) -> dict:
        """Filter dictionary to requested fields."""
        if not self.fields:
            return data
        
        return {
            key: value
            for key, value in data.items()
            if key in self.fields
        }
    
    def filter_model(self, model: BaseModel) -> dict:
        """Filter Pydantic model to requested fields."""
        data = model.dict()
        return self.filter_dict(data)

# Usage
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    user = await UserService(db).get_user(user_id)
    
    # Allow field selection
    if fields:
        selector = FieldSelection(fields)
        return selector.filter_model(user)
    
    return user
```

## Resource Management

### 1. Connection Management
```python
# core/connections.py
from contextlib import asynccontextmanager
import asyncio

class ConnectionPool:
    """Manage external service connections."""
    
    def __init__(self, max_connections: int = 10):
        self.semaphore = asyncio.Semaphore(max_connections)
        self.connections = []
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from pool."""
        async with self.semaphore:
            # Get or create connection
            if self.connections:
                conn = self.connections.pop()
            else:
                conn = await self._create_connection()
            
            try:
                yield conn
            finally:
                # Return to pool
                if len(self.connections) < 10:
                    self.connections.append(conn)
                else:
                    await conn.close()

# Usage
stripe_pool = ConnectionPool(max_connections=5)

async def process_payment(amount: int):
    async with stripe_pool.acquire() as stripe:
        return await stripe.charge.create(amount=amount)
```

### 2. Memory Management
```python
# utils/memory.py
import gc
import psutil
import os

class MemoryManager:
    """Monitor and manage memory usage."""
    
    MEMORY_THRESHOLD = 80  # Percentage
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    @staticmethod
    def check_memory():
        """Check if memory usage is too high."""
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > MemoryManager.MEMORY_THRESHOLD:
            # Force garbage collection
            gc.collect()
            
            # Log warning
            logger.warning(
                f"High memory usage: {memory_percent}%"
            )
            
            # Clear caches if needed
            if memory_percent > 90:
                await cache.flushdb()

# Periodic memory check
@repeat_every(seconds=60)
async def monitor_memory():
    MemoryManager.check_memory()
```

### 3. Rate Limiting
```python
# middleware/rate_limit.py
from datetime import datetime, timedelta
import hashlib

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        rate: int = 100,
        per: int = 60,
        burst: int = 10
    ):
        self.rate = rate
        self.per = per
        self.burst = burst
    
    async def check_rate_limit(
        self,
        key: str,
        redis: aioredis.Redis
    ) -> bool:
        """Check if request is rate limited."""
        now = datetime.utcnow().timestamp()
        
        # Use Lua script for atomic operations
        lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local per = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        local info = redis.call('HMGET', key, 'tokens', 'last')
        local tokens = tonumber(info[1]) or rate
        local last = tonumber(info[2]) or now
        
        -- Calculate new tokens
        local elapsed = math.max(0, now - last)
        local new_tokens = math.min(rate + burst, tokens + (elapsed * rate / per))
        
        if new_tokens < 1 then
            return 0
        end
        
        -- Consume token
        redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last', now)
        redis.call('EXPIRE', key, per * 2)
        
        return 1
        """
        
        allowed = await redis.eval(
            lua_script,
            keys=[key],
            args=[self.rate, self.per, self.burst, now]
        )
        
        return bool(allowed)

# Usage in middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Generate rate limit key
    client_id = request.client.host
    path = request.url.path
    key = f"rate_limit:{client_id}:{path}"
    
    # Check rate limit
    limiter = RateLimiter(rate=100, per=60)
    allowed = await limiter.check_rate_limit(key, redis)
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"},
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0"
            }
        )
    
    return await call_next(request)
```

## Monitoring & Profiling

### 1. Performance Metrics
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Middleware to collect metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Track active connections
    active_connections.inc()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    
    finally:
        active_connections.dec()
```

### 2. Query Profiling
```python
# utils/profiling.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

query_logger = logging.getLogger("query_profiler")

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    if settings.DEBUG:
        query_logger.debug(f"Query: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Log slow queries
    if total > 1.0:  # 1 second threshold
        query_logger.warning(
            f"Slow query ({total:.2f}s): {statement[:100]}..."
        )
    
    # Record metric
    db_query_duration.labels(
        query_type=statement.split()[0].upper()
    ).observe(total)
```

### 3. APM Integration
```python
# monitoring/apm.py
from elasticapm import Client
from elasticapm.contrib.starlette import ElasticAPM

# Configure APM
apm_client = Client({
    'SERVICE_NAME': 'cybersec-backend',
    'SERVER_URL': settings.APM_SERVER_URL,
    'SECRET_TOKEN': settings.APM_SECRET_TOKEN,
    'ENVIRONMENT': settings.ENVIRONMENT
})

# Add APM middleware
app.add_middleware(
    ElasticAPM,
    client=apm_client
)

# Custom transactions
from elasticapm import async_capture_span

class ReportService:
    @async_capture_span()
    async def generate_compliance_report(self, company_id: int):
        """Generate report with APM tracking."""
        # Span for data fetching
        with async_capture_span('fetch_compliance_data'):
            data = await self.fetch_compliance_data(company_id)
        
        # Span for processing
        with async_capture_span('process_compliance_data'):
            processed = await self.process_data(data)
        
        # Span for PDF generation
        with async_capture_span('generate_pdf'):
            pdf = await self.generate_pdf(processed)
        
        return pdf
```

## Load Testing

### 1. Locust Configuration
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": f"user{random.randint(1, 1000)}@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_dashboard(self):
        """Most common operation."""
        self.client.get("/api/v1/dashboard", headers=self.headers)
    
    @task(2)
    def list_courses(self):
        """List courses with pagination."""
        page = random.randint(1, 10)
        self.client.get(
            f"/api/v1/courses?page={page}&size=20",
            headers=self.headers
        )
    
    @task(1)
    def heavy_report(self):
        """Generate heavy report."""
        self.client.post(
            "/api/v1/reports/compliance",
            json={"type": "gdpr", "format": "pdf"},
            headers=self.headers
        )

class AdminUser(HttpUser):
    wait_time = between(2, 5)
    weight = 1  # 10% of users
    
    @task
    def analytics_dashboard(self):
        """Admin analytics."""
        self.client.get("/api/v1/admin/analytics", headers=self.headers)
```

### 2. Load Test Scenarios
```bash
# Gradual ramp-up test
locust -f locustfile.py \
    --host=https://api.cybersec-platform.de \
    --users=1000 \
    --spawn-rate=10 \
    --run-time=30m

# Spike test
locust -f locustfile.py \
    --host=https://api.cybersec-platform.de \
    --users=5000 \
    --spawn-rate=500 \
    --run-time=10m

# Endurance test
locust -f locustfile.py \
    --host=https://api.cybersec-platform.de \
    --users=500 \
    --spawn-rate=5 \
    --run-time=4h
```

## Common Bottlenecks

### 1. Database Bottlenecks
```python
# Problem: Slow count queries
# BAD
total = await db.scalar(select(func.count(User.id)))

# GOOD: Use approximate count for large tables
total = await db.scalar(
    text("SELECT reltuples FROM pg_class WHERE relname = 'users'")
)

# Problem: Lock contention
# BAD: Long transactions
async with db.begin():
    users = await db.execute(select(User))
    for user in users:
        # Long processing...
        await process_user(user)

# GOOD: Process in batches
batch_size = 100
offset = 0
while True:
    async with db.begin():
        users = await db.execute(
            select(User).offset(offset).limit(batch_size)
        )
        if not users:
            break
        
        for user in users:
            await process_user(user)
        
        offset += batch_size
```

### 2. Memory Leaks
```python
# Problem: Unbounded cache growth
# BAD
cache = {}

@router.get("/data/{key}")
async def get_data(key: str):
    if key not in cache:
        cache[key] = await fetch_data(key)
    return cache[key]

# GOOD: Use LRU cache
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_data_cached(key: str):
    return await fetch_data(key)

# BETTER: Use Redis with TTL
async def get_data(key: str):
    return await redis_cache.get_or_set(
        key,
        lambda: fetch_data(key),
        ttl=300
    )
```

### 3. Blocking Operations
```python
# Problem: Blocking I/O
# BAD
import requests

@router.get("/external-api")
async def call_external_api():
    response = requests.get("https://api.external.com/data")
    return response.json()

# GOOD: Use async HTTP client
import httpx

@router.get("/external-api")
async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.external.com/data")
        return response.json()

# Problem: CPU-bound operations
# BAD
@router.post("/process-image")
async def process_image(file: UploadFile):
    image_data = await file.read()
    # Heavy CPU processing blocks event loop
    processed = heavy_image_processing(image_data)
    return processed

# GOOD: Use thread pool
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

@router.post("/process-image")
async def process_image(file: UploadFile):
    image_data = await file.read()
    
    # Run in thread pool
    loop = asyncio.get_event_loop()
    processed = await loop.run_in_executor(
        executor,
        heavy_image_processing,
        image_data
    )
    return processed
```

## Performance Checklist

### Development Phase
- [ ] Profile queries with EXPLAIN ANALYZE
- [ ] Add appropriate database indexes
- [ ] Implement query result caching
- [ ] Use eager loading for relationships
- [ ] Batch database operations
- [ ] Implement pagination for lists
- [ ] Add field selection support
- [ ] Use async operations throughout

### Pre-Production
- [ ] Run load tests with expected traffic
- [ ] Configure connection pooling
- [ ] Set up Redis caching layer
- [ ] Enable response compression
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Profile memory usage
- [ ] Test with production data volume

### Production Optimization
- [ ] Monitor slow query logs
- [ ] Track cache hit rates
- [ ] Monitor memory usage trends
- [ ] Analyze APM data for bottlenecks
- [ ] Review and optimize hot paths
- [ ] Implement auto-scaling rules
- [ ] Set up performance alerts
- [ ] Regular performance reviews

### Monitoring Metrics
- [ ] Response time (p50, p95, p99)
- [ ] Requests per second
- [ ] Error rates
- [ ] Database query time
- [ ] Cache hit/miss ratio
- [ ] Memory usage
- [ ] CPU utilization
- [ ] Active connections

---

For specific performance issues or optimization strategies, consult the performance team or refer to the monitoring dashboards.