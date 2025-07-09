/**
 * Phishing simulation dashboard component
 */

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Shield,
  Mail,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  BarChart3,
  Plus
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { phishingApi } from '../../services/phishingApi';
import type { PhishingDashboard as DashboardData, CampaignStatus } from '../../types/phishing';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { formatPercentage } from '../../utils/format';

const PhishingDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await phishingApi.getDashboard();
      setDashboard(data);
    } catch (err) {
      setError(t('phishing.dashboard.loadError'));
      console.error('Failed to load phishing dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: CampaignStatus) => {
    switch (status) {
      case CampaignStatus.DRAFT:
        return 'bg-gray-100 text-gray-800';
      case CampaignStatus.SCHEDULED:
        return 'bg-blue-100 text-blue-800';
      case CampaignStatus.RUNNING:
        return 'bg-green-100 text-green-800';
      case CampaignStatus.COMPLETED:
        return 'bg-purple-100 text-purple-800';
      case CampaignStatus.CANCELLED:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getClickRateTrend = (rate: number) => {
    if (rate > 30) {
      return { icon: TrendingUp, color: 'text-red-600', label: t('phishing.dashboard.highRisk') };
    } else if (rate > 15) {
      return { icon: Activity, color: 'text-yellow-600', label: t('phishing.dashboard.mediumRisk') };
    } else {
      return { icon: TrendingDown, color: 'text-green-600', label: t('phishing.dashboard.lowRisk') };
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-lg">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  const clickRateTrend = getClickRateTrend(dashboard.overall_click_rate);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('phishing.dashboard.title')}</h1>
          <p className="mt-1 text-sm text-gray-500">{t('phishing.dashboard.subtitle')}</p>
        </div>
        <Link
          to="/phishing/campaigns/new"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          {t('phishing.campaigns.create')}
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Campaigns */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Shield className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {t('phishing.dashboard.totalCampaigns')}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboard.total_campaigns}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Active Campaigns */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Mail className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {t('phishing.dashboard.activeCampaigns')}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboard.active_campaigns}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Users Tested */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {t('phishing.dashboard.usersTested')}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {dashboard.total_users_tested}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Overall Click Rate */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <clickRateTrend.icon className={`h-6 w-6 ${clickRateTrend.color}`} />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {t('phishing.dashboard.overallClickRate')}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className={`text-2xl font-semibold ${clickRateTrend.color}`}>
                      {formatPercentage(dashboard.overall_click_rate)}
                    </div>
                    <div className="ml-2 flex items-baseline text-sm text-gray-600">
                      {clickRateTrend.label}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Campaigns */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              {t('phishing.dashboard.recentCampaigns')}
            </h3>
            <Link
              to="/phishing/campaigns"
              className="text-sm font-medium text-blue-600 hover:text-blue-500"
            >
              {t('phishing.dashboard.viewAll')}
            </Link>
          </div>
        </div>
        <div className="px-4 py-5 sm:p-6">
          {dashboard.recent_campaigns.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              {t('phishing.dashboard.noCampaigns')}
            </p>
          ) : (
            <div className="space-y-4">
              {dashboard.recent_campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <Link
                      to={`/phishing/campaigns/${campaign.id}`}
                      className="text-sm font-medium text-gray-900 hover:text-blue-600"
                    >
                      {campaign.name}
                    </Link>
                    <div className="mt-1 flex items-center space-x-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          campaign.status
                        )}`}
                      >
                        {t(`phishing.status.${campaign.status}`)}
                      </span>
                      {campaign.started_at && (
                        <span className="text-xs text-gray-500">
                          {new Date(campaign.started_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {formatPercentage(campaign.click_rate)}
                      </p>
                      <p className="text-xs text-gray-500">{t('phishing.dashboard.clickRate')}</p>
                    </div>
                    <BarChart3 className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertTriangle className="h-6 w-6 text-blue-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              {t('phishing.dashboard.quickActions.title')}
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc space-y-1 pl-5">
                <li>
                  <Link to="/phishing/templates" className="font-medium hover:text-blue-600">
                    {t('phishing.dashboard.quickActions.browseTemplates')}
                  </Link>
                </li>
                <li>
                  <Link to="/phishing/analytics" className="font-medium hover:text-blue-600">
                    {t('phishing.dashboard.quickActions.viewAnalytics')}
                  </Link>
                </li>
                <li>
                  <Link to="/phishing/compliance" className="font-medium hover:text-blue-600">
                    {t('phishing.dashboard.quickActions.complianceReport')}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhishingDashboard;