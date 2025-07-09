import React from 'react';
import { 
  Users, 
  Building2, 
  GraduationCap, 
  Mail, 
  Shield, 
  TrendingUp,
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  Target,
  Award,
  BookOpen,
  Eye,
  FileText
} from 'lucide-react';
import { StatsCard } from '../components/Dashboard';
import { useApi, useDocumentTitle } from '../hooks';
import type { DashboardStats } from '../types';
import apiClient from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';

const COLORS = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export const DashboardEnhanced: React.FC = () => {
  const { t } = useTranslation();
  useDocumentTitle('dashboard.title');
  const { data: stats, loading, error } = useApi<DashboardStats>(
    () => apiClient.getDashboardStats()
  );

  // Mock data for charts
  const phishingTrends = [
    { month: 'Jan', sent: 120, clicked: 45, reported: 65 },
    { month: 'Feb', sent: 150, clicked: 38, reported: 85 },
    { month: 'Mar', sent: 180, clicked: 32, reported: 110 },
    { month: 'Apr', sent: 200, clicked: 28, reported: 140 },
    { month: 'May', sent: 220, clicked: 22, reported: 165 },
    { month: 'Jun', sent: 250, clicked: 18, reported: 195 },
  ];

  const trainingProgress = [
    { module: 'Password Security', completed: 85, inProgress: 10, notStarted: 5 },
    { module: 'Phishing Awareness', completed: 72, inProgress: 18, notStarted: 10 },
    { module: 'Data Protection', completed: 68, inProgress: 20, notStarted: 12 },
    { module: 'Social Engineering', completed: 60, inProgress: 25, notStarted: 15 },
    { module: 'Mobile Security', completed: 55, inProgress: 30, notStarted: 15 },
  ];

  const riskScore = [
    { subject: 'Email Security', score: 85, fullMark: 100 },
    { subject: 'Password Strength', score: 72, fullMark: 100 },
    { subject: 'Device Security', score: 68, fullMark: 100 },
    { subject: 'Data Handling', score: 78, fullMark: 100 },
    { subject: 'Incident Response', score: 82, fullMark: 100 },
    { subject: 'Compliance', score: 90, fullMark: 100 },
  ];

  const departmentStats = [
    { name: 'IT', value: 95, users: 45 },
    { name: 'Finance', value: 88, users: 32 },
    { name: 'HR', value: 82, users: 28 },
    { name: 'Sales', value: 75, users: 65 },
    { name: 'Marketing', value: 70, users: 38 },
  ];

  const recentIncidents = [
    { type: 'Phishing Attempt', count: 12, trend: -25 },
    { type: 'Password Breach', count: 3, trend: -50 },
    { type: 'Data Leak', count: 1, trend: -75 },
    { type: 'Malware Detection', count: 5, trend: -40 },
  ];

  if (loading) {
    return <LoadingSpinner size="large" className="mt-12" />;
  }

  if (error) {
    return <ErrorMessage message={error.detail} className="mt-4" />;
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-6"
    >
      {/* Header Section */}
      <motion.div variants={itemVariants}>
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {t('dashboard.title')}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Generate Report
            </button>
            <button className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-2">
              <Eye className="w-4 h-4" />
              View Details
            </button>
          </div>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div 
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <StatsCard
          title="Security Score"
          value={`${stats?.compliance_score || 85}%`}
          icon={Shield}
          change={5}
          changeType="increase"
          color="success"
          subtitle="Above industry average"
        />
        <StatsCard
          title="Active Threats"
          value={12}
          icon={AlertCircle}
          change={25}
          changeType="decrease"
          color="danger"
          subtitle="Down from last week"
        />
        <StatsCard
          title="Training Completion"
          value="78%"
          icon={GraduationCap}
          change={12}
          changeType="increase"
          color="primary"
          subtitle="352 of 450 users"
        />
        <StatsCard
          title="Phishing Success"
          value="92%"
          icon={Target}
          change={8}
          changeType="increase"
          color="success"
          subtitle="Detection rate"
        />
      </motion.div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Phishing Campaign Trends */}
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Phishing Campaign Performance
            </h2>
            <select className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1 bg-white dark:bg-gray-700">
              <option>Last 6 months</option>
              <option>Last year</option>
              <option>All time</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={phishingTrends}>
              <defs>
                <linearGradient id="colorSent" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorReported" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }} 
              />
              <Area 
                type="monotone" 
                dataKey="sent" 
                stroke="#0ea5e9" 
                fillOpacity={1} 
                fill="url(#colorSent)" 
                strokeWidth={2}
              />
              <Area 
                type="monotone" 
                dataKey="reported" 
                stroke="#22c55e" 
                fillOpacity={1} 
                fill="url(#colorReported)" 
                strokeWidth={2}
              />
              <Area 
                type="monotone" 
                dataKey="clicked" 
                stroke="#ef4444" 
                fill="#ef4444" 
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Legend />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Risk Assessment Radar */}
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Security Risk Assessment
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={riskScore}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" stroke="#6b7280" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#6b7280" />
              <Radar 
                name="Current Score" 
                dataKey="score" 
                stroke="#0ea5e9" 
                fill="#0ea5e9" 
                fillOpacity={0.6}
                strokeWidth={2}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Training Progress and Department Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Training Progress */}
        <motion.div variants={itemVariants} className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Training Module Progress
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trainingProgress} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" domain={[0, 100]} stroke="#6b7280" />
              <YAxis type="category" dataKey="module" stroke="#6b7280" width={120} />
              <Tooltip />
              <Legend />
              <Bar dataKey="completed" stackId="a" fill="#22c55e" />
              <Bar dataKey="inProgress" stackId="a" fill="#f59e0b" />
              <Bar dataKey="notStarted" stackId="a" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Department Performance */}
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Department Performance
          </h2>
          <div className="space-y-4">
            {departmentStats.map((dept, index) => (
              <div key={dept.name}>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {dept.name}
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {dept.value}% ({dept.users} users)
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${dept.value}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                    className="h-2 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Recent Activity and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Security Incidents */}
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Recent Security Incidents
          </h2>
          <div className="space-y-4">
            {recentIncidents.map((incident, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    incident.trend < -50 ? 'bg-green-100 text-green-600' : 
                    incident.trend < 0 ? 'bg-yellow-100 text-yellow-600' : 
                    'bg-red-100 text-red-600'
                  }`}>
                    <AlertCircle className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{incident.type}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {incident.count} incidents this month
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-sm">
                  {incident.trend < 0 ? (
                    <>
                      <TrendingUp className="w-4 h-4 text-green-500 rotate-180" />
                      <span className="text-green-600 font-medium">{Math.abs(incident.trend)}%</span>
                    </>
                  ) : (
                    <>
                      <TrendingUp className="w-4 h-4 text-red-500" />
                      <span className="text-red-600 font-medium">{incident.trend}%</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Quick Actions with Icons */}
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Quick Actions
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <button className="flex flex-col items-center justify-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors group">
              <Mail className="w-8 h-8 text-blue-600 mb-2 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">Launch Campaign</span>
            </button>
            <button className="flex flex-col items-center justify-center p-6 bg-green-50 dark:bg-green-900/20 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors group">
              <BookOpen className="w-8 h-8 text-green-600 mb-2 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">Create Training</span>
            </button>
            <button className="flex flex-col items-center justify-center p-6 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors group">
              <Users className="w-8 h-8 text-purple-600 mb-2 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">Invite Users</span>
            </button>
            <button className="flex flex-col items-center justify-center p-6 bg-orange-50 dark:bg-orange-900/20 rounded-lg hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors group">
              <FileText className="w-8 h-8 text-orange-600 mb-2 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-gray-900 dark:text-white">View Reports</span>
            </button>
          </div>
        </motion.div>
      </div>

      {/* Achievement Banner */}
      <motion.div 
        variants={itemVariants}
        className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg p-6 text-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Award className="w-12 h-12" />
            <div>
              <h3 className="text-xl font-semibold">Outstanding Security Performance!</h3>
              <p className="text-blue-100">
                Your organization has achieved a 92% phishing detection rate this month, 
                exceeding the industry average by 35%.
              </p>
            </div>
          </div>
          <button className="px-6 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium">
            View Details
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};