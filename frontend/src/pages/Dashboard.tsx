import React from 'react';
import { Users, Building2, GraduationCap, Mail, Shield, TrendingUp } from 'lucide-react';
import { StatsCard } from '../components/Dashboard';
import { useApi, useDocumentTitle } from '../hooks';
import type { DashboardStats } from '../types';
import apiClient from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { useTranslation } from 'react-i18next';

export const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  useDocumentTitle('dashboard.title');
  const { data: stats, loading, error } = useApi<DashboardStats>(
    () => apiClient.getDashboardStats()
  );

  if (loading) {
    return <LoadingSpinner size="large" className="mt-12" />;
  }

  if (error) {
    return <ErrorMessage message={error.detail} className="mt-4" />;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-secondary-900">{t('dashboard.title')}</h1>
        <p className="text-secondary-600 mt-1">{t('dashboard.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatsCard
          title={t('dashboard.stats.totalUsers')}
          value={stats?.total_users || 0}
          icon={Users}
          change={12}
          changeType="increase"
          color="primary"
        />
        <StatsCard
          title={t('dashboard.stats.activeUsers')}
          value={stats?.active_users || 0}
          icon={TrendingUp}
          change={8}
          changeType="increase"
          color="success"
        />
        <StatsCard
          title={t('dashboard.stats.companies')}
          value={stats?.total_companies || 0}
          icon={Building2}
          color="warning"
        />
        <StatsCard
          title={t('dashboard.stats.coursesCompleted')}
          value={stats?.courses_completed || 0}
          icon={GraduationCap}
          change={25}
          changeType="increase"
          color="primary"
        />
        <StatsCard
          title={t('dashboard.stats.phishingCampaigns')}
          value={stats?.phishing_campaigns || 0}
          icon={Mail}
          color="danger"
        />
        <StatsCard
          title={t('dashboard.stats.complianceScore')}
          value={`${stats?.compliance_score || 0}%`}
          icon={Shield}
          change={5}
          changeType="increase"
          color="success"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">{t('dashboard.recentActivity.title')}</h2>
          <div className="space-y-4">
            {[
              { user: 'John Doe', action: t('dashboard.recentActivity.completedCourse'), time: t('dashboard.recentActivity.hoursAgo', { hours: 2 }) },
              { user: 'Jane Smith', action: t('dashboard.recentActivity.failedPhishing'), time: t('dashboard.recentActivity.hoursAgo', { hours: 3 }) },
              { user: 'Mike Johnson', action: t('dashboard.recentActivity.joinedPlatform'), time: t('dashboard.recentActivity.hoursAgo', { hours: 5 }) },
              { user: 'Sarah Williams', action: t('dashboard.recentActivity.completedQuiz'), time: t('dashboard.recentActivity.hoursAgo', { hours: 6 }) },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-3 border-b border-secondary-100 last:border-0">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-semibold mr-3">
                    {activity.user.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-secondary-900">{activity.user}</p>
                    <p className="text-sm text-secondary-600">{activity.action}</p>
                  </div>
                </div>
                <p className="text-sm text-secondary-500">{activity.time}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">{t('dashboard.quickActions.title')}</h2>
          <div className="space-y-3">
            <button className="w-full btn-primary justify-start">
              <Mail className="w-5 h-5 mr-2" />
              {t('dashboard.quickActions.launchPhishing')}
            </button>
            <button className="w-full btn-secondary justify-start">
              <GraduationCap className="w-5 h-5 mr-2" />
              {t('dashboard.quickActions.createCourse')}
            </button>
            <button className="w-full btn-secondary justify-start">
              <Users className="w-5 h-5 mr-2" />
              {t('dashboard.quickActions.inviteUsers')}
            </button>
            <button className="w-full btn-secondary justify-start">
              <Shield className="w-5 h-5 mr-2" />
              {t('dashboard.quickActions.generateReport')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};