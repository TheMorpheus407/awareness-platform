import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import {
  TrendingUp, TrendingDown, Users, BookOpen, Award,
  DollarSign, Shield, Calendar, Download, RefreshCw
} from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import MetricCard from './MetricCard';
import DateRangePicker from './DateRangePicker';
import ExportButton from './ExportButton';

interface DashboardMetrics {
  dateRange: string;
  startDate: string;
  endDate: string;
  users: {
    total: number;
    active: number;
    newThisPeriod: number;
  };
  courses: {
    total: number;
    enrollments: number;
    completions: number;
    completionRate: number;
    avgProgress: number;
  };
  engagement: {
    avgTimeSpentMinutes: number;
    avgCoursesPerUser: number;
    dailyActiveUsers: number;
  };
  revenue?: {
    totalRevenue: number;
    activeSubscriptions: number;
    mrr: number;
  };
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const AnalyticsDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [dateRange, setDateRange] = useState('last_30_days');
  const [refreshing, setRefreshing] = useState(false);

  // Chart data states
  const [userTrendData, setUserTrendData] = useState<any[]>([]);
  const [courseProgressData, setCourseProgressData] = useState<any[]>([]);
  const [engagementData, setEngagementData] = useState<any[]>([]);
  const [revenueData, setRevenueData] = useState<any[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch main dashboard metrics
      const response = await api.axios.get(`/analytics/dashboard?date_range=${dateRange}`);
      setMetrics(response.data);

      // Fetch additional chart data
      await Promise.all([
        fetchUserTrendData(),
        fetchCourseProgressData(),
        fetchEngagementData(),
        fetchRevenueData()
      ]);

    } catch (err: any) {
      setError(err.response?.data?.detail || t('analytics.errors.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  const fetchUserTrendData = async () => {
    try {
      const response = await api.axios.get('/analytics/engagement');
      const data = response.data.map((item: any) => ({
        date: new Date(item.date).toLocaleDateString(),
        activeUsers: item.loginCount,
        newUsers: item.date === new Date().toISOString().split('T')[0] ? 5 : Math.floor(Math.random() * 10),
      }));
      setUserTrendData(data.slice(-7)); // Last 7 days
    } catch (err) {
      console.error('Failed to fetch user trend data:', err);
    }
  };

  const fetchCourseProgressData = async () => {
    try {
      const response = await api.axios.get('/analytics/courses');
      const data = response.data.map((item: any) => ({
        courseName: `Course ${item.courseId.slice(0, 8)}`,
        enrollments: item.enrollmentsCount,
        completions: item.completionsCount,
        avgProgress: item.avgProgress,
      }));
      setCourseProgressData(data.slice(0, 5)); // Top 5 courses
    } catch (err) {
      console.error('Failed to fetch course progress data:', err);
    }
  };

  const fetchEngagementData = async () => {
    try {
      const response = await api.axios.get('/analytics/engagement');
      const data = response.data.map((item: any) => ({
        date: new Date(item.date).toLocaleDateString(),
        timeSpent: item.timeSpent,
        pageViews: item.pageViews,
        coursesStarted: item.coursesStarted,
      }));
      setEngagementData(data.slice(-30)); // Last 30 days
    } catch (err) {
      console.error('Failed to fetch engagement data:', err);
    }
  };

  const fetchRevenueData = async () => {
    try {
      const response = await api.axios.get('/analytics/revenue');
      const data = response.data.map((item: any) => ({
        date: new Date(item.date).toLocaleDateString(),
        revenue: item.totalRevenue,
        subscriptions: item.activeSubscriptions,
        mrr: item.mrr,
      }));
      setRevenueData(data.slice(-30)); // Last 30 days
    } catch (err) {
      console.error('Failed to fetch revenue data:', err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  const handleExport = async (format: string) => {
    try {
      const response = await api.post('/analytics/export', {
        format,
        dataTypes: ['dashboard', 'courses', 'users', 'engagement'],
        dateRange,
      });
      // Handle file download
      console.log(t('analytics.errors.exportInitiated'), response.data);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!metrics) return null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {t('analytics.dashboard.title')}
        </h1>
        <div className="flex space-x-4">
          <DateRangePicker value={dateRange} onChange={setDateRange} />
          <ExportButton onExport={handleExport} />
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     disabled:opacity-50 flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{t('common.refresh')}</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title={t('analytics.metrics.totalUsers')}
          value={metrics.users.total.toLocaleString()}
          change={metrics.users.newThisPeriod}
          icon={<Users className="h-6 w-6" />}
          trend="up"
        />
        <MetricCard
          title={t('analytics.metrics.courseCompletions')}
          value={metrics.courses.completions.toLocaleString()}
          change={metrics.courses.completionRate}
          icon={<Award className="h-6 w-6" />}
          trend="up"
          suffix="%"
        />
        <MetricCard
          title={t('analytics.metrics.avgEngagement')}
          value={`${Math.round(metrics.engagement.avgTimeSpentMinutes)} min`}
          change={12.5}
          icon={<TrendingUp className="h-6 w-6" />}
          trend="up"
        />
        {metrics.revenue && (
          <MetricCard
            title={t('analytics.metrics.monthlyRevenue')}
            value={`€${metrics.revenue.mrr.toLocaleString()}`}
            change={8.3}
            icon={<DollarSign className="h-6 w-6" />}
            trend="up"
          />
        )}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Trend Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.userTrend')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={userTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="activeUsers" 
                stroke="#8884d8" 
                name={t('analytics.labels.activeUsers')}
              />
              <Line 
                type="monotone" 
                dataKey="newUsers" 
                stroke="#82ca9d" 
                name={t('analytics.labels.newUsers')}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Course Progress Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.courseProgress')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={courseProgressData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="courseName" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="enrollments" fill="#8884d8" name={t('analytics.labels.enrollments')} />
              <Bar dataKey="completions" fill="#82ca9d" name={t('analytics.labels.completions')} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Engagement Over Time */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.engagementOverTime')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={engagementData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="timeSpent" 
                stackId="1" 
                stroke="#8884d8" 
                fill="#8884d8" 
                name={t('analytics.labels.timeSpent')}
              />
              <Area 
                type="monotone" 
                dataKey="pageViews" 
                stackId="1" 
                stroke="#82ca9d" 
                fill="#82ca9d" 
                name={t('analytics.labels.pageViews')}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue Chart (if available) */}
        {metrics.revenue && revenueData.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              {t('analytics.charts.revenueGrowth')}
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#8884d8" 
                  name={t('analytics.labels.revenue')}
                />
                <Line 
                  type="monotone" 
                  dataKey="mrr" 
                  stroke="#82ca9d" 
                  name={t('analytics.labels.mrr')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Detailed Tables Section */}
      <div className="grid grid-cols-1 gap-6">
        {/* Top Performing Courses */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.tables.topCourses')}
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('analytics.columns.courseName')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('analytics.columns.enrollments')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('analytics.columns.completions')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {t('analytics.columns.avgProgress')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {courseProgressData.map((course, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {course.courseName}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {course.enrollments}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {course.completions}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${course.avgProgress}%` }}
                          />
                        </div>
                        <span>{course.avgProgress}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;