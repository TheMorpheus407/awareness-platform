import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QrCodeIcon, ShieldCheckIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import { CheckIcon } from '@heroicons/react/24/solid';
import apiClient from '../../services/api';
import type { TwoFactorSetupResponse } from '../../types/auth';

interface TwoFactorSetupProps {
  onComplete: () => void;
  onCancel: () => void;
}

export const TwoFactorSetup: React.FC<TwoFactorSetupProps> = ({ onComplete, onCancel }) => {
  const { t } = useTranslation();
  const [step, setStep] = useState<'password' | 'setup' | 'verify'>('password');
  const [password, setPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [setupData, setSetupData] = useState<TwoFactorSetupResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.setup2FA(password);
      setSetupData(response);
      setStep('setup');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.twoFactor.errors.setupFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await apiClient.verify2FASetup(verificationCode);
      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.twoFactor.errors.invalidCode'));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, type: 'secret' | 'codes') => {
    navigator.clipboard.writeText(text);
    if (type === 'secret') {
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    } else {
      setCopiedCodes(true);
      setTimeout(() => setCopiedCodes(false), 2000);
    }
  };

  if (step === 'password') {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center mb-4">
          <ShieldCheckIcon className="h-8 w-8 text-indigo-600 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">{t('auth.twoFactor.setup.title')}</h2>
        </div>
        
        <p className="text-gray-600 mb-6">
          {t('auth.twoFactor.setup.passwordPrompt')}
        </p>

        <form onSubmit={handlePasswordSubmit}>
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              {t('auth.twoFactor.setup.confirmPassword')}
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
              disabled={loading}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              disabled={loading || !password}
            >
              {loading ? t('common.processing') : t('common.continue')}
            </button>
          </div>
        </form>
      </div>
    );
  }

  if (step === 'setup' && setupData) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('auth.twoFactor.setup.authenticatorTitle')}</h2>

        <div className="space-y-6">
          {/* Step 1: Install App */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('auth.twoFactor.setup.step1.title')}</h3>
            <p className="text-gray-600">
              {t('auth.twoFactor.setup.step1.description')}
            </p>
          </div>

          {/* Step 2: Scan QR Code */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('auth.twoFactor.setup.step2.title')}</h3>
            <p className="text-gray-600 mb-4">
              {t('auth.twoFactor.setup.step2.description')}
            </p>
            <div className="flex justify-center mb-4">
              <img 
                src={`data:image/png;base64,${setupData.qr_code}`} 
                alt="2FA QR Code" 
                className="border-2 border-gray-300 rounded"
              />
            </div>
            
            {/* Manual entry option */}
            <div className="bg-gray-50 p-4 rounded-md">
              <p className="text-sm text-gray-600 mb-2">{t('auth.twoFactor.setup.manualEntry')}</p>
              <div className="flex items-center justify-between bg-white p-2 rounded border border-gray-300">
                <code className="text-sm font-mono">{setupData.manual_entry_key}</code>
                <button
                  type="button"
                  onClick={() => copyToClipboard(setupData.manual_entry_key, 'secret')}
                  className="ml-2 p-1 text-gray-500 hover:text-gray-700"
                >
                  {copiedSecret ? (
                    <CheckIcon className="h-5 w-5 text-green-500" />
                  ) : (
                    <ClipboardDocumentIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Step 3: Save Backup Codes */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('auth.twoFactor.setup.step3.title')}</h3>
            <p className="text-gray-600 mb-4">
              {t('auth.twoFactor.setup.step3.description')}
            </p>
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-md">
              <div className="flex justify-between items-start mb-3">
                <p className="text-sm font-medium text-yellow-800">{t('auth.twoFactor.setup.backupCodesLabel')}</p>
                <button
                  type="button"
                  onClick={() => copyToClipboard(setupData.backup_codes.join('\n'), 'codes')}
                  className="p-1 text-yellow-700 hover:text-yellow-900"
                >
                  {copiedCodes ? (
                    <CheckIcon className="h-5 w-5 text-green-600" />
                  ) : (
                    <ClipboardDocumentIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {setupData.backup_codes.map((code, index) => (
                  <code key={index} className="text-sm font-mono bg-white px-2 py-1 rounded">
                    {code}
                  </code>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={() => setStep('verify')}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            {t('auth.twoFactor.setup.continueToVerification')}
          </button>
        </div>
      </div>
    );
  }

  if (step === 'verify') {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('auth.twoFactor.verify.title')}</h2>
        
        <p className="text-gray-600 mb-6">
          {t('auth.twoFactor.verify.description')}
        </p>

        <form onSubmit={handleVerification}>
          <div className="mb-4">
            <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
              {t('auth.twoFactor.verify.codeLabel')}
            </label>
            <input
              type="text"
              id="code"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-center text-2xl font-mono"
              placeholder="000000"
              maxLength={6}
              pattern="[0-9]{6}"
              required
              autoComplete="one-time-code"
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setStep('setup')}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
              disabled={loading}
            >
              {t('common.back')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              disabled={loading || verificationCode.length !== 6}
            >
              {loading ? t('auth.twoFactor.verify.verifying') : t('auth.twoFactor.verify.complete')}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return null;
};