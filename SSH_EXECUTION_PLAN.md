# 🚨 SSH Production Fix Execution Plan

**Server**: 83.228.205.20  
**User**: ubuntu  
**Created**: 2025-07-09  
**Purpose**: Fix backend path issue and initialize database to reach 100% Stage 1 completion

## 📋 Pre-Flight Checklist

Before starting, ensure you have:
- [ ] SSH access to ubuntu@83.228.205.20
- [ ] sudo privileges on the server
- [ ] At least 30 minutes for the complete process
- [ ] A backup plan ready (see Section 7)

## 🚀 Step-by-Step Execution Plan

### Step 1: Connect and Create Backup
```bash
# Connect to server
ssh ubuntu@83.228.205.20

# Create timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup of current state
cd /opt
sudo cp -r awareness awareness-backup-$TIMESTAMP
echo "✅ Backup created: awareness-backup-$TIMESTAMP"
```

### Step 2: Navigate to Application Directory
```bash
cd /opt/awareness

# Verify you're in the correct directory
pwd
# Expected output: /opt/awareness

# Check current directory structure
ls -la
# Should show: backend/, frontend/, docker-compose.prod.yml, etc.
```

### Step 3: Verify Current Container Status
```bash
# Check all containers are running
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Save container IDs for reference
BACKEND_CONTAINER=$(sudo docker ps -qf "name=backend")
FRONTEND_CONTAINER=$(sudo docker ps -qf "name=frontend")
POSTGRES_CONTAINER=$(sudo docker ps -qf "name=postgres")
echo "Backend: $BACKEND_CONTAINER"
echo "Frontend: $FRONTEND_CONTAINER"
echo "Postgres: $POSTGRES_CONTAINER"
```

### Step 4: Fix Backend Path Issue
```bash
# Check current backend structure
echo "=== Checking backend structure ==="
ls -la backend/
ls -la backend/backend/ 2>/dev/null || echo "No nested backend directory"

# Option A: If backend/backend/ exists (nested structure)
if [ -d "backend/backend" ]; then
    echo "⚠️ Found nested backend structure. Fixing..."
    
    # Create symlinks for all Python files
    cd backend
    for file in backend/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            if [ ! -f "$filename" ]; then
                sudo ln -sf "$file" "$filename"
                echo "Created symlink: $filename"
            fi
        fi
    done
    
    # Create symlinks for directories
    for dir in backend/*/; do
        if [ -d "$dir" ] && [ "$dir" != "backend/backend/" ]; then
            dirname=$(basename "$dir")
            if [ ! -d "$dirname" ]; then
                sudo ln -sf "$dir" "$dirname"
                echo "Created directory symlink: $dirname"
            fi
        fi
    done
    
    cd ..
    echo "✅ Backend path structure fixed"
else
    echo "✅ Backend structure is correct (no nested directory)"
fi

# Verify fix
echo "=== Verifying backend structure ==="
sudo docker exec $BACKEND_CONTAINER ls -la /app/ | head -20
```

### Step 5: Restart Services with New Configuration
```bash
# Stop all services gracefully
echo "=== Stopping services ==="
sudo docker-compose -f docker-compose.prod.yml down

# Wait for complete shutdown
sleep 5

# Start services
echo "=== Starting services ==="
sudo docker-compose -f docker-compose.prod.yml up -d

# Wait for services to fully start
echo "Waiting for services to start..."
sleep 30

# Verify all containers are running
sudo docker ps --format "table {{.Names}}\t{{.Status}}"

# Update container references
BACKEND_CONTAINER=$(sudo docker ps -qf "name=backend")
```

### Step 6: Initialize Database
```bash
echo "=== Step 6.1: Running Database Migrations ==="

# First, check if alembic is accessible
sudo docker exec $BACKEND_CONTAINER which alembic
if [ $? -ne 0 ]; then
    echo "⚠️ Alembic not found, installing..."
    sudo docker exec $BACKEND_CONTAINER pip install alembic
fi

# Run migrations
sudo docker exec $BACKEND_CONTAINER alembic upgrade head

if [ $? -ne 0 ]; then
    echo "⚠️ Migration failed, trying enum fix..."
    
    # Fix enum issues if they exist
    sudo docker exec $BACKEND_CONTAINER python scripts/fix_enum_conflicts.py
    
    # Retry migration
    sudo docker exec $BACKEND_CONTAINER alembic upgrade head
    
    if [ $? -ne 0 ]; then
        echo "❌ Migration still failing. Checking logs..."
        sudo docker logs --tail 50 $BACKEND_CONTAINER
    else
        echo "✅ Migrations completed after enum fix"
    fi
else
    echo "✅ Migrations completed successfully"
fi

echo "=== Step 6.2: Initializing Database Tables ==="

# Initialize tables
sudo docker exec $BACKEND_CONTAINER python scripts/init_db_tables.py

if [ $? -ne 0 ]; then
    echo "⚠️ Table initialization failed. Trying alternative method..."
    
    # Alternative: Direct database initialization
    sudo docker exec $BACKEND_CONTAINER python -c "
from db.session import engine
from models.base import Base
Base.metadata.create_all(bind=engine)
print('✅ Tables created directly')
"
fi

echo "=== Step 6.3: Creating Admin User ==="

# Create admin user
sudo docker exec $BACKEND_CONTAINER python scripts/create_admin_user.py

if [ $? -ne 0 ]; then
    echo "⚠️ Admin user creation failed. Creating manually..."
    
    # Alternative: Create admin user manually
    sudo docker exec -it $BACKEND_CONTAINER python << 'EOF'
from db.session import get_db
from models.user import User
from core.security import get_password_hash
from datetime import datetime

db = next(get_db())
admin = User(
    email="admin@bootstrap-awareness.de",
    hashed_password=get_password_hash("Admin123!@#"),
    is_active=True,
    is_superuser=True,
    is_verified=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(admin)
db.commit()
print("✅ Admin user created manually")
print("Email: admin@bootstrap-awareness.de")
print("Password: Admin123!@#")
EOF
fi
```

### Step 7: Comprehensive Verification
```bash
echo "=== Running Comprehensive Verification ==="

# 7.1 Check container health
echo "1. Container Status:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 7.2 Test backend API
echo -e "\n2. Backend API Health:"
curl -s http://localhost:8000/api/health | python3 -m json.tool || echo "❌ Backend API not responding"

# 7.3 Test database connection
echo -e "\n3. Database Connection:"
sudo docker exec $BACKEND_CONTAINER python -c "
from db.session import get_db
try:
    db = next(get_db())
    db.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# 7.4 Check if tables exist
echo -e "\n4. Database Tables:"
sudo docker exec $POSTGRES_CONTAINER psql -U postgres -d awareness_platform -c "\dt" | grep -E "(users|companies|courses)" && echo "✅ Core tables exist" || echo "❌ Core tables missing"

# 7.5 Test frontend
echo -e "\n5. Frontend Status:"
curl -s http://localhost | grep -q "Cybersecurity Awareness Platform" && echo "✅ Frontend showing correct content" || echo "❌ Frontend not showing expected content"

# 7.6 Test HTTPS
echo -e "\n6. HTTPS/SSL Status:"
curl -sI https://bootstrap-awareness.de | grep -q "200 OK" && echo "✅ HTTPS working" || echo "⚠️ HTTPS issue"

# 7.7 Check API endpoints
echo -e "\n7. API Endpoints Test:"
curl -s http://localhost:8000/api/users/ -H "Accept: application/json" | python3 -m json.tool || echo "Note: This may require authentication"

# 7.8 Final summary
echo -e "\n=== VERIFICATION COMPLETE ==="
echo "If all checks show ✅, the platform is fully operational!"
echo "Stage 1 should now be at 100% completion."
```

### Step 8: Post-Deployment Monitoring
```bash
# Monitor logs for any issues
echo "=== Monitoring Logs (Press Ctrl+C to stop) ==="
sudo docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

## 🔄 Rollback Plan

If something goes wrong at any step:

### Quick Rollback (Less than 5 minutes into process)
```bash
# Stop current containers
sudo docker-compose -f docker-compose.prod.yml down

# Restore from backup
cd /opt
sudo rm -rf awareness
sudo mv awareness-backup-$TIMESTAMP awareness

# Restart services
cd awareness
sudo docker-compose -f docker-compose.prod.yml up -d
```

### Database-Only Rollback
```bash
# If only database initialization failed
sudo docker exec $POSTGRES_CONTAINER psql -U postgres -c "DROP DATABASE IF EXISTS awareness_platform;"
sudo docker exec $POSTGRES_CONTAINER psql -U postgres -c "CREATE DATABASE awareness_platform;"

# Retry initialization steps
```

### Nuclear Option (Complete Reset)
```bash
# Remove all containers and volumes
cd /opt/awareness
sudo docker-compose -f docker-compose.prod.yml down -v

# Remove all data
sudo rm -rf postgres_data redis_data

# Restart fresh
sudo docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Important Notes

1. **Admin Credentials** (after successful creation):
   - Email: admin@bootstrap-awareness.de
   - Password: Admin123!@# (change immediately!)

2. **Expected Completion Time**: 15-30 minutes

3. **Success Indicators**:
   - All containers show "Up" status
   - Backend API returns healthy status
   - Database has tables created
   - Admin user can log in
   - Frontend shows the actual platform (not Vite)

4. **Common Issues and Fixes**:
   - **"No such file or directory"**: The backend path issue needs fixing (Step 4)
   - **"Connection refused"**: Wait longer for services to start
   - **"Enum already exists"**: Run the enum fix script
   - **"Permission denied"**: Ensure using sudo for docker commands

## 🎯 Expected Final State

After successful execution:
- ✅ All containers running and healthy
- ✅ Database initialized with all tables
- ✅ Admin user created and can log in
- ✅ API endpoints responding correctly
- ✅ Frontend displaying the platform
- ✅ SSL/HTTPS working
- ✅ **Stage 1: 100% Complete!**

## 🆘 Emergency Contacts

If you encounter issues that can't be resolved:
1. Check container logs: `sudo docker logs [container-name]`
2. Review this plan for missed steps
3. Use the rollback procedures
4. Document any new issues for the development team

---

**Remember**: Take your time, verify each step, and don't skip the verification checks. Good luck! 🚀