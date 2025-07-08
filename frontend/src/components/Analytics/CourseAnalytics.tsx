import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { BookOpen, Users, Clock, Trophy, TrendingUp } from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import MetricCard from './MetricCard';

interface CourseAnalyticsData {
  courseId: string;
  courseName: string;
  enrollmentsCount: number;
  completionsCount: number;
  avgProgress: number;
  avgScore: number;
  totalTimeSpent: number;
  uniqueUsers: number;
  date: string;
}

const CourseAnalytics: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courseData, setCourseData] = useState<CourseAnalyticsData[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>('all');
  const [courses, setCourses] = useState<any[]>([]);

  useEffect(() => {
    fetchCourseAnalytics();
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await api.get('/courses');
      setCourses(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch courses:', err);
    }
  };

  const fetchCourseAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = selectedCourse !== 'all' ? `?course_id=${selectedCourse}` : '';
      const response = await api.get(`/analytics/courses${params}`);
      setCourseData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load course analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCourse) {
      fetchCourseAnalytics();
    }
  }, [selectedCourse]);

  // Aggregate metrics
  const totalEnrollments = courseData.reduce((sum, course) => sum + course.enrollmentsCount, 0);
  const totalCompletions = courseData.reduce((sum, course) => sum + course.completionsCount, 0);
  const avgCompletionRate = totalEnrollments > 0 ? (totalCompletions / totalEnrollments * 100) : 0;
  const avgCourseScore = courseData.length > 0
    ? courseData.reduce((sum, course) => sum + course.avgScore, 0) / courseData.length
    : 0;

  // Prepare chart data
  const progressOverTime = courseData.map(course => ({
    date: new Date(course.date).toLocaleDateString(),
    enrollments: course.enrollmentsCount,
    completions: course.completionsCount,
    avgProgress: course.avgProgress,
  }));

  const courseComparison = courses.map(course => {
    const analytics = courseData.filter(c => c.courseId === course.id);
    const avgMetrics = analytics.length > 0 ? {
      enrollments: analytics.reduce((sum, a) => sum + a.enrollmentsCount, 0) / analytics.length,
      completions: analytics.reduce((sum, a) => sum + a.completionsCount, 0) / analytics.length,
      avgScore: analytics.reduce((sum, a) => sum + a.avgScore, 0) / analytics.length,
    } : { enrollments: 0, completions: 0, avgScore: 0 };

    return {
      courseName: course.title,
      ...avgMetrics,
    };
  }).slice(0, 5); // Top 5 courses

  // Radar chart data for course performance
  const performanceMetrics = selectedCourse !== 'all' && courseData.length > 0 ? [{
    metric: t('analytics.metrics.engagement'),
    value: courseData[0].avgProgress,
  }, {
    metric: t('analytics.metrics.completion'),
    value: (courseData[0].completionsCount / courseData[0].enrollmentsCount * 100) || 0,
  }, {
    metric: t('analytics.metrics.score'),
    value: courseData[0].avgScore,
  }, {
    metric: t('analytics.metrics.timeInvestment'),
    value: Math.min((courseData[0].totalTimeSpent / 60), 100), // Convert to hours, cap at 100
  }, {
    metric: t('analytics.metrics.participation'),
    value: (courseData[0].uniqueUsers / courseData[0].enrollmentsCount * 100) || 0,
  }] : [];

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="space-y-6">
      {/* Header with Course Selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('analytics.courseAnalytics.title')}
        </h2>
        <select
          value={selectedCourse}
          onChange={(e) => setSelectedCourse(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="all">{t('analytics.courseAnalytics.allCourses')}</option>
          {courses.map(course => (
            <option key={course.id} value={course.id}>
              {course.title}
            </option>
          ))}
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title={t('analytics.metrics.totalEnrollments')}
          value={totalEnrollments}
          icon={<Users className="h-6 w-6" />}
          trend="up"
          change={12}
        />
        <MetricCard
          title={t('analytics.metrics.completions')}
          value={totalCompletions}
          icon={<Trophy className="h-6 w-6" />}
          trend="up"
          change={8}
        />
        <MetricCard
          title={t('analytics.metrics.avgCompletionRate')}
          value={avgCompletionRate.toFixed(1)}
          suffix="%"
          icon={<TrendingUp className="h-6 w-6" />}
          trend={avgCompletionRate > 70 ? 'up' : 'down'}
        />
        <MetricCard
          title={t('analytics.metrics.avgScore')}
          value={avgCourseScore.toFixed(1)}
          suffix="%"
          icon={<BookOpen className="h-6 w-6" />}
          trend={avgCourseScore > 75 ? 'up' : 'down'}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Progress Over Time */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.progressOverTime')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={progressOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="enrollments" 
                stroke="#8884d8" 
                name={t('analytics.labels.enrollments')}
              />
              <Line 
                type="monotone" 
                dataKey="completions" 
                stroke="#82ca9d" 
                name={t('analytics.labels.completions')}
              />
              <Line 
                type="monotone" 
                dataKey="avgProgress" 
                stroke="#ffc658" 
                name={t('analytics.labels.avgProgress')}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Course Comparison */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            {t('analytics.charts.courseComparison')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={courseComparison}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="courseName" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="enrollments" fill="#8884d8" name={t('analytics.labels.enrollments')} />
              <Bar dataKey="completions" fill="#82ca9d" name={t('analytics.labels.completions')} />
              <Bar dataKey="avgScore" fill="#ffc658" name={t('analytics.labels.avgScore')} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Performance Radar Chart (for single course) */}
        {selectedCourse !== 'all' && performanceMetrics.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 lg:col-span-2">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              {t('analytics.charts.coursePerformance')}
            </h3>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={performanceMetrics}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar 
                  name={t('analytics.labels.performance')} 
                  dataKey="value" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.6} 
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Course Details Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('analytics.tables.courseDetails')}
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.date')}
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.avgScore')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {t('analytics.columns.timeSpent')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {courseData.slice(0, 10).map((course, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {new Date(course.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {course.enrollmentsCount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {course.completionsCount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${course.avgProgress}%` }}
                        />
                      </div>
                      <span>{course.avgProgress.toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {course.avgScore.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {course.totalTimeSpent} min
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

export default CourseAnalytics;