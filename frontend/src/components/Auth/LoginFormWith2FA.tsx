import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, LogIn, ShieldCheck, Key } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import type { LoginCredentials, LoginWith2FACredentials } from '../../types';
import { LoadingSpinner } from '../Common';
import { useTranslation } from 'react-i18next';
import apiClient from '../../services/api';

export const LoginFormWith2FA: React.FC = () => {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuth();
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [credentials, setCredentials] = useState<LoginCredentials | null>(null);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginCredentials>();

  const {
    register: register2FA,
    handleSubmit: handleSubmit2FA,
    formState: { errors: errors2FA },
    reset: reset2FA,
  } = useForm<{ totpCode?: string; backupCode?: string }>();

  const onSubmitInitial = async (data: LoginCredentials) => {
    setError('');
    setIsLoading(true);
    setCredentials(data);

    try {
      const response = await apiClient.login(data.email, data.password);
      
      // If login successful without 2FA
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Get user data
      const userData = await apiClient.getCurrentUser();
      setToken(response.access_token);
      setUser(userData);
      
      navigate('/dashboard');
    } catch (error: any) {
      if (error.requires2FA) {
        setRequires2FA(true);
        setIsLoading(false);
      } else {
        setError(error.response?.data?.detail || 'Invalid email or password');
        setIsLoading(false);
      }
    }
  };

  const onSubmit2FA = async (data: { totpCode?: string; backupCode?: string }) => {
    if (!credentials) return;
    
    setError('');
    setIsLoading(true);

    try {
      let response;
      
      if (useBackupCode && data.backupCode) {
        response = await apiClient.loginWithBackupCode(
          credentials.email,
          credentials.password,
          data.backupCode
        );
      } else if (data.totpCode) {
        response = await apiClient.loginWith2FA(
          credentials.email,
          credentials.password,
          data.totpCode
        );
      }

      if (response) {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        
        // Get user data
        const userData = await apiClient.getCurrentUser();
        setToken(response.access_token);
        setUser(userData);
        
        navigate('/dashboard');
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Invalid authentication code');
      reset2FA();
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setRequires2FA(false);
    setUseBackupCode(false);
    setCredentials(null);
    setError('');
    reset2FA();
  };

  // Initial login form
  if (!requires2FA) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
                <LogIn className="w-8 h-8 text-primary-600" />
              </div>
              <h2 className="text-3xl font-bold text-secondary-900">{t('auth.login.title')}</h2>
              <p className="text-secondary-600 mt-2">{t('auth.login.subtitle')}</p>
            </div>

            <form onSubmit={handleSubmit(onSubmitInitial)} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-secondary-700 mb-2">
                  {t('auth.login.emailLabel')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-secondary-400" />
                  </div>
                  <input
                    {...register('email', {
                      required: t('auth.errors.emailRequired'),
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: t('auth.errors.invalidEmail'),
                      },
                    })}
                    type="email"
                    autoComplete="email"
                    className="pl-10 input-field"
                    placeholder={t('auth.login.emailPlaceholder')}
                  />
                </div>
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-secondary-700 mb-2">
                  {t('auth.login.passwordLabel')}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-secondary-400" />
                  </div>
                  <input
                    {...register('password', {
                      required: t('auth.errors.passwordRequired'),
                      minLength: {
                        value: 6,
                        message: t('auth.errors.passwordMinLength'),
                      },
                    })}
                    type="password"
                    autoComplete="current-password"
                    className="pl-10 input-field"
                    placeholder={t('auth.login.passwordPlaceholder')}
                  />
                </div>
                {errors.password && (
                  <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                )}
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
                  {error}
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-secondary-700">
                    {t('auth.login.rememberMe')}
                  </label>
                </div>

                <div className="text-sm">
                  <a href="#" className="font-medium text-primary-600 hover:text-primary-500">
                    {t('auth.login.forgotPassword')}
                  </a>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary py-3 flex items-center justify-center"
              >
                {isLoading ? (
                  <LoadingSpinner size="small" />
                ) : (
                  <>
                    <LogIn className="w-5 h-5 mr-2" />
                    {t('auth.login.signIn')}
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-secondary-600">
                {t('auth.login.noAccount')}{' '}
                <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500">
                  {t('auth.login.signUp')}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2FA form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <ShieldCheck className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-secondary-900">Two-Factor Authentication</h2>
            <p className="text-secondary-600 mt-2">
              {useBackupCode ? 'Enter your backup code' : 'Enter the code from your authenticator app'}
            </p>
          </div>

          <form onSubmit={handleSubmit2FA(onSubmit2FA)} className="space-y-6">
            {!useBackupCode ? (
              <div>
                <label htmlFor="totpCode" className="block text-sm font-medium text-secondary-700 mb-2">
                  Authentication Code
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Key className="h-5 w-5 text-secondary-400" />
                  </div>
                  <input
                    {...register2FA('totpCode', {
                      required: 'Authentication code is required',
                      pattern: {
                        value: /^[0-9]{6}$/,
                        message: 'Code must be 6 digits',
                      },
                    })}
                    type="text"
                    autoComplete="one-time-code"
                    className="pl-10 input-field text-center text-2xl font-mono"
                    placeholder="000000"
                    maxLength={6}
                  />
                </div>
                {errors2FA.totpCode && (
                  <p className="mt-1 text-sm text-red-600">{errors2FA.totpCode.message}</p>
                )}
              </div>
            ) : (
              <div>
                <label htmlFor="backupCode" className="block text-sm font-medium text-secondary-700 mb-2">
                  Backup Code
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Key className="h-5 w-5 text-secondary-400" />
                  </div>
                  <input
                    {...register2FA('backupCode', {
                      required: 'Backup code is required',
                      pattern: {
                        value: /^[A-Z0-9]{4}-[A-Z0-9]{4}$/,
                        message: 'Invalid backup code format',
                      },
                    })}
                    type="text"
                    className="pl-10 input-field text-center font-mono"
                    placeholder="XXXX-XXXX"
                    maxLength={9}
                  />
                </div>
                {errors2FA.backupCode && (
                  <p className="mt-1 text-sm text-red-600">{errors2FA.backupCode.message}</p>
                )}
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary py-3 flex items-center justify-center"
              >
                {isLoading ? (
                  <LoadingSpinner size="small" />
                ) : (
                  <>
                    <ShieldCheck className="w-5 h-5 mr-2" />
                    Verify
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={() => setUseBackupCode(!useBackupCode)}
                className="w-full text-sm text-primary-600 hover:text-primary-700"
              >
                {useBackupCode ? 'Use authenticator app instead' : 'Use backup code instead'}
              </button>

              <button
                type="button"
                onClick={handleBack}
                className="w-full text-sm text-secondary-600 hover:text-secondary-700"
              >
                Back to login
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};