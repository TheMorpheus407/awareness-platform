#!/bin/bash
# Fix backend imports

# Remove limiter import from auth.py
sed -i '/from core.middleware import limiter/d' /opt/awareness/backend/api/routes/auth.py

# Remove any @limiter decorators (if they exist)
sed -i '/@limiter/d' /opt/awareness/backend/api/routes/auth.py

# Also create a dummy limiter if needed
cat > /opt/awareness/backend/core/rate_limit.py << 'EOF'
# Dummy rate limiter for now
class DummyLimiter:
    def limit(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

limiter = DummyLimiter()
EOF

echo "Backend fixes applied"