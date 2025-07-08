import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  HardDrive,
  Memory,
  Cpu,
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  BookOpen,
  AlertCircle,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Progress } from '../ui/Progress';
import { useTranslation } from 'react-i18next';
import { api } from '../../services/api';
import { formatDistanceToNow } from 'date-fns';

interface HealthCheck {
  status: string;
  timestamp: string;
  version: string;
  environment: string;
  checks: {
    database: {
      status: string;
      response_time_ms?: number;
      connection_pool?: {
        size: number;
        checked_in: number;
        checked_out: number;
        overflow: number;
        total: number;
      };
    };
    disk: {
      status: string;
      usage_percent: number;
      free_gb: number;
      total_gb: number;
    };
    memory: {
      status: string;
      usage_percent: number;
      available_gb: number;
      total_gb: number;
    };
    cpu: {
      status: string;
      usage_percent: number;
      core_count: number;
    };
  };
}

interface PerformanceSummary {
  timeframe: string;
  metrics: {
    avg_response_time_ms: number;
    p95_response_time_ms: number;
    p99_response_time_ms: number;
    total_requests: number;
    error_rate: number;
    active_users: number;
    course_completions: number;
    successful_payments: number;
  };
  trends: {
    response_time: string;
    traffic: string;
    errors: string;
  };
}

interface Alert {
  id: string;
  severity: 'warning' | 'critical';
  title: string;
  message: string;
  timestamp: string;
}

export const MonitoringDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [performance, setPerformance] = useState<PerformanceSummary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  const fetchMonitoringData = async () => {
    try {
      const [healthRes, perfRes, alertsRes] = await Promise.all([
        api.get('/monitoring/health/detailed'),
        api.get('/monitoring/performance/summary?timeframe=24h'),
        api.get('/monitoring/alerts/active'),
      ]);

      setHealth(healthRes.data);
      setPerformance(perfRes.data);
      setAlerts(alertsRes.data.alerts);
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'warning':
        return 'text-yellow-600';
      case 'unhealthy':
      case 'critical':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'unhealthy':
      case 'critical':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'decreasing':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('monitoring.title')}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {t('monitoring.subtitle')}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1 text-sm"
          >
            <option value={10000}>{t('monitoring.refresh.10s')}</option>
            <option value={30000}>{t('monitoring.refresh.30s')}</option>
            <option value={60000}>{t('monitoring.refresh.1m')}</option>
            <option value={300000}>{t('monitoring.refresh.5m')}</option>
          </select>
          {health && (
            <Badge
              variant={health.status === 'healthy' ? 'success' : 'destructive'}
            >
              {health.status.toUpperCase()}
            </Badge>
          )}
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
          <Card.Header>
            <h2 className="text-lg font-semibold text-red-800 dark:text-red-200">
              {t('monitoring.alerts.active')}
            </h2>
          </Card.Header>
          <Card.Content>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-start space-x-3 p-3 bg-white dark:bg-gray-800 rounded-lg"
                >
                  {alert.severity === 'critical' ? (
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {alert.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {alert.message}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      {formatDistanceToNow(new Date(alert.timestamp), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      )}

      {/* System Health */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Database */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Database className="w-5 h-5 text-gray-600" />
                  <h3 className="font-medium">{t('monitoring.database')}</h3>
                </div>
                {getStatusIcon(health.checks.database.status)}
              </div>
              {health.checks.database.response_time_ms && (
                <p className="text-sm text-gray-600">
                  {t('monitoring.responseTime')}: {health.checks.database.response_time_ms}ms
                </p>
              )}
              {health.checks.database.connection_pool && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-500">
                    {t('monitoring.connections')}: {health.checks.database.connection_pool.checked_out}/{health.checks.database.connection_pool.total}
                  </p>
                  <Progress
                    value={(health.checks.database.connection_pool.checked_out / health.checks.database.connection_pool.total) * 100}
                    className="h-2"
                  />
                </div>
              )}
            </Card.Content>
          </Card>

          {/* Disk */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-5 h-5 text-gray-600" />
                  <h3 className="font-medium">{t('monitoring.disk')}</h3>
                </div>
                {getStatusIcon(health.checks.disk.status)}
              </div>
              <p className="text-sm text-gray-600">
                {health.checks.disk.free_gb} GB {t('monitoring.free')} / {health.checks.disk.total_gb} GB
              </p>
              <div className="mt-2">
                <Progress
                  value={health.checks.disk.usage_percent}
                  className="h-2"
                  indicatorClassName={
                    health.checks.disk.usage_percent > 90
                      ? 'bg-red-600'
                      : health.checks.disk.usage_percent > 80
                      ? 'bg-yellow-600'
                      : 'bg-green-600'
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  {health.checks.disk.usage_percent}% {t('monitoring.used')}
                </p>
              </div>
            </Card.Content>
          </Card>

          {/* Memory */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Memory className="w-5 h-5 text-gray-600" />
                  <h3 className="font-medium">{t('monitoring.memory')}</h3>
                </div>
                {getStatusIcon(health.checks.memory.status)}
              </div>
              <p className="text-sm text-gray-600">
                {health.checks.memory.available_gb} GB {t('monitoring.available')} / {health.checks.memory.total_gb} GB
              </p>
              <div className="mt-2">
                <Progress
                  value={health.checks.memory.usage_percent}
                  className="h-2"
                  indicatorClassName={
                    health.checks.memory.usage_percent > 90
                      ? 'bg-red-600'
                      : health.checks.memory.usage_percent > 80
                      ? 'bg-yellow-600'
                      : 'bg-green-600'
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  {health.checks.memory.usage_percent}% {t('monitoring.used')}
                </p>
              </div>
            </Card.Content>
          </Card>

          {/* CPU */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-5 h-5 text-gray-600" />
                  <h3 className="font-medium">{t('monitoring.cpu')}</h3>
                </div>
                {getStatusIcon(health.checks.cpu.status)}
              </div>
              <p className="text-sm text-gray-600">
                {health.checks.cpu.core_count} {t('monitoring.cores')}
              </p>
              <div className="mt-2">
                <Progress
                  value={health.checks.cpu.usage_percent}
                  className="h-2"
                  indicatorClassName={
                    health.checks.cpu.usage_percent > 80
                      ? 'bg-red-600'
                      : health.checks.cpu.usage_percent > 60
                      ? 'bg-yellow-600'
                      : 'bg-green-600'
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  {health.checks.cpu.usage_percent}% {t('monitoring.usage')}
                </p>
              </div>
            </Card.Content>
          </Card>
        </div>
      )}

      {/* Performance Metrics */}
      {performance && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Response Time */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{t('monitoring.responseTime')}</h3>
                {getTrendIcon(performance.trends.response_time)}
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {performance.metrics.avg_response_time_ms}ms
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                P95: {performance.metrics.p95_response_time_ms}ms
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                P99: {performance.metrics.p99_response_time_ms}ms
              </p>
            </Card.Content>
          </Card>

          {/* Active Users */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{t('monitoring.activeUsers')}</h3>
                <Users className="w-5 h-5 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {performance.metrics.active_users}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('monitoring.last30Minutes')}
              </p>
            </Card.Content>
          </Card>

          {/* Course Completions */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{t('monitoring.courseCompletions')}</h3>
                <BookOpen className="w-5 h-5 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {performance.metrics.course_completions}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('monitoring.last24Hours')}
              </p>
            </Card.Content>
          </Card>

          {/* Revenue */}
          <Card>
            <Card.Content className="p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{t('monitoring.successfulPayments')}</h3>
                <DollarSign className="w-5 h-5 text-gray-600" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {performance.metrics.successful_payments}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t('monitoring.last24Hours')}
              </p>
            </Card.Content>
          </Card>
        </div>
      )}

      {/* Request Stats */}
      {performance && (
        <Card>
          <Card.Header>
            <h2 className="text-lg font-semibold">{t('monitoring.requestStats')}</h2>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('monitoring.totalRequests')}
                  </h3>
                  {getTrendIcon(performance.trends.traffic)}
                </div>
                <p className="text-2xl font-bold">
                  {performance.metrics.total_requests.toLocaleString()}
                </p>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('monitoring.errorRate')}
                  </h3>
                  {getTrendIcon(performance.trends.errors)}
                </div>
                <p className="text-2xl font-bold">
                  {(performance.metrics.error_rate * 100).toFixed(2)}%
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('monitoring.uptime')}
                </h3>
                <p className="text-2xl font-bold text-green-600">99.9%</p>
              </div>
            </div>
          </Card.Content>
        </Card>
      )}
    </div>
  );
}