# 📊 Monitoring Setup Guide

## Overview
This guide provides step-by-step instructions for setting up comprehensive monitoring for the Cybersecurity Awareness Platform in production.

## 1. Error Tracking with Sentry

### Backend Setup
```python
# requirements.txt
sentry-sdk[fastapi]==1.39.1

# app/core/config.py
SENTRY_DSN: str = Field(default="", env="SENTRY_DSN")

# main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )
```

### Frontend Setup
```bash
npm install @sentry/react @sentry/tracing

# src/config/sentry.ts
import * as Sentry from "@sentry/react";
import { Integrations } from "@sentry/tracing";

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  integrations: [
    new Integrations.BrowserTracing(),
  ],
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});

# src/App.tsx
import { ErrorBoundary } from "@sentry/react";
```

## 2. Application Performance Monitoring (APM)

### Option 1: DataDog (Recommended)
```bash
# Install agent on server
DD_API_KEY=<your-api-key> DD_SITE="datadoghq.eu" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"

# Python integration
pip install ddtrace

# Add to docker-compose.prod.yml
environment:
  - DD_AGENT_HOST=datadog-agent
  - DD_TRACE_ENABLED=true
```

### Option 2: New Relic
```bash
# Install agent
pip install newrelic

# Generate config
newrelic-admin generate-config <license-key> newrelic.ini

# Run with agent
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn main:app
```

## 3. Infrastructure Monitoring

### Prometheus + Grafana Setup
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=<secure-password>
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3001:3000"

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"

volumes:
  prometheus_data:
  grafana_data:
```

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
```

## 4. Custom Metrics

### Backend Metrics Endpoint
```python
# app/api/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter

router = APIRouter()

# Define metrics
request_count = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration')
active_users = Gauge('app_active_users', 'Active users')

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Middleware to track metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    request_duration.observe(duration)
    
    return response
```

## 5. Log Aggregation

### ELK Stack Setup
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

### Logstash Configuration
```ruby
# logstash.conf
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  if [logger_name] =~ "uvicorn" {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "awareness-%{+YYYY.MM.dd}"
  }
}
```

## 6. Health Checks & Alerts

### Enhanced Health Check Endpoint
```python
# app/api/health.py
@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        checks["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis check (if using)
    try:
        redis_client.ping()
        checks["checks"]["redis"] = {"status": "healthy"}
    except:
        checks["checks"]["redis"] = {"status": "unhealthy"}
    
    # Disk space check
    disk_usage = psutil.disk_usage('/')
    checks["checks"]["disk"] = {
        "status": "healthy" if disk_usage.percent < 90 else "unhealthy",
        "usage_percent": disk_usage.percent
    }
    
    # Memory check
    memory = psutil.virtual_memory()
    checks["checks"]["memory"] = {
        "status": "healthy" if memory.percent < 90 else "unhealthy",
        "usage_percent": memory.percent
    }
    
    return checks
```

### Alert Configuration
```bash
# Install alertmanager
docker run -d -p 9093:9093 \
  -v ./alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager

# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@bootstrap-awareness.de'
  smtp_auth_username: 'alerts@bootstrap-awareness.de'
  smtp_auth_password: '<app-password>'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email-notifications'

receivers:
- name: 'email-notifications'
  email_configs:
  - to: 'admin@bootstrap-awareness.de'
    headers:
      Subject: 'Awareness Platform Alert: {{ .GroupLabels.alertname }}'
```

## 7. Uptime Monitoring

### External Monitoring Services
1. **UptimeRobot** (Free tier available)
   - Monitor: https://bootstrap-awareness.de
   - Check interval: 5 minutes
   - Alert contacts: Email, SMS, Slack

2. **Pingdom** (More advanced)
   - Real user monitoring
   - Transaction monitoring
   - Page speed monitoring

### Internal Uptime Check
```python
# app/tasks/monitoring.py
import httpx
from datetime import datetime, timedelta

async def check_services():
    services = [
        ("API", "http://localhost:8000/api/health"),
        ("Frontend", "http://localhost:3000"),
        ("Database", "postgresql://..."),
    ]
    
    results = []
    for name, url in services:
        try:
            if name == "Database":
                # Check database connection
                async with get_db() as db:
                    await db.execute("SELECT 1")
                status = "up"
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=5.0)
                    status = "up" if response.status_code == 200 else "down"
        except:
            status = "down"
        
        results.append({
            "service": name,
            "status": status,
            "checked_at": datetime.utcnow()
        })
    
    # Store results and send alerts if needed
    return results
```

## 8. Dashboard Creation

### Grafana Dashboard JSON
```json
{
  "dashboard": {
    "title": "Awareness Platform Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(app_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, app_request_duration_seconds)"
          }
        ]
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "app_active_users"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(app_errors_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## 9. Automated Reports

### Daily Health Report
```python
# app/tasks/reports.py
from app.core.email import send_email

async def send_daily_health_report():
    # Collect metrics
    metrics = {
        "uptime": calculate_uptime(),
        "total_requests": get_request_count(),
        "error_rate": get_error_rate(),
        "active_users": get_active_user_count(),
        "disk_usage": get_disk_usage(),
        "backup_status": check_last_backup(),
    }
    
    # Generate report
    report = generate_html_report(metrics)
    
    # Send email
    await send_email(
        to="admin@bootstrap-awareness.de",
        subject="Daily Health Report",
        body=report
    )
```

## 10. Quick Setup Script

```bash
#!/bin/bash
# monitoring-setup.sh

echo "🚀 Setting up monitoring..."

# 1. Create monitoring network
docker network create monitoring

# 2. Start Prometheus & Grafana
docker-compose -f docker-compose.monitoring.yml up -d

# 3. Configure Sentry
echo "SENTRY_DSN=<your-dsn>" >> .env

# 4. Set up alerts
mkdir -p monitoring/alerts
cp alertmanager.yml monitoring/alerts/

# 5. Create dashboards
mkdir -p monitoring/dashboards
cp dashboards/*.json monitoring/dashboards/

# 6. Start log aggregation
docker-compose -f docker-compose.logging.yml up -d

echo "✅ Monitoring setup complete!"
echo "📊 Grafana: http://localhost:3001"
echo "📈 Prometheus: http://localhost:9090"
echo "📋 Kibana: http://localhost:5601"
```

## Checklist

- [ ] Sentry error tracking configured
- [ ] APM solution selected and installed
- [ ] Prometheus & Grafana running
- [ ] Custom metrics implemented
- [ ] Log aggregation configured
- [ ] Health check endpoints created
- [ ] Alerts configured
- [ ] Uptime monitoring active
- [ ] Dashboards created
- [ ] Daily reports automated

---

*Last Updated: January 8, 2025*