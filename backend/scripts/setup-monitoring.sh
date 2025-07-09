#!/bin/bash
# Setup monitoring for the Cybersecurity Awareness Platform

set -e

echo "🚀 Setting up monitoring stack..."

# Check if running with proper permissions
if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then 
    echo "Please run as root or ensure your user is in the docker group"
    exit 1
fi

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/{prometheus/{alerts,data},grafana/{provisioning/{dashboards,datasources},data},loki/data,alertmanager/data,promtail/positions}

# Set proper permissions
echo "🔐 Setting permissions..."
chmod -R 755 monitoring/
if [ -d monitoring/prometheus/data ]; then
    chmod -R 777 monitoring/prometheus/data
fi
if [ -d monitoring/grafana/data ]; then
    chmod -R 777 monitoring/grafana/data
fi
if [ -d monitoring/loki/data ]; then
    chmod -R 777 monitoring/loki/data
fi

# Create Grafana datasource configuration
echo "📊 Configuring Grafana datasources..."
cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
EOF

# Create dashboard provisioning config
cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# Check for required environment variables
echo "🔍 Checking environment variables..."
required_vars=("DB_USER" "DB_PASSWORD" "DB_HOST" "DB_PORT" "DB_NAME")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=($var)
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "⚠️  Missing required environment variables: ${missing_vars[*]}"
    echo "Please set them in your .env file or export them"
    exit 1
fi

# Create monitoring network if it doesn't exist
echo "🌐 Creating monitoring network..."
docker network create monitoring 2>/dev/null || echo "Network already exists"

# Check if main application network exists
if ! docker network ls | grep -q awareness_network; then
    echo "⚠️  Warning: awareness_network not found. Creating it..."
    docker network create awareness_network
fi

# Pull latest images
echo "📥 Pulling latest monitoring images..."
docker-compose -f docker-compose.monitoring.yml pull

# Start monitoring stack
echo "🚀 Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
services=("prometheus:9090" "grafana:3000" "alertmanager:9093" "loki:3100")

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port | grep -q "200\|302"; then
        echo "✅ $service_name is running on port $port"
    else
        echo "❌ $service_name failed to start on port $port"
    fi
done

# Create example .env file if it doesn't exist
if [ ! -f monitoring/.env ]; then
    echo "📝 Creating example monitoring .env file..."
    cat > monitoring/.env.example << EOF
# Grafana Admin Credentials
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=changeme

# SMTP Configuration for Alerts
SMTP_PASSWORD=your-smtp-password

# Optional: External monitoring services
SENTRY_DSN=
PAGERDUTY_KEY=
SLACK_WEBHOOK_URL=
EOF
fi

echo ""
echo "✅ Monitoring stack setup complete!"
echo ""
echo "📊 Access points:"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - AlertManager: http://localhost:9093"
echo ""
echo "📌 Next steps:"
echo "  1. Update monitoring/.env with your configuration"
echo "  2. Configure alert notification channels in AlertManager"
echo "  3. Import additional Grafana dashboards as needed"
echo "  4. Set up external monitoring (UptimeRobot, Pingdom, etc.)"
echo ""
echo "🔍 To view logs:"
echo "  docker-compose -f docker-compose.monitoring.yml logs -f [service-name]"
echo ""
echo "🛑 To stop monitoring:"
echo "  docker-compose -f docker-compose.monitoring.yml down"