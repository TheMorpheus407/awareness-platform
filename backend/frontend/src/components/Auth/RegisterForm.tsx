import React from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, Building, UserPlus } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import type { RegisterCredentials } from '../../types';
import { LoadingSpinner } from '../Common';
import { useTranslation } from 'react-i18next';

export const RegisterForm: React.FC = () => {
  const navigate = useNavigate();
  const { register: registerUser, isLoading } = useAuth();
  const { t } = useTranslation();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterCredentials & { confirmPassword: string }>();

  const password = watch('password');

  const onSubmit = async (data: RegisterCredentials & { confirmPassword: string }) => {
    try {
      const { confirmPassword, ...registerData } = data;
      await registerUser(registerData);
      navigate('/dashboard');
    } catch (error) {
      // Error is handled in the store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <UserPlus className="w-8 h-8 text-primary-600" />
            </div>
            <h2 className="text-3xl font-bold text-secondary-900">{t('auth.register.title')}</h2>
            <p className="text-secondary-600 mt-2">{t('auth.register.subtitle')}</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.register.fullNameLabel')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-secondary-400" />
                </div>
                <input
                  {...register('full_name', {
                    required: t('auth.errors.nameRequired'),
                    minLength: {
                      value: 2,
                      message: t('auth.errors.nameMinLength'),
                    },
                  })}
                  type="text"
                  autoComplete="name"
                  className="pl-10 input-field"
                  placeholder={t('auth.register.fullNamePlaceholder')}
                />
              </div>
              {errors.full_name && (
                <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.register.emailLabel')}
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
                  placeholder={t('auth.register.emailPlaceholder')}
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="company_name" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.register.companyNameLabel')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building className="h-5 w-5 text-secondary-400" />
                </div>
                <input
                  {...register('company_name')}
                  type="text"
                  autoComplete="organization"
                  className="pl-10 input-field"
                  placeholder={t('auth.register.companyNamePlaceholder')}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.register.passwordLabel')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-secondary-400" />
                </div>
                <input
                  {...register('password', {
                    required: t('auth.errors.passwordRequired'),
                    minLength: {
                      value: 8,
                      message: t('auth.errors.passwordMinLength8'),
                    },
                    pattern: {
                      value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                      message: t('auth.errors.passwordPattern'),
                    },
                  })}
                  type="password"
                  autoComplete="new-password"
                  className="pl-10 input-field"
                  placeholder={t('auth.register.passwordPlaceholder')}
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-secondary-700 mb-2">
                {t('auth.register.confirmPasswordLabel')}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-secondary-400" />
                </div>
                <input
                  {...register('confirmPassword', {
                    required: t('auth.errors.confirmPasswordRequired'),
                    validate: (value) => value === password || t('auth.errors.passwordMismatch'),
                  })}
                  type="password"
                  autoComplete="new-password"
                  className="pl-10 input-field"
                  placeholder={t('auth.register.confirmPasswordPlaceholder')}
                />
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
              )}
            </div>

            <div className="flex items-center">
              <input
                id="agree-terms"
                name="agree-terms"
                type="checkbox"
                required
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
              />
              <label htmlFor="agree-terms" className="ml-2 block text-sm text-secondary-700">
                {t('auth.terms.agree')}{' '}
                <a href="#" className="text-primary-600 hover:text-primary-500">
                  {t('auth.terms.termsAndConditions')}
                </a>{' '}
                {t('auth.terms.and')}{' '}
                <a href="#" className="text-primary-600 hover:text-primary-500">
                  {t('auth.terms.privacyPolicy')}
                </a>
              </label>
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
                  <UserPlus className="w-5 h-5 mr-2" />
                  {t('auth.register.createAccount')}
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-secondary-600">
              {t('auth.register.hasAccount')}{' '}
              <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
                {t('auth.register.signIn')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};