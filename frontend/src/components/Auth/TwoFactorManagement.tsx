import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheckIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import apiClient from '../../services/api';
import type { BackupCodesStatus } from '../../types/auth';

interface TwoFactorManagementProps {
  isEnabled: boolean;
  onStatusChange: () => void;
}

export const TwoFactorManagement: React.FC<TwoFactorManagementProps> = ({ 
  isEnabled, 
  onStatusChange 
}) => {
  const { t } = useTranslation();
  const [showDisableForm, setShowDisableForm] = useState(false);
  const [showRegenerateForm, setShowRegenerateForm] = useState(false);
  const [backupCodesStatus, setBackupCodesStatus] = useState<BackupCodesStatus | null>(null);
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [newBackupCodes, setNewBackupCodes] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isEnabled) {
      fetchBackupCodesStatus();
    }
  }, [isEnabled]);

  const fetchBackupCodesStatus = async () => {
    try {
      const status = await apiClient.getBackupCodesStatus();
      setBackupCodesStatus(status);
    } catch (err) {
      console.error('Failed to fetch backup codes status:', err);
    }
  };

  const handleDisable2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await apiClient.disable2FA(password, totpCode);
      setPassword('');
      setTotpCode('');
      setShowDisableForm(false);
      onStatusChange();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.twoFactor.errors.disableFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateBackupCodes = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.regenerateBackupCodes(password, totpCode);
      setNewBackupCodes(response.backup_codes);
      setPassword('');
      setTotpCode('');
      fetchBackupCodesStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.twoFactor.errors.regenerateFailed'));
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setPassword('');
    setTotpCode('');
    setError('');
    setShowDisableForm(false);
    setShowRegenerateForm(false);
    setNewBackupCodes([]);
  };

  if (!isEnabled) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <ShieldCheckIcon className="h-6 w-6 text-gray-400 mr-3" />
            <h3 className="text-lg font-medium text-gray-900">{t('auth.twoFactor.title')}</h3>
          </div>
          <span className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded-full">
            {t('auth.twoFactor.status.disabled')}
          </span>
        </div>
        <p className="text-gray-600">
          {t('auth.twoFactor.disabledMessage')}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <ShieldCheckIcon className="h-6 w-6 text-green-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Two-Factor Authentication</h3>
        </div>
        <span className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full">
          {t('auth.twoFactor.status.enabled')}
        </span>
      </div>

      {/* Backup Codes Status */}
      {backupCodesStatus && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">{t('auth.twoFactor.backupCodes.title')}</h4>
          <p className="text-sm text-gray-600 mb-2">
            {t('auth.twoFactor.backupCodes.remaining', { remaining: backupCodesStatus.remaining_codes, total: backupCodesStatus.total_codes })}
          </p>
          {backupCodesStatus.remaining_codes <= 2 && (
            <div className="flex items-center text-yellow-700 text-sm">
              <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
              <span>{t('auth.twoFactor.backupCodes.lowWarning')}</span>
            </div>
          )}
        </div>
      )}

      {/* New Backup Codes Display */}
      {newBackupCodes.length > 0 && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="font-medium text-yellow-800 mb-2">{t('auth.twoFactor.backupCodes.newCodesTitle')}</h4>
          <p className="text-sm text-yellow-700 mb-3">
            {t('auth.twoFactor.backupCodes.newCodesMessage')}
          </p>
          <div className="grid grid-cols-2 gap-2 mb-3">
            {newBackupCodes.map((code, index) => (
              <code key={index} className="text-sm font-mono bg-white px-2 py-1 rounded border border-yellow-300">
                {code}
              </code>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setNewBackupCodes([])}
            className="text-sm text-yellow-700 hover:text-yellow-800 underline"
          >
            {t('auth.twoFactor.backupCodes.confirmSaved')}
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-3">
        {!showDisableForm && !showRegenerateForm && (
          <>
            <button
              type="button"
              onClick={() => setShowRegenerateForm(true)}
              className="w-full px-4 py-2 text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100"
            >
              {t('auth.twoFactor.actions.regenerate')}
            </button>
            <button
              type="button"
              onClick={() => setShowDisableForm(true)}
              className="w-full px-4 py-2 text-red-600 bg-red-50 rounded-md hover:bg-red-100"
            >
              {t('auth.twoFactor.actions.disable')}
            </button>
          </>
        )}

        {/* Disable 2FA Form */}
        {showDisableForm && (
          <form onSubmit={handleDisable2FA} className="space-y-4">
            <h4 className="font-medium text-gray-900">{t('auth.twoFactor.confirmDisable.title')}</h4>
            
            <div>
              <label htmlFor="disable-password" className="block text-sm font-medium text-gray-700 mb-1">
                {t('auth.twoFactor.confirmDisable.passwordLabel')}
              </label>
              <input
                type="password"
                id="disable-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                required
                autoComplete="current-password"
              />
            </div>

            <div>
              <label htmlFor="disable-code" className="block text-sm font-medium text-gray-700 mb-1">
                {t('auth.twoFactor.confirmDisable.codeLabel')}
              </label>
              <input
                type="text"
                id="disable-code"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 text-center font-mono"
                placeholder="000000"
                maxLength={6}
                pattern="[0-9]{6}"
                required
                autoComplete="one-time-code"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                {error}
              </div>
            )}

            <div className="flex space-x-3">
              <button
                type="button"
                onClick={resetForm}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                disabled={loading}
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                disabled={loading || !password || totpCode.length !== 6}
              >
                {loading ? t('auth.twoFactor.confirmDisable.disabling') : t('auth.twoFactor.confirmDisable.confirmButton')}
              </button>
            </div>
          </form>
        )}

        {/* Regenerate Backup Codes Form */}
        {showRegenerateForm && (
          <form onSubmit={handleRegenerateBackupCodes} className="space-y-4">
            <h4 className="font-medium text-gray-900">{t('auth.twoFactor.regenerate.title')}</h4>
            
            <div>
              <label htmlFor="regen-password" className="block text-sm font-medium text-gray-700 mb-1">
                {t('auth.twoFactor.regenerate.passwordLabel')}
              </label>
              <input
                type="password"
                id="regen-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
                autoComplete="current-password"
              />
            </div>

            <div>
              <label htmlFor="regen-code" className="block text-sm font-medium text-gray-700 mb-1">
                {t('auth.twoFactor.confirmDisable.codeLabel')}
              </label>
              <input
                type="text"
                id="regen-code"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-center font-mono"
                placeholder="000000"
                maxLength={6}
                pattern="[0-9]{6}"
                required
                autoComplete="one-time-code"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
                {error}
              </div>
            )}

            <div className="flex space-x-3">
              <button
                type="button"
                onClick={resetForm}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                disabled={loading}
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                disabled={loading || !password || totpCode.length !== 6}
              >
                {loading ? t('auth.twoFactor.regenerate.generating') : t('auth.twoFactor.regenerate.confirmButton')}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};