/**
 * Phishing campaign list component
 */

import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  Calendar,
  Users,
  Mail,
  MousePointer,
  AlertTriangle,
  MoreVertical,
  Play,
  Pause,
  X,
  BarChart3
} from 'lucide-react';
import { phishingApi } from '../../services/phishingApi';
import type { PhishingCampaign } from '../../types/phishing';
import { CampaignStatus } from '../../types/phishing';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { formatPercentage, formatDate } from '../../utils/format';

const CampaignList: React.FC = () => {
  const { t } = useTranslation();
  const [campaigns, setCampaigns] = useState<PhishingCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showActions, setShowActions] = useState<number | null>(null);

  useEffect(() => {
    loadCampaigns();
  }, [statusFilter]);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const params = statusFilter !== 'all' ? { status: statusFilter } : undefined;
      const data = await phishingApi.getCampaigns(params);
      setCampaigns(data);
    } catch (err) {
      setError(t('phishing.campaigns.loadError'));
      console.error('Failed to load campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartCampaign = async (id: number) => {
    try {
      await phishingApi.startCampaign(id);
      await loadCampaigns();
    } catch (err) {
      console.error('Failed to start campaign:', err);
    }
  };

  const handleCancelCampaign = async (id: number) => {
    if (window.confirm(t('phishing.campaigns.confirmCancel'))) {
      try {
        await phishingApi.cancelCampaign(id);
        await loadCampaigns();
      } catch (err) {
        console.error('Failed to cancel campaign:', err);
      }
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

  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('phishing.campaigns.title')}</h1>
          <p className="mt-1 text-sm text-gray-500">{t('phishing.campaigns.subtitle')}</p>
        </div>
        <Link
          to="/phishing/campaigns/new"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          {t('phishing.campaigns.create')}
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={t('phishing.campaigns.search')}
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as CampaignStatus | 'all')}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="all">{t('phishing.campaigns.allStatuses')}</option>
              <option value={CampaignStatus.DRAFT}>{t('phishing.status.draft')}</option>
              <option value={CampaignStatus.SCHEDULED}>{t('phishing.status.scheduled')}</option>
              <option value={CampaignStatus.RUNNING}>{t('phishing.status.running')}</option>
              <option value={CampaignStatus.COMPLETED}>{t('phishing.status.completed')}</option>
              <option value={CampaignStatus.CANCELLED}>{t('phishing.status.cancelled')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Campaign List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {filteredCampaigns.length === 0 ? (
          <div className="text-center py-12">
            <Mail className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {t('phishing.campaigns.noCampaigns')}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {t('phishing.campaigns.noCampaignsDescription')}
            </p>
            <div className="mt-6">
              <Link
                to="/phishing/campaigns/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                {t('phishing.campaigns.createFirst')}
              </Link>
            </div>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {filteredCampaigns.map((campaign) => (
              <li key={campaign.id}>
                <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center">
                          <Link
                            to={`/phishing/campaigns/${campaign.id}`}
                            className="text-sm font-medium text-blue-600 hover:text-blue-500 truncate"
                          >
                            {campaign.name}
                          </Link>
                          <span
                            className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                              campaign.status
                            )}`}
                          >
                            {t(`phishing.status.${campaign.status}`)}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500">
                          <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                          {campaign.started_at
                            ? t('phishing.campaigns.startedAt', {
                                date: formatDate(campaign.started_at)
                              })
                            : campaign.scheduled_at
                            ? t('phishing.campaigns.scheduledFor', {
                                date: formatDate(campaign.scheduled_at)
                              })
                            : t('phishing.campaigns.notScheduled')}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      {/* Campaign Stats */}
                      <div className="flex items-center space-x-6 text-sm">
                        <div className="flex items-center text-gray-500">
                          <Users className="h-4 w-4 mr-1" />
                          <span>{campaign.total_recipients}</span>
                        </div>
                        <div className="flex items-center text-gray-500">
                          <Mail className="h-4 w-4 mr-1" />
                          <span>{campaign.emails_sent}</span>
                        </div>
                        <div className="flex items-center text-gray-500">
                          <MousePointer className="h-4 w-4 mr-1" />
                          <span>{formatPercentage(campaign.click_rate)}</span>
                        </div>
                        <div className="flex items-center text-gray-500">
                          <AlertTriangle className="h-4 w-4 mr-1" />
                          <span>{campaign.reported}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="relative">
                        <button
                          onClick={() => setShowActions(showActions === campaign.id ? null : campaign.id)}
                          className="p-2 rounded-full hover:bg-gray-200"
                        >
                          <MoreVertical className="h-5 w-5 text-gray-500" />
                        </button>
                        {showActions === campaign.id && (
                          <div className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5">
                            <Link
                              to={`/phishing/campaigns/${campaign.id}`}
                              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            >
                              <BarChart3 className="h-4 w-4 mr-2" />
                              {t('phishing.campaigns.viewDetails')}
                            </Link>
                            {campaign.status === CampaignStatus.SCHEDULED && (
                              <button
                                onClick={() => handleStartCampaign(campaign.id)}
                                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                              >
                                <Play className="h-4 w-4 mr-2" />
                                {t('phishing.campaigns.start')}
                              </button>
                            )}
                            {(campaign.status === CampaignStatus.RUNNING ||
                              campaign.status === CampaignStatus.SCHEDULED) && (
                              <button
                                onClick={() => handleCancelCampaign(campaign.id)}
                                className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-gray-100"
                              >
                                <X className="h-4 w-4 mr-2" />
                                {t('phishing.campaigns.cancel')}
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default CampaignList;