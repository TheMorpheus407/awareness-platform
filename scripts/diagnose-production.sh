#!/bin/bash
# Diagnose production deployment issues

echo "=== Awareness Platform Production Diagnosis ==="
echo "Date: $(date)"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check system info
print_section "System Information"
echo "Hostname: $(hostname)"
echo "IP: $(hostname -I | awk '{print $1}')"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Uptime: $(uptime -p)"

# 2. Check Docker
print_section "Docker Status"
if command -v docker &> /dev/null; then
    print_ok "Docker installed"
    echo "Version: $(docker --version)"
    echo ""
    echo "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
else
    print_error "Docker not installed"
fi

# 3. Check Docker Compose
print_section "Docker Compose"
if command -v docker-compose &> /dev/null; then
    print_ok "Docker Compose installed"
    echo "Version: $(docker-compose --version)"
    
    # Check for docker-compose.yml
    if [ -f /home/awareness/awareness-platform/docker-compose.yml ]; then
        print_ok "docker-compose.yml found"
        echo ""
        echo "Services defined:"
        docker-compose -f /home/awareness/awareness-platform/docker-compose.yml config --services 2>/dev/null
    else
        print_error "docker-compose.yml not found in /home/awareness/awareness-platform/"
    fi
else
    print_error "Docker Compose not installed"
fi

# 4. Check Nginx
print_section "Nginx Status"
if command -v nginx &> /dev/null; then
    print_ok "Nginx installed"
    echo "Version: $(nginx -v 2>&1)"
    
    if systemctl is-active --quiet nginx; then
        print_ok "Nginx is running"
    else
        print_error "Nginx is not running"
    fi
    
    # Check config
    echo ""
    echo "Config test:"
    nginx -t 2>&1
    
    # Check sites
    echo ""
    echo "Enabled sites:"
    ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "Sites-enabled directory not found"
else
    print_error "Nginx not installed"
fi

# 5. Check ports
print_section "Port Status"
echo "Listening ports:"
ss -tlnp | grep -E "(80|443|8000|5173|5432|6379)" || echo "No relevant ports found"

# 6. Check processes
print_section "Application Processes"
echo "Python processes:"
ps aux | grep -E "(python|uvicorn)" | grep -v grep | head -5 || echo "No Python processes found"
echo ""
echo "Node processes:"
ps aux | grep -E "(node|npm)" | grep -v grep | head -5 || echo "No Node processes found"

# 7. Check systemd services
print_section "Systemd Services"
for service in awareness-backend awareness-frontend postgresql redis docker; do
    if systemctl list-unit-files | grep -q "^$service.service"; then
        status=$(systemctl is-active $service 2>/dev/null)
        if [ "$status" = "active" ]; then
            print_ok "$service: $status"
        else
            print_error "$service: $status"
        fi
    else
        print_warning "$service: not found"
    fi
done

# 8. Check application directories
print_section "Application Structure"
APP_DIR="/home/awareness/awareness-platform"
if [ -d "$APP_DIR" ]; then
    print_ok "Application directory exists: $APP_DIR"
    echo ""
    echo "Directory structure:"
    tree -L 2 -d "$APP_DIR" 2>/dev/null || ls -la "$APP_DIR"
else
    print_error "Application directory not found: $APP_DIR"
    echo "Checking other locations..."
    find /home -name "awareness-platform" -type d 2>/dev/null | head -5
fi

# 9. Check logs
print_section "Recent Logs"
echo "Nginx error log (last 10 lines):"
tail -10 /var/log/nginx/error.log 2>/dev/null || echo "Log not found"
echo ""
echo "Docker logs (if using Docker):"
docker logs awareness-platform-backend-1 --tail 10 2>/dev/null || echo "Backend container not found"
docker logs awareness-platform-frontend-1 --tail 10 2>/dev/null || echo "Frontend container not found"

# 10. Test endpoints
print_section "Endpoint Tests"
echo "Testing localhost endpoints..."
echo ""
echo "Backend health (port 8000):"
curl -s http://localhost:8000/api/health | jq . 2>/dev/null || echo "Failed to connect"
echo ""
echo "Frontend (port 5173):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5173 2>/dev/null || echo "Failed to connect"
echo ""
echo "Nginx (port 80):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/ 2>/dev/null || echo "Failed to connect"

# 11. Check SSL
print_section "SSL Certificate"
if [ -d /etc/letsencrypt/live/bootstrap-awareness.de ]; then
    print_ok "SSL certificate directory exists"
    openssl x509 -in /etc/letsencrypt/live/bootstrap-awareness.de/cert.pem -text -noout | grep -E "(Subject:|Not After)" 2>/dev/null
else
    print_error "SSL certificate not found"
fi

# Summary
print_section "Summary"
echo "Diagnosis complete. Key issues to address:"
echo "1. Check if application is deployed in the correct directory"
echo "2. Verify Docker/Docker Compose setup or systemd services"
echo "3. Ensure backend and frontend services are running"
echo "4. Fix Nginx configuration to properly proxy requests"
echo "5. Run database migrations if needed"