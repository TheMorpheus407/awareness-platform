# Monitoring & Observability Spezifikation
**Version 1.0 | Comprehensive Monitoring Strategy**

## 1. Monitoring Architecture

### 1.1 Technology Stack
```yaml
Metrics:
  - Prometheus (Time-series metrics)
  - Grafana (Visualization)
  - AlertManager (Alert routing)

Logging:
  - Elasticsearch (Log storage)
  - Logstash/Fluentd (Log aggregation)
  - Kibana (Log visualization)

Tracing:
  - Jaeger (Distributed tracing)
  - OpenTelemetry (Instrumentation)

APM:
  - Application Performance Monitoring
  - Real User Monitoring (RUM)
  - Synthetic Monitoring

Status:
  - Statuspage (Public status)
  - PagerDuty (Incident management)
```

### 1.2 Monitoring Layers
```
┌─────────────────────────────────────┐
│         Business Metrics            │
├─────────────────────────────────────┤
│      Application Performance        │
├─────────────────────────────────────┤
│        Service Health              │
├─────────────────────────────────────┤
│      Infrastructure Metrics         │
└─────────────────────────────────────┘
```

## 2. Metrics Collection

### 2.1 Application Metrics

```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps

# Request metrics
request_count = Counter(
    'app_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Business metrics
active_users = Gauge(
    'app_active_users',
    'Currently active users',
    ['company_id']
)

courses_completed = Counter(
    'app_courses_completed_total',
    'Total courses completed',
    ['company_id', 'course_id']
)

phishing_clicks = Counter(
    'app_phishing_clicks_total',
    'Total phishing simulation clicks',
    ['company_id', 'campaign_id']
)

risk_score_distribution = Histogram(
    'app_user_risk_score',
    'User risk score distribution',
    ['company_id'],
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

# Performance metrics
database_query_duration = Histogram(
    'app_database_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

cache_hits = Counter(
    'app_cache_hits_total',
    'Cache hit count',
    ['cache_type']
)

cache_misses = Counter(
    'app_cache_misses_total',
    'Cache miss count',
    ['cache_type']
)

# Queue metrics
task_queue_size = Gauge(
    'app_task_queue_size',
    'Number of tasks in queue',
    ['queue_name']
)

task_processing_duration = Histogram(
    'app_task_processing_duration_seconds',
    'Task processing duration',
    ['task_type']
)

# Decorator for timing functions
def timed_metric(metric: Histogram):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
```

### 2.2 Custom Business Metrics

```python
# backend/app/services/metrics_service.py
class MetricsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def collect_business_metrics(self):
        """Collect custom business metrics"""
        
        # User engagement metrics
        active_users_24h = self.db.query(User).filter(
            User.last_login_at > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        active_users.labels(company_id="all").set(active_users_24h)
        
        # Compliance metrics
        companies = self.db.query(Company).all()
        for company in companies:
            # Training completion rate
            total_users = self.db.query(User).filter(
                User.company_id == company.id,
                User.is_active == True
            ).count()
            
            if total_users > 0:
                completed_mandatory = self.db.query(User).join(
                    UserCourseProgress
                ).filter(
                    User.company_id == company.id,
                    UserCourseProgress.is_mandatory == True,
                    UserCourseProgress.status == 'completed'
                ).distinct().count()
                
                completion_rate = (completed_mandatory / total_users) * 100
                
                compliance_rate.labels(
                    company_id=str(company.id),
                    compliance_type="training"
                ).set(completion_rate)
        
        # Risk metrics
        risk_distribution = self.db.query(
            User.risk_score,
            func.count(User.id)
        ).group_by(User.risk_score).all()
        
        for score, count in risk_distribution:
            risk_score_distribution.labels(company_id="all").observe(score)
```

### 2.3 Infrastructure Metrics

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Application metrics
  - job_name: 'cybersec-app'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

## 3. Logging Strategy

### 3.1 Structured Logging

```python
# backend/app/core/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger
from datetime import datetime
import traceback

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'cybersec-backend'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('APP_VERSION', 'unknown')
        
        # Add trace context if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'span_id'):
            log_record['span_id'] = record.span_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'company_id'):
            log_record['company_id'] = record.company_id
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stacktrace': traceback.format_exception(*record.exc_info)
            }

def setup_logging():
    """Configure structured logging"""
    # Remove default handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Setup JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
```

### 3.2 Log Aggregation

```yaml
# fluentd/fluent.conf
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

# Parse Docker logs
<filter docker.**>
  @type parser
  key_name log
  <parse>
    @type json
  </parse>
</filter>

# Add metadata
<filter **>
  @type record_transformer
  <record>
    hostname ${hostname}
    cluster cybersec-prod
  </record>
</filter>

# Route to Elasticsearch
<match **>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix cybersec
  <buffer>
    @type memory
    flush_interval 10s
  </buffer>
</match>
```

### 3.3 Log Correlation

```python
# backend/app/middleware/correlation.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        logger = logging.getLogger()
        with logging.LoggerAdapter(logger, {'trace_id': correlation_id}):
            response = await call_next(request)
        
        # Add to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response
```

## 4. Distributed Tracing

### 4.1 OpenTelemetry Setup

```python
# backend/app/core/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_tracing(app):
    """Configure distributed tracing"""
    
    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: "cybersec-backend",
        "service.version": os.getenv("APP_VERSION", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(span_processor)
    
    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    
    return trace.get_tracer(__name__)

# Usage in application
tracer = setup_tracing(app)

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user.id", user_id)
        
        # Database query
        with tracer.start_as_current_span("db_query"):
            user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            span.set_status(Status(StatusCode.ERROR, "User not found"))
            raise HTTPException(status_code=404)
        
        span.set_attribute("user.role", user.role)
        return user
```

## 5. Alerting Configuration

### 5.1 Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: application
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(app_requests_total{status=~"5.."}[5m]))
            /
            sum(rate(app_requests_total[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High response time
      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95,
            sum(rate(app_request_duration_seconds_bucket[5m])) by (le)
          ) > 2
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # Database connection pool exhausted
      - alert: DatabasePoolExhausted
        expr: |
          app_database_connections_active / app_database_connections_max > 0.9
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value | humanizePercentage }} of connections in use"

  - name: business
    interval: 60s
    rules:
      # Low training completion rate
      - alert: LowTrainingCompletionRate
        expr: |
          app_training_completion_rate < 70
        for: 1h
        labels:
          severity: warning
          team: customer-success
        annotations:
          summary: "Low training completion rate"
          description: "Company {{ $labels.company_id }} has {{ $value }}% completion rate"

      # High risk score
      - alert: HighRiskScore
        expr: |
          app_users_high_risk_count > 10
        for: 30m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "High number of high-risk users"
          description: "{{ $value }} users with risk score > 70"

      # Phishing campaign failure
      - alert: PhishingCampaignFailure
        expr: |
          app_phishing_campaign_failures_total > 0
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Phishing campaign failed"
          description: "Campaign {{ $labels.campaign_id }} failed to execute"

  - name: infrastructure
    interval: 30s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          (
            100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
          ) > 80
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes
          ) / node_memory_MemTotal_bytes * 100 > 85
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% on {{ $labels.instance }}"

      # Disk space low
      - alert: DiskSpaceLow
        expr: |
          (
            node_filesystem_avail_bytes / node_filesystem_size_bytes * 100
          ) < 15
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value }}% disk space left on {{ $labels.device }}"
```

### 5.2 AlertManager Configuration

```yaml
# alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: ${SLACK_WEBHOOK_URL}

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  
  routes:
    # Critical alerts
    - match:
        severity: critical
      receiver: pagerduty
      continue: true
    
    # Security alerts
    - match:
        team: security
      receiver: security-team
    
    # Business alerts
    - match:
        team: customer-success
      receiver: customer-success

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: ${PAGERDUTY_SERVICE_KEY}
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'

  - name: 'security-team'
    slack_configs:
      - channel: '#security-alerts'
        title: 'Security Alert: {{ .GroupLabels.alertname }}'
    email_configs:
      - to: 'security@cybersec-platform.de'

  - name: 'customer-success'
    email_configs:
      - to: 'customer-success@cybersec-platform.de'
        headers:
          Subject: 'Customer Alert: {{ .GroupLabels.alertname }}'
```

## 6. Dashboards

### 6.1 Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "CyberSec Platform Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(app_requests_total[5m])) by (method)",
            "legendFormat": "{{ method }}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(app_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "{{ endpoint }}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "sum(app_active_users)",
            "legendFormat": "Total Active Users"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Training Completion Rate",
        "targets": [
          {
            "expr": "avg(app_training_completion_rate)",
            "legendFormat": "Average Completion Rate"
          }
        ],
        "type": "gauge",
        "options": {
          "min": 0,
          "max": 100,
          "thresholds": [
            { "value": 70, "color": "yellow" },
            { "value": 85, "color": "green" }
          ]
        }
      },
      {
        "title": "Risk Score Distribution",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, sum(rate(app_user_risk_score_bucket[1h])) by (le))",
            "legendFormat": "Median Risk Score"
          }
        ],
        "type": "heatmap"
      },
      {
        "title": "Database Performance",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(app_database_query_duration_seconds_bucket[5m])) by (le, operation))",
            "legendFormat": "{{ operation }}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### 6.2 Business Metrics Dashboard

```python
# backend/app/api/metrics_dashboard.py
@router.get("/metrics/dashboard")
async def get_dashboard_metrics(
    timeframe: str = "24h",
    current_user: User = Depends(get_current_admin)
):
    """Get metrics for executive dashboard"""
    
    # Parse timeframe
    hours = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}.get(timeframe, 24)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    metrics = {
        "overview": {
            "total_users": db.query(User).filter(
                User.company_id == current_user.company_id,
                User.is_active == True
            ).count(),
            
            "active_users": db.query(User).filter(
                User.company_id == current_user.company_id,
                User.last_login_at > since
            ).count(),
            
            "courses_completed": db.query(UserCourseProgress).filter(
                UserCourseProgress.company_id == current_user.company_id,
                UserCourseProgress.completed_at > since,
                UserCourseProgress.status == "completed"
            ).count(),
            
            "avg_risk_score": db.query(func.avg(User.risk_score)).filter(
                User.company_id == current_user.company_id
            ).scalar() or 0
        },
        
        "training": {
            "completion_rate": calculate_completion_rate(current_user.company_id),
            "overdue_trainings": count_overdue_trainings(current_user.company_id),
            "popular_courses": get_popular_courses(current_user.company_id, limit=5)
        },
        
        "phishing": {
            "campaigns_run": db.query(PhishingCampaign).filter(
                PhishingCampaign.company_id == current_user.company_id,
                PhishingCampaign.completed_at > since
            ).count(),
            
            "avg_click_rate": calculate_avg_click_rate(current_user.company_id, since),
            "improvement_trend": calculate_phishing_improvement(current_user.company_id)
        },
        
        "compliance": {
            "nis2_compliant": check_nis2_compliance(current_user.company_id),
            "dsgvo_compliant": check_dsgvo_compliance(current_user.company_id),
            "next_audit_date": get_next_audit_date(current_user.company_id)
        }
    }
    
    return metrics
```

## 7. Health Checks & SLIs

### 7.1 Health Check Implementation

```python
# backend/app/api/health.py
from typing import Dict, Any
import psutil
import aioredis

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe(
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Kubernetes readiness probe"""
    checks = {
        "database": False,
        "redis": False,
        "disk_space": False
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Check Redis
    try:
        await redis.ping()
        checks["redis"] = True
    except Exception:
        pass
    
    # Check disk space
    disk_usage = psutil.disk_usage('/')
    if disk_usage.percent < 90:
        checks["disk_space"] = True
    
    # Overall status
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }

@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_admin)
) -> Dict[str, Any]:
    """Detailed health check for monitoring"""
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": os.getenv("APP_VERSION", "unknown"),
        "uptime_seconds": get_uptime(),
        "components": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "celery": await check_celery_health(),
            "storage": await check_storage_health()
        },
        "metrics": {
            "active_connections": get_active_connections(),
            "queue_size": get_queue_sizes(),
            "cache_stats": get_cache_stats()
        }
    }
```

### 7.2 SLI/SLO Definition

```yaml
# sli-slo.yaml
service_level_indicators:
  availability:
    description: "Service is responding to requests"
    measurement: |
      sum(rate(app_requests_total{status!~"5.."}[5m]))
      /
      sum(rate(app_requests_total[5m]))
    
  latency:
    description: "95th percentile latency"
    measurement: |
      histogram_quantile(0.95,
        sum(rate(app_request_duration_seconds_bucket[5m])) by (le)
      )
    
  error_rate:
    description: "Percentage of failed requests"
    measurement: |
      sum(rate(app_requests_total{status=~"5.."}[5m]))
      /
      sum(rate(app_requests_total[5m]))

service_level_objectives:
  - name: "API Availability"
    sli: availability
    target: 99.9
    window: 30d
    
  - name: "API Latency"
    sli: latency
    target_value: 1.0  # 1 second
    window: 30d
    
  - name: "Error Rate"
    sli: error_rate
    target_value: 0.001  # 0.1%
    window: 30d
```

## 8. Performance Monitoring

### 8.1 APM Integration

```python
# backend/app/core/apm.py
from elasticapm import Client
from elasticapm.contrib.starlette import ElasticAPM

def setup_apm(app):
    """Configure Application Performance Monitoring"""
    
    apm_config = {
        'SERVICE_NAME': 'cybersec-backend',
        'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL'),
        'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN'),
        'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
        'CAPTURE_BODY': 'all',
        'CAPTURE_HEADERS': True,
        'TRANSACTION_SAMPLE_RATE': 0.1 if os.getenv('ENVIRONMENT') == 'production' else 1.0
    }
    
    apm = ElasticAPM(app, Client(apm_config))
    
    return apm

# Custom performance tracking
@contextmanager
def track_performance(operation: str, **tags):
    """Track custom operation performance"""
    client = elasticapm.get_client()
    
    if client:
        transaction = client.begin_transaction(operation)
        for key, value in tags.items():
            elasticapm.tag(**{key: value})
    
    start_time = time.time()
    
    try:
        yield
    except Exception as e:
        if client:
            client.capture_exception()
        raise
    finally:
        duration = time.time() - start_time
        
        # Record custom metric
        custom_metrics.record(
            f"app.operation.{operation}",
            duration,
            tags=tags
        )
        
        if client:
            client.end_transaction(operation, "success")
```

### 8.2 Database Query Monitoring

```python
# backend/app/core/db_monitoring.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    
    # Log slow query candidates
    if "SELECT" in statement and len(statement) > 500:
        logger.debug(f"Complex query detected: {statement[:100]}...")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Extract operation and table
    operation = statement.split()[0].upper()
    table = "unknown"
    
    if "FROM" in statement:
        parts = statement.split("FROM")[1].split()
        if parts:
            table = parts[0].strip('"')
    
    # Record metric
    database_query_duration.labels(
        operation=operation,
        table=table
    ).observe(total)
    
    # Log slow queries
    if total > 1.0:
        logger.warning(
            f"Slow query detected",
            extra={
                "duration": total,
                "statement": statement[:200],
                "operation": operation,
                "table": table
            }
        )
```

## 9. Real User Monitoring (RUM)

### 9.1 Frontend Performance Tracking

```typescript
// frontend/src/utils/rum.ts
class RealUserMonitoring {
  private startTime: number;
  private metrics: PerformanceMetrics = {};
  
  constructor() {
    this.startTime = performance.now();
    this.initializeObservers();
  }
  
  private initializeObservers() {
    // First Contentful Paint
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.fcp = entry.startTime;
          this.sendMetric('fcp', entry.startTime);
        }
      }
    }).observe({ entryTypes: ['paint'] });
    
    // Largest Contentful Paint
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      this.metrics.lcp = lastEntry.renderTime || lastEntry.loadTime;
      this.sendMetric('lcp', this.metrics.lcp);
    }).observe({ entryTypes: ['largest-contentful-paint'] });
    
    // First Input Delay
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.metrics.fid = entry.processingStart - entry.startTime;
        this.sendMetric('fid', this.metrics.fid);
      }
    }).observe({ entryTypes: ['first-input'] });
    
    // Cumulative Layout Shift
    let clsValue = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
      this.metrics.cls = clsValue;
      this.sendMetric('cls', clsValue);
    }).observe({ entryTypes: ['layout-shift'] });
  }
  
  public trackPageView(page: string) {
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    const pageMetrics = {
      page,
      loadTime: navigationEntry.loadEventEnd - navigationEntry.loadEventStart,
      domContentLoaded: navigationEntry.domContentLoadedEventEnd - navigationEntry.domContentLoadedEventStart,
      ttfb: navigationEntry.responseStart - navigationEntry.requestStart,
      ...this.metrics
    };
    
    this.sendAnalytics('pageview', pageMetrics);
  }
  
  public trackError(error: Error, context?: any) {
    this.sendAnalytics('error', {
      message: error.message,
      stack: error.stack,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  }
  
  public trackUserAction(action: string, category: string, value?: any) {
    this.sendAnalytics('user_action', {
      action,
      category,
      value,
      timestamp: Date.now()
    });
  }
  
  private sendMetric(metric: string, value: number) {
    // Send to backend
    fetch('/api/v1/metrics/rum', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        metric,
        value,
        timestamp: Date.now(),
        url: window.location.href,
        userAgent: navigator.userAgent
      })
    }).catch(() => {
      // Fail silently
    });
  }
  
  private sendAnalytics(event: string, data: any) {
    // Queue for batch sending
    this.analyticsQueue.push({ event, data, timestamp: Date.now() });
    
    if (this.analyticsQueue.length >= 10) {
      this.flushAnalytics();
    }
  }
}

// Initialize RUM
export const rum = new RealUserMonitoring();
```

## 10. Incident Management

### 10.1 Incident Response Automation

```python
# backend/app/services/incident_management.py
from typing import Dict, Any, List
import asyncio
from enum import Enum

class IncidentSeverity(Enum):
    P1 = "critical"     # Complete outage
    P2 = "high"         # Major functionality impaired
    P3 = "medium"       # Minor functionality impaired
    P4 = "low"          # Cosmetic issue

class IncidentManager:
    def __init__(self, pagerduty_client, slack_client, jira_client):
        self.pagerduty = pagerduty_client
        self.slack = slack_client
        self.jira = jira_client
        self.active_incidents = {}
    
    async def create_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        affected_services: List[str],
        alert_data: Dict[str, Any]
    ) -> str:
        """Create and manage new incident"""
        
        incident_id = str(uuid.uuid4())
        
        # Create incident record
        incident = {
            "id": incident_id,
            "title": title,
            "description": description,
            "severity": severity,
            "affected_services": affected_services,
            "status": "triggered",
            "created_at": datetime.utcnow(),
            "timeline": []
        }
        
        self.active_incidents[incident_id] = incident
        
        # Create PagerDuty incident for P1/P2
        if severity in [IncidentSeverity.P1, IncidentSeverity.P2]:
            pd_incident = await self.pagerduty.create_incident(
                title=title,
                service_id=self._get_service_id(affected_services[0]),
                urgency="high" if severity == IncidentSeverity.P1 else "low"
            )
            incident["pagerduty_id"] = pd_incident["id"]
        
        # Create Slack channel for coordination
        if severity in [IncidentSeverity.P1, IncidentSeverity.P2]:
            channel_name = f"inc-{incident_id[:8]}"
            await self.slack.create_channel(channel_name)
            await self.slack.post_message(
                channel=channel_name,
                text=f"Incident: {title}\nSeverity: {severity.value}\nDescription: {description}"
            )
            incident["slack_channel"] = channel_name
        
        # Create JIRA ticket
        jira_issue = await self.jira.create_issue(
            project="INC",
            summary=title,
            description=description,
            issue_type="Incident",
            priority=self._severity_to_priority(severity),
            labels=["incident", severity.value] + affected_services
        )
        incident["jira_key"] = jira_issue["key"]
        
        # Start automated diagnostics
        asyncio.create_task(self._run_diagnostics(incident_id))
        
        return incident_id
    
    async def _run_diagnostics(self, incident_id: str):
        """Run automated diagnostics"""
        incident = self.active_incidents[incident_id]
        
        diagnostics = []
        
        # Check service health
        for service in incident["affected_services"]:
            health = await self._check_service_health(service)
            diagnostics.append({
                "type": "health_check",
                "service": service,
                "result": health
            })
        
        # Check recent deployments
        recent_deployments = await self._get_recent_deployments()
        diagnostics.append({
            "type": "recent_deployments",
            "result": recent_deployments
        })
        
        # Check error logs
        error_spike = await self._check_error_logs()
        diagnostics.append({
            "type": "error_analysis",
            "result": error_spike
        })
        
        # Update incident
        incident["diagnostics"] = diagnostics
        
        # Post to Slack
        if incident.get("slack_channel"):
            await self.slack.post_message(
                channel=incident["slack_channel"],
                text="Automated diagnostics complete",
                blocks=self._format_diagnostics(diagnostics)
            )
    
    async def update_incident_status(
        self,
        incident_id: str,
        status: str,
        message: str,
        user: str
    ):
        """Update incident status"""
        incident = self.active_incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        
        # Add to timeline
        incident["timeline"].append({
            "timestamp": datetime.utcnow(),
            "status": status,
            "message": message,
            "user": user
        })
        
        incident["status"] = status
        
        # Update external systems
        tasks = []
        
        if incident.get("pagerduty_id"):
            tasks.append(
                self.pagerduty.update_incident(
                    incident["pagerduty_id"],
                    status=status
                )
            )
        
        if incident.get("jira_key"):
            tasks.append(
                self.jira.transition_issue(
                    incident["jira_key"],
                    self._status_to_transition(status)
                )
            )
        
        if incident.get("slack_channel"):
            tasks.append(
                self.slack.post_message(
                    channel=incident["slack_channel"],
                    text=f"Status Update: {status}\n{message}\n- {user}"
                )
            )
        
        await asyncio.gather(*tasks)
        
        # Generate postmortem template for resolved P1/P2
        if status == "resolved" and incident["severity"] in [IncidentSeverity.P1, IncidentSeverity.P2]:
            await self._create_postmortem_template(incident)
```

### 10.2 Automated Remediation

```python
# backend/app/services/auto_remediation.py
class AutoRemediationService:
    def __init__(self):
        self.remediation_rules = self._load_remediation_rules()
    
    def _load_remediation_rules(self) -> Dict[str, Callable]:
        return {
            "high_memory_usage": self.remediate_high_memory,
            "database_connection_exhausted": self.remediate_db_connections,
            "high_error_rate": self.remediate_high_errors,
            "disk_space_low": self.remediate_disk_space
        }
    
    async def handle_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alert and attempt remediation"""
        
        alert_name = alert["labels"]["alertname"]
        
        if alert_name not in self.remediation_rules:
            return {
                "status": "no_action",
                "reason": "No remediation rule defined"
            }
        
        # Check if we should remediate
        if not self._should_remediate(alert):
            return {
                "status": "skipped",
                "reason": "Remediation conditions not met"
            }
        
        # Execute remediation
        try:
            result = await self.remediation_rules[alert_name](alert)
            
            # Log remediation
            await self._log_remediation(alert, result)
            
            return {
                "status": "success",
                "actions": result
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def remediate_high_memory(self, alert: Dict[str, Any]) -> List[str]:
        """Remediate high memory usage"""
        actions = []
        
        # Clear caches
        await redis_client.flushdb()
        actions.append("Cleared Redis cache")
        
        # Restart workers with high memory
        workers = await self._get_high_memory_workers()
        for worker in workers:
            await self._restart_worker(worker)
            actions.append(f"Restarted worker {worker}")
        
        # Trigger garbage collection
        import gc
        gc.collect()
        actions.append("Triggered garbage collection")
        
        return actions
    
    async def remediate_db_connections(self, alert: Dict[str, Any]) -> List[str]:
        """Remediate database connection issues"""
        actions = []
        
        # Kill idle connections
        idle_connections = await self._get_idle_db_connections()
        for conn in idle_connections:
            await self._kill_db_connection(conn)
            actions.append(f"Killed idle connection {conn}")
        
        # Increase pool size temporarily
        await self._adjust_db_pool_size(increase=10)
        actions.append("Increased DB pool size by 10")
        
        # Schedule pool size reduction
        asyncio.create_task(
            self._schedule_pool_size_reduction(minutes=30)
        )
        
        return actions
```

Diese umfassende Monitoring & Observability Spezifikation stellt sicher, dass die Plattform optimal überwacht wird und Probleme proaktiv erkannt und behoben werden können.