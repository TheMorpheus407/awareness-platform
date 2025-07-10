import React, { useState } from 'react';
import { Search, Plus, Edit, Trash2, Users, Globe } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import type { Company, PaginatedResponse } from '../types';
import apiClient from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

export const Companies: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  
  const { data, loading, error } = useApi<PaginatedResponse<Company>>(
    () => apiClient.getCompanies(page, 20),
    [page]
  );

  const filteredCompanies = data?.items.filter(company =>
    company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.domain.toLowerCase().includes(searchTerm.toLowerCase())
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
        <h1 className="text-2xl font-bold text-secondary-900">{t('companies.title')}</h1>
        <p className="text-secondary-600 mt-1">{t('companies.subtitle')}</p>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="relative flex-1 max-w-md mb-4 sm:mb-0">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
            <input
              type="text"
              placeholder={t('companies.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field"
            />
          </div>
          <button className="btn-primary">
            <Plus className="w-5 h-5 mr-2" />
            {t('companies.addCompany')}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCompanies?.map((company) => (
            <div key={company.id} className="border border-secondary-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 font-semibold text-lg">
                  {company.name.charAt(0).toUpperCase()}
                </div>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  company.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {company.is_active ? t('users.status.active') : t('users.status.inactive')}
                </span>
              </div>
              
              <h3 className="font-semibold text-secondary-900 mb-2">{company.name}</h3>
              
              <div className="space-y-2 text-sm text-secondary-600 mb-4">
                <div className="flex items-center">
                  <Globe className="w-4 h-4 mr-2" />
                  {company.domain}
                </div>
                <div className="flex items-center">
                  <Users className="w-4 h-4 mr-2" />
                  {t('companies.maxUsers', { count: company.max_users })}
                </div>
              </div>
              
              <p className="text-xs text-secondary-500 mb-4">
                {t('companies.table.created')} {format(new Date(company.created_at), 'MMM d, yyyy')}
              </p>
              
              <div className="flex space-x-2">
                <button className="flex-1 btn-secondary py-2 text-sm">
                  <Edit className="w-4 h-4 mr-1" />
                  {t('common.edit')}
                </button>
                <button className="p-2 text-secondary-600 hover:text-red-600 border border-secondary-300 rounded-lg hover:border-red-300">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {data && data.pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-secondary-600">
              {t('common.showing', { 
                from: (page - 1) * 20 + 1, 
                to: Math.min(page * 20, data.total), 
                total: data.total, 
                entity: t('companies.title').toLowerCase() 
              })}
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-secondary-300 rounded text-sm font-medium disabled:opacity-50"
              >
                {t('common.back')}
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page === data.pages}
                className="px-3 py-1 border border-secondary-300 rounded text-sm font-medium disabled:opacity-50"
              >
                {t('common.next')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};