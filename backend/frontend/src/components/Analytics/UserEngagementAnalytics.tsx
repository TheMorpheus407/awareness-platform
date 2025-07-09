import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter
} from 'recharts';
import { 
  Users, Clock, MousePointer, BookOpen, Target, 
  Activity, TrendingUp, Award 
} from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import MetricCard from './MetricCard';
import DateRangePicker from './DateRangePicker';

interface UserEngagementData {
  userId: string;
  userName?: string;
  date: string;
  loginCount: number;
  pageViews: number;
  timeSpent: number;
  coursesStarted: number;
  coursesCompleted: number;
  quizzesTaken: number;
  avgQuizScore: number | null;
  phishingAttempts: number;
  phishingReported: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const UserEngagementAnalytics: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [engagementData, setEngagementData] = useState<UserEngagementData[]>([]);
  const [dateRange, setDateRange] = useState('last_30_days');
  const [selectedUser, setSelectedUser] = useState<string>('all');
  const [users, setUsers] = useState<any[]>([]);

  useEffect(() => {
    fetchUsers();
    fetchEngagementData();
  }, [dateRange, selectedUser]);

  const fetchUsers = async () => {
    try {
      const response = await api.axios.get('/users');
      setUsers(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
  };

  const fetchEngagementData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = selectedUser !== 'all' ? `?user_id=${selectedUser}` : '';
      const response = await api.axios.get(`/analytics/engagement${params}`);
      setEngagementData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load engagement data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate aggregate metrics
  const totalLogins = engagementData.reduce((sum, data) => sum + data.loginCount, 0);
  const totalPageViews = engagementData.reduce((sum, data) => sum + data.pageViews, 0);
  const totalTimeSpent = engagementData.reduce((sum, data) => sum + data.timeSpent, 0);
  const avgTimePerSession = totalLogins > 0 ? totalTimeSpent / totalLogins : 0;
  const totalCoursesCompleted = engagementData.reduce((sum, data) => sum + data.coursesCompleted, 0);
  const avgQuizScores = engagementData.filter(d => d.avgQuizScore !== null);
  const overallAvgQuizScore = avgQuizScores.length > 0
    ? avgQuizScores.reduce((sum, d) => sum + (d.avgQuizScore || 0), 0) / avgQuizScores.length
    : 0;

  // Prepare chart data
  const engagementTrend = engagementData.map(data => ({
    date: new Date(data.date).toLocaleDateString(),
    logins: data.loginCount,
    pageViews: data.pageViews,
    timeSpent: Math.round(data.timeSpent / 60), // Convert to hours
  }));

  const learningProgress = engagementData.map(data => ({
    date: new Date(data.date).toLocaleDateString(),
    started: data.coursesStarted,
    completed: data.coursesCompleted,
    quizzes: data.quizzesTaken,
  }));

  // Activity distribution pie chart
  const activityDistribution = [
    { name: t('analytics.activities.learning'), value: totalTimeSpent * 0.6 },
    { name: t('analytics.activities.assessments'), value: totalTimeSpent * 0.2 },
    { name: t('analytics.activities.browsing'), value: totalTimeSpent * 0.15 },
    { name: t('analytics.activities.other'), value: totalTimeSpent * 0.05 },
  ];

  // Scatter plot data for engagement vs performance
  const engagementVsPerformance = engagementData
    .filter(d => d.avgQuizScore !== null)
    .map(data => ({
      timeSpent: data.timeSpent,
      score: data.avgQuizScore,
      courses: data.coursesCompleted,
    }));

  // User leaderboard
  const userLeaderboard = users
    .map(user => {
      const userData = engagementData.filter(d => d.userId === user.id);
      return {
        name: `${user.firstName} ${user.lastName}`,
        totalTime: userData.reduce((sum, d) => sum + d.timeSpent, 0),
        coursesCompleted: userData.reduce((sum, d) => sum + d.coursesCompleted, 0),
        avgScore: userData.filter(d => d.avgQuizScore !== null).reduce((sum, d) => sum + (d.avgQuizScore || 0), 0) / userData.length || 0,
      };
    })
    .sort((a, b) => b.coursesCompleted - a.coursesCompleted)
    .slice(0, 10);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('analytics.userEngagement.title')}
        </h2>
        <div className="flex space-x-4">
          <DateRangePicker value={dateRange} onChange={setDateRange} />
          <select
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">{t('analytics.userEngagement.allUsers')}</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.firstName} {user.lastName}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title={t('analytics.metrics.totalLogins')}
          value={totalLogins}
          icon={<Users className="h-6 w-6" />}
          trend="up"
          change={15}
        />
        <MetricCard
          title={t('analytics.metrics.avgTimePerSession')}
          value={`${Math.round(avgTimePerSession)} min`}
          icon={<Clock className="h-6 w-6" />}
          trend="up"
          change={8}
        />
        <MetricCard
          title={t('analytics.metrics.coursesCompleted')}
          value={totalCoursesCompleted}
          icon={<Award className="h-6 w-6" />}
          trend="up"
          change={12}
        />
        <MetricCard
          title={t('analytics.metrics.avgQuizScore')}
          value={overallAvgQuizScore.toFixed(1)}
          suffix="%"
          icon={<Target className="h-6 w-6" />}
          trend={overallAvgQuizScore > 75 ? 'up' : 'down'}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Engagement Trend */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.engagementTrend')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={engagementTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="logins" 
                stackId="1"
                stroke="#8884d8" 
                fill="#8884d8"
                name={t('analytics.labels.logins')}
              />
              <Area 
                type="monotone" 
                dataKey="pageViews" 
                stackId="1"
                stroke="#82ca9d" 
                fill="#82ca9d"
                name={t('analytics.labels.pageViews')}
              />
              <Area 
                type="monotone" 
                dataKey="timeSpent" 
                stackId="1"
                stroke="#ffc658" 
                fill="#ffc658"
                name={t('analytics.labels.hoursSpent')}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Learning Progress */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.learningProgress')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={learningProgress}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="started" fill="#8884d8" name={t('analytics.labels.coursesStarted')} />
              <Bar dataKey="completed" fill="#82ca9d" name={t('analytics.labels.coursesCompleted')} />
              <Bar dataKey="quizzes" fill="#ffc658" name={t('analytics.labels.quizzesTaken')} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Activity Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.activityDistribution')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={activityDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {activityDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Engagement vs Performance */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.engagementVsPerformance')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timeSpent" 
                name={t('analytics.labels.timeSpent')}
                unit=" min"
              />
              <YAxis 
                dataKey="score" 
                name={t('analytics.labels.score')}
                unit="%"
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter 
                name={t('analytics.labels.users')} 
                data={engagementVsPerformance} 
                fill="#8884d8"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* User Leaderboard */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('analytics.tables.topPerformers')}
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.rank')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.user')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.timeSpent')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.coursesCompleted')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.avgScore')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {userLeaderboard.map((user, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div className="flex items-center">
                      {index < 3 ? (
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold
                          ${index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : 'bg-orange-600'}`}>
                          {index + 1}
                        </div>
                      ) : (
                        <span className="text-gray-500">{index + 1}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {user.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {Math.round(user.totalTime / 60)} hours
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {user.coursesCompleted}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div className="flex items-center">
                      <span>{user.avgScore.toFixed(1)}%</span>
                      {user.avgScore >= 90 && <Award className="ml-2 h-4 w-4 text-yellow-500" />}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default UserEngagementAnalytics;