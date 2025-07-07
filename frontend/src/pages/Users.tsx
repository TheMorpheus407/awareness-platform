import React, { useState } from 'react';
import { Search, Plus, Edit, Trash2, MoreVertical } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import type { User, PaginatedResponse } from '../types';
import apiClient from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Common';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

export const Users: React.FC = () => {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  
  const { data, loading, error } = useApi<PaginatedResponse<User>>(
    () => apiClient.getUsers(page, 20),
    [page]
  );

  const filteredUsers = data?.items.filter(user =>
    user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.username.toLowerCase().includes(searchTerm.toLowerCase())
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
        <h1 className="text-2xl font-bold text-secondary-900">{t('users.title')}</h1>
        <p className="text-secondary-600 mt-1">{t('users.subtitle')}</p>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="relative flex-1 max-w-md mb-4 sm:mb-0">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
            <input
              type="text"
              placeholder={t('users.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 input-field"
            />
          </div>
          <button className="btn-primary">
            <Plus className="w-5 h-5 mr-2" />
            {t('users.addUser')}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-secondary-200">
                <th className="text-left py-3 px-4 font-semibold text-sm text-secondary-700">{t('users.table.name')}</th>
                <th className="text-left py-3 px-4 font-semibold text-sm text-secondary-700">{t('users.table.email')}</th>
                <th className="text-left py-3 px-4 font-semibold text-sm text-secondary-700">{t('users.table.role')}</th>
                <th className="text-left py-3 px-4 font-semibold text-sm text-secondary-700">{t('users.table.status')}</th>
                <th className="text-left py-3 px-4 font-semibold text-sm text-secondary-700">{t('users.table.created')}</th>
                <th className="text-right py-3 px-4 font-semibold text-sm text-secondary-700">{t('users.table.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers?.map((user) => (
                <tr key={user.id} className="border-b border-secondary-100 hover:bg-secondary-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-semibold mr-3">
                        {(user.full_name || user.username).charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium text-secondary-900">{user.full_name || user.username}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-secondary-600">{user.email}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.role === 'admin' 
                        ? 'bg-purple-100 text-purple-800' 
                        : user.role === 'company_admin'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? t('users.status.active') : t('users.status.inactive')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-secondary-600">
                    {format(new Date(user.created_at), 'MMM d, yyyy')}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button className="p-1 text-secondary-600 hover:text-primary-600">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="p-1 text-secondary-600 hover:text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <button className="p-1 text-secondary-600 hover:text-secondary-900">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data && data.pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-secondary-600">
              Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, data.total)} of {data.total} users
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