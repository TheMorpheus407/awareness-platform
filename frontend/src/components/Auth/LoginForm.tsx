import React from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, LogIn } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import type { LoginCredentials } from '../../types';
import { LoadingSpinner, LanguageSwitcher } from '../Common';
import { useTranslation } from 'react-i18next';

export const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const { t } = useTranslation();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginCredentials>();

  const onSubmit = async (data: LoginCredentials) => {
    try {
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch (error) {
      // Error is handled in the store
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-primary-50 to-primary-100 px-4 sm:px-6 lg:px-8">
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>
      <div className="flex-1 flex items-center justify-center">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <LogIn className="w-8 h-8 text-primary-600" />
            </div>
            <h2 className="text-3xl font-bold text-secondary-900">{t('auth.login.title')}</h2>
            <p className="text-secondary-600 mt-2">{t('auth.login.subtitle')}</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" aria-label={t('auth.login.formLabel')}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.login.emailLabel')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-secondary-400" aria-hidden="true" />
                </div>
                <input
                  {...register('email', {
                    required: t('auth.errors.emailRequired'),
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: t('auth.errors.invalidEmail'),
                    },
                  })}
                  id="email"
                  type="email"
                  autoComplete="email"
                  className="pl-10 input-field"
                  placeholder={t('auth.login.emailPlaceholder')}
                  aria-required="true"
                  aria-invalid={errors.email ? 'true' : 'false'}
                  aria-describedby={errors.email ? 'email-error' : undefined}
                />
              </div>
              {errors.email && (
                <p id="email-error" role="alert" className="mt-1 text-sm text-red-600" aria-live="polite">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.login.passwordLabel')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-secondary-400" aria-hidden="true" />
                </div>
                <input
                  {...register('password', {
                    required: t('auth.errors.passwordRequired'),
                    minLength: {
                      value: 6,
                      message: t('auth.errors.passwordMinLength'),
                    },
                  })}
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  className="pl-10 input-field"
                  placeholder={t('auth.login.passwordPlaceholder')}
                  aria-required="true"
                  aria-invalid={errors.password ? 'true' : 'false'}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
              </div>
              {errors.password && (
                <p id="password-error" role="alert" className="mt-1 text-sm text-red-600" aria-live="polite">{errors.password.message}</p>
              )}
            </div>

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
                <a href="#" className="font-medium text-primary-600 hover:text-primary-500" aria-label={t('auth.login.forgotPasswordAriaLabel')}>
                  {t('auth.login.forgotPassword')}
                </a>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary py-3 flex items-center justify-center"
              aria-label={t('auth.login.signInAriaLabel')}
              aria-busy={isLoading}
              aria-disabled={isLoading}
            >
              {isLoading ? (
                <LoadingSpinner size="small" />
              ) : (
                <>
                  <LogIn className="w-5 h-5 mr-2" aria-hidden="true" />
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
  </div>
  );
};