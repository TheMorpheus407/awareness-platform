# Troubleshooting Guide

## Overview
This guide helps diagnose and resolve common issues with the Cybersecurity Awareness Platform backend. It covers debugging techniques, common errors, and their solutions.

## Table of Contents
1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Database Problems](#database-problems)
4. [Authentication Issues](#authentication-issues)
5. [Performance Problems](#performance-problems)
6. [Deployment Issues](#deployment-issues)
7. [Integration Errors](#integration-errors)
8. [Debugging Tools](#debugging-tools)
9. [Emergency Procedures](#emergency-procedures)
10. [Support Escalation](#support-escalation)

## Quick Diagnostics

### Health Check Script
```bash
#!/bin/bash
# quick_health_check.sh

echo "=== System Health Check ==="

# 1. Check if backend is running
echo -n "Backend API: "
curl -s http://localhost:8000/health > /dev/null && echo "✓ OK" || echo "✗ FAILED"

# 2. Check database connection
echo -n "Database: "
psql $DATABASE_URL -c "SELECT 1" > /dev/null 2>&1 && echo "✓ OK" || echo "✗ FAILED"

# 3. Check Redis
echo -n "Redis: "
redis-cli ping > /dev/null 2>&1 && echo "✓ OK" || echo "✗ FAILED"

# 4. Check disk space
echo -n "Disk Space: "
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✓ OK ($DISK_USAGE% used)"
else
    echo "✗ WARNING ($DISK_USAGE% used)"
fi

# 5. Check memory
echo -n "Memory: "
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -lt 80 ]; then
    echo "✓ OK ($MEM_USAGE% used)"
else
    echo "✗ WARNING ($MEM_USAGE% used)"
fi

# 6. Check critical services
echo -n "Nginx: "
systemctl is-active nginx > /dev/null && echo "✓ OK" || echo "✗ FAILED"

echo -n "PostgreSQL: "
systemctl is-active postgresql > /dev/null && echo "✓ OK" || echo "✗ FAILED"
```

### API Endpoint Test
```python
# scripts/test_endpoints.py
import asyncio
import httpx
from datetime import datetime

async def test_endpoints():
    """Test critical API endpoints."""
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("/health", "GET", None, 200),
        ("/api/v1/auth/login", "POST", {"username": "test@example.com", "password": "test"}, [200, 401]),
        ("/api/v1/courses", "GET", None, [200, 401]),
        ("/api/v1/users/me", "GET", None, 401),  # Should fail without auth
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint, method, data, expected_status in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{base_url}{endpoint}")
                else:
                    response = await client.post(f"{base_url}{endpoint}", json=data)
                
                if isinstance(expected_status, list):
                    status_ok = response.status_code in expected_status
                else:
                    status_ok = response.status_code == expected_status
                
                print(f"{'✓' if status_ok else '✗'} {method} {endpoint}: {response.status_code}")
                
            except Exception as e:
                print(f"✗ {method} {endpoint}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
```

## Common Issues

### 1. Backend Won't Start

#### Symptoms
- `uvicorn: command not found`
- `ModuleNotFoundError`
- Port already in use

#### Solutions
```bash
# Check if virtual environment is activated
which python
# Should show: /path/to/venv/bin/python

# If not, activate it
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check port usage
sudo lsof -i :8000
# Kill process if needed
sudo kill -9 <PID>

# Start with explicit python path
/opt/cybersec/app/venv/bin/python main.py
```

### 2. Import Errors

#### Symptoms
```
ImportError: cannot import name 'User' from 'backend.models'
ModuleNotFoundError: No module named 'backend'
```

#### Solutions
```bash
# Check PYTHONPATH
echo $PYTHONPATH

# Set correct path
export PYTHONPATH=/opt/cybersec/app:$PYTHONPATH

# Verify imports
python -c "from backend.models.user import User; print('OK')"

# Fix circular imports
# Check for circular dependencies in __init__.py files
```

### 3. Configuration Errors

#### Symptoms
- `KeyError: 'DATABASE_URL'`
- Settings not loading
- Wrong environment

#### Solutions
```bash
# Check environment variables
env | grep -E "(DATABASE|REDIS|SECRET)"

# Verify .env file exists and is readable
ls -la .env
cat .env | grep -v "SECRET\|PASSWORD"

# Test configuration loading
python -c "from backend.core.config import settings; print(settings.dict())"

# Set environment explicitly
export ENVIRONMENT=production
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
```

## Database Problems

### 1. Connection Errors

#### Symptoms
```
asyncpg.exceptions.ConnectionDoesNotExistError
sqlalchemy.exc.OperationalError: connection refused
```

#### Diagnosis
```bash
# Test direct connection
psql $DATABASE_URL -c "SELECT version();"

# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Verify connection parameters
python scripts/test_db_connection.py
```

#### Solutions
```bash
# Restart PostgreSQL
sudo systemctl restart postgresql

# Check pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf
# Ensure: local all all md5

# Check postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf
# Ensure: listen_addresses = '*'

# Reset user password
sudo -u postgres psql
ALTER USER cybersec WITH PASSWORD 'newpassword';
\q
```

### 2. Migration Issues

#### Symptoms
- `alembic.util.exc.CommandError`
- Table already exists
- Column not found

#### Solutions
```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Fix broken migration state
alembic stamp head

# Manually fix version table
psql $DATABASE_URL
UPDATE alembic_version SET version_num = 'abc123';

# Generate SQL to compare
alembic upgrade head --sql > migration.sql
# Review and apply manually if needed
```

### 3. Performance Issues

#### Symptoms
- Slow queries
- Database locks
- High CPU usage

#### Diagnosis
```sql
-- Check slow queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds';

-- Check locks
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

## Authentication Issues

### 1. Login Failures

#### Symptoms
- "Invalid credentials"
- "Token expired"
- 401 Unauthorized

#### Debugging
```python
# scripts/debug_auth.py
from backend.core.security import verify_password, create_access_token
from backend.models.user import User
from backend.db.session import SessionLocal
import asyncio

async def debug_auth(email: str, password: str):
    async with SessionLocal() as db:
        # Check if user exists
        user = await db.query(User).filter(User.email == email).first()
        if not user:
            print(f"✗ User not found: {email}")
            return
        
        print(f"✓ User found: {user.email}")
        print(f"  Active: {user.is_active}")
        print(f"  Verified: {user.is_verified}")
        
        # Check password
        if verify_password(password, user.hashed_password):
            print("✓ Password correct")
        else:
            print("✗ Password incorrect")
        
        # Generate token
        token = create_access_token({"sub": str(user.id)})
        print(f"✓ Token generated: {token[:20]}...")

asyncio.run(debug_auth("test@example.com", "testpassword"))
```

### 2. JWT Token Issues

#### Symptoms
- "Could not validate credentials"
- "Token signature invalid"
- Tokens not working after deployment

#### Solutions
```bash
# Verify SECRET_KEY is consistent
echo $SECRET_KEY | wc -c  # Should be 64+ characters

# Generate new secret key
openssl rand -hex 32

# Test token generation/validation
python -c "
from backend.core.security import create_access_token, decode_access_token
token = create_access_token({'sub': '123'})
print(f'Token: {token}')
payload = decode_access_token(token)
print(f'Decoded: {payload}')
"

# Check for clock skew
date
# Sync time if needed
sudo ntpdate -s time.nist.gov
```

### 3. 2FA Problems

#### Symptoms
- TOTP codes not working
- QR code generation fails
- Backup codes lost

#### Solutions
```python
# scripts/reset_2fa.py
import asyncio
from backend.db.session import SessionLocal
from backend.models.user import User

async def reset_2fa(user_email: str):
    async with SessionLocal() as db:
        user = await db.query(User).filter(User.email == user_email).first()
        if user:
            user.totp_secret = None
            user.two_factor_enabled = False
            await db.commit()
            print(f"✓ 2FA reset for {user_email}")

asyncio.run(reset_2fa("user@example.com"))
```

## Performance Problems

### 1. High Memory Usage

#### Diagnosis
```bash
# Check process memory
ps aux | grep python | grep main.py

# Detailed memory info
cat /proc/$(pgrep -f main.py)/status | grep -E "(VmSize|VmRSS|VmPeak)"

# Python memory profiling
pip install memory_profiler
python -m memory_profiler main.py
```

#### Solutions
```python
# Add memory monitoring
import psutil
import gc

def check_memory():
    process = psutil.Process()
    mem_info = process.memory_info()
    print(f"RSS: {mem_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {mem_info.vms / 1024 / 1024:.2f} MB")
    
    # Force garbage collection
    gc.collect()
    
    # Clear caches if needed
    if mem_info.rss > 1024 * 1024 * 1024:  # 1GB
        print("High memory usage, clearing caches...")
        # Clear your caches here
```

### 2. Slow Response Times

#### Diagnosis
```bash
# Test endpoint performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/courses

# curl-format.txt:
time_namelookup:  %{time_namelookup}s\n
time_connect:  %{time_connect}s\n
time_appconnect:  %{time_appconnect}s\n
time_pretransfer:  %{time_pretransfer}s\n
time_redirect:  %{time_redirect}s\n
time_starttransfer:  %{time_starttransfer}s\n
time_total:  %{time_total}s\n
```

#### Solutions
- Enable query logging
- Add caching
- Optimize database queries
- Use connection pooling

### 3. CPU Spikes

#### Diagnosis
```bash
# Monitor CPU usage
top -p $(pgrep -f main.py)

# Profile Python code
pip install py-spy
py-spy top --pid $(pgrep -f main.py)

# Generate flame graph
py-spy record -o profile.svg --pid $(pgrep -f main.py)
```

## Deployment Issues

### 1. Docker Container Crashes

#### Symptoms
- Container exits immediately
- Restart loop
- No logs

#### Debugging
```bash
# Check container logs
docker logs cybersec-backend --tail 100

# Run interactively
docker run -it --rm cybersec-backend:latest /bin/bash

# Check container health
docker inspect cybersec-backend | jq '.[0].State.Health'

# Debug with shell
docker exec -it cybersec-backend /bin/bash
```

### 2. Nginx 502 Bad Gateway

#### Diagnosis
```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test backend directly
curl http://localhost:8000/health

# Check Nginx configuration
sudo nginx -t
```

#### Solutions
```nginx
# Fix upstream configuration
upstream backend {
    server localhost:8000 max_fails=3 fail_timeout=30s;
    server localhost:8001 backup;
}

# Increase timeouts
location / {
    proxy_pass http://backend;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

### 3. SSL/TLS Issues

#### Symptoms
- Certificate errors
- Mixed content warnings
- HTTPS redirect loops

#### Solutions
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/domain/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect api.cybersec-platform.de:443

# Renew certificates
sudo certbot renew --dry-run
sudo certbot renew

# Fix permissions
sudo chown -R www-data:www-data /etc/letsencrypt/
```

## Integration Errors

### 1. Email Service Failures

#### Debugging
```python
# scripts/test_email.py
import asyncio
from backend.services.email import EmailService

async def test_email():
    service = EmailService()
    try:
        await service.send_email(
            to="test@example.com",
            subject="Test Email",
            body="This is a test"
        )
        print("✓ Email sent successfully")
    except Exception as e:
        print(f"✗ Email failed: {e}")

asyncio.run(test_email())
```

#### Solutions
```bash
# Test SMTP connection
telnet smtp.gmail.com 587
EHLO localhost
STARTTLS

# Check email credentials
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('user@gmail.com', 'app-password')
server.quit()
print('✓ SMTP connection successful')
"
```

### 2. Payment Integration Issues

#### Common Stripe Errors
```python
# Handle Stripe errors properly
try:
    charge = stripe.Charge.create(
        amount=amount,
        currency="eur",
        source=token
    )
except stripe.error.CardError as e:
    # Card was declined
    logger.error(f"Card declined: {e.user_message}")
except stripe.error.RateLimitError as e:
    # Too many requests
    logger.error("Stripe rate limit hit")
except stripe.error.InvalidRequestError as e:
    # Invalid parameters
    logger.error(f"Invalid Stripe request: {e}")
except stripe.error.AuthenticationError as e:
    # Authentication failed
    logger.error("Stripe authentication failed")
except stripe.error.APIConnectionError as e:
    # Network communication failed
    logger.error("Stripe API connection failed")
except stripe.error.StripeError as e:
    # Generic error
    logger.error(f"Stripe error: {e}")
```

### 3. S3/Storage Issues

#### Debugging
```bash
# Test S3 connection
aws s3 ls s3://your-bucket/ --profile cybersec

# Check credentials
aws configure list --profile cybersec

# Test upload
echo "test" > test.txt
aws s3 cp test.txt s3://your-bucket/test.txt --profile cybersec
```

## Debugging Tools

### 1. Interactive Debugging
```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or for async code
import asyncio
import aiodebugger
asyncio.run(aiodebugger.set_trace())

# Remote debugging with debugpy
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### 2. Logging Enhancement
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# SQL query logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# HTTP request logging
import httpx
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```

### 3. Request Tracing
```python
# middleware/request_id.py
import uuid
from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    
    # Add to request state
    request.state.request_id = request_id
    
    # Add to logs
    logger.contextualize(request_id=request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response
```

## Emergency Procedures

### 1. Service Down
```bash
#!/bin/bash
# emergency_restart.sh

# 1. Stop all services
sudo systemctl stop cybersec-backend
sudo systemctl stop nginx
sudo systemctl stop redis

# 2. Clear potentially corrupted data
redis-cli FLUSHDB

# 3. Restart database
sudo systemctl restart postgresql

# 4. Start services in order
sudo systemctl start redis
sudo systemctl start cybersec-backend
sudo systemctl start nginx

# 5. Verify health
sleep 10
curl http://localhost:8000/health
```

### 2. Database Corruption
```bash
# 1. Stop application
sudo systemctl stop cybersec-backend

# 2. Backup current state
pg_dump $DATABASE_URL > backup_emergency_$(date +%Y%m%d_%H%M%S).sql

# 3. Check database
psql $DATABASE_URL -c "VACUUM ANALYZE;"
psql $DATABASE_URL -c "REINDEX DATABASE cybersec_platform;"

# 4. If needed, restore from backup
psql $DATABASE_URL < last_known_good_backup.sql
```

### 3. Security Breach
```bash
# 1. Isolate the system
sudo ufw default deny incoming
sudo ufw default deny outgoing

# 2. Preserve evidence
tar -czf evidence_$(date +%Y%m%d_%H%M%S).tar.gz /var/log/

# 3. Rotate all secrets
python scripts/rotate_secrets.py

# 4. Force logout all users
redis-cli FLUSHDB

# 5. Audit logs
grep -E "(DELETE|DROP|INSERT|UPDATE)" /var/log/postgresql/*.log
```

## Support Escalation

### Level 1: Self-Service
1. Check this troubleshooting guide
2. Review application logs
3. Run diagnostic scripts
4. Check monitoring dashboards

### Level 2: Development Team
1. Create detailed issue report
2. Include:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Relevant logs
3. Tag with severity level

### Level 3: Infrastructure Team
1. Database performance issues
2. Network/connectivity problems
3. Security incidents
4. Hardware failures

### Emergency Contacts
- **On-Call Developer**: +49-xxx-xxx-xxxx
- **Database Admin**: +49-xxx-xxx-xxxx
- **Security Team**: security@cybersec-platform.de
- **Infrastructure**: infrastructure@cybersec-platform.de

### Issue Template
```markdown
## Issue Summary
Brief description of the problem

## Environment
- Environment: production/staging/development
- Version: x.x.x
- Time: YYYY-MM-DD HH:MM:SS UTC

## Steps to Reproduce
1. Step one
2. Step two
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Error Messages
```
Paste full error messages here
```

## Logs
```
Relevant log entries
```

## Attempted Solutions
- What has been tried
- Results of attempts

## Impact
- Number of users affected
- Business impact
- Urgency level
```

---

For additional support or specific issues not covered in this guide, contact the development team or refer to the internal wiki.